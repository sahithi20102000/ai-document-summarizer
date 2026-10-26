"""Tests for main.py (AI Document Summarizer).

AWS is replaced with mocks before main.py is imported, so the tests need no
credentials, no network and cost nothing. Run with:  pytest -v
"""
import importlib
import io
import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

BEDROCK_REPLY = "- Point one\n- Point two\n- Point three"


def make_bedrock_response(text=BEDROCK_REPLY):
    """Shape of a real invoke_model response: a streaming body holding JSON."""
    payload = json.dumps({"content": [{"text": text}]}).encode()
    return {"body": io.BytesIO(payload)}


@pytest.fixture
def aws():
    """Import main.py with boto3 mocked. Returns (module, mock clients by service)."""
    clients = {"s3": MagicMock(name="s3"), "bedrock-runtime": MagicMock(name="bedrock")}
    clients["bedrock-runtime"].invoke_model.side_effect = lambda **kwargs: make_bedrock_response()

    def fake_client(service_name, *args, **kwargs):
        return clients[service_name]

    sys.modules.pop("main", None)
    with patch("boto3.client", side_effect=fake_client):
        module = importlib.import_module("main")
    yield module, clients
    sys.modules.pop("main", None)


def fake_pdf_reader(page_texts):
    """Stand-in for PyPDF2.PdfReader so tests do not need real PDF files."""
    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakeReader:
        def __init__(self, *args, **kwargs):
            self.pages = [FakePage(t) for t in page_texts]

    return FakeReader


def sent_body(clients):
    """The JSON body that was sent to Bedrock, as a dict."""
    call = clients["bedrock-runtime"].invoke_model.call_args
    return json.loads(call.kwargs["body"])


# --- health check -----------------------------------------------------------

def test_health_check_reports_running(aws):
    module, _ = aws
    response = TestClient(module.app).get("/")
    assert response.status_code == 200
    assert "running" in json.dumps(response.json()).lower()


# --- extract_text -----------------------------------------------------------

def test_extract_text_decodes_plain_text(aws):
    module, _ = aws
    assert module.extract_text(b"hello world", "notes.txt") == "hello world"


def test_extract_text_reads_every_pdf_page_in_order(aws):
    module, _ = aws
    with patch.object(module, "PdfReader", fake_pdf_reader(["First page", "Second page"])):
        text = module.extract_text(b"%PDF-fake", "report.pdf")
    assert "First page" in text and "Second page" in text
    assert text.index("First page") < text.index("Second page")


# --- summarize_with_bedrock -------------------------------------------------

def test_summarize_returns_the_models_text(aws):
    module, _ = aws
    assert module.summarize_with_bedrock("Some document text.") == BEDROCK_REPLY


def test_summarize_sends_expected_request_format(aws):
    module, clients = aws
    module.summarize_with_bedrock("Some document text.")
    body = sent_body(clients)
    assert body["anthropic_version"] == "bedrock-2023-05-31"
    assert body["max_tokens"] == 500


def test_summarize_sends_document_text_to_the_model(aws):
    module, clients = aws
    module.summarize_with_bedrock("Quarterly revenue rose twelve percent.")
    assert "Quarterly revenue rose twelve percent." in json.dumps(sent_body(clients))


def test_summarize_only_sends_the_first_4000_characters(aws):
    module, clients = aws
    long_text = "x" * 4000 + "TAILMARKER"
    module.summarize_with_bedrock(long_text)
    body_text = json.dumps(sent_body(clients))
    assert "x" * 4000 in body_text
    assert "TAILMARKER" not in body_text


# --- POST /summarize --------------------------------------------------------

def test_summarize_endpoint_with_text_file(aws):
    module, clients = aws
    response = TestClient(module.app).post(
        "/summarize", files={"file": ("notes.txt", b"Meeting notes about the launch.", "text/plain")}
    )
    assert response.status_code == 200
    assert response.json() == {"filename": "notes.txt", "summary": BEDROCK_REPLY}


def test_summarize_endpoint_stores_the_upload_in_s3(aws):
    module, clients = aws
    TestClient(module.app).post(
        "/summarize", files={"file": ("notes.txt", b"Meeting notes.", "text/plain")}
    )
    s3_calls = clients["s3"].method_calls
    assert s3_calls, "expected the file to be sent to S3"
    assert "notes.txt" in str(s3_calls)


def test_summarize_endpoint_with_pdf(aws):
    module, _ = aws
    with patch.object(module, "PdfReader", fake_pdf_reader(["Contract terms", "Signatures"])):
        response = TestClient(module.app).post(
            "/summarize", files={"file": ("contract.pdf", b"%PDF-fake", "application/pdf")}
        )
    assert response.status_code == 200
    assert response.json()["filename"] == "contract.pdf"
    assert response.json()["summary"] == BEDROCK_REPLY


def test_summarize_endpoint_rejects_request_without_a_file(aws):
    module, _ = aws
    response = TestClient(module.app).post("/summarize")
    assert response.status_code == 422


# --- known gap --------------------------------------------------------------

@pytest.mark.xfail(reason="main.py has no error handling yet; a Bedrock failure crashes the request")
def test_bedrock_failure_returns_a_clean_error(aws):
    module, clients = aws
    clients["bedrock-runtime"].invoke_model.side_effect = RuntimeError("Bedrock unavailable")
    client = TestClient(module.app, raise_server_exceptions=False)
    response = client.post("/summarize", files={"file": ("notes.txt", b"text", "text/plain")})
    assert response.status_code == 502
