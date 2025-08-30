from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from google import genai
from google.genai.types import Content, Part, GenerateContentConfig, ThinkingConfig
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

app = FastAPI()
api_key=os.getenv("GEMINI_API_KEY")

if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable is not set!")
    print("Please set GEMINI_API_KEY with your Gemini API key")
    client = None
else:
    client = genai.Client(api_key=api_key)

# Session-based history store
sessions = {}

# Authentication
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=360

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_user={
    "allkeeey":{
        "username": "theallkeeeymist",
        "hashed_password": pwd_context.hash("Sudhanshu12345")
    }
}

class StartSessionResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_user.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode=data.copy()
    expire=datetime.utcnow()+(expires_delta or timedelta(minutes=120))
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str=Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user=fake_user.get(username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends()):
    user=authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400 , detail="Incorrect username or password")
    access_token=create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/", response_model=StartSessionResponse)
def start_chat():
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id}

@app.post("/chatbot")
def chat_bot(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        if not client:
            return {"error": "Gemini API client not initialized. Please set GEMINI_API_KEY environment variable."}
            
        if request.session_id not in sessions:
            return {"error": "Invalid session_id"}

        # Append user input
        user_input = Content(role="user", parts=[Part(text=request.message)])
        sessions[request.session_id].append(user_input)

        if len(sessions[request.session_id])>2:
            history = sessions[request.session_id][-2:]
        else:
            history=sessions[request.session_id]

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                system_instruction=(
                    "You are a highly experienced Data Science interviewer in 2025. "
                    "You ask realistic, challenging questions on statistics, probability, machine learning, "
                    "SQL, data preprocessing, model evaluation, MLOps, and current AI trends like LLMs, RAG, and vector databases. "
                    "Ask one question at a time, alternating between theory, coding, and case studies. "
                    "If the candidate’s answer is incomplete or wrong, ask a follow-up question before explaining the correct answer in detail. "
                    "Occasionally ask about cutting-edge industry developments to test adaptability. "
                    "Keep a professional but challenging tone."
                ),
                temperature=1.5,
                max_output_tokens=60000,
            )
        )

        # Extract reply with proper null checks
        if (response and response.candidates and 
            response.candidates[0] and 
            response.candidates[0].content and 
            response.candidates[0].content.parts and 
            response.candidates[0].content.parts[0]):
            
            part = response.candidates[0].content.parts[0]
            if part and part.text:
                bot_text = part.text.strip()
                sessions[request.session_id].append(Content(role="model", parts=[Part(text=bot_text)]))
                return {"response": bot_text}
            else:
                return {"error": "Invalid response format from AI model"}
        else:
            return {"error": "Failed to generate response from AI model"}

    except Exception as e:
        print("Exception caught in /chatbot:", str(e))
        return {"error": str(e)}
