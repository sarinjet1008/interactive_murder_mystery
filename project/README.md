# Interactive Murder Mystery Game 🕵️‍♀️

An immersive detective game where you interrogate AI-powered suspects to solve a yacht murder mystery. Built with React/TypeScript frontend and now supports both Node.js and Python backends.

## 🎮 Game Overview

Step into the shoes of a detective investigating a murder on a luxury yacht. Question AI-powered suspects, uncover clues, and piece together the truth. Each suspect has a unique personality, backstory, and secrets powered by OpenAI's language models.

## ✨ Features

- **AI-Powered Suspects**: Each character responds with unique personality and backstory
- **Dynamic Conversations**: Natural language interrogation with context-aware responses
- **Clue Discovery**: Unlock new evidence as you progress through the investigation
- **Multiple Suspects**: Question various characters with different motives and alibis
- **Rich Storytelling**: Immersive narrative with multiple possible outcomes

## 🚀 Quick Start

### Option 1: Node.js Backend (Original)
```bash
# Install dependencies
npm install

# Start both frontend and backend
npm start

# Or start separately
npm run backend    # Node.js server on port 5000
npm run dev        # Frontend on port 5173
```

### Option 2: Python Backend (Recommended for AI Development)
```bash
# Run automated setup
./setup_python_backend.sh

# Start both frontend and Python backend
npm run start-python

# Or start separately
npm run backend-python-dev  # Python server on port 5000
npm run dev                 # Frontend on port 5173
```

## 🐍 Python Backend Migration

The Python backend offers significant advantages for AI/LLM development:

- **Better AI Ecosystem**: Native integration with Python AI libraries
- **Type Safety**: Full type hints and validation with Pydantic
- **Enhanced Error Handling**: Robust retry mechanisms with exponential backoff
- **Auto Documentation**: Interactive API docs at `/docs`
- **Future-Ready**: Easy integration with advanced AI features

### Migration Steps

1. **Setup Python Environment**:
   ```bash
   ./setup_python_backend.sh
   ```

2. **Validate Installation**:
   ```bash
   python3 validate_python_setup.py
   ```

3. **Test Python Backend**:
   ```bash
   npm run backend-python-dev
   ```

4. **Switch to Python**:
   ```bash
   npm run start-python
   ```

For detailed migration instructions, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## 🛠️ Setup Requirements

### System Requirements
- Node.js 18+ (for frontend)
- Python 3.8+ (for Python backend option)
- OpenAI API key

### Environment Setup

1. **Get OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key for the next step

2. **Configure Environment**:
   ```bash
   # Create .env file in project root
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

3. **Install Dependencies**:
   ```bash
   # Frontend dependencies
   npm install
   
   # Python backend dependencies (if using Python)
   ./setup_python_backend.sh
   ```

## 📁 Project Structure

```
project/
├── src/                    # React frontend
│   ├── components/        # UI components
│   ├── data/             # Game data (suspects, clues, prompts)
│   └── types/            # TypeScript definitions
├── backend/              # Server implementations
│   ├── server.js         # Node.js Express server
│   └── server.py         # Python FastAPI server
├── app/                  # Additional Python utilities
├── public/               # Static assets
├── requirements.txt      # Python dependencies
├── package.json          # Node.js dependencies
└── docs/                 # Documentation
    ├── MIGRATION_GUIDE.md
    └── IMPLEMENTATION_COMPARISON.md
```

## 🎯 Game Data Structure

### Suspects
Located in `src/data/suspects/`, each suspect has:
- **Backstory**: Character history and personality
- **Timeline**: Claimed whereabouts during the murder
- **Relationships**: Connections to the victim
- **Tone**: Speaking style and personality traits

### Clues
Located in `src/data/clues/dayX/`, organized by investigation days:
- Day-specific evidence for each suspect
- Supports both JSON and text formats
- Gradually reveals the mystery

### Prompts
Located in `src/data/prompts/`, contains:
- Interrogation prompt templates
- Character behavior guidelines
- Response formatting rules

## 🔧 Development

### Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start frontend development server |
| `npm run backend` | Start Node.js backend |
| `npm run backend-python-dev` | Start Python backend (dev mode) |
| `npm run start` | Start both frontend + Node.js backend |
| `npm run start-python` | Start both frontend + Python backend |
| `npm run build` | Build for production |
| `npm run lint` | Run ESLint |

### Backend Comparison

| Feature | Node.js | Python |
|---------|---------|--------|
| Type Safety | ❌ | ✅ |
| Auto Documentation | ❌ | ✅ |
| AI Ecosystem | ⚠️ | ✅ |
| Error Handling | ⚠️ | ✅ |
| Performance | ✅ | ✅ |

See [IMPLEMENTATION_COMPARISON.md](IMPLEMENTATION_COMPARISON.md) for detailed comparison.

## 🧪 Testing

### Health Checks
```bash
# Test Node.js backend
curl http://localhost:5000/health

# Test Python backend with OpenAI
curl "http://localhost:5000/health?test_openai=true"

# Validate Python setup
python3 validate_python_setup.py
```

### API Endpoints
- `POST /api/ask` - Question suspects
- `GET /api/clue?day=X&suspect=NAME` - Get clues
- `GET /health` - Health check
- `GET /docs` - API documentation (Python only)

## 🚀 Deployment

### Development
```bash
# Node.js version
npm start

# Python version
npm run start-python
```

### Production
```bash
# Build frontend
npm run build

# Deploy backend (choose one)
node backend/server.js                          # Node.js
source venv/bin/activate && python backend/server.py  # Python
```

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Check `.env` file exists and contains valid key
   - Verify key has sufficient credits
   - Test with health endpoint

2. **Python Import Errors**:
   - Run `./setup_python_backend.sh`
   - Activate virtual environment: `source venv/bin/activate`
   - Install requirements: `pip install -r requirements.txt`

3. **Port Conflicts**:
   - Backend runs on port 5000
   - Frontend runs on port 5173
   - Check for existing processes

4. **Missing Game Data**:
   - Ensure `src/data/` directory contains suspects, clues, and prompts
   - Check file paths match expected structure

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true

# Python backend debug
export PYTHONPATH=.
python backend/server.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT models
- FastAPI for the excellent Python web framework
- React team for the frontend framework
- All contributors to the open-source libraries used

## 🔮 Future Enhancements

With the Python backend, the following features are now easily achievable:

- **Local LLM Integration**: Run models locally for privacy
- **Vector Databases**: Store and search conversation history
- **Advanced Prompt Engineering**: Dynamic prompt generation
- **Conversation Memory**: Persistent character memory across sessions
- **Multi-language Support**: Translate responses in real-time
- **Voice Integration**: Text-to-speech for character voices
- **Game Analytics**: Track player choices and optimize difficulty

---

**Happy Detecting! 🕵️‍♀️**