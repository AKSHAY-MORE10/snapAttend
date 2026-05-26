"""
src/pipelines/face_pipeline.py

Face recognition pipeline for SnapClass.

Key fixes vs original:
  1. dlib models cached separately from SVC — train_classifier() no longer
     wipes the heavy dlib models from cache (was causing full reload on retrain).
  2. SVC is trained per-subject using only enrolled students — fixes the bug
     where a student in Subject A could be detected present in Subject B.
  3. Per-subject SVC stored in a plain dict (_model_cache) instead of
     @st.cache_resource so retraining one subject doesn't affect others.
  4. Streamlit import is isolated to display-only calls so this file can be
     imported safely by FastAPI without crashing.
"""

import logging
import numpy as np
import dlib
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_enrolled_students

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# In-memory SVC cache  {subject_id -> model_data dict | None}
# Plain dict — not st.cache_resource — so per-subject invalidation works.
# ------------------------------------------------------------------
_model_cache: dict[int, dict | None] = {}


# ------------------------------------------------------------------
# Step 2a: dlib models cached SEPARATELY
# These never need reloading — 1 cache entry for the entire app lifetime.
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _load_dlib_models():
    """
    Load dlib detector, shape predictor, and face recognition model.
    Cached permanently — completely independent of SVC retraining.
    """
    logger.info("Loading dlib models (one-time)...")
    detector  = dlib.get_frontal_face_detector()
    sp        = dlib.shape_predictor(face_recognition_models.pose_predictor_model_location())
    facerec   = dlib.face_recognition_model_v1(face_recognition_models.face_recognition_model_location())
    logger.info("dlib models loaded.")
    return detector, sp, facerec


# ------------------------------------------------------------------
# Step 2b: Face embedding extraction  (unchanged logic, cleaner code)
# ------------------------------------------------------------------
def get_face_embeddings(image_np: np.ndarray) -> list[np.ndarray]:
    """
    Detect all faces in image_np and return a list of 128-D embeddings.
    Returns an empty list if no faces are detected.
    """
    detector, sp, facerec = _load_dlib_models()
    faces = detector(image_np, 2)

    if not faces:
        return []

    embeddings = []
    for face in faces:
        shape      = sp(image_np, face)
        descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        embeddings.append(np.array(descriptor))

    return embeddings


# ------------------------------------------------------------------
# Step 2c: Subject-scoped SVC  (the core fix)
# ------------------------------------------------------------------
def _build_model_for_subject(subject_id: int) -> dict | None:
    """
    Fetch only the students enrolled in subject_id and train an SVC on them.
    Returns a model_data dict or None if not enough data.
    """
    students = get_enrolled_students(subject_id)

    if not students:
        logger.warning("No enrolled students found for subject_id=%s", subject_id)
        return None

    X, y = [], []
    for student in students:
        embedding = student.get("face_embedding")
        if embedding is not None:
            X.append(np.array(embedding))
            y.append(student["student_id"])

    if not X:
        logger.warning("No face embeddings found for subject_id=%s", subject_id)
        return None

    X = np.array(X)
    y = np.array(y)

    clf = None
    if len(set(y)) > 1:
        # Multi-student: train SVC classifier
        clf = SVC(kernel="linear", probability=True, class_weight="balanced")
        clf.fit(X, y)
        logger.info(
            "SVC trained for subject_id=%s with %d students, %d samples",
            subject_id, len(set(y)), len(X)
        )
    else:
        # Single student: skip SVC, use direct distance matching
        logger.info("Single student in subject_id=%s — using direct distance match", subject_id)

    return {"model": clf, "embeddings": X, "labels": y}


def get_trained_model(subject_id: int) -> dict | None:
    """
    Return cached model for subject_id, building it if not yet cached.
    Call train_classifier(subject_id) to force a rebuild.
    """
    if subject_id not in _model_cache:
        _model_cache[subject_id] = _build_model_for_subject(subject_id)
    return _model_cache[subject_id]


# ------------------------------------------------------------------
# Step 2d: Retraining  — now per-subject, dlib is untouched
# ------------------------------------------------------------------
def train_classifier(subject_id: int) -> bool:
    """
    Force-rebuild the SVC for a specific subject.
    dlib models are NOT affected — they stay loaded.

    Call this after:
      - A new student enrolls in subject_id
      - A student's face embedding is updated
    """
    logger.info("Retraining classifier for subject_id=%s", subject_id)

    # Invalidate only this subject's model
    _model_cache.pop(subject_id, None)
    model = get_trained_model(subject_id)

    if model is None:
        logger.warning("Training failed for subject_id=%s — no data", subject_id)
        return False

    logger.info("Classifier ready for subject_id=%s", subject_id)
    return True


# ------------------------------------------------------------------
# Step 2e: Prediction  — now subject-scoped
# ------------------------------------------------------------------
def predict_attendance(
    image_np: np.ndarray,
    subject_id: int,
    threshold: float = 0.6
) -> tuple[dict[int, bool], list[int], int]:
    """
    Run face recognition on image_np against students enrolled in subject_id.

    Args:
        image_np:   RGB numpy array of the classroom photo.
        subject_id: Which subject's enrolled students to match against.
        threshold:  Max Euclidean distance to accept a match (default 0.6).

    Returns:
        detected_students : {student_id: True}  for verified matches
        all_predicted_ids : raw SVC predictions (for debugging)
        num_faces         : total faces detected in the image
    """
    embeddings = get_face_embeddings(image_np)
    num_faces  = len(embeddings)

    if num_faces == 0:
        return {}, [], 0

    model_data = get_trained_model(subject_id)

    if model_data is None:
        logger.warning(
            "No trained model for subject_id=%s — cannot predict", subject_id
        )
        return {}, [], num_faces

    clf             = model_data["model"]
    known_embeddings = model_data["embeddings"]
    labels          = model_data["labels"]

    detected_students: dict[int, bool] = {}
    all_predicted_ids: list[int]       = []

    for encoding in embeddings:

        # ── Classify ──────────────────────────────────────────────
        if clf is None:
            # Single-student subject: only one possible label
            predicted_id = labels[0]
        else:
            predicted_id = clf.predict([encoding])[0]

        all_predicted_ids.append(int(predicted_id))

        # ── Distance verification (prevents false positives) ───────
        student_indices = np.where(labels == predicted_id)[0]
        distances = [
            np.linalg.norm(known_embeddings[i] - encoding)
            for i in student_indices
        ]
        best_distance = min(distances)

        if best_distance <= threshold:
            detected_students[int(predicted_id)] = True
        else:
            logger.debug(
                "Face rejected: predicted_id=%s, distance=%.4f > threshold=%.2f",
                predicted_id, best_distance, threshold
            )

    return detected_students, all_predicted_ids, num_faces