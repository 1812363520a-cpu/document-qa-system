const state = {
  conversationId: null,
};

const apiStatus = document.querySelector("#apiStatus");
const documentList = document.querySelector("#documentList");
const documentMessage = document.querySelector("#documentMessage");
const uploadForm = document.querySelector("#uploadForm");
const documentFile = document.querySelector("#documentFile");
const fileLabel = document.querySelector("#fileLabel");
const refreshDocuments = document.querySelector("#refreshDocuments");
const conversation = document.querySelector("#conversation");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#questionInput");
const chatMessage = document.querySelector("#chatMessage");
const newConversation = document.querySelector("#newConversation");

function setMessage(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle("error", isError);
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP status text.
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function formatBytes(value) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function documentTypeLabel(fileType) {
  return fileType.toUpperCase();
}

async function checkApi() {
  try {
    const health = await request("/api/health");
    apiStatus.textContent = health.environment;
  } catch (error) {
    apiStatus.textContent = "Offline";
  }
}

async function loadDocuments() {
  try {
    const documents = await request("/api/documents");
    renderDocuments(documents);
    setMessage(documentMessage, documents.length ? `${documents.length} document(s)` : "No documents");
  } catch (error) {
    setMessage(documentMessage, error.message, true);
  }
}

function renderDocuments(documents) {
  documentList.replaceChildren();
  for (const documentItem of documents) {
    const item = document.createElement("li");
    item.className = "document-item";

    const detail = document.createElement("div");
    const name = document.createElement("div");
    name.className = "document-name";
    name.textContent = documentItem.filename;
    const meta = document.createElement("div");
    meta.className = "document-meta";
    meta.textContent = `${documentTypeLabel(documentItem.file_type)} · ${formatBytes(documentItem.size_bytes)}`;
    detail.append(name, meta);

    const remove = document.createElement("button");
    remove.className = "danger-button";
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", () => deleteDocument(documentItem.id));

    item.append(detail, remove);
    documentList.append(item);
  }
}

async function deleteDocument(documentId) {
  try {
    await request(`/api/documents/${documentId}`, { method: "DELETE" });
    await loadDocuments();
    setMessage(documentMessage, "Deleted");
  } catch (error) {
    setMessage(documentMessage, error.message, true);
  }
}

function renderMessages(messages) {
  conversation.replaceChildren();
  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No messages";
    conversation.append(empty);
    return;
  }
  for (const message of messages) {
    const bubble = document.createElement("article");
    bubble.className = `bubble ${message.role}`;
    const meta = document.createElement("div");
    meta.className = "bubble-meta";
    meta.textContent = message.role;
    const content = document.createElement("div");
    content.textContent = message.content;
    bubble.append(meta, content);
    conversation.append(bubble);
  }
  conversation.scrollTop = conversation.scrollHeight;
}

async function loadConversation() {
  if (!state.conversationId) {
    renderMessages([]);
    return;
  }
  const messages = await request(`/api/conversations/${state.conversationId}/messages`);
  renderMessages(messages);
}

documentFile.addEventListener("change", () => {
  fileLabel.textContent = documentFile.files[0]?.name || "Choose file";
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!documentFile.files.length) {
    setMessage(documentMessage, "Select a file", true);
    return;
  }
  const formData = new FormData();
  formData.append("file", documentFile.files[0]);
  try {
    setMessage(documentMessage, "Uploading");
    await request("/api/documents/upload", {
      method: "POST",
      body: formData,
    });
    uploadForm.reset();
    fileLabel.textContent = "Choose file";
    await loadDocuments();
    setMessage(documentMessage, "Uploaded");
  } catch (error) {
    setMessage(documentMessage, error.message, true);
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  try {
    setMessage(chatMessage, "Sending");
    const payload = { question };
    if (state.conversationId) {
      payload.conversation_id = state.conversationId;
    }
    const answer = await request("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.conversationId = answer.conversation_id;
    questionInput.value = "";
    await loadConversation();
    setMessage(chatMessage, answer.insufficient_context ? "Insufficient context" : "Answered");
  } catch (error) {
    setMessage(chatMessage, error.message, true);
  }
});

refreshDocuments.addEventListener("click", loadDocuments);

newConversation.addEventListener("click", () => {
  state.conversationId = null;
  renderMessages([]);
  setMessage(chatMessage, "New conversation");
});

checkApi();
loadDocuments();
renderMessages([]);
