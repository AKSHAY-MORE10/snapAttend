import numpy as np
import io
import librosa
import streamlit as st
from resemblyzer import VoiceEncoder, preprocess_wav


# -----------------------------
# Load Encoder (Cached)
# -----------------------------
@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()


# -----------------------------
# Normalize Vector
# -----------------------------
def normalize(vec):
    vec = np.array(vec)
    return vec / (np.linalg.norm(vec) + 1e-9)


# -----------------------------
# Get Voice Embedding
# -----------------------------
def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)

        if len(audio) < sr * 0.5:
            st.warning("Audio too short")
            return None

        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)

        return normalize(embedding)

    except Exception:
        st.error("Voice recognition error")
        return None


# -----------------------------
# Identify Speaker
# -----------------------------
def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    new_embedding = normalize(new_embedding)

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding is None:
            continue

        stored_embedding = normalize(stored_embedding)

        similarity = np.dot(new_embedding, stored_embedding)

        if similarity > best_score:
            best_score = similarity
            best_sid = sid

    if best_score >= threshold:
        return best_sid, float(best_score)

    return None, float(best_score)


# -----------------------------
# Bulk Audio Processing
# -----------------------------
def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)

        if len(audio) == 0:
            return {}

        # Split into speech segments
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}

        for start, end in segments:

            # Ignore very short segments
            if (end - start) < sr * 0.5:
                continue

            segment_audio = audio[start:end]

            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)
            embedding = normalize(embedding)

            sid, score = identify_speaker(
                embedding, candidates_dict, threshold
            )

            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results

    except Exception:
        st.error("Bulk processing error")
        return {}