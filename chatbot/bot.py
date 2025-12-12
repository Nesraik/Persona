from available_tools import Tools
from langfuse import Langfuse, observe
from langfuse.openai import OpenAI
from rag import ContextRetriever
import json
import shutil
import os
from utils.jinjaProcessor import *
import requests
from dotenv import load_dotenv
load_dotenv(override=True)
langfuse = Langfuse()

class Chatbot(Tools):
    def __init__(self):
        super().__init__()
        self.tools = json.loads(process_template_no_var('prompts/tool_desc.jinja'))
        self.client = OpenAI(
            base_url=os.environ.get("GEMINI_BASE_URL"),
            api_key= os.environ.get("GEMINI_API_KEY")
        )
        self.functions = {
            "search_google": self.search_google,
            "open_webpage": self.open_webpage,
            "get_current_date_and_time": self.get_current_date_and_time,
            "search_youtube_video": self.search_youtube_video
        }
        
    @observe(name = "bot_response")
    def _generate_response(self,messages):
        response = self.client.chat.completions.create(
            model = "gemini-2.5-flash",
            messages = messages,
            tools= self.tools,
            temperature=0.1,
            top_p=0.1,
            reasoning_effort = "none"
        )
        return response.choices[0].message

    def generate_single_chat_message(self,user_prompt,messages,flag, files, session_id):
        try:
            if os.listdir("vectordb") != [] or files:
                self.Retriever = ContextRetriever(files=files, session_id=session_id)
                context = self.Retriever.retrieveContext(user_message=user_prompt,chat_history=messages)
        except:
            context = None
         
        temp = {
            "tools": self.tools,
            "context": context if context else "No additional context provided."
        }

        system_prompt = process_template('prompts/system_prompt.jinja', temp)

        if flag == False:
            try:
                shutil.rmtree("vectordb")
            except:
                pass
            os.makedirs("vectordb", exist_ok=True)

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
            flag = True
        else:
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            messages[0]['content'] = system_prompt

        while True:
            response = self._generate_response(messages)
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls if response.tool_calls is not None else []
            })

            if response.tool_calls is None:
                break
            
            for tool in response.tool_calls:

                if tool is None:
                    continue

                # Check for function name
                try:
                    function_name = self.functions[tool.function.name]
                except:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": "N/A",
                        "content": "Function not found in tools_dict"
                    })

                    continue

                function_args = json.loads(tool.function.arguments)

                # Check for function arguments
                try:    
                    function_output = function_name(**function_args)
                    content = json.dumps(function_output, indent=4)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": tool.function.name,
                        "content": content
                    })  

                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": tool.function.name,
                        "content": f"Error: {str(e)} calling {function_name.__name__} with args {function_args}"
                    })

        return messages, flag
    
    def run_conversation(self):
        messages = []
        flag = False

        count = 0
        while True:
            
            # Delete this for production
            tester_message = input("Tester Message: ")
            if tester_message.strip().lower() == 'exit':
                print("Exiting the chatbot.")
                break
                
            messages, flag = self.generate_single_chat_message(tester_message, messages,flag)

            count += 1
