from openai import OpenAI
from utils.config_setup import Config
import os
from pypdf import PdfReader
import json

Config = Config()

class LLM:
    def __init__ (
            self,
            pdf):
        
        self.api_key = Config.api_key
        self.website_url = Config.website_url
        self.prompt = Config.prompt
        self.prompt_xero = Config.xero_prompt
        self.pdf = pdf

    def extract_pdf(self, path_pdf):
        reader = PdfReader(path_pdf)
        text=""
        for page in reader.pages:
            text += page.extract_text() +"\n"
        return text
    
    def deepseek(self,text):
        client = OpenAI(api_key=self.api_key, base_url=self.website_url)
        user_input = text
        response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": self.prompt_xero},
                            {"role": "user", "content": user_input},
                        ],
                        response_format={
                            'type': 'json_object'
                        },
                        stream=False
                    )
        content = response.choices[0].message.content
        return content