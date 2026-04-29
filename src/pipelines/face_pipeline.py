import numpy as np
import dlib
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


# -----------------------------
# Load Models (Cached)
# -----------------------------
@st.cache_resource
def load_dlib_model():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


# -----------------------------
# Face Embedding Pipeline
# -----------------------------
def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_model()
    faces = detector(image_np, 2)  # better detection

    if len(faces) == 0:
        return []

    encodings = []

    for face in faces:
        shape = sp(image_np, face)
        descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(descriptor))

    return encodings


# -----------------------------
# Train Model
# -----------------------------
@st.cache_resource
def get_trained_model():
    student_db = get_all_students()

    if not student_db:
        return None

    X = []
    y = []

    for student in student_db:
        embedding = student.get("face_embedding")
        if embedding is not None:
            X.append(np.array(embedding))
            y.append(student.get("student_id"))

    if len(X) == 0:
        return None

    X = np.array(X)
    y = np.array(y)

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")

    # Handle case with only 1 student
    if len(set(y)) > 1:
        clf.fit(X, y)
    else:
        clf = None  # Skip training

    return {
        "model": clf,
        "embeddings": X,
        "labels": y
    }


# -----------------------------
# Retrain Trigger
# -----------------------------
def train_classifier():
    st.cache_resource.clear()
    model = get_trained_model()

    if model is None:
        st.warning("No students available for training.")
        return False

    st.success("Model trained successfully!")
    return True


# -----------------------------
# Predict Attendance
# -----------------------------
def predict_attendance(image_np, threshold=0.6):
    model_data = get_trained_model()

    if model_data is None:
        st.warning("Model not trained.")
        return {}

    embeddings = get_face_embeddings(image_np)

    if len(embeddings) == 0:
        st.warning("No faces detected.")
        return {}

    clf = model_data["model"]
    known_embeddings = model_data["embeddings"]
    labels = model_data["labels"]

    detected_students = {}

    for encoding in embeddings:

        # ---------------------
        # Case 1: Only 1 student
        # ---------------------
        if clf is None:
            predicted_id = labels[0]

        else:
            predicted_id = clf.predict([encoding])[0]

        # ---------------------
        # Distance Verification (IMPORTANT)
        # ---------------------
        student_indices = np.where(labels == predicted_id)[0]

        # Take closest embedding of that student
        distances = [
            np.linalg.norm(known_embeddings[i] - encoding)
            for i in student_indices
        ]

        best_distance = min(distances)

        if best_distance <= threshold:
            detected_students[int(predicted_id)] = True

    return detected_students