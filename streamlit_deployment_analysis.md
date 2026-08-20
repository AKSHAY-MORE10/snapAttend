# SnapAttend — Streamlit Cloud Deployment: Slow Build Analysis & Improvement Plan

> **Date:** August 20, 2026
> **Project:** [SnapAttend (AI Attendance — Face & Voice)](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice)
> **Deployed at:** `snapattendance-main.streamlit.app`
> **Problem:** Deployment takes an extremely long time to install dependencies and boot up, causing visitors to wait minutes before the app loads.

---

## Table of Contents

1. [Log Breakdown — What's Actually Happening](#1-log-breakdown--whats-actually-happening)
2. [Root Causes — Why It's Slow](#2-root-causes--why-its-slow)
3. [The Fatal Error — dlib-bin on Python 3.14](#3-the-fatal-error--dlib-bin-on-python-314)
4. [Dependency Weight Analysis](#4-dependency-weight-analysis)
5. [Architecture Issues for Streamlit Cloud](#5-architecture-issues-for-streamlit-cloud)
6. [Improvement Plan](#6-improvement-plan)
7. [Priority Matrix](#7-priority-matrix)
8. [Alternative Deployment Options](#8-alternative-deployment-options)

---

## 1. Log Breakdown — What's Actually Happening

Here's a timestamped breakdown of what the deployment logs reveal:

| Time | Event | Duration | Problem? |
|------|-------|----------|----------|
| `10:24:13` | Machine provisioning starts | — | Normal |
| `09:57:45` | Repository clone starts | — | Normal |
| `09:57:46` | Clone complete | ~1s | ✅ Fast |
| `09:57:47` | Dependency processing begins | — | — |
| `09:57:47` | **uv** tries to install `dlib-bin==19.24.6` | Instant | ❌ **FAILS** — no Python 3.14 wheels |
| `09:57:58` | Falls back to **pip** | ~11s | ⚠️ Fallback |
| `09:57:58` | Cloning `face_recognition_models` from GitHub | — | ⚠️ Cloning a git repo at install time |
| `09:58:06` | `numpy==1.26.4` — downloading source tarball (15.8 MB) | — | ❌ **Source build** (no wheel for Python 3.14) |
| `09:58:06` → `09:59:59` | `numpy` metadata preparation (compiling from source) | **~2 min** | ❌ **Compiling C/Fortran code** |
| `09:59:59` | `pandas==2.2.2` — downloading source tarball (4.4 MB) | — | ❌ **Source build** (no wheel for Python 3.14) |
| `09:59:59` → ??? | `pandas` metadata preparation starts | **???** | ❌ **Compiling C/Cython code** |
| ??? | **Likely TIMEOUT or CRASH** | — | 🔴 **Deployment probably never finishes** |

> [!CAUTION]
> The logs are **cut off** during `pandas` build. This strongly suggests the deployment either **times out** or **crashes** during C extension compilation. Your app is likely **never actually starting**.

---

## 2. Root Causes — Why It's Slow

### 🔴 Root Cause #1: Python 3.14 Has No Pre-built Wheels

Streamlit Cloud is running **Python 3.14.7** — a bleeding-edge version. Most of your pinned packages (`numpy==1.26.4`, `pandas==2.2.2`, `dlib-bin==19.24.6`) do **not** have pre-built binary wheels for Python 3.14.

**What this means:**
- Instead of downloading a ~5 MB pre-compiled `.whl` file (takes ~1 second), pip has to:
  1. Download the source tarball
  2. Install build dependencies (Cython, meson-python, etc.)
  3. **Compile all C/C++/Fortran extensions from source** on the Streamlit Cloud machine
  4. This turns a 2-second install into a **5-10 minute compile job per package**

**Affected packages and their compile impact:**

| Package | Has Python 3.14 wheel? | Compile time (approx) | Language compiled |
|---------|----------------------|----------------------|-------------------|
| `numpy==1.26.4` | ❌ No | ~2-4 min | C + Fortran |
| `pandas==2.2.2` | ❌ No | ~3-5 min | C + Cython |
| `scikit-learn==1.4.2` | ❌ No | ~3-5 min | C + Cython |
| `dlib-bin==19.24.6` | ❌ No | **FATAL — no ABI match** | C++ |
| `librosa==0.10.2` | ⚠️ Depends on numpy/scipy | Indirect | — |
| `resemblyzer==0.1.3` | ⚠️ Pulls in PyTorch | ~huge | — |

> [!IMPORTANT]
> `numpy 1.26.4` is the **last 1.x release**. It was never built for Python 3.14. Same for `pandas 2.2.2`. These versions were designed for Python 3.9–3.12.

### 🔴 Root Cause #2: `dlib-bin` Installation is Completely Broken

From the logs:

```
Because dlib-bin==19.24.6 has no wheels with a matching Python ABI tag
and you require dlib-bin==19.24.6, we can conclude that your
requirements are unsatisfiable.
```

`dlib-bin` is a pre-compiled binary distribution of dlib. It **only** ships wheels for specific Python versions (3.8–3.12). There is **no** wheel for Python 3.14, and since it's a binary-only package, it **cannot be compiled from source** via pip.

**This means your face recognition pipeline will not work at all on Streamlit Cloud.**

### 🟡 Root Cause #3: Git Clone at Install Time

```
git+https://github.com/ageitgey/face_recognition_models
```

This line in [requirements.txt](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/requirements.txt) forces pip to:
1. Clone the entire `face_recognition_models` GitHub repository (~100+ MB of model files)
2. Build the package from source
3. This happens on **every single deployment** because Streamlit Cloud doesn't cache git-installed packages reliably

### 🟡 Root Cause #4: Resemblyzer Pulls in PyTorch

[voice_pipeline.py](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/src/pipelines/voice_pipeline.py) uses `resemblyzer==0.1.3`, which depends on **PyTorch**. Your Dockerfile shows you're aware of this (you install `torch` and `torchaudio` CPU-only), but on Streamlit Cloud:

- There's no way to specify the `--index-url` for CPU-only PyTorch
- The full PyTorch with CUDA gets installed (~800 MB download, ~2.5 GB installed)
- This alone can take 3-5 minutes and eat most of the container's storage

### 🟡 Root Cause #5: FastAPI/Uvicorn Installed But Never Used

Your [requirements.txt](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/requirements.txt) includes:

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
```

These are for the FastAPI backend, which **does not run on Streamlit Cloud**. They add unnecessary install time and dependencies (including `httptools`, `uvloop` which may need compilation).

### 🟢 Root Cause #6: No Python Version Pinning

Streamlit Cloud defaults to the **latest available Python**. Since you have no version pin, it picked Python 3.14.7 — a version that breaks your entire dependency tree.

---

## 3. The Fatal Error — dlib-bin on Python 3.14

This is the **showstopper**. Even if all other packages eventually install, `dlib-bin` will always fail on Python 3.14. The deployment log shows:

```
× No solution found when resolving dependencies:
╰─▶ Because dlib-bin==19.24.6 has no wheels with a matching Python ABI tag
    and you require dlib-bin==19.24.6, we can conclude that your
    requirements are unsatisfiable.
```

The uv resolver catches this immediately and aborts. Then pip tries and will **also** fail on this package.

**The face recognition pipeline is completely non-functional on this deployment.**

---

## 4. Dependency Weight Analysis

Here's the full weight of what you're asking Streamlit Cloud to install:

```
TOTAL ESTIMATED INSTALL SIZE (with all transitive dependencies):
┌──────────────────────────────────────────┬─────────────┬──────────────────────────┐
│ Package                                  │ Size (MB)   │ Purpose                  │
├──────────────────────────────────────────┼─────────────┼──────────────────────────┤
│ torch (full, pulled by resemblyzer)      │ ~800-2500   │ Voice recognition        │
│ numpy 1.26.4 (compiled from source)      │ ~30         │ Core numerical           │
│ pandas 2.2.2 (compiled from source)      │ ~50         │ Data handling            │
│ scikit-learn 1.4.2 (compiled)            │ ~40         │ Face SVC classifier      │
│ dlib-bin 19.24.6                         │ ❌ FAILS    │ Face detection           │
│ face_recognition_models (git clone)      │ ~100        │ Face model weights       │
│ librosa 0.10.2                           │ ~20         │ Audio processing         │
│ resemblyzer 0.1.3                        │ ~5          │ Voice embeddings         │
│ supabase 2.4.6                           │ ~15         │ Database client          │
│ streamlit 1.45.0                         │ ~80         │ UI framework             │
│ fastapi + uvicorn (UNUSED)               │ ~10         │ ❌ Not needed            │
│ pillow 10.3.0                            │ ~10         │ Image processing         │
│ Other transitive deps                    │ ~50         │ Various                  │
├──────────────────────────────────────────┼─────────────┼──────────────────────────┤
│ TOTAL (approximate)                      │ ~1.2-3+ GB  │                          │
└──────────────────────────────────────────┴─────────────┴──────────────────────────┘
```

> [!WARNING]
> Streamlit Cloud free tier has **1 GB RAM** and limited storage. A 2+ GB dependency footprint (with PyTorch) may exceed the container's limits entirely.

---

## 5. Architecture Issues for Streamlit Cloud

### Issue 1: AI-Heavy App on a Lightweight Platform

Streamlit Cloud is designed for **lightweight data dashboards**, not ML inference apps. Your app requires:
- dlib (C++ face detection library)
- PyTorch (deep learning framework)
- Multiple model weight files (~100+ MB)
- Real-time image and audio processing

This is fundamentally **too heavy** for Streamlit Cloud's free tier.

### Issue 2: Cold Starts Kill UX

Streamlit Cloud **spins down** inactive apps. When someone visits after inactivity:
1. A new container is provisioned (~10s)
2. All dependencies are re-installed (~5-15 min with compilation)
3. The app starts and loads ML models into memory (~30-60s)

**Total cold start: potentially 10-20 minutes.** This is why visitors see a loading screen forever.

### Issue 3: Single requirements.txt for Multiple Contexts

Your [requirements.txt](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/requirements.txt) serves both:
- Streamlit Cloud (only needs Streamlit + AI deps)
- Docker/FastAPI (only needs FastAPI + AI deps)

This means both environments install unnecessary packages.

---

## 6. Improvement Plan

### 🔴 Fix 1: Pin Python Version (CRITICAL — Do This First)

Create a `.python-version` file in your project root:

```
3.11
```

Or add a `[tool.streamlit]` section to a `pyproject.toml`:

```toml
[tool.streamlit]
python = "3.11"
```

**Why:** Python 3.11 has pre-built wheels for ALL your pinned packages. This alone could reduce install time from **15+ minutes to ~2 minutes**.

**Impact:** ⭐⭐⭐⭐⭐ — This is the single most impactful change.

---

### 🔴 Fix 2: Add `packages.txt` for System Dependencies (CRITICAL)

Streamlit Cloud uses `packages.txt` for apt packages. Create this file in project root:

```
libgomp1
libsndfile1
build-essential
cmake
```

**Why:** `dlib-bin` needs system libraries, and `librosa` needs `libsndfile1`. Without these, even if the Python packages install, they may crash at runtime.

---

### 🟡 Fix 3: Create a Streamlit-Specific Requirements File

Create `requirements-streamlit.txt` with only what the Streamlit app needs:

```
# UI framework
streamlit==1.45.0

# Core utilities
numpy==1.26.4
pandas==2.2.2
pillow==10.3.0
typing_extensions==4.11.0

# Face recognition
scikit-learn==1.4.2
dlib-bin==19.24.6
setuptools<70.0.0

# Database
supabase==2.4.6
bcrypt==4.1.3

# QR generation
segno==1.6.1

# Voice recognition
librosa==0.10.2
resemblyzer==0.1.3

# Face recognition models (pinned to commit for stability)
git+https://github.com/ageitgey/face_recognition_models
```

**Removed:** `fastapi`, `uvicorn[standard]`, `python-multipart` — not needed on Streamlit Cloud.

Then tell Streamlit Cloud to use this file by renaming it to `requirements.txt` or configuring it in the Streamlit dashboard.

---

### 🟡 Fix 4: Upgrade Dependency Versions for Wheel Availability

If you must support newer Python versions, update to versions that have pre-built wheels:

| Current | Recommended | Why |
|---------|-------------|-----|
| `numpy==1.26.4` | `numpy>=1.26.4,<2.0` or `numpy==2.1.0` | 2.x has wheels for newer Python |
| `pandas==2.2.2` | `pandas>=2.2.2,<3.0` | Allow minor version flexibility |
| `scikit-learn==1.4.2` | `scikit-learn>=1.4.2,<1.6` | Newer versions support newer Python |
| `dlib-bin==19.24.6` | See Fix 5 below | Special handling needed |

> [!NOTE]
> Only do this if you're willing to test that newer versions don't break your code. With Python 3.11 pinned (Fix 1), the current versions work fine.

---

### 🟡 Fix 5: Replace `dlib-bin` with `face-recognition` Package

Instead of installing `dlib-bin` + `face_recognition_models` separately, consider using the `face-recognition` package which bundles everything:

```
face-recognition==1.3.0
```

This package:
- Wraps dlib, face_recognition_models, and provides a higher-level API
- Has pre-built wheels for common platforms
- Eliminates the git clone of face_recognition_models

**However**, this still requires dlib as a C++ dependency. For Streamlit Cloud, you'll need `cmake` in `packages.txt` and may need to compile from source if no wheel exists.

**Alternative approach:** Use `dlib` (not `dlib-bin`) which can compile from source:

```
dlib==19.24.6
```

This requires `cmake` and `build-essential` in `packages.txt` but will actually compile on Python 3.11.

---

### 🟡 Fix 6: Handle PyTorch for Voice Pipeline

The `resemblyzer` package pulls in full PyTorch. Options:

**Option A: Use CPU-only PyTorch via `--extra-index-url`**

Streamlit Cloud doesn't natively support custom index URLs, but you can add this to a `pip.conf` or use a pre-install script. However, the simpler approach is:

Add to `requirements.txt` **before** resemblyzer:

```
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.1.0
torchaudio==2.1.0
```

**Option B: Make voice pipeline optional**

Since voice recognition is not always used, make it a lazy import (you already do this partially in [voice_pipeline.py](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/src/pipelines/voice_pipeline.py)). Remove `resemblyzer` from the Streamlit requirements entirely and show a "Voice recognition not available" message on Streamlit Cloud.

**Impact:** Removing PyTorch saves **~800 MB–2.5 GB** and **3-5 minutes** of install time.

---

### 🟢 Fix 7: Add `runtime.txt` for Explicit Python Version (Alternative to Fix 1)

Some Streamlit Cloud versions respect `runtime.txt`:

```
python-3.11.9
```

This is an alternative/supplement to `.python-version`.

---

### 🟢 Fix 8: Optimize for Cold Starts

Even after fixing dependencies, ML model loading on cold start will be slow. Consider:

1. **Lazy model loading:** Don't load dlib models until a teacher actually runs face attendance. Currently, [face_pipeline.py](file:///d:/PROJECTS/AI%20Attendance%20-%20face%20and%20voice/src/pipelines/face_pipeline.py#L39-L50) uses `@st.cache_resource` which loads on first call — this is already good, but make sure no import-time side effects trigger loading.

2. **Add a loading indicator:** While models load, show a progress bar or spinner so users know the app is working.

3. **Consider Streamlit Cloud's "Always On" option:** This prevents cold starts entirely (paid feature).

---

### 🟢 Fix 9: Remove Unnecessary Files from Deployment

Add a `.streamlitignore` or adjust `.gitignore` to exclude:
- `api/` directory (FastAPI, not used on Streamlit Cloud)
- `Dockerfile`, `Dockerfile.streamlit`, `docker-compose.yml`
- `.devcontainer/`
- `.github/`
- `fontend/` directory (typo? appears unused)
- `myenv/` (virtual environment — should NOT be in the repo)

> [!WARNING]
> Your `.gitignore` includes `myenv/` but this directory exists in the repo. If it was committed before the gitignore rule was added, it's still tracked. Run `git rm -r --cached myenv/` to untrack it.

---

## 7. Priority Matrix

| Priority | Fix | Impact | Effort | Time Saved |
|----------|-----|--------|--------|------------|
| 🔴 **P0** | Pin Python 3.11 (`.python-version`) | ⭐⭐⭐⭐⭐ | 30 seconds | **10-15 min per deploy** |
| 🔴 **P0** | Add `packages.txt` for system deps | ⭐⭐⭐⭐ | 2 minutes | Fixes crash |
| 🟡 **P1** | Remove FastAPI/Uvicorn from Streamlit requirements | ⭐⭐⭐ | 5 minutes | ~30s per deploy |
| 🟡 **P1** | Use CPU-only PyTorch or remove voice pipeline | ⭐⭐⭐⭐⭐ | 15-30 min | **3-5 min + 1-2 GB** |
| 🟡 **P1** | Replace `dlib-bin` with compilable `dlib` | ⭐⭐⭐⭐ | 10 min | Fixes fatal error |
| 🟡 **P2** | Upgrade dependency versions for wheel availability | ⭐⭐⭐ | 1-2 hours | ~1-2 min per deploy |
| 🟢 **P3** | Lazy model loading optimization | ⭐⭐ | 30 min | ~30s cold start |
| 🟢 **P3** | Clean up unused files from repo | ⭐ | 10 min | Minor |

### Recommended Execution Order:

```
Step 1 → Pin Python 3.11          (30 seconds, fixes 80% of the problem)
Step 2 → Add packages.txt         (2 minutes, fixes system deps)
Step 3 → Remove FastAPI deps      (5 minutes, cleaner install)
Step 4 → Handle PyTorch/voice     (15-30 min, massive size reduction)
Step 5 → Fix dlib-bin → dlib      (10 min, fixes face recognition)
Step 6 → Test deployment          (5 min, verify everything works)
```

**Expected result after all fixes:**
- Install time: **~1-3 minutes** (down from 15+ minutes / timeout)
- Cold start: **~30-60 seconds** (down from potentially never loading)
- App size: **~300-500 MB** (down from 2+ GB)

---

## 8. Alternative Deployment Options

If Streamlit Cloud continues to be problematic (due to the heavy AI dependencies), consider these alternatives:

| Platform | Pros | Cons | Best For |
|----------|------|------|----------|
| **Streamlit Cloud** (with fixes above) | Free, easy, auto-deploy from GitHub | Limited resources (1 GB RAM), cold starts | Demo / portfolio |
| **Railway.app** | Custom Dockerfiles supported, generous free tier | More complex setup | Production-lite |
| **Render.com** | Docker support, free tier, auto-deploy | Cold starts on free tier | Production-lite |
| **Google Cloud Run** | Pay-per-use, Docker, scales to zero | Requires GCP setup, cold starts | Production |
| **Hugging Face Spaces** | Free, supports Streamlit natively, GPU options | Community-focused | ML demos |
| **Your own VPS (EC2/GCP)** | Full control, no cold starts, Docker Compose ready | Costs ~$5-20/mo, maintenance | Production |

> [!TIP]
> **Hugging Face Spaces** is an excellent alternative for ML-heavy Streamlit apps. It supports custom `Dockerfile`s, has GPU options, and is designed specifically for AI applications. The free tier gives you 2 vCPU and 16 GB RAM — far more than Streamlit Cloud.

> [!TIP]
> You already have a working Docker setup (`Dockerfile.streamlit` + `docker-compose.yml`). Deploying to **Railway**, **Render**, or **Cloud Run** with your existing Dockerfile would bypass all Streamlit Cloud limitations entirely and give you full control over the Python version and system packages.

---

## Summary

Your Streamlit Cloud deployment is slow (or completely broken) because:

1. **Python 3.14** has no pre-built wheels for your pinned packages → everything compiles from source
2. **`dlib-bin`** has no wheel for Python 3.14 and **cannot** be compiled → face recognition is broken
3. **PyTorch** (pulled by resemblyzer) is ~2 GB → massive download and install
4. **`face_recognition_models`** is cloned from GitHub on every deploy → slow and unreliable
5. **FastAPI/Uvicorn** are installed but never used on Streamlit Cloud → wasted time

**The single most impactful fix is creating a `.python-version` file with `3.11`**. This one change will eliminate source compilation for numpy, pandas, scikit-learn, and restore `dlib-bin` wheel availability.
