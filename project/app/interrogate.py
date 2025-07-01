import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def load_prompt_template():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "data", "prompts", "interrogation_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def load_story_context(name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "story", f"{name.lower().replace(' ', '_')}.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def load_suspect_data(name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "suspects", f"{name.lower()}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def ask_question(suspect_name: str, question: str) -> str:
    try:
        # Load the template
        prompt_template = load_prompt_template()
        
        # Load the suspect data
        data = load_suspect_data(suspect_name)
        
        # Extract relevant information
        backstory = data.get("backstory", "")
        timeline = data.get("timeline", {})
        relationship = data.get("relationship_to_victim", "Unknown relationship")
        tone = data.get("tone", "neutral")
        
        # Format the prompt
        filled_prompt = prompt_template.format(
            name=suspect_name,
            question=question,
            tone=tone,
            backstory=backstory,
            time_range=timeline.get("time_range", ""),
            location=timeline.get("location", ""),
            relationship_to_victim=relationship
        )
        
        # Create messages
        system_message = {
            "role": "system",
            "content": "You are a detective AI assistant. Your task is to help generate responses for a character in a murder mystery interrogation."
        }
        user_message = {
            "role": "user",
            "content": filled_prompt
        }
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                system_message,
                user_message
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"(Error generating response: {str(e)})"
