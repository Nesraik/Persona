from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
from bot import Chatbot

app = FastAPI()
chatbot = Chatbot()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

class BotRequest(BaseModel):
    user_prompt: str
    messages: List[Dict[str, Any]]
    flag: bool = False

@app.post("/chat")
async def chat_endpoint(request: BotRequest):
    """
    API endpoint to handle chat messages.
    """
    try:
        messages, flag = chatbot.generate_single_chat_message(
            user_prompt=request.user_prompt,
            messages=request.messages,
            flag=request.flag
        )
        return {"messages": messages, "flag": flag}
    
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Check file type
    if file.content_type != "application/pdf":
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    # Read the file content (if needed)
    contents = await file.read()

    with open(f"chatbot/input_files/uploaded_{file.filename}", "wb") as f:
        f.write(contents)

    return {"filename": file.filename, "content_type": file.content_type}