from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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