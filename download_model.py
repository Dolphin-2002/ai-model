"""Download a small GGUF chat model from Hugging Face."""

from huggingface_hub import hf_hub_download
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

# TinyLlama 1.1B Chat – Q4_K_M quantisation (~670 MB)
# Good balance of quality and speed for CPU inference.
REPO_ID = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
FILENAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"


def main():
    dest = MODEL_DIR / FILENAME
    if dest.exists():
        print(f"Model already exists: {dest}")
        return

    print(f"Downloading {FILENAME} from {REPO_ID} …")
    print("This may take a few minutes depending on your connection.\n")

    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=str(MODEL_DIR),
    )

    print(f"\nModel saved to: {path}")
    print("You can now start the server:  python server.py")


if __name__ == "__main__":
    main()
