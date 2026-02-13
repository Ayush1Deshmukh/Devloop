import sys
import os

print("--- 🔍 STARTING DIAGNOSTIC ---")

# 1. Check Library
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    import langchain_google_genai
    print(f"✅ Library Installed: version {getattr(langchain_google_genai, '__version__', 'unknown')}")
except ImportError:
    print("❌ CRITICAL: langchain-google-genai library is MISSING.")
    sys.exit(1)

# 2. Define Credentials
API_KEY = "AIzaSyCd-rE-SHyHWOIckT8AZnCzABqAdkRqGgg"

# 3. Try Connection with multiple model aliases
models_to_test = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro", "gemini-1.5-pro-latest"]

for model_name in models_to_test:
    print(f"\n🧪 Testing Model: '{model_name}'...")
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=API_KEY)
        response = llm.invoke("Hello, strictly reply with 'WORKING'.")
        print(f"🎉 SUCCESS! The model '{model_name}' is working.")
        print(f"🤖 AI Said: {response.content}")
        print(f"\n👉 ACTION REQUIRED: Update your config.py to use: LLM_MODEL='{model_name}'")
        sys.exit(0) # Stop at the first working model
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"⚠️  Model not found (404). This alias is invalid for your library version.")
        elif "429" in error_msg:
            print(f"⚠️  Quota Exceeded (429).")
        else:
            print(f"❌ Error: {error_msg}")

print("\n💥 DIAGNOSTIC FAILED: No models worked.")