import gc
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from llama_cpp import Llama

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_DIR = Path(__file__).parent / "models"
CONTEXT_SIZE = int(os.environ.get("CONTEXT_SIZE", "2048"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))

# ---------------------------------------------------------------------------
# Model manager
# ---------------------------------------------------------------------------
llm = None
current_model_name: str | None = None


def get_available_models() -> list[dict]:
    """Scan the models/ directory for .gguf files."""
    models = []
    if MODEL_DIR.exists():
        for f in sorted(MODEL_DIR.iterdir()):
            if f.suffix == ".gguf" and f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                if size_mb >= 1024:
                    size_str = f"{size_mb / 1024:.1f} GB"
                else:
                    size_str = f"{size_mb:.0f} MB"
                models.append({
                    "name": f.name,
                    "size": size_str,
                    "size_bytes": f.stat().st_size,
                })
    return models


def load_model(model_name: str):
    """Load a GGUF model by filename. Unloads the previous model first."""
    global llm, current_model_name

    model_path = MODEL_DIR / model_name
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Unload previous model
    if llm is not None:
        del llm
        gc.collect()
        print(f"Unloaded previous model: {current_model_name}")

    print(f"Loading model: {model_path} …")
    llm = Llama(
        model_path=str(model_path),
        n_ctx=CONTEXT_SIZE,
        n_threads=os.cpu_count() or 4,
        verbose=False,
    )
    current_model_name = model_name
    print(f"Model loaded: {model_name}")


# Load initial model
initial_model = os.environ.get("MODEL_NAME", "")
if not initial_model:
    available = get_available_models()
    if available:
        initial_model = available[0]["name"]

if initial_model and (MODEL_DIR / initial_model).exists():
    load_model(initial_model)
else:
    print("No model loaded. Place .gguf files in the models/ directory.")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Local AI Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    messages: list[dict]


class ChatResponse(BaseModel):
    role: str
    content: str


class SwitchModelRequest(BaseModel):
    model_name: str


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/models")
async def list_models():
    """List all available .gguf models and which one is active."""
    models = get_available_models()
    return {
        "models": models,
        "active": current_model_name,
    }


@app.post("/api/models/switch")
async def switch_model(req: SwitchModelRequest):
    """Switch to a different model at runtime."""
    available = [m["name"] for m in get_available_models()]
    if req.model_name not in available:
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_name}")

    if req.model_name == current_model_name:
        return {"status": "ok", "message": "Model already active", "active": current_model_name}

    try:
        load_model(req.model_name)
        return {"status": "ok", "message": f"Switched to {req.model_name}", "active": current_model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send the conversation history to the model and return its reply."""
    if llm is None:
        raise HTTPException(status_code=503, detail="No model loaded. Select a model first.")
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages list is empty")

    prompt = build_prompt(req.messages)

    output = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        stop=["</s>", "<|im_end|>", "<|user|>"],
        echo=False,
    )

    text = output["choices"][0]["text"].strip()
    return ChatResponse(role="assistant", content=text)


def build_prompt(messages: list[dict]) -> str:
    """Convert a list of {role, content} messages into a ChatML prompt."""
    prompt_parts: list[str] = []
    prompt_parts.append("<|im_start|>system\nYou are a helpful assistant.<|im_end|>")
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    prompt_parts.append("<|im_start|>assistant\n")
    return "\n".join(prompt_parts)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
