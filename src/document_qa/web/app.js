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
const sendButton = document.querySelector("#sendButton");
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
    name.title = documentItem.filename;
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

function setChatLoading(isLoading) {
  sendButton.disabled = isLoading;
  questionInput.disabled = isLoading;
  sendButton.classList.toggle("is-loading", isLoading);
  const label = sendButton.querySelector(".button-label");
  label.textContent = isLoading ? "Sending" : "Send";
}

function renderMarkdown(markdown) {
  const fragment = document.createDocumentFragment();
  const lines = markdown.split(/\r?\n/);
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const orderedMatch = line.match(/^\s*\d+\.\s+(.*)$/);
    if (orderedMatch) {
      const list = document.createElement("ol");
      while (index < lines.length) {
        const match = lines[index].match(/^\s*\d+\.\s+(.*)$/);
        if (!match) break;
        const item = document.createElement("li");
        item.append(renderInlineMarkdown(match[1]));
        list.append(item);
        index += 1;
      }
      fragment.append(list);
      continue;
    }

    const unorderedMatch = line.match(/^\s*[-*]\s+(.*)$/);
    if (unorderedMatch) {
      const list = document.createElement("ul");
      while (index < lines.length) {
        const match = lines[index].match(/^\s*[-*]\s+(.*)$/);
        if (!match) break;
        const item = document.createElement("li");
        item.append(renderInlineMarkdown(match[1]));
        list.append(item);
        index += 1;
      }
      fragment.append(list);
      continue;
    }

    const headingMatch = line.match(/^\s{0,3}(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      const heading = document.createElement(`h${headingMatch[1].length + 3}`);
      heading.append(renderInlineMarkdown(headingMatch[2]));
      fragment.append(heading);
      index += 1;
      continue;
    }

    const paragraphLines = [];
    while (index < lines.length && lines[index].trim()) {
      if (
        lines[index].match(/^\s*\d+\.\s+/) ||
        lines[index].match(/^\s*[-*]\s+/) ||
        lines[index].match(/^\s{0,3}#{1,3}\s+/)
      ) {
        break;
      }
      paragraphLines.push(lines[index]);
      index += 1;
    }
    const paragraph = document.createElement("p");
    paragraph.append(renderInlineMarkdown(paragraphLines.join("\n")));
    fragment.append(paragraph);
  }

  if (!fragment.childNodes.length) {
    fragment.append(document.createTextNode(markdown));
  }
  return fragment;
}

function renderInlineMarkdown(text) {
  const fragment = document.createDocumentFragment();
  const pattern = /(`([^`]+)`)|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)/g;
  let cursor = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      appendTextWithLineBreaks(fragment, text.slice(cursor, match.index));
    }
    if (match[2]) {
      const code = document.createElement("code");
      code.textContent = match[2];
      fragment.append(code);
    } else if (match[4]) {
      const strong = document.createElement("strong");
      strong.textContent = match[4];
      fragment.append(strong);
    } else if (match[6]) {
      const emphasis = document.createElement("em");
      emphasis.textContent = match[6];
      fragment.append(emphasis);
    }
    cursor = pattern.lastIndex;
  }

  if (cursor < text.length) {
    appendTextWithLineBreaks(fragment, text.slice(cursor));
  }
  return fragment;
}

function appendTextWithLineBreaks(parent, text) {
  const parts = text.split("\n");
  for (const [index, part] of parts.entries()) {
    if (index > 0) {
      parent.append(document.createElement("br"));
    }
    parent.append(document.createTextNode(part));
  }
}

function createMessageBubble(role, content, options = {}) {
  const bubble = document.createElement("article");
  bubble.className = `bubble ${role}`;
  if (options.pending) {
    bubble.classList.add("pending");
  }
  const meta = document.createElement("div");
  meta.className = "bubble-meta";
  meta.textContent = role;
  const body = document.createElement("div");
  body.className = "bubble-content";
  if (options.pending) {
    const spinner = document.createElement("span");
    spinner.className = "inline-spinner";
    spinner.setAttribute("aria-hidden", "true");
    const thinking = document.createElement("span");
    thinking.textContent = content;
    body.append(spinner, thinking);
  } else {
    if (role === "assistant") {
      body.append(renderMarkdown(content));
    } else {
      body.textContent = content;
    }
  }
  bubble.append(meta, body);
  return bubble;
}

function appendMessage(role, content, options = {}) {
  const empty = conversation.querySelector(".empty-state");
  if (empty) {
    empty.remove();
  }
  const bubble = createMessageBubble(role, content, options);
  conversation.append(bubble);
  conversation.scrollTop = conversation.scrollHeight;
  return bubble;
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
    conversation.append(createMessageBubble(message.role, message.content));
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
  if (sendButton.disabled) return;
  const question = questionInput.value.trim();
  if (!question) return;
  appendMessage("user", question);
  const pendingBubble = appendMessage("assistant", "AI is thinking", { pending: true });
  questionInput.value = "";
  setChatLoading(true);
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
    pendingBubble.replaceWith(createMessageBubble("assistant", answer.answer));
    conversation.scrollTop = conversation.scrollHeight;
    setMessage(chatMessage, answer.insufficient_context ? "Insufficient context" : "Answered");
  } catch (error) {
    pendingBubble.remove();
    setMessage(chatMessage, error.message, true);
  } finally {
    setChatLoading(false);
    questionInput.focus();
  }
});

refreshDocuments.addEventListener("click", loadDocuments);

newConversation.addEventListener("click", () => {
  state.conversationId = null;
  renderMessages([]);
  setChatLoading(false);
  setMessage(chatMessage, "New conversation");
});

checkApi();
loadDocuments();
renderMessages([]);
