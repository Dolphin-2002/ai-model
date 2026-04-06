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
# Change this to match your downloaded .gguf filename
MODEL_NAME = os.environ.get(
    "MODEL_NAME", "OpenAI-20B-NEO-CODEPlus-Uncensored-IQ4_NL.gguf"
)
MODEL_PATH = MODEL_DIR / MODEL_NAME

CONTEXT_SIZE = int(os.environ.get("CONTEXT_SIZE", "2048"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))

# ---------------------------------------------------------------------------
# Load model
# ---------------------------------------------------------------------------
if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found at {MODEL_PATH}.\n"
        "Run:  python download_model.py\n"
        "Or place your .gguf file in the models/ directory and set MODEL_NAME."
    )

print(f"Loading model: {MODEL_PATH} …")
llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=CONTEXT_SIZE,
    n_threads=os.cpu_count() or 4,
    verbose=False,
)
print("Model loaded.")

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
    messages: list[dict]  # [{"role": "user"|"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    role: str
    content: str


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send the conversation history to the model and return its reply."""
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages list is empty")

    # Build a prompt from the conversation (ChatML-style for TinyLlama)
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
