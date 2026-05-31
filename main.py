import boto3
import json
from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
import io

app = FastAPI()

s3 = boto3.client(
    's3',
    region_name='us-east-2',
    aws_access_key_id='YOUR_ACCESS_KEY_HERE',
    aws_secret_access_key='YOUR_SECRET_KEY_HERE'
)

bedrock = boto3.client(
    'bedrock-runtime',
    region_name='us-east-2',
    aws_access_key_id='YOUR_ACCESS_KEY_HERE',
    aws_secret_access_key='YOUR_SECRET_KEY_HERE'
)

BUCKET = 'doc-summarizer-sahithi-2025'
MODEL_ID = 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

def extract_text(file_bytes, filename):
    if filename.endswith('.pdf'):
        reader = PdfReader(io.BytesIO(file_bytes))
        return " ".join(page.extract_text() for page in reader.pages)
    return file_bytes.decode('utf-8')

def summarize_with_bedrock(text):
    prompt = f"""You are a document summarizer.
Generate a concise executive summary in 3 to 5 bullet points.

Document:
{text[:4000]}

Summary:"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    })

    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    result = json.loads(response['body'].read())
    return result['content'][0]['text']

@app.post("/summarize")
async def summarize(file: UploadFile = File(...)):
    file_bytes = await file.read()
    s3.put_object(Bucket=BUCKET, Key=file.filename, Body=file_bytes)
    text = extract_text(file_bytes, file.filename)
    summary = summarize_with_bedrock(text)
    return {"filename": file.filename, "summary": summary}

@app.get("/")
def root():
    return {"message": "AI Document Summarizer is running"}
