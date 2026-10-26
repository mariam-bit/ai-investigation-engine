import os
import time

from google import genai
from google.genai import types, errors

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("Set GEMINI_API_KEY first:  $env:GEMINI_API_KEY=\"your-key\"")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=20000,  
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
]

print(f"{'MODEL':32} {'RESULT':10} TIME")
print("-" * 55)
for model in CANDIDATES:
    start = time.time()
    try:
        r = client.models.generate_content(model=model, contents="Reply with the single word: ok")
        result = "WORKS"
        detail = (r.text or "").strip()[:20]
    except errors.APIError as e:
        result = f"FAIL {e.code}"
        detail = ""
    except Exception as e:
        result = "FAIL"
        detail = type(e).__name__
    print(f"{model:32} {result:10} {time.time() - start:5.1f}s  {detail}")