import os
import re

from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from unicodedata import category

api_key=os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"]=api_key
PINECONE_API_KEY="pcsk_6eGeyp_2GFpNjLN82RXDmZMttrH3Q6RkihuYi4WyeBRXfQxUJfPC5wWJWnzQTkBvavWMpw"

# Connect to pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name="ds-interview-question"
if index_name not in [i.name for i in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index=pc.Index(index_name)

# Load dataset
with open("ds_questions.txt", "r", encoding="utf-8") as f:
    raw_text=f.read()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs=splitter.create_documents([raw_text])

# Embed chunks
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Store in Pinecone
vectors=[]
for i, doc in enumerate(docs):
    # Extract category & difficulty from text
    category_match=re.search(r"\[Category:\s*(.*?)\]", doc.page_content)
    difficulty_match=re.search(r"\[Difficulty:\s*(.*?)\]", doc.page_content)

    category=category_match.group(1) if category_match else "Unknown"
    difficulty=difficulty_match.group(1) if difficulty_match else "Unknown"

    vec=embeddings.embed_query(doc.page_content)
    vectors.append((
        str(i),
        vec,
        {
            "text": doc.page_content,
            "category": category,
            "difficulty": difficulty
        }
    ))

index.upsert(vectors)
print("Data stored into Pinecone!")