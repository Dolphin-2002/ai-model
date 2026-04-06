const chatArea = document.getElementById("chatArea");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Conversation history sent to the backend each request
const messages = [];

// ── Auto-resize textarea ────────────────────────────────────
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});

// ── Submit on Enter (Shift+Enter for newline) ───────────────
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

// ── Form submit ─────────────────────────────────────────────
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = userInput.value.trim();
  if (!text) return;

  // Remove welcome message if present
  const welcome = chatArea.querySelector(".welcome-msg");
  if (welcome) welcome.remove();

  // Add user message
  appendMessage("user", text);
  messages.push({ role: "user", content: text });

  userInput.value = "";
  userInput.style.height = "auto";
  setLoading(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    appendMessage("assistant", data.content);
    messages.push({ role: "assistant", content: data.content });
  } catch (err) {
    appendMessage("assistant", `⚠️ Error: ${err.message}`);
  } finally {
    setLoading(false);
  }
});

// ── Helpers ─────────────────────────────────────────────────
function appendMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "role-label";
  label.textContent = role === "user" ? "You" : "AI";

  const body = document.createElement("span");
  body.textContent = content;

  div.appendChild(label);
  div.appendChild(body);
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function setLoading(on) {
  sendBtn.disabled = on;
  userInput.disabled = on;

  const existing = chatArea.querySelector(".thinking");
  if (on) {
    const dots = document.createElement("div");
    dots.className = "thinking";
    dots.innerHTML = "<span></span><span></span><span></span>";
    chatArea.appendChild(dots);
    chatArea.scrollTop = chatArea.scrollHeight;
  } else if (existing) {
    existing.remove();
  }

  if (!on) userInput.focus();
}
