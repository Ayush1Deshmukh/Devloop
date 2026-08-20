import sys
import os

from dotenv import load_dotenv

print("--- 🔍 DIAGNOSTIC START ---")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✅ Library: langchain_google_genai is installed.")
except ImportError:
    print("❌ CRITICAL: Library 'langchain_google_genai' is MISSING.")
    sys.exit(1)

# Key is read from the environment / .env — never hardcode secrets in source.
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ CRITICAL: GOOGLE_API_KEY is not set. Add it to your .env file.")
    sys.exit(1)

# Models to test. The gemini-1.5-* family is retired — probing it only ever
# produced 404s, which made this script look like the key was broken.
models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.0-flash-lite"]

print(f"--- Testing {len(models)} Models ---")

for m in models:
    print(f"\n👉 Testing Model: {m}")
    try:
        llm = ChatGoogleGenerativeAI(model=m, google_api_key=os.environ["GOOGLE_API_KEY"])
        res = llm.invoke("Reply with 'WORKING'")
        print(f"🎉 SUCCESS! The working model name is: {m}")
        print(f"🤖 Response: {res.content}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

print("\n💥 ALL MODELS FAILED.")
sys.exit(1)
