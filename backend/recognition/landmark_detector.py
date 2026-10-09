import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional, Any
from dataclasses import dataclass

class MockHandedness:
    def __init__(self, index, score, label):
        self.classification = [MockClassification(index, score, label)]

class MockClassification:
    def __init__(self, index, score, label):
        self.index = index
        self.score = score
        self.label = label

class LandmarkDetector:
    """
    MediaPipe Holistic wrapper for real-time full-body tracking on webcam frames.
    Captures Face, Pose (shoulders, chest), and Hands for deeper Ollama context.
    Maps hand results back to legacy multi_hand format for Sklearn compat.
    """

    def __init__(self, static_image_mode: bool = False, max_num_hands: int = 2,
                 min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=static_image_mode,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(self, frame_bgr: np.ndarray, draw_overlay: bool = True,
                      mirror_frame: bool = False) -> Tuple[Any, Any, np.ndarray]:
        """
        Processes BGR image from webcam or frame buffer using Holistic model.
        Returns:
            (multi_hand_landmarks, multi_handedness, annotated_frame_bgr)
            (We map holistic hands back to multi_hand format for legacy support)
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return None, None, frame_bgr

        if len(frame_bgr.shape) != 3 or frame_bgr.shape[2] != 3:
            return None, None, frame_bgr

        working_frame = cv2.flip(frame_bgr, 1) if mirror_frame else frame_bgr

        frame_rgb = cv2.cvtColor(working_frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        results = self.holistic.process(frame_rgb)

        annotated_frame = working_frame.copy() if draw_overlay else working_frame

        if draw_overlay:
            # Draw Face
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.face_landmarks,
                self.mp_holistic.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style())
            # Draw Pose (Shoulders, Chest, Arms)
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
            # Draw Hands
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.left_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_hand_landmarks_style())
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.right_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_hand_landmarks_style())

        # Map to legacy multi_hand_landmarks and multi_handedness
        multi_hand_landmarks = []
        multi_handedness = []

        if results.left_hand_landmarks:
            multi_hand_landmarks.append(results.left_hand_landmarks)
            multi_handedness.append(MockHandedness(0, 0.99, "Left"))
        if results.right_hand_landmarks:
            multi_hand_landmarks.append(results.right_hand_landmarks)
            multi_handedness.append(MockHandedness(1, 0.99, "Right"))

        if not multi_hand_landmarks:
            multi_hand_landmarks = None
            multi_handedness = None

        return multi_hand_landmarks, multi_handedness, annotated_frame

    def close(self):
        """Release MediaPipe resources"""
        if self.holistic:
            self.holistic.close()
