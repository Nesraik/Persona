from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
import shutil
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

BASE_UPLOAD_DIR = 'INPUT_DIR'

@app.post("/chat")
async def chat_endpoint(
    user_prompt: str = Form(...),
    messages: str = Form(...),
    flag: bool = Form(False),
    files: List[UploadFile] = File([]),
    session_id: str = Form(None)
):
    """
    API endpoint to handle chat messages.
    """
    try:
        try:
            parsed_messages = json.loads(messages)
        except json.JSONDecodeError:
            return JSONResponse(status_code=400, content={"error": "Invalid JSON format for 'messages'"})

        saved_file_paths = []

        if not os.path.exists(BASE_UPLOAD_DIR):
            os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
        
        for file in files:
            if file.content_type != "application/pdf":
                pass 
            
            file_path = os.path.join(BASE_UPLOAD_DIR, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            saved_file_paths.append(file_path)
        
        response_messages, response_flag = chatbot.generate_single_chat_message(
            user_prompt=user_prompt,
            messages=parsed_messages,
            flag=flag,
            files=saved_file_paths,
            session_id=session_id
        )
        shutil.rmtree("INPUT_DIR", ignore_errors=True)
        
        return {"messages": response_messages, "flag": response_flag}

    except Exception as e:
        shutil.rmtree("INPUT_DIR", ignore_errors=True)
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})