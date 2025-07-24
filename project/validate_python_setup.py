#!/usr/bin/env python3
"""
Validation script to check if Python backend setup is correct.
Run this script to verify all dependencies are installed and configured properly.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking required dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'pydantic',
        'tenacity',
        'python_dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: source venv/bin/activate && pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\n🔐 Checking environment configuration...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found")
        print("💡 Create .env file with OPENAI_API_KEY=your_key_here")
        return False
    
    print("✅ .env file exists")
    
    # Check if OPENAI_API_KEY is set (don't print the actual key)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("❌ OPENAI_API_KEY not found in .env file")
            return False
        elif api_key == 'your_openai_api_key_here':
            print("❌ OPENAI_API_KEY contains placeholder value")
            print("💡 Update .env file with your actual OpenAI API key")
            return False
        else:
            print("✅ OPENAI_API_KEY is configured")
            return True
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_data_files():
    """Check if required data files exist."""
    print("\n📁 Checking required data files...")
    
    required_paths = [
        'src/data/prompts/interrogation_prompt.txt',
        'src/data/suspects/',
        'src/data/clues/'
    ]
    
    missing_files = []
    
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"✅ {path_str}")
        else:
            print(f"❌ {path_str} - Not found")
            missing_files.append(path_str)
    
    if missing_files:
        print(f"\n⚠️  Missing data files: {', '.join(missing_files)}")
        print("💡 Make sure your game data files are in the correct locations")
        return False
    
    print("✅ All required data files are present")
    return True

def test_server_import():
    """Test if the server module can be imported."""
    print("\n🚀 Testing server module import...")
    
    try:
        sys.path.append('backend')
        import server
        print("✅ Backend server module imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing server module: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Validating Python backend setup for Murder Mystery game\n")
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_data_files(),
        test_server_import()
    ]
    
    print("\n" + "="*50)
    
    if all(checks):
        print("🎉 All checks passed! Python backend is ready to use.")
        print("\n🚀 To start the backend:")
        print("   npm run backend-python-dev")
        print("   or")
        print("   source venv/bin/activate && cd backend && python server.py")
        print("\n📖 See MIGRATION_GUIDE.md for more information")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n💡 Run ./setup_python_backend.sh to fix common issues")
        return 1

if __name__ == "__main__":
    exit(main())