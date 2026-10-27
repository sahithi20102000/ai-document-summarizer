import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def test_home_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI Document" in response.text
    assert 'id="form"' in response.text


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Document Summarizer is running"}


def test_summarize_text_file(monkeypatch):
    monkeypatch.setattr(main, "summarize", lambda text: "- point one\n- point two")
    response = client.post(
        "/summarize", files={"file": ("notes.txt", b"Hello world. This is a test document.")}
    )
    assert response.status_code == 200
    assert response.json() == {"filename": "notes.txt", "summary": "- point one\n- point two"}


def test_empty_file_is_rejected():
    response = client.post("/summarize", files={"file": ("empty.txt", b"   ")})
    assert response.status_code == 400


def test_unreadable_pdf_is_rejected():
    response = client.post("/summarize", files={"file": ("broken.pdf", b"not a real pdf")})
    assert response.status_code == 400


def test_large_file_is_rejected():
    big = b"a" * (main.MAX_FILE_BYTES + 1)
    response = client.post("/summarize", files={"file": ("big.txt", big)})
    assert response.status_code == 413


def test_summarize_pasted_text(monkeypatch):
    monkeypatch.setattr(main, "summarize", lambda text: "- pasted summary")
    response = client.post("/summarize-text", json={"text": "Some pasted words."})
    assert response.status_code == 200
    assert response.json() == {"filename": "Pasted text", "summary": "- pasted summary"}


def test_empty_pasted_text_is_rejected():
    response = client.post("/summarize-text", json={"text": "   "})
    assert response.status_code == 400


def test_missing_api_key_gives_clear_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/summarize-text", json={"text": "Some words."})
    assert response.status_code == 500
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
