# Local AI Chat

A self-contained, browser-based chat application that runs **GGUF AI models locally** on your machine — no cloud, no API keys, complete privacy. Switch between multiple models through the web UI without restarting the server.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [How to Download & Install Models](#how-to-download--install-models)
- [How to Switch Models](#how-to-switch-models)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Recommended Models](#recommended-models)

---

## Features

- **100% local** — runs entirely on your machine, no internet required after setup
- **GGUF model support** — works with any `.gguf` quantized model via `llama-cpp-python`
- **Live model switching** — change models from the web UI without restarting the server
- **Auto-detection** — automatically discovers all `.gguf` files in the `models/` directory
- **Dark-themed chat UI** — clean, responsive interface with typing indicators
- **New chat** — clear conversation and start fresh with one click
- **Toast notifications** — visual feedback when switching models
- **CPU-optimized** — runs on any machine, no GPU required

---

## Project Structure

```
ai-model/
├── models/                  # Place your .gguf model files here
│   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
├── static/
│   ├── index.html           # Chat UI (HTML)
│   ├── style.css            # Styles (dark theme)
│   └── script.js            # Frontend logic (chat, model switching)
├── server.py                # FastAPI backend (inference + model management)
├── download_model.py        # Script to download TinyLlama from Hugging Face
├── requirements.txt         # Python dependencies
├── .gitignore               # Excludes venv, models, __pycache__
└── README.md                # This file
```

---

## Prerequisites

- **Python 3.10+** (tested with 3.13)
- **pip** (comes with Python)
- **C/C++ compiler** — required to build `llama-cpp-python` from source
  - **Linux**: `sudo apt install build-essential cmake` (Debian/Ubuntu)
  - **macOS**: `xcode-select --install`
  - **Windows**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- **RAM**: At least 2× the model file size (e.g., 1.5 GB RAM for a 670 MB model)

---

## Installation

### Step 1: Clone or navigate to the project

```bash
cd ~/ai-model
```

### Step 2: Create a virtual environment

```bash
python3 -m venv venv
```

### Step 3: Activate the virtual environment

```bash
# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `llama-cpp-python` compiles C++ code during installation. This may take 5-10 minutes on the first install. If you see build errors, ensure you have a C++ compiler installed (see [Prerequisites](#prerequisites)).

---

## Quick Start

```bash
# 1. Activate the virtual environment
source venv/bin/activate

# 2. Download a starter model (TinyLlama 1.1B, ~670 MB)
python download_model.py

# 3. Start the server
python server.py

# 4. Open in your browser
# → http://localhost:8000
```

That's it! The chat UI will load and you can start talking to the AI.

---

## How to Download & Install Models

### Option 1: Use the included download script

```bash
source venv/bin/activate
python download_model.py
```

This downloads **TinyLlama 1.1B Chat (Q4_K_M)** — a small, fast model ideal for testing.

### Option 2: Download from Hugging Face manually

1. Go to [huggingface.co/models](https://huggingface.co/models?search=gguf)
2. Search for any model with `GGUF` in the name
3. Download the `.gguf` file (look for `Q4_K_M` for good quality/speed balance)
4. Move the file to the `models/` directory:

```bash
mv ~/Downloads/some-model.Q4_K_M.gguf ~/ai-model/models/
```

### Option 3: Use the Hugging Face CLI

```bash
# Install the CLI (if not already installed)
pip install huggingface-hub

# Download a model directly into models/
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir models/
```

### Understanding quantization formats

GGUF models come in different quantization levels. Smaller quantization = faster + less RAM, but slightly lower quality:

| Quantization | Quality | Speed | RAM Usage | Recommended For |
|-------------|---------|-------|-----------|-----------------|
| `Q2_K`      | Low     | Fast  | Lowest    | Very limited RAM |
| `Q4_K_M`    | Good    | Good  | Medium    | **Best all-round choice** |
| `Q5_K_M`    | Better  | Fair  | Higher    | When quality matters |
| `Q6_K`      | High    | Slow  | High      | Best quality, needs RAM |
| `Q8_0`      | Highest | Slowest | Highest | Maximum quality |

---

## How to Switch Models

### From the Web UI (recommended)

1. Click the **gear button** (⚙) in the top-right corner of the header
2. A dropdown shows all `.gguf` files found in `models/`
3. Click any model to switch — the previous model is unloaded and the new one is loaded
4. A toast notification confirms the switch
5. Chat history is cleared when you switch models

### From the command line

Set the `MODEL_NAME` environment variable when starting the server:

```bash
# Use a specific model
MODEL_NAME="mistral-7b-instruct-v0.2.Q4_K_M.gguf" python server.py

# Default: loads the first .gguf file found alphabetically
python server.py
```

### Via the API

```bash
# List available models
curl http://localhost:8000/api/models

# Switch model
curl -X POST http://localhost:8000/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_name": "mistral-7b-instruct-v0.2.Q4_K_M.gguf"}'
```

---

## Configuration

All configuration is done through environment variables:

| Variable       | Default                          | Description                                    |
|----------------|----------------------------------|------------------------------------------------|
| `MODEL_NAME`   | First `.gguf` file in `models/`  | Which model to load on startup                 |
| `CONTEXT_SIZE`  | `2048`                          | Context window size (tokens). Higher = more memory |
| `MAX_TOKENS`   | `512`                            | Maximum tokens per response                    |

Example with all options:

```bash
MODEL_NAME="mistral-7b.gguf" CONTEXT_SIZE=4096 MAX_TOKENS=1024 python server.py
```

---

## API Reference

### `GET /` — Serve the chat UI

Returns the `index.html` page.

### `GET /api/models` — List available models

**Response:**
```json
{
  "models": [
    {"name": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", "size": "669 MB", "size_bytes": 669000000},
    {"name": "mistral-7b-instruct-v0.2.Q4_K_M.gguf", "size": "4.4 GB", "size_bytes": 4370000000}
  ],
  "active": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
}
```

### `POST /api/models/switch` — Switch the active model

**Request:**
```json
{"model_name": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"}
```

**Response:**
```json
{"status": "ok", "message": "Switched to tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", "active": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"}
```

### `POST /api/chat` — Send a chat message

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, who are you?"}
  ]
}
```

**Response:**
```json
{"role": "assistant", "content": "I'm a helpful AI assistant running locally on your machine!"}
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'llama_cpp'`

You forgot to activate the virtual environment:
```bash
source venv/bin/activate
```

### `ValueError: Failed to load model from file`

Your `llama-cpp-python` version is too old for the model format. Upgrade it:
```bash
pip install --upgrade llama-cpp-python
```

### `[Errno 98] Address already in use`

Another process is using port 8000. Kill it and restart:
```bash
kill $(lsof -t -i:8000)
python server.py
```

### Model loads but responses are very slow

- **Expected behavior for large models on CPU.** A 20B model may take 30-60 seconds per response.
- Use a smaller model (TinyLlama 1.1B responds in 2-5 seconds).
- Reduce `MAX_TOKENS` to get shorter, faster responses:
  ```bash
  MAX_TOKENS=128 python server.py
  ```

### Out of memory / system freezes

The model is too large for your RAM. Use a smaller quantization or smaller model:
- `Q4_K_M` uses ~60% less RAM than full precision
- `Q2_K` uses even less but with lower quality
- Or switch to a smaller model entirely (1B-3B parameter range)

---

## Recommended Models

| Model | Parameters | GGUF Size (Q4_K_M) | Quality | CPU Speed | Download Command |
|-------|-----------|-------------------|---------|-----------|------------------|
| **TinyLlama 1.1B** | 1.1B | ~670 MB | Fair | Fast (~2s) | `python download_model.py` |
| **Phi-2** | 2.7B | ~1.7 GB | Good | Moderate (~5s) | `huggingface-cli download TheBloke/phi-2-GGUF phi-2.Q4_K_M.gguf --local-dir models/` |
| **Mistral 7B Instruct** | 7B | ~4.4 GB | Very Good | Slow (~15s) | `huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF mistral-7b-instruct-v0.2.Q4_K_M.gguf --local-dir models/` |
| **Llama 2 13B Chat** | 13B | ~7.9 GB | Excellent | Very Slow (~30s) | `huggingface-cli download TheBloke/Llama-2-13B-chat-GGUF llama-2-13b-chat.Q4_K_M.gguf --local-dir models/` |

> CPU speed estimates are for a modern multi-core CPU. Actual performance varies by hardware.

---

## Git Setup

This project is configured with:
- **Username:** Dolphin-2002
- **Email:** dolphin.co.solution@gmail.com

The `.gitignore` excludes `venv/`, model files (`*.gguf`), and `__pycache__/` from version control.

```bash
# First commit
git add .
git commit -m "Initial commit: Local AI Chat app"

# Push to GitHub (after creating a repo)
git remote add origin https://github.com/Dolphin-2002/ai-model.git
git push -u origin main
```
