const chatArea = document.getElementById("chatArea");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const modelBtn = document.getElementById("modelBtn");
const modelDropdown = document.getElementById("modelDropdown");
const modelList = document.getElementById("modelList");
const activeModelLabel = document.getElementById("activeModelLabel");
const newChatBtn = document.getElementById("newChatBtn");
const toast = document.getElementById("toast");

// Conversation history sent to the backend each request
let messages = [];
let activeModel = null;
let switchingModel = false;

// ── Init ────────────────────────────────────────────────────
loadModels();

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

// ── Model dropdown toggle ───────────────────────────────────
modelBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  const isOpen = modelDropdown.classList.toggle("show");
  modelBtn.classList.toggle("open", isOpen);
  if (isOpen) loadModels();
});

document.addEventListener("click", (e) => {
  if (!modelDropdown.contains(e.target) && e.target !== modelBtn) {
    modelDropdown.classList.remove("show");
    modelBtn.classList.remove("open");
  }
});

// ── New chat button ─────────────────────────────────────────
newChatBtn.addEventListener("click", () => {
  messages = [];
  chatArea.innerHTML = '<div class="welcome-msg"><p>Send a message to start chatting with the local AI model.</p></div>';
  userInput.focus();
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

// ── Model management ────────────────────────────────────────
async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    activeModel = data.active;
    activeModelLabel.textContent = activeModel
      ? truncateName(activeModel)
      : "No model";
    renderModelList(data.models, data.active);
  } catch {
    activeModelLabel.textContent = "Error";
  }
}

function renderModelList(models, active) {
  modelList.innerHTML = "";
  if (models.length === 0) {
    modelList.innerHTML = '<div style="padding:10px 12px;color:var(--text-muted);font-size:0.82rem;">No .gguf files found in models/</div>';
    return;
  }
  for (const m of models) {
    const item = document.createElement("div");
    item.className = "model-item" + (m.name === active ? " active" : "");
    item.innerHTML = `
      <div class="model-item-info">
        <span class="model-item-name">${escapeHtml(m.name)}</span>
        <span class="model-item-size">${m.size}</span>
      </div>
      ${m.name === active ? '<span class="model-item-badge">Active</span>' : ""}
    `;
    item.addEventListener("click", () => switchModel(m.name));
    modelList.appendChild(item);
  }
}

async function switchModel(name) {
  if (name === activeModel || switchingModel) return;
  switchingModel = true;

  // Show loading state in dropdown
  const items = modelList.querySelectorAll(".model-item");
  items.forEach((el) => {
    const itemName = el.querySelector(".model-item-name").textContent;
    if (itemName === name) {
      const badge = el.querySelector(".model-item-badge");
      if (badge) badge.remove();
      const loading = document.createElement("span");
      loading.className = "model-item-loading";
      loading.textContent = "Loading…";
      el.appendChild(loading);
    }
  });

  showToast(`Loading ${truncateName(name)}…`);

  try {
    const res = await fetch("/api/models/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: name }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to switch model");
    }

    const data = await res.json();
    activeModel = data.active;
    activeModelLabel.textContent = truncateName(activeModel);
    showToast(`Switched to ${truncateName(name)}`);
    await loadModels();

    // Clear chat on model switch
    messages = [];
    chatArea.innerHTML = '<div class="welcome-msg"><p>Model changed. Send a message to start chatting.</p></div>';
  } catch (err) {
    showToast(`⚠️ ${err.message}`);
    await loadModels();
  } finally {
    switchingModel = false;
    modelDropdown.classList.remove("show");
    modelBtn.classList.remove("open");
  }
}

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

function truncateName(name) {
  return name.length > 28 ? name.slice(0, 25) + "…" : name;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove("show"), 3000);
}
