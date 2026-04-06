# Local AI Chat

A self-contained chat web app that runs a GGUF model locally on your machine (CPU).

## Project Structure

```
ai-model/
├── models/                # Place .gguf files here
├── static/
│   ├── index.html         # Chat UI
│   ├── style.css          # Styles
│   └── script.js          # Frontend logic
├── server.py              # FastAPI backend
├── download_model.py      # Downloads a small GGUF model
└── requirements.txt       # Python dependencies
```

## Quick Start

### 1. Create a virtual environment & install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download a model

```bash
python download_model.py
```

This downloads **TinyLlama 1.1B Chat** (~670 MB) — a small model that runs well on CPU.

### 3. Start the server

```bash
python server.py
```

### 4. Open in browser

Go to **http://localhost:8000**

## Using a Different Model

1. Place your `.gguf` file in the `models/` directory.
2. Set the `MODEL_NAME` environment variable:

```bash
MODEL_NAME="your-model.gguf" python server.py
```

## Environment Variables

| Variable       | Default                                  | Description                |
|----------------|------------------------------------------|----------------------------|
| `MODEL_NAME`   | `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` | GGUF filename in `models/` |
| `CONTEXT_SIZE` | `2048`                                   | Context window size        |
| `MAX_TOKENS`   | `512`                                    | Max tokens per response    |
