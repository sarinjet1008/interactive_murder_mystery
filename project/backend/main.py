import os
import sys
import time
import json
import glob
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

# Load environment variables from .env in project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
    print("❌ OPENAI_API_KEY not found or still contains placeholder value", file=sys.stderr)
    print("Please update your .env file with a valid OpenAI API key", file=sys.stderr)
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

# Retry config
MAX_RETRIES = 3
INITIAL_BACKOFF_MS = 1000
MAX_BACKOFF_MS = 10000
REQUEST_TIMEOUT = 30  # seconds

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: Capitalize first letter
def capitalize_first_letter(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s

# Helper: Load prompt template
def load_prompt_template() -> str:
    prompt_path = BASE_DIR / "src" / "data" / "prompts" / "interrogation_prompt.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found at: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")

# Helper: Load suspect data
def load_suspect_data(name: str) -> dict:
    suspect_path = BASE_DIR / "src" / "data" / "suspects" / f"{name.lower()}.json"
    if suspect_path.exists():
        try:
            return json.loads(suspect_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Error parsing suspect data for {name}: {e}", file=sys.stderr)
            return {}
    print(f"⚠️ Suspect data not found for: {name}", file=sys.stderr)
    return {}

# Helper: Load clue data
def load_clue_data(day: int, suspect: str) -> str:
    day_formats = [f"day{day}", f"day {day}"]
    for day_format in day_formats:
        clue_dir = BASE_DIR / "src" / "data" / "clues" / day_format
        if not clue_dir.exists():
            continue
        files = list(clue_dir.iterdir())
        suspect_lower = suspect.lower()
        matching_files = [f for f in files if f.name.lower().startswith(suspect_lower) and (f.suffix in [".json", ".txt"])]
        if matching_files:
            file = matching_files[0]
            try:
                if file.suffix == ".json":
                    data = json.loads(file.read_text(encoding="utf-8"))
                    clue_text = data.get("clue") or data.get("text") or data.get("content") or "No clue text found in JSON"
                    return f"🧩 Clue about {capitalize_first_letter(suspect)}: {clue_text}"
                else:
                    clue = file.read_text(encoding="utf-8").strip()
                    return f"🧩 Clue about {capitalize_first_letter(suspect)}: {clue}"
            except Exception as e:
                print(f"❌ Error reading clue file {file}: {e}", file=sys.stderr)
    return f"No new clues for {capitalize_first_letter(suspect)} today."

# Helper: OpenAI call with retry
def call_openai_with_retry(messages, temperature=0.7):
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"🤖 Attempt {attempt+1}/{MAX_RETRIES} - Sending request to OpenAI...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                timeout=REQUEST_TIMEOUT,
            )
            print(f"✅ OpenAI request successful on attempt {attempt+1}")
            return response
        except Exception as e:
            last_error = e
            print(f"❌ Attempt {attempt+1} failed: {e}", file=sys.stderr)
            # Check for retryable errors
            retryable = any(
                kw in str(e).lower() for kw in [
                    "timeout", "network", "connection", "econnreset", "enotfound", "econnrefused", "etimedout", "enetunreach", "ehostunreach"
                ]
            )
            if hasattr(e, "http_status") and e.http_status and e.http_status >= 500:
                retryable = True
            if not retryable:
                raise e
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Connection to OpenAI failed after {MAX_RETRIES} attempts. This may be due to network issues or OpenAI service unavailability. Please check your internet connection and try again.")
            backoff = min(INITIAL_BACKOFF_MS * (2 ** attempt), MAX_BACKOFF_MS) / 1000.0
            print(f"⏳ Waiting {backoff}s before retry...")
            time.sleep(backoff)
    raise last_error

# Request/response models
class AskRequest(BaseModel):
    suspect: str
    question: str

@app.post("/api/ask")
async def ask_endpoint(req: AskRequest):
    suspect = req.suspect
    question = req.question
    print(f"📝 Received question for {suspect}: {question}")
    if not suspect or not question:
        raise HTTPException(status_code=400, detail="Missing suspect or question")
    try:
        prompt_template = load_prompt_template()
        data = load_suspect_data(suspect)
        backstory = data.get("backstory", "")
        timeline = data.get("timeline", {})
        relationship = data.get("relationship_to_victim", "Unknown relationship")
        tone = data.get("tone", "neutral")
        filled_prompt = (
            prompt_template.replace("{name}", capitalize_first_letter(suspect))
            .replace("{question}", question)
            .replace("{tone}", tone)
            .replace("{backstory}", backstory)
            .replace("{time_range}", timeline.get("time_range", ""))
            .replace("{location}", timeline.get("claimed_location", "") or timeline.get("location", ""))
            .replace("{relationship_to_victim}", relationship)
        )
        system_message = {
            "role": "system",
            "content": "You are a detective AI assistant. Your task is to help generate responses for a character in a murder mystery interrogation.",
        }
        user_message = {"role": "user", "content": filled_prompt}
        completion = call_openai_with_retry([system_message, user_message], 0.7)
        response = completion["choices"][0]["message"]["content"].strip()
        print(f"✅ Generated response for {suspect}")
        return {"response": response}
    except Exception as e:
        print(f"❌ Error generating response: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")

@app.get("/api/clue")
async def clue_endpoint(day: int, suspect: str):
    print(f"🔍 Loading clue for day {day}, suspect: {suspect}")
    if not day or not suspect:
        raise HTTPException(status_code=400, detail="Missing or invalid day or suspect parameter")
    try:
        clue = load_clue_data(day, suspect)
        print(f"✅ Loaded clue for {suspect}: {clue}")
        return {"clue": clue}
    except Exception as e:
        print(f"❌ Error loading clue: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Error loading clue: {e}")

@app.get("/health")
async def health_endpoint(test_openai: Optional[bool] = False):
    health_data = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here"),
        "server_version": "1.2.0",
        "retry_config": {
            "max_retries": MAX_RETRIES,
            "initial_backoff_ms": INITIAL_BACKOFF_MS,
            "max_backoff_ms": MAX_BACKOFF_MS,
            "request_timeout_ms": REQUEST_TIMEOUT * 1000,
        },
    }
    if test_openai and health_data["openai_configured"]:
        try:
            print("🔍 Testing OpenAI connection...")
            test_completion = call_openai_with_retry([
                {"role": "user", "content": 'Say "OK" if you can hear me.'}
            ], 0)
            health_data["openai_test"] = "success"
            health_data["openai_response"] = test_completion["choices"][0]["message"]["content"].strip()
            print("✅ OpenAI connection test successful")
        except Exception as e:
            print(f"❌ OpenAI connection test failed: {e}", file=sys.stderr)
            health_data["openai_test"] = "failed"
            health_data["openai_error"] = str(e)
    return health_data

# To run: uvicorn main:app --host 0.0.0.0 --port 5000