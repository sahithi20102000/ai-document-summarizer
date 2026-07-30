# AI Document Summarizer

## Overview

AI Document Summarizer is a cloud-based application that uses Generative AI to automatically generate concise summaries from uploaded documents.

The application allows users to upload PDF or text documents, extracts the document content, stores the file in Amazon S3, and uses Amazon Bedrock with Claude models to generate an executive summary.

## Features

* Upload PDF and text documents through REST API
* Extract text from PDF files
* Store uploaded documents in Amazon S3
* Generate AI-powered summaries using Amazon Bedrock
* Return concise summaries through FastAPI endpoints
* Supports cloud-based AI inference using foundation models

## Architecture

The application follows this workflow:

```
User Upload
     |
     v
FastAPI Backend
     |
     +----------------+
     |                |
     v                v
Amazon S3       Document Processing
                      |
                      v
              Amazon Bedrock
              (Claude Model)
                      |
                      v
              Generated Summary
```

## Technologies Used

### Backend

* Python
* FastAPI

### Cloud Services

* Amazon S3
* Amazon Bedrock
* AWS SDK for Python (Boto3)

### AI / NLP

* Anthropic Claude foundation model
* Prompt-based text summarization

### Document Processing

* PyPDF2

## API Endpoints

### Health Check

```
GET /
```

Response:

```json
{
  "message": "AI Document Summarizer is running"
}
```

### Summarize Document

```
POST /summarize
```

Accepts:

* PDF files
* Text files

Returns:

```json
{
  "filename": "document.pdf",
  "summary": "Generated document summary"
}
```

## How to Run Locally

### Clone Repository

```bash
git clone https://github.com/sahithi20102000/ai-document-summarizer.git
```

### Install Dependencies

```bash
pip install fastapi uvicorn boto3 PyPDF2 python-multipart
```

### Configure AWS Credentials

Set AWS credentials using environment variables:

```bash
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_DEFAULT_REGION=us-east-2
```

Make sure your AWS account has access to:

* Amazon S3
* Amazon Bedrock models

### Start Application

```bash
uvicorn main:app --reload
```

The API will run at:

```
http://localhost:8000
```

## Project Structure

```
ai-document-summarizer/
|
├── main.py
├── README.md
└── .gitignore
```

## My Contributions

* Designed and developed the FastAPI backend service
* Integrated Amazon S3 for document storage
* Implemented PDF text extraction workflow
* Integrated Amazon Bedrock for Generative AI summarization
* Developed REST API endpoints for document processing
* Designed prompt-based summarization workflow using Claude models

## Future Improvements

* Add frontend interface for document upload
* Implement authentication and user management
* Add support for additional document formats
* Deploy using AWS Lambda and API Gateway
* Add document history and summary storage

## Author

Sahithi Gangasani
