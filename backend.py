from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai.types import Content, Part, GenerateContentConfig, ThinkingConfig
import uuid
import os


app = FastAPI()
api_key=os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Session-based history store (in-memory for demo)
sessions = {}

class StartSessionResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/", response_model=StartSessionResponse)
def start_chat():
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id}

@app.post("/chatbot")
def chat_bot(request: ChatRequest):
    try:
        if request.session_id not in sessions:
            return {"error": "Invalid session_id"}

        # Append user input
        user_input = Content(role="user", parts=[Part(text=request.message)])
        sessions[request.session_id].append(user_input)

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=sessions[request.session_id],
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                system_instruction=(
                    "You are a motivational speaker, act like one but just make you act like A VERY RUDE one. "
                    "If they say they feel anxious, motivate them using degradation and insults."
                    "Dont talk about anything else rather than motivational stuff. If they ask anything else say something like"
                    "Dhat teri maa ki choot"
                )
            )
        )

        # Extract reply
        bot_text = response.candidates[0].content.parts[0].text.strip()
        sessions[request.session_id].append(Content(role="model", parts=[Part(text=bot_text)]))

        return {"response": bot_text}

    except Exception as e:
        print("Exception caught in /chatbot:", str(e))
        return {"error": str(e)}
