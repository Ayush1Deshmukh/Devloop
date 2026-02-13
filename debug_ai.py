import sys
import os

print("--- 🔍 DIAGNOSTIC START ---")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✅ Library: langchain_google_genai is installed.")
except ImportError:
    print("❌ CRITICAL: Library 'langchain_google_genai' is MISSING.")
    sys.exit(1)

# Your Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCd-rE-SHyHWOIckT8AZnCzABqAdkRqGgg"

# Models to test
models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-flash-latest"]

print(f"--- Testing {len(models)} Models ---")

for m in models:
    print(f"\n👉 Testing Model: {m}")
    try:
        llm = ChatGoogleGenerativeAI(model=m)
        res = llm.invoke("Reply with 'WORKING'")
        print(f"🎉 SUCCESS! The working model name is: {m}")
        print(f"🤖 Response: {res.content}")
        sys.exit(0) 
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

print("\n💥 ALL MODELS FAILED.")
