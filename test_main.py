import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def test_root():
    response = client.get("/")
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


def test_large_file_is_rejected():
    big = b"a" * (main.MAX_FILE_BYTES + 1)
    response = client.post("/summarize", files={"file": ("big.txt", big)})
    assert response.status_code == 413
