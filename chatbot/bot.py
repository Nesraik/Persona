from available_tools import Tools
from langfuse import Langfuse
from langfuse.openai import OpenAI
from langfuse.decorators import observe
import json
from utils.jinjaProcessor import *
import requests
from dotenv import load_dotenv
load_dotenv(override=True)
langfuse = Langfuse()

class Chatbot(Tools):
    def __init__(self):
        super().__init__()
        self.api_keys = []
        self.current_index = 0
        self._insert_api_key()
        self.tools = json.loads(process_template_no_var('prompts/tool_desc.jinja'))
        self.functions = {
            "search_google": self.search_google,
            "open_webpage": self.open_webpage,
            "get_current_date_and_time": self.get_current_date_and_time,
            "search_youtube_video": self.search_youtube_video
        }
           
    def _insert_api_key(self):
        with open("llm_api_keys.txt") as f:
            for line in f.readlines():
                self.api_keys.append(line.strip())

    def _get_client(self):
        return OpenAI(
            base_url=os.environ.get("CHATBOT_BASE_URL"),
            api_key= self.api_keys[self.current_index]
        )
    
    @observe(name = "bot_response")
    def _generate_response(self,messages):
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model = os.environ.get("CHATBOT_MODEL"),
                messages = messages,
                tools= self.tools,
                temperature=0.1,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
            )
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                self.current_index = (self.current_index + 1) % len(self.api_keys)
                client = self._get_client()
                response = client.chat.completions.create(
                    model = os.environ.get("CHATBOT_MODEL"),
                    messages = messages,
                    tools= self.tools,
                    temperature=0.1,
                    top_p=0.1,
                    presence_penalty=0.0,
                    frequency_penalty=0.0,
                )
        return response.choices[0].message

    def generate_single_chat_message(self,user_prompt,messages,flag):

        #context = self.Retriever.retrieveContext(user_message=user_prompt,chat_history=messages)

        temp = {
            "tools": self.tools,
            #"context": context
        }

        system_prompt = process_template('prompts/system_prompt.jinja', temp)

        if flag == False:
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
                "content": response.content
            })

            if response.tool_calls is None:
                break
            
            for tool in response.tool_calls:

                if tool is None:
                    continue

                # Check for function name
                try:
                    print("Tool Function Name:", tool.function.name)
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
