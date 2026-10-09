import pytest
import numpy as np
from pathlib import Path

from backend.recognition.feature_extractor import LandmarkFeatureExtractor, FEATURE_VECTOR_LENGTH
from backend.recognition.sign_classifier import SignClassifierManager
from backend.recognition.temporal_smoother import TemporalSmoother
from backend.recognition.sign_vocabulary import get_sign_list, ASL_VOCABULARY, ISL_VOCABULARY

def test_feature_extractor_empty():
    extractor = LandmarkFeatureExtractor()
    features = extractor.extract_features(None, None)
    assert features.shape == (FEATURE_VECTOR_LENGTH,)
    assert np.all(features == 0)

def test_classifier_status():
    mgr = SignClassifierManager()
    status = mgr.get_status()
    assert "ASL" in status
    assert "ISL" in status
    assert status["ASL"]["available"] is True
    assert status["ISL"]["available"] is True
    assert len(status["ASL"]["classes"]) > 5
    assert len(status["ISL"]["classes"]) > 5

def test_classifier_predict_none():
    mgr = SignClassifierManager()
    empty_features = np.zeros(FEATURE_VECTOR_LENGTH, dtype=np.float32)
    sign, conf, probs = mgr.predict(empty_features, "ASL")
    assert sign == "NONE"
    assert conf == 1.0

def test_temporal_smoother_debouncing():
    smoother = TemporalSmoother(window_size=6, confidence_threshold=0.6, debounce_frames=8)

    # Send 10 identical 'HELLO' signs
    emitted_count = 0
    for _ in range(10):
        stable_sign, newly_emitted, sentence = smoother.process_frame_prediction("HELLO", 0.95)
        if newly_emitted:
            emitted_count += 1

    # Should only emit HELLO once, preventing "HELLO HELLO HELLO"
    assert emitted_count == 1
    assert smoother.get_sentence() == "HELLO"

    # Reset with neutral frames
    for _ in range(5):
        smoother.process_frame_prediction("NONE", 0.0)

    # Now sign THANK_YOU
    emitted_thank_you = False
    for _ in range(8):
        stable, new_emit, sentence = smoother.process_frame_prediction("THANK_YOU", 0.90)
        if new_emit:
            emitted_thank_you = True

    assert emitted_thank_you is True
    assert smoother.get_sentence() == "HELLO THANK_YOU"

def test_sentence_editing():
    smoother = TemporalSmoother()
    smoother.append_manual_word("HELLO")
    smoother.append_manual_word("WATER")
    assert smoother.get_sentence() == "HELLO WATER"

    smoother.delete_last_word()
    assert smoother.get_sentence() == "HELLO"

    smoother.clear_sentence()
    assert smoother.get_sentence() == ""


class MockLandmark:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class MockHandLandmarks:
    def __init__(self):
        self.landmark = [MockLandmark(i/100, i/100, i/100) for i in range(21)]

class MockClassification:
    def __init__(self, label):
        self.label = label

class MockHandedness:
    def __init__(self, label):
        self.classification = [MockClassification(label)]

def test_feature_extractor_left_hand_presence():
    extractor = LandmarkFeatureExtractor()
    lms = [MockHandLandmarks()]
    handedness = [MockHandedness("Left")]
    features = extractor.extract_features(lms, handedness)
    assert features[0] == 1.0
    assert features[80] == 0.0

def test_feature_extractor_right_hand_presence():
    extractor = LandmarkFeatureExtractor()
    lms = [MockHandLandmarks()]
    handedness = [MockHandedness("Right")]
    features = extractor.extract_features(lms, handedness)
    assert features[0] == 0.0
    assert features[80] == 1.0

def test_feature_extractor_two_hand_presence():
    extractor = LandmarkFeatureExtractor()
    lms = [MockHandLandmarks(), MockHandLandmarks()]
    handedness = [MockHandedness("Left"), MockHandedness("Right")]
    features = extractor.extract_features(lms, handedness)
    assert features[0] == 1.0
    assert features[80] == 1.0
    assert features[160] == 1.0

def test_feature_extractor_no_hand_presence():
    extractor = LandmarkFeatureExtractor()
    features = extractor.extract_features([], [])
    assert features[0] == 0.0
    assert features[80] == 0.0
    assert features[160] == 0.0
