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
* Automated tests that run on every push through GitHub Actions

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

### Testing and CI

* Pytest
* GitHub Actions

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
pip install -r requirements-dev.txt
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

## Running Tests

```bash
pytest -v
```

The tests mock AWS, so no credentials are needed. They cover the health check, text extraction for text and PDF files, the request sent to Bedrock, and the `/summarize` endpoint. They run automatically on every push through GitHub Actions.

One test is marked as an expected failure: the app does not yet handle Bedrock errors cleanly. It will start passing once that error handling is added.

## Project Structure

```
ai-document-summarizer/
|
├── .github/workflows/ci.yml
├── main.py
├── test_main.py
├── requirements-dev.txt
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
* Wrote automated Pytest tests with mocked AWS services and a GitHub Actions workflow

## Future Improvements

* Add frontend interface for document upload
* Implement authentication and user management
* Add support for additional document formats
* Deploy using AWS Lambda and API Gateway
* Add document history and summary storage
* Handle Bedrock and S3 errors with clear API error responses

## Author

Sahithi Gangasani
