import io

import anthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from PyPDF2 import PdfReader

app = FastAPI()

MODEL = "claude-haiku-5-5"
MAX_FILE_BYTES = 4 * 1024 * 1024  # Vercel rejects request bodies above ~4.5 MB

# The client reads the ANTHROPIC_API_KEY environment variable automatically.
client = anthropic.Anthropic()


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

    text = extract_text(file_bytes, file.filename)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in file.")

    try:
        summary = summarize(text)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"filename": file.filename, "summary": summary}


@app.get("/")
def root():
    return {"message": "AI Document Summarizer is running"}
