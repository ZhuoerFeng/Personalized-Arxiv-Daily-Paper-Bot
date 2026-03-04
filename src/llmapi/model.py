import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
# import openai
# print(openai.__version__)

class GateWays:
    def __init__(self, model_name):
        self.model = model_name
        self.api_url = 
        self.api_key = 
        self.client = OpenAI(base_url=self.api_url, api_key=self.api_key)
        

    def get_api_result(self, messages:list, tools: list = None, temperature: float = 1.0, max_completion_tokens: int = 5000):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            timeout=240
        )
        # print(response)
        # return response.choices[0].message
        return response
    


if __name__ == '__main__':
    gateway = GateWays(model_name="gemini-2.5-pro")
    test_messages = [
        {"role": "user", "content": "你好。"}
    ]
    
    result = gateway.get_api_result(messages=test_messages, temperature=0.1).choices[0].message.content
    print(result)   

