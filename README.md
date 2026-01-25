# Navis Chrome Extension

**Don't just browse. Arrive.**

A voice-driven AI navigation agent implemented as a Chrome extension with a **Python backend** that helps users navigate websites by understanding their goals and guiding them step-by-step to their destination.

## 🚀 Quick Start (Python-First Architecture)

### Prerequisites
- Python 3.8+
- Chrome Browser
- OpenAI API Key
- Git

### Setup Development Environment

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd Navis-Chrome-Extension
   ```

2. **Run the Python backend setup:**
   ```bash
   python setup_python_backend.py
   ```

3. **Configure your API keys:**
   ```bash
   # Edit navis-backend/.env and add your OpenAI API key
   OPENAI_API_KEY=your_key_here
   ```

4. **Start the Python backend:**
   ```bash
   # Windows
   start_navis_backend.bat
   
   # Linux/Mac
   ./start_navis_backend.sh
   ```

5. **Load the Chrome extension:**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension` folder

6. **Start using Navis:**
   - Click the Navis icon in Chrome
   - Click "Tell me your goal" and speak your navigation intent
   - Review and execute the generated plan

## 🏗️ Architecture (Python-First)

Navis uses a **Python backend + Chrome extension frontend** approach:

### Python Backend (Core Logic)
- **Voice Processing**: Speech-to-text using Python libraries
- **AI Integration**: LLM calls for intent parsing and planning
- **DOM Analysis**: Web scraping and analysis using Selenium
- **Action Execution**: Browser automation through WebDriver
- **Plan Generation**: Structured planning with pre-defined tools

### Chrome Extension (Minimal JavaScript)
- **User Interface**: Simple popup and overlay components
- **Communication**: Bridge between user and Python backend
- **Visual Feedback**: Highlighting and progress indicators
- **Page Integration**: Content scripts for UI injection

### Key Benefits:
- **No JavaScript Knowledge Required**: Everything in Python
- **Fast**: Only 2 LLM calls per user goal
- **Cheap**: DOM-first approach reduces API costs by 90%
- **Reliable**: Structured planning vs unpredictable agent behavior
- **Maintainable**: Python ecosystem for AI/ML integration

## 📁 Project Structure

```
Navis-Chrome-Extension/
├── .kiro/spec/              # Project specifications
│   ├── requirements.md      # Detailed requirements
│   └── design.md           # Technical design
├── navis-backend/          # Python backend (core logic)
│   ├── main.py            # FastAPI server
│   ├── requirements.txt   # Python dependencies
│   ├── voice/             # Voice processing
│   ├── ai/                # LLM integration
│   ├── dom/               # DOM analysis with Selenium
│   └── execution/         # Action execution
├── extension/              # Chrome extension (minimal JS)
│   ├── manifest.json      # Extension configuration
│   ├── popup/             # Extension popup UI
│   ├── content.js         # Content script
│   └── background.js      # Background script
├── scripts/               # Development scripts
│   ├── setup.py          # Environment setup
│   └── test.py           # Test runner
├── tests/                 # Test files
├── setup_python_backend.py # Backend setup script
├── start_navis_backend.*   # Startup scripts
└── README.md              # This file
```

## 🛠️ Development

### Available Scripts

- **Setup Backend:** `python setup_python_backend.py`
- **Start Backend:** `start_navis_backend.bat` (Windows) or `./start_navis_backend.sh` (Unix)
- **Run Tests:** `python scripts/test.py`

### Key Technologies

- **Backend:** Python, FastAPI, Selenium, OpenAI API
- **Frontend:** Minimal JavaScript (Chrome Extension APIs only)
- **AI Integration:** OpenAI API for intent parsing and planning
- **Web Automation:** Selenium WebDriver for DOM analysis and actions

## 📋 Development Status

- ✅ Project structure and specifications
- ✅ Python backend architecture designed
- ✅ FastAPI server with voice processing
- ✅ LLM integration for intent parsing and planning
- ✅ Selenium-based DOM analysis
- ✅ Chrome extension with Python backend communication
- ✅ Setup scripts and documentation
- 🔄 Testing and refinement (next)
- 🔄 Error handling and fallbacks (next)
- 🔄 Performance optimization (next)

## 🤝 Contributing

1. Set up the Python backend: `python setup_python_backend.py`
2. Add your OpenAI API key to `navis-backend/.env`
3. Start the backend: `start_navis_backend.bat` (Windows) or `./start_navis_backend.sh` (Unix)
4. Load the Chrome extension from the `extension` folder
5. Test with voice commands and iterate

## 💡 Why Python-First?

This architecture lets you:
- **Write everything in Python** (no JavaScript knowledge needed)
- **Use familiar libraries** (requests, selenium, openai, etc.)
- **Easier debugging** with Python tools and logging
- **Rich AI/ML ecosystem** for advanced features
- **Better testing** with pytest and Python testing tools
- **Maintainable codebase** with Python best practices

The Chrome extension is just a thin UI layer that communicates with your Python backend where all the real work happens!

## 📄 License

[Add your license here]

## 🔗 Links

- [Project Specifications](.kiro/spec/)
- [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)