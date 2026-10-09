import base64
import json
import logging
from typing import Dict, Any, Optional, List
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from pydantic import BaseModel, Field

from backend.config import SUPPORTED_LANGUAGES, CONFIDENCE_THRESHOLD, DEBOUNCE_FRAMES, TEMPORAL_SMOOTHING_WINDOW
from backend.recognition.landmark_detector import LandmarkDetector
from backend.recognition.feature_extractor import LandmarkFeatureExtractor
from backend.recognition.sign_classifier import SignClassifierManager
from backend.recognition.temporal_smoother import TemporalSmoother
from backend.recognition.sign_vocabulary import get_sign_list, get_vocabulary
from backend.ollama.ollama_client import OllamaService
from backend.ollama.vision_recognizer import OllamaVisionRecognizer
from backend.recognition.hybrid_recognizer import HybridSignRecognizer
from backend.translation.translator import TranslationManager
from backend.tts.speech_engine import LocalTTSEngine
from backend.avatar.animation_planner import AvatarAnimationPlanner

logger = logging.getLogger("SignBridge.API")

router = APIRouter(prefix="/api")

# Singletons initialized for the API
classifier_mgr = SignClassifierManager()
detector = LandmarkDetector(static_image_mode=False, max_num_hands=2)
extractor = LandmarkFeatureExtractor()
ollama_svc = OllamaService()

import os
vision_model_name = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
vision_svc = OllamaVisionRecognizer(host=host, vision_model=vision_model_name)
hybrid_recognizer = HybridSignRecognizer(vision_svc, debug=True)

translator = TranslationManager(ollama_svc)
tts_engine = LocalTTSEngine()
avatar_planner = AvatarAnimationPlanner()

# Separate temporal smoothers for ASL and ISL to prevent state bleed
smoothers = {
    "ASL": TemporalSmoother(window_size=TEMPORAL_SMOOTHING_WINDOW),
    "ISL": TemporalSmoother(window_size=TEMPORAL_SMOOTHING_WINDOW),
    "AUTO": TemporalSmoother(window_size=TEMPORAL_SMOOTHING_WINDOW)
}

# --- Request / Response Models ---

class RecognizeRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image frame (JPEG or PNG)")
    mode: str = Field("ASL", description="Sign language mode: ASL or ISL")
    confidence_threshold: Optional[float] = None
    draw_landmarks: bool = True

class TranslateRequest(BaseModel):
    text: str = Field(..., description="English text to translate")
    target_language: str = Field("hi", description="Target language code (e.g. hi, ta, te, kn, mr, etc.)")

class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to speak")
    language_code: Optional[str] = "en"
    voice_hint: Optional[str] = None

class AvatarSignRequest(BaseModel):
    text: str = Field(..., description="Text for avatar to perform in sign language")
    mode: str = Field("ASL", description="ASL or ISL")

class SentenceActionRequest(BaseModel):
    action: str = Field(..., description="clear, delete_last, append")
    mode: str = Field("ASL", description="ASL or ISL")
    word: Optional[str] = None

class VisionAssistRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image frame")
    context: Optional[str] = ""

# --- Endpoints ---

@router.get("/health")
async def get_system_health():
    """
    Returns unified system health across Camera, AI Models, Ollama, TTS, and Avatar.
    """
    ollama_health = await vision_svc.get_health()
    tts_status = tts_engine.get_status()
    models_status = classifier_mgr.get_status()

    # Quick test if camera index 0 is openable
    camera_accessible = True
    try:
        cap = cv2.VideoCapture(0)
        camera_accessible = cap.isOpened()
        if camera_accessible:
            cap.release()
    except Exception:
        camera_accessible = False

    return {
        "status": "healthy",
        "camera": {
            "connected": camera_accessible,
            "status": "Connected" if camera_accessible else "Offline / In Use"
        },
        "models": {
            "asl": models_status.get("ASL", {}),
            "isl": models_status.get("ISL", {})
        },
        "ollama": ollama_health,
        "tts": tts_status,
        "avatar": {
            "ready": True,
            "asl_signs_count": len(avatar_planner.asl_dict),
            "isl_signs_count": len(avatar_planner.isl_dict),
            "fingerspelling_count": len(avatar_planner.fingerspelling_dict)
        }
    }

@router.get("/models")
def get_models_info():
    """
    Returns model status, availability, and supported sign classes.
    """
    return classifier_mgr.get_status()

@router.get("/supported-signs")
def get_supported_signs(mode: str = "ASL"):
    """
    Returns supported sign vocabulary for given mode (ASL or ISL).
    """
    try:
        vocab = get_vocabulary(mode)
        model_classes = classifier_mgr.get_status(mode).get("classes", [])
        return {
            "mode": mode.upper(),
            "signs": vocab,
            "trained_classes": model_classes,
            "model_available": classifier_mgr.is_available(mode)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/supported-languages")
def get_languages():
    """
    Returns all 12 supported Indian languages + English.
    """
    return translator.get_supported_languages()

def _decode_base64_image(base64_str: str) -> Optional[np.ndarray]:
    """Helper to convert base64 data URI or raw base64 to OpenCV BGR image"""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None

@router.post("/recognize")
async def recognize_sign(req: RecognizeRequest):
    """
    Core sign recognition pipeline:
    Image Frame -> MediaPipe Landmarks -> Feature Extraction -> Classifier -> Temporal Smoothing -> Sentence
    """
    mode = req.mode.upper()
    if mode not in ("ASL", "ISL", "AUTO"):
        raise HTTPException(status_code=400, detail="Mode must be 'ASL', 'ISL', or 'AUTO'")

    smoother = smoothers[mode]
    if req.confidence_threshold is not None:
        smoother.update_settings(confidence_threshold=req.confidence_threshold)

    frame = _decode_base64_image(req.image)
    if frame is None:
        raise HTTPException(status_code=400, detail="Failed to decode base64 image")

    # 1. Landmark Detection
    multi_lms, handedness, annotated = detector.process_frame(frame, draw_overlay=req.draw_landmarks)

    # Convert landmarks to JSON-serializable structure
    landmarks_data = []
    if multi_lms and handedness:
        for idx, hand_lms in enumerate(multi_lms):
            label = handedness[idx].classification[0].label
            score = float(handedness[idx].classification[0].score)
            points = [{"x": float(p.x), "y": float(p.y), "z": float(p.z)} for p in hand_lms.landmark]
            landmarks_data.append({"hand": label, "score": score, "points": points})

    # 2. Check if model is available
    if mode != "AUTO" and not classifier_mgr.is_available(mode):
        return {
            "status": "model_not_available",
            "mode": mode,
            "sign": None,
            "confidence": 0.0,
            "stable_sign": None,
            "sentence": smoother.get_sentence(),
            "message": f"{mode} model not trained or available. Run scripts/train_models.py to train starter model.",
            "landmarks": landmarks_data
        }

    # 3. Feature Extraction
    features = extractor.extract_features(multi_lms, handedness)

    # 4. Classification
    has_hands = bool(multi_lms and len(multi_lms) > 0)
    if mode == "AUTO":
        asl_sign, asl_conf, asl_probs = classifier_mgr.predict(features, "ASL") if classifier_mgr.is_available("ASL") else (None, 0.0, {})
        isl_sign, isl_conf, isl_probs = classifier_mgr.predict(features, "ISL") if classifier_mgr.is_available("ISL") else (None, 0.0, {})
        
        if asl_conf >= isl_conf and asl_conf > 0:
            best_mode, local_sign, local_conf, probs = "ASL", asl_sign, asl_conf, asl_probs
        elif isl_conf > 0:
            best_mode, local_sign, local_conf, probs = "ISL", isl_sign, isl_conf, isl_probs
        else:
            best_mode, local_sign, local_conf, probs = "ASL", None, 0.0, {}
            
        hybrid_eval = hybrid_recognizer.evaluate_sign(
            mode=best_mode,
            local_sign=local_sign,
            local_conf=local_conf,
            local_probs=probs,
            frame_bgr=frame,
            has_hands=has_hands,
            landmarks_data=landmarks_data
        )
        
        final_sign = hybrid_eval.get("final_sign")
        final_conf = hybrid_eval.get("final_confidence", 0.0)
        
        combined_sign = f"{best_mode}:{final_sign}" if final_sign else None
        stable_sign, newly_emitted, sentence = smoother.process_frame_prediction(combined_sign, final_conf)
        
    else:
        local_sign, local_conf, probs = classifier_mgr.predict(features, mode)
        hybrid_eval = hybrid_recognizer.evaluate_sign(
            mode=mode,
            local_sign=local_sign,
            local_conf=local_conf,
            local_probs=probs,
            frame_bgr=frame,
            has_hands=has_hands,
            landmarks_data=landmarks_data
        )
        final_sign = hybrid_eval.get("final_sign")
        final_conf = hybrid_eval.get("final_confidence", 0.0)
        stable_sign, newly_emitted, sentence = smoother.process_frame_prediction(final_sign, final_conf)

    annotated_b64 = None
    if req.draw_landmarks and annotated is not None:
        _, buffer = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

    return {
        "status": "success",
        "mode": hybrid_eval.get("mode", mode),
        "raw_sign": hybrid_eval.get("local_sign"),
        "confidence": hybrid_eval.get("final_confidence", 0.0),
        "ollama_sign": hybrid_eval.get("ollama_sign"),
        "ollama_confidence": hybrid_eval.get("ollama_confidence", 0.0),
        "stable_sign": stable_sign,
        "newly_emitted": newly_emitted,
        "sentence": sentence,
        "top_probabilities": dict(sorted(probs.items(), key=lambda item: item[1], reverse=True)[:4]) if probs else {},
        "landmarks": landmarks_data,
        "annotated_frame": annotated_b64,
        "recognition_source": hybrid_eval.get("recognition_source", "none")
    }

@router.post("/sentence/update")
def update_sentence(req: SentenceActionRequest):
    mode = req.mode.upper()
    if mode not in smoothers:
        raise HTTPException(status_code=400, detail="Invalid mode")
    smoother = smoothers[mode]

    if req.action == "clear":
        new_sent = smoother.clear_sentence()
    elif req.action == "delete_last":
        new_sent = smoother.delete_last_word()
    elif req.action == "append" and req.word:
        new_sent = smoother.append_manual_word(req.word)
    else:
        new_sent = smoother.get_sentence()

    return {"sentence": new_sent, "mode": mode}

@router.post("/translate")
async def translate_text(req: TranslateRequest):
    """
    Translates English sentence to target Indian language.
    """
    result = await translator.translate(req.text, req.target_language)
    return result

class RefineSentenceRequest(BaseModel):
    text: str = Field(..., description="Telegraphic sign gloss tokens to refine into fluent English")

@router.post("/ollama/refine")
async def refine_sentence(req: RefineSentenceRequest):
    """
    Uses Ollama (llama3.2:1b) to turn sign language glosses into a grammatically fluent sentence.
    """
    result = await ollama_svc.refine_sentence(req.text)
    return result

@router.post("/speak")
def speak_text(req: SpeakRequest):
    """
    Asynchronous text-to-speech execution.
    """
    tts_engine.speak_async(req.text, voice_hint=req.voice_hint or req.language_code)
    return {"status": "dispatched", "text": req.text}

@router.post("/avatar/sign")
def plan_avatar_signing(req: AvatarSignRequest):
    """
    Plans 3D signing avatar animation sequence from text with missing sign fallback.
    """
    plan = avatar_planner.plan_sequence(req.text, req.mode)
    return plan

@router.post("/vision-assist")
async def vision_assist(req: VisionAssistRequest):
    """
    Sends frame to Ollama Vision Model for ambiguous or difficult sign interpretation.
    """
    base64_data = req.image
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]
    res = await ollama_svc.analyze_vision_frame(base64_data, req.context)
    return res

# --- WebSocket Stream for Low-Latency Real-Time Feed ---

@router.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    High-speed WebSocket connection for real-time webcam frame streaming and recognition.
    """
    await websocket.accept()
    mode = "AUTO"
    smoother = smoothers[mode]

    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)

            msg_type = data.get("type", "frame")

            if msg_type == "set_mode":
                new_mode = data.get("mode", "ASL").upper()
                if new_mode in ("ASL", "ISL", "AUTO"):
                    mode = new_mode
                    smoother = smoothers[mode]
                await websocket.send_json({"type": "mode_changed", "mode": mode})
                continue

            elif msg_type == "frame":
                image_b64 = data.get("image", "")
                if not image_b64:
                    continue

                frame = _decode_base64_image(image_b64)
                if frame is None:
                    continue

                is_cropped = data.get("is_cropped", False)
                multi_lms = None
                landmarks_pts = []

                if not is_cropped:
                    multi_lms, handedness, _ = detector.process_frame(frame, draw_overlay=False)
                    if multi_lms and handedness:
                        for idx, hand_lms in enumerate(multi_lms):
                            label = handedness[idx].classification[0].label
                            points = [{"x": float(p.x), "y": float(p.y), "z": float(p.z)} for p in hand_lms.landmark]
                            landmarks_pts.append({"hand": label, "points": points})

                # We disable local classifier check for emergency stabilization
                has_hands = bool(multi_lms and len(multi_lms) > 0) or is_cropped
                
                local_sign = None
                local_conf = 0.0
                probs = {}

                hybrid_eval = hybrid_recognizer.evaluate_sign(
                    mode=mode,
                    local_sign=local_sign,
                    local_conf=local_conf,
                    local_probs=probs,
                    frame_bgr=frame,
                    has_hands=has_hands,
                    landmarks_data=landmarks_pts
                )

                final_sign = hybrid_eval.get("final_sign")
                final_conf = hybrid_eval.get("final_confidence", 0.0)
                stable_sign, newly_emitted, sentence = smoother.process_frame_prediction(final_sign, final_conf)

                await websocket.send_json({
                    "type": "result",
                    "mode": mode,
                    "sign": final_sign if (final_sign and final_sign != "NONE") else "",
                    "confidence": round(final_conf, 2),
                    "local_sign": hybrid_eval.get("local_sign"),
                    "local_confidence": hybrid_eval.get("local_confidence"),
                    "ollama_sign": hybrid_eval.get("ollama_sign"),
                    "ollama_confidence": hybrid_eval.get("ollama_confidence"),
                    "stable_sign": stable_sign,
                    "newly_emitted": newly_emitted,
                    "sentence": sentence,
                    "model_available": True,
                    "landmarks": landmarks_pts,
                    "source": hybrid_eval.get("recognition_source"),
                    "ollama_status": hybrid_eval.get("ollama_status")
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@router.post("/debug/vision-test")
async def debug_vision_test(req: VisionAssistRequest):
    import time
    t0 = time.time()
    res = await vision_svc.recognize_sign(req.image, {}, {}, [], [])
    return {"model": vision_svc.vision_model, "parsed_response": res, "latency": time.time() - t0}

@router.post("/debug/landmarks")
async def debug_landmarks(req: VisionAssistRequest):
    frame = _decode_base64_image(req.image)
    multi_lms, handedness, _ = detector.process_frame(frame, draw_overlay=False)
    pts = []
    has_left, has_right = False, False
    if multi_lms and handedness:
        features = extractor.extract_features(multi_lms, handedness)
        has_left, has_right = features[0] > 0.5, features[80] > 0.5
        for idx, hand_lms in enumerate(multi_lms):
            label = handedness[idx].classification[0].label
            pts.append({"hand": label, "points": [{"x": p.x, "y": p.y, "z": p.z} for p in hand_lms.landmark]})
    return {"hands": len(pts), "left": has_left, "right": has_right, "landmarks": pts}

