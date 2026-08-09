# SnapClass — Setup Guide

## What's Inside

```
snapclass/
├── api/             ← FastAPI backend (REST API)
├── src/             ← Python services (face, voice, database)
├── fontend/
│   ├── snapclass-app/              ← React frontend (Vite)
│   └── ai-attendance-project-landing/  ← Landing page (untouched)
├── requirements.txt ← Python dependencies
└── SETUP.md         ← This file
```

---

## Prerequisites

- **Python 3.10 – 3.12** (3.13 has some compatibility issues with dlib)
- **Node.js 18+** and npm
- A **Supabase** project with the required tables
- (Optional) A `.env` file or Supabase credentials configured in `src/database/config.py`

---

## Step 1 — Python Backend Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install all Python dependencies
pip install -r requirements.txt

# 3. Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```

The API will be available at: **http://127.0.0.1:8000**
Interactive docs at: **http://127.0.0.1:8000/docs**

---

## Step 2 — React Frontend Setup

```powershell
# In a NEW terminal window:
cd fontend\snapclass-app

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

The app will open at: **http://localhost:5173**

---

## Step 3 — Open the App

1. Make sure **both** the FastAPI server and React dev server are running
2. Go to **http://localhost:5173** in your browser
3. Choose **Teacher Portal** or **Student Portal**

---

## Build for Production

```powershell
cd fontend\snapclass-app
npm run build
# Output is in fontend/snapclass-app/dist/
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r requirements.txt` inside your activated venv |
| `dlib` install fails | Use Python 3.10–3.12 (not 3.13). Install Visual C++ Build Tools on Windows. |
| `CORS error` in browser | Make sure FastAPI is running on port 8000 |
| Webcam not showing | Allow camera permissions in your browser |
| Supabase errors | Check your credentials in `src/database/config.py` |

---

## Running Both Servers (Quick Commands)

**Terminal 1 (Backend):**
```
venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```
cd fontend\snapclass-app
npm run dev
```
