import pytest
from fastapi.testclient import TestClient
import numpy as np
import cv2
import base64

from backend.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "models" in data
    assert "ollama" in data
    assert "avatar" in data

def test_api_models():
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "ASL" in data
    assert "ISL" in data
    assert data["ASL"]["available"] is True
    assert data["ISL"]["available"] is True

def test_api_supported_signs():
    res_asl = client.get("/api/supported-signs?mode=ASL")
    assert res_asl.status_code == 200
    asl_data = res_asl.json()
    assert "HELLO" in asl_data["signs"]

    res_isl = client.get("/api/supported-signs?mode=ISL")
    assert res_isl.status_code == 200
    isl_data = res_isl.json()
    assert "NAMASTE" in isl_data["signs"]

def test_api_supported_languages():
    res = client.get("/api/supported-languages")
    assert res.status_code == 200
    langs = res.json()
    assert "hi" in langs
    assert "ta" in langs
    assert "te" in langs
    assert "en" in langs

def test_api_translate():
    payload = {"text": "HELLO", "target_language": "hi"}
    res = client.post("/api/translate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["translated_text"] == "नमस्ते"

def test_api_avatar_sign():
    payload = {"text": "WATER", "mode": "ASL"}
    res = client.post("/api/avatar/sign", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["sequence"]) == 1
    assert data["sequence"][0]["word"] == "WATER"

def test_api_recognize_blank_frame():
    # Create black 320x240 image
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", blank)
    b64_img = base64.b64encode(buffer).decode("utf-8")

    payload = {
        "image": f"data:image/jpeg;base64,{b64_img}",
        "mode": "ASL",
        "confidence_threshold": 0.5,
        "draw_landmarks": False
    }
    res = client.post("/api/recognize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["raw_sign"] in ("NONE", None)
