"""Lists the Gemini models your GOOGLE_API_KEY can actually use.

Previously this used `google.generativeai`, a package Google has fully retired —
importing it printed a FutureWarning and it was the only reason that dependency
existed. It now calls the same REST diagnostic the Streamlit sidebar uses, so
there is one implementation of "is this key OK?" instead of two.
"""

import sys

from dotenv import load_dotenv

from logic import get_owner_api_key, verify_api_key

load_dotenv()

api_key = get_owner_api_key()
if not api_key:
    print("❌ GOOGLE_API_KEY is not set. Add it to your .env file.")
    sys.exit(1)

print("🔍 Checking which models this API key can use...")
print("-" * 52)

ok, message, models = verify_api_key(api_key)
# The message carries Markdown emphasis for the Streamlit sidebar; strip it
# so a terminal doesn't show literal **asterisks**.
message = message.replace("**", "")

if not ok:
    print(f"❌ {message}")
    sys.exit(1)

for name in models:
    print(f"✅ {name}")

print("-" * 52)
print(f"✨ {message}")
print("👉 Set LLM_MODEL in .env to one of the names above.")
