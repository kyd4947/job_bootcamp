import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 사용 가능한 모든 모델 출력
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"모델 이름: {m.name}")