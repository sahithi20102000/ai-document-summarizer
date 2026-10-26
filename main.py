import io
import json

import boto3
from fastapi import FastAPI, File, HTTPException, UploadFile
from PyPDF2 import PdfReader

app = FastAPI()

REGION = "us-east-2"
BUCKET = "doc-summarizer-sahithi-2025"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MAX_FILE_BYTES = 4 * 1024 * 1024  # Vercel rejects request bodies above ~4.5 MB

# No keys here: boto3 reads AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# (and AWS_DEFAULT_REGION) from the environment automatically.
s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def extract_text(file_bytes, filename):
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return " ".join((page.extract_text() or "") for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


def summarize_with_bedrock(text):
    prompt = f"""You are a document summarizer.
Generate a concise executive summary in 3 to 5 bullet points.
Document:
{text[:4000]}
Summary:"""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


@app.post("/summarize")
async def summarize(file: UploadFile = File(...)):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 4 MB).")

    text = extract_text(file_bytes, file.filename)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in file.")

    s3.put_object(Bucket=BUCKET, Key=file.filename, Body=file_bytes)
    summary = summarize_with_bedrock(text)
    return {"filename": file.filename, "summary": summary}


@app.get("/")
def root():
    return {"message": "AI Document Summarizer is running"}
