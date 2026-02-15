import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
    exit()

genai.configure(api_key=api_key)

print(f"🔍 Checking available models for your API key...")
print("-" * 40)

try:
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ AVAILABLE: {m.name}")
            count += 1
    
    if count == 0:
        print("⚠️ No models found! Your API Key might be invalid or have no permissions.")
    else:
        print("-" * 40)
        print(f"✨ Found {count} usable models.")
        print("👉 Use one of the names above in your logic.py file.")

except Exception as e:
    print(f"❌ API Error: {e}")