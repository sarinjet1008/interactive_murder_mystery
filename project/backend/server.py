#!/usr/bin/env python3
"""
FastAPI backend for the Interactive Murder Mystery game.
Converts the Node.js Express server to Python with enhanced LLM integration.
"""

import os
import json
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_MS = 1000
MAX_BACKOFF_MS = 10000
REQUEST_TIMEOUT_MS = 30000

app = FastAPI(
    title="Murder Mystery Backend",
    description="FastAPI backend for interactive murder mystery game",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate API key on startup
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    logger.error("❌ OPENAI_API_KEY not found or still contains placeholder value")
    logger.error("Please update your .env file with a valid OpenAI API key")
    logger.error("Get your API key from: https://platform.openai.com/api-keys")
    raise ValueError("OPENAI_API_KEY not properly configured")

logger.info("✅ OpenAI API key loaded successfully")

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=openai_api_key,
    timeout=REQUEST_TIMEOUT_MS / 1000,  # Convert to seconds
)

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    suspect: str
    question: str

class QuestionResponse(BaseModel):
    response: str

class ClueResponse(BaseModel):
    clue: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    openai_configured: bool
    server_version: str
    retry_config: Dict[str, int]
    openai_test: Optional[str] = None
    openai_response: Optional[str] = None
    openai_error: Optional[str] = None

# Helper functions
def get_base_dir() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def capitalize_first_letter(string: str) -> str:
    """Capitalize the first letter of a string."""
    return string.capitalize() if string else ""

def load_prompt_template() -> str:
    """Load the interrogation prompt template."""
    prompt_path = get_base_dir() / "src" / "data" / "prompts" / "interrogation_prompt.txt"
    if not prompt_path.exists():
        logger.error(f"❌ Prompt template not found at: {prompt_path}")
        raise FileNotFoundError("Prompt template file not found")
    return prompt_path.read_text(encoding="utf-8")

def load_suspect_data(name: str) -> Dict[str, Any]:
    """Load suspect data from JSON file."""
    suspect_path = get_base_dir() / "src" / "data" / "suspects" / f"{name.lower()}.json"
    if suspect_path.exists():
        try:
            return json.loads(suspect_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            logger.error(f"❌ Error parsing suspect data for {name}: {error}")
            return {}
    logger.warning(f"⚠️ Suspect data not found for: {name}")
    return {}

def load_clue_data(day: int, suspect: str) -> str:
    """Load clue data for a specific day and suspect."""
    base_dir = get_base_dir()
    
    # Try both day 1 and day1 format
    day_formats = [f"day{day}", f"day {day}"]
    
    for day_format in day_formats:
        clue_dir = base_dir / "src" / "data" / "clues" / day_format
        
        # Check if the directory exists
        if not clue_dir.exists():
            logger.info(f"📁 Directory not found: {clue_dir}")
            continue
        
        try:
            # Read all files in the directory
            files = list(clue_dir.iterdir())
            logger.info(f"📂 Found files in {day_format}: {[f.name for f in files]}")
            
            # Look for files that start with the suspect name (case-insensitive)
            suspect_lower = suspect.lower()
            matching_files = [
                f for f in files 
                if f.name.lower().startswith(suspect_lower) 
                and f.suffix.lower() in ['.json', '.txt']
            ]
            
            logger.info(f"🔍 Matching files for {suspect}: {[f.name for f in matching_files]}")
            
            if matching_files:
                # Use the first matching file
                file_path = matching_files[0]
                
                try:
                    if file_path.suffix.lower() == '.json':
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        clue_text = data.get('clue') or data.get('text') or data.get('content') or 'No clue text found in JSON'
                        logger.info(f"✅ Loaded JSON clue for {suspect}: {clue_text}")
                        return f"🧩 Clue about {capitalize_first_letter(suspect)}: {clue_text}"
                    else:  # .txt file
                        clue = file_path.read_text(encoding="utf-8").strip()
                        logger.info(f"✅ Loaded TXT clue for {suspect}: {clue}")
                        return f"🧩 Clue about {capitalize_first_letter(suspect)}: {clue}"
                except Exception as error:
                    logger.error(f"❌ Error reading clue file {file_path}: {error}")
        except Exception as error:
            logger.error(f"❌ Error reading directory {clue_dir}: {error}")
    
    logger.info(f"⚠️ No clue files found for {suspect} on day {day}")
    return f"No new clues for {capitalize_first_letter(suspect)} today."

# Enhanced retry mechanism with exponential backoff
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=INITIAL_BACKOFF_MS/1000, max=MAX_BACKOFF_MS/1000),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=before_sleep_log(logger, logging.INFO)
)
async def call_openai_with_retry(messages: list, temperature: float = 0.7) -> str:
    """Call OpenAI API with retry mechanism and detailed error handling."""
    try:
        logger.info("🤖 Sending request to OpenAI...")
        
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
        )
        
        logger.info("✅ OpenAI request successful")
        return completion.choices[0].message.content.strip()
        
    except Exception as error:
        logger.error(f"❌ OpenAI request failed: {error}")
        
        # Check for specific error types
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid OpenAI API key")
            elif error.status_code == 429:
                raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded")
            elif error.status_code == 402:
                raise HTTPException(status_code=402, detail="OpenAI API quota exceeded")
        
        # Re-raise for retry mechanism
        raise

# API Endpoints

@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question to a suspect and get AI-generated response."""
    logger.info(f"📝 Received question for {request.suspect}: {request.question}")

    if not request.suspect or not request.question:
        raise HTTPException(status_code=400, detail="Missing suspect or question")

    try:
        prompt_template = load_prompt_template()
        data = load_suspect_data(request.suspect)

        backstory = data.get('backstory', '')
        timeline = data.get('timeline', {})
        relationship = data.get('relationship_to_victim', 'Unknown relationship')
        tone = data.get('tone', 'neutral')

        # Fill the prompt template
        filled_prompt = prompt_template.replace('{name}', capitalize_first_letter(request.suspect))
        filled_prompt = filled_prompt.replace('{question}', request.question)
        filled_prompt = filled_prompt.replace('{tone}', tone)
        filled_prompt = filled_prompt.replace('{backstory}', backstory)
        filled_prompt = filled_prompt.replace('{time_range}', timeline.get('time_range', ''))
        filled_prompt = filled_prompt.replace('{location}', timeline.get('claimed_location') or timeline.get('location', ''))
        filled_prompt = filled_prompt.replace('{relationship_to_victim}', relationship)

        system_message = {
            "role": "system",
            "content": "You are a detective AI assistant. Your task is to help generate responses for a character in a murder mystery interrogation."
        }
        user_message = {
            "role": "user",
            "content": filled_prompt
        }

        # Use the retry mechanism for the OpenAI API call
        response = await call_openai_with_retry([system_message, user_message], 0.7)
        logger.info(f"✅ Generated response for {request.suspect}")

        return QuestionResponse(response=response)

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"❌ Error generating response: {error}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(error)}")

@app.get("/api/clue", response_model=ClueResponse)
async def get_clue(day: int, suspect: str):
    """Load clue for a specific day and suspect."""
    logger.info(f"🔍 Loading clue for day {day}, suspect: {suspect}")

    if day is None or not suspect:
        raise HTTPException(status_code=400, detail="Missing or invalid day or suspect parameter")

    try:
        clue = load_clue_data(day, suspect)
        logger.info(f"✅ Loaded clue for {suspect}: {clue}")
        return ClueResponse(clue=clue)
    except Exception as error:
        logger.error(f"❌ Error loading clue: {error}")
        raise HTTPException(status_code=500, detail=f"Error loading clue: {str(error)}")

@app.get("/health", response_model=HealthResponse)
async def health_check(test_openai: bool = False):
    """Health check endpoint with optional OpenAI connection test."""
    health_data = HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        openai_configured=bool(openai_api_key and openai_api_key != "your_openai_api_key_here"),
        server_version="2.0.0",
        retry_config={
            "max_retries": MAX_RETRIES,
            "initial_backoff_ms": INITIAL_BACKOFF_MS,
            "max_backoff_ms": MAX_BACKOFF_MS,
            "request_timeout_ms": REQUEST_TIMEOUT_MS
        }
    )

    # Optional: Test OpenAI connection if requested
    if test_openai and health_data.openai_configured:
        try:
            logger.info("🔍 Testing OpenAI connection...")
            response = await call_openai_with_retry([
                {"role": "user", "content": "Say 'OK' if you can hear me."}
            ], 0)
            health_data.openai_test = "success"
            health_data.openai_response = response
            logger.info("✅ OpenAI connection test successful")
        except Exception as error:
            logger.error(f"❌ OpenAI connection test failed: {error}")
            health_data.openai_test = "failed"
            health_data.openai_error = str(error)

    return health_data

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("🚀 Python FastAPI server starting up...")
    logger.info(f"📡 Health check available at http://localhost:5000/health")
    logger.info(f"🔑 OpenAI API key: {'Configured' if openai_api_key and openai_api_key != 'your_openai_api_key_here' else 'Missing or Invalid'}")
    logger.info(f"🔄 Retry mechanism: {MAX_RETRIES} attempts with exponential backoff")
    logger.info(f"⏱️  Request timeout: {REQUEST_TIMEOUT_MS}ms")
    
    if not openai_api_key or openai_api_key == "your_openai_api_key_here":
        logger.warning("⚠️  WARNING: OpenAI API key is not properly configured!")
        logger.warning("   Please update your .env file with a valid API key from:")
        logger.warning("   https://platform.openai.com/api-keys")
    else:
        logger.info("💡 Tip: Test OpenAI connection with: curl \"http://localhost:5000/health?test_openai=true\"")

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )