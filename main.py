import io

import anthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from PyPDF2 import PdfReader

app = FastAPI(title="AI Document Summarizer")

MODEL = "claude-haiku-5-5"
MAX_FILE_BYTES = 4 * 1024 * 1024  # Vercel rejects request bodies above ~4.5 MB

# The client reads the ANTHROPIC_API_KEY environment variable automatically.
client = anthropic.Anthropic()

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Document Summarizer</title>
<style>
  :root {
    --bg: #F2F4F7; --surface: #FFFFFF; --fg: #14181F; --muted: #566170;
    --line: #D5DBE3; --mark: #FFE55C; --mark-fg: #14181F; --danger: #B3261E;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0E1217; --surface: #161C23; --fg: #E8ECF1; --muted: #9AA6B4;
      --line: #27303A; --mark: #FFE55C; --mark-fg: #14181F; --danger: #FF8A80;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    font-size: 17px; line-height: 1.6; padding: 48px 16px 64px;
  }
  main { max-width: 680px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
  h1 { font-size: clamp(32px, 7vw, 48px); line-height: 1.05; letter-spacing: -0.02em; margin: 0; }
  h1 mark { background: linear-gradient(transparent 12%, var(--mark) 12%, var(--mark) 92%, transparent 92%); color: var(--mark-fg); padding: 0 0.12em; margin: 0 -0.12em; }
  p.lead { margin: 0; color: var(--muted); }
  form { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
  label { font-weight: 600; font-size: 15px; }
  input[type=file] { font: inherit; color: var(--fg); max-width: 100%; }
  button {
    font: inherit; font-weight: 600; min-height: 46px; padding: 0 20px; border-radius: 6px;
    border: 1px solid var(--fg); background: var(--fg); color: var(--bg); cursor: pointer; align-self: flex-start;
  }
  button:disabled { opacity: 0.55; cursor: progress; }
  button:focus-visible, input:focus-visible { outline: 3px solid #3B6CF0; outline-offset: 3px; }
  .hint { font-size: 14px; color: var(--muted); margin: 0; }
  #result { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 20px; }
  #result h2 { margin: 0 0 4px; font-size: 14px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
  #filename { margin: 0 0 12px; font-size: 14px; color: var(--muted); overflow-wrap: anywhere; }
  #points { margin: 0; padding-left: 1.2em; display: flex; flex-direction: column; gap: 10px; }
  #points li::marker { color: var(--fg); }
  #error { color: var(--danger); margin: 0; font-weight: 500; }
  a { color: inherit; }
</style>
</head>
<body>
<main>
  <div>
    <h1>AI Document <mark>Summarizer</mark></h1>
  </div>
  <p class="lead">Upload a PDF or a text file and get a short executive summary in a few bullet points.</p>

  <form id="form">
    <label for="file">Choose a file</label>
    <input id="file" name="file" type="file" accept=".pdf,.txt,.md,text/plain,application/pdf" required>
    <button id="go" type="submit">Summarize</button>
    <p class="hint">PDF or text, up to 4 MB. Scanned PDFs with no selectable text can't be read.</p>
  </form>

  <p id="error" role="alert" hidden></p>

  <section id="result" hidden aria-live="polite">
    <h2>Summary</h2>
    <p id="filename"></p>
    <ul id="points"></ul>
  </section>

  <p class="hint">Built with FastAPI and the Claude API. The API reference is at <a href="/docs">/docs</a>.</p>
</main>
<script>
  var form = document.getElementById("form");
  var fileInput = document.getElementById("file");
  var go = document.getElementById("go");
  var errorEl = document.getElementById("error");
  var result = document.getElementById("result");
  var points = document.getElementById("points");
  var filename = document.getElementById("filename");

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = false;
    result.hidden = true;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var file = fileInput.files[0];
    if (!file) { showError("Choose a file first."); return; }
    if (file.size > 4 * 1024 * 1024) { showError("That file is over 4 MB. Choose a smaller one."); return; }

    errorEl.hidden = true;
    result.hidden = true;
    go.disabled = true;
    go.textContent = "Summarizing...";

    var data = new FormData();
    data.append("file", file);

    fetch("/summarize", { method: "POST", body: data })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (body) {
          if (!res.ok) { throw new Error(body.detail || "Something went wrong. Try again."); }
          return body;
        });
      })
      .then(function (body) {
        points.innerHTML = "";
        body.summary.split("\\n").forEach(function (line) {
          var text = line.replace(/^\\s*([-*\\u2022]|\\d+[.)])\\s*/, "").trim();
          if (!text) { return; }
          var li = document.createElement("li");
          li.textContent = text;
          points.appendChild(li);
        });
        filename.textContent = body.filename;
        result.hidden = false;
      })
      .catch(function (err) { showError(err.message); })
      .then(function () { go.disabled = false; go.textContent = "Summarize"; });
  });
</script>
</body>
</html>
"""


def extract_text(file_bytes, filename):
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return " ".join((page.extract_text() or "") for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


def summarize(text):
    prompt = f"""You are a document summarizer.
Generate a concise executive summary in 3 to 5 bullet points.
Document:
{text[:4000]}
Summary:"""
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


@app.post("/summarize")
async def summarize_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 4 MB).")

    try:
        text = extract_text(file_bytes, file.filename)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read that file. Try a different PDF or a text file.")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in file.")

    try:
        summary = summarize(text)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"filename": file.filename, "summary": summary}


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


@app.get("/health")
def health():
    return {"message": "AI Document Summarizer is running"}
