# Voice Assistant Project

A Python-based voice assistant that provides a GUI, live transcription, translation support, and a modular voice engine. Designed for simplicity and extensibility.

## Features

- **GUI Assistant (`gui_assistant.py`)**  
  - Simple graphical interface to start/stop the assistant and view status.  
  - Hooks into the live transcription and voice engine modules.

- **Live Transcription (`live_transcriber.py`)**  
  - Captures audio from the microphone and converts speech to text in real time.  
  - Streams transcribed text to the GUI or other consumers.

- **Translation Support (`translations.json`)**  
  - JSON file containing language mappings, key phrases, or response templates.  
  - Enables the assistant to look up translations or localized strings on the fly.

- **Voice Engine (`voice_engine.py`)**  
  - Text-to-speech (TTS) and speech-to-text (STT) components.  
  - Modular design makes it easy to swap out TTS/STT providers or add new languages.

## Prerequisites

- Python 3.8 or higher  
- `pip` package manager  
- Microphone (for STT) and speakers/headphones (for TTS)

## Requirements

All dependencies are listed in **`requirements.txt`**. To install, run:

```bash
pip install -r requirements.txt

my-voice-project/
├── gui_assistant.py      # Main GUI entry point
├── live_transcriber.py   # Captures and transcribes microphone input
├── translations.json     # JSON file with translation strings/templates
├── voice_engine.py       # Text-to-Speech / Speech-to-Text engine logic
├── requirements.txt      # Python dependencies (pinned versions)
├── .gitignore            # Ignore patterns (virtualenv, __pycache__, etc.)
└── LICENSE               # MIT License text
