import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { studentFaceLogin, studentRegister, enrollStudent } from '../api/client'
import { useReactMediaRecorder } from 'react-media-recorder'
import Header from '../components/Header'
import Footer from '../components/Footer'
import WebcamCapture from '../components/WebcamCapture'
import './AuthPage.css'

// States the login flow can be in
const PHASE = {
  IDLE:         'idle',        // waiting for webcam capture
  LOADING:      'loading',     // face-login API call in flight
  UNRECOGNIZED: 'unrecognized',// face not found → show registration form
  REGISTER:     'register',    // registration form (+ optional voice)
  SAVING:       'saving',      // registration API call in flight
}

export default function StudentLogin() {
  const navigate      = useNavigate()
  const { setStudent } = useAuth()
  const toast         = useToast()
  const [searchParams] = useSearchParams()
  const joinCode      = searchParams.get('join-code') || ''

  const [phase,         setPhase]         = useState(PHASE.IDLE)
  const [capturedBlob,  setCapturedBlob]  = useState(null)
  const [capturedUrl,   setCapturedUrl]   = useState(null)
  const [error,         setError]         = useState('')
  const [regForm,       setRegForm]       = useState({ name: '', roll_number: '' })
  const [recordVoice,   setRecordVoice]   = useState(false)

  // voice recording via react-media-recorder (reuse same pattern as VoiceAttendanceModal)
  const { status, startRecording, stopRecording, mediaBlobUrl, clearBlobUrl } =
    useReactMediaRecorder({ audio: true, blobPropertyBag: { type: 'audio/wav' } })
  const isRecording = status === 'recording'
  const hasVoice    = !!mediaBlobUrl && status !== 'recording'

  // ── Webcam handlers ───────────────────────────────────────────

  const handleCapture = useCallback((blob) => {
    setCapturedBlob(blob)
    setCapturedUrl(URL.createObjectURL(blob))
  }, [])

  const handleRetake = () => {
    if (capturedUrl) URL.revokeObjectURL(capturedUrl)
    setCapturedBlob(null)
    setCapturedUrl(null)
    setPhase(PHASE.IDLE)
    setError('')
  }

  // ── Face login ────────────────────────────────────────────────

  const handleFaceLogin = async () => {
    if (!capturedBlob) {
      setError('Please capture a photo first.')
      return
    }
    setPhase(PHASE.LOADING)
    setError('')
    try {
      const { data } = await studentFaceLogin(capturedBlob)
      if (data.matched) {
        setStudent(data.student)
        toast(`Welcome, ${data.student.name}! 🎉`, 'success')
        navigate('/student/dashboard', { replace: true })
      } else {
        // Not recognised — show registration
        setPhase(PHASE.UNRECOGNIZED)
        const reason = {
          no_face:        'No face detected. Make sure your face is visible and try again.',
          multiple_faces: 'Multiple faces detected. Please be alone in the frame.',
          no_model:       'Face recognition model not yet trained. Please register instead.',
          unrecognized:   'Face not recognised. Please register your account below.',
        }
        setError(reason[data.reason] || 'Face not recognised.')
      }
    } catch (err) {
      setPhase(PHASE.IDLE)
      setError(err.response?.data?.detail || 'Face login failed. Please try again.')
    }
  }

  // ── Registration ──────────────────────────────────────────────

  const updateReg = (k, v) => setRegForm(f => ({ ...f, [k]: v }))

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!regForm.name || !regForm.roll_number) {
      setError('Name and roll number are required.')
      return
    }
    if (!capturedBlob) {
      setError('No face photo. Please retake a photo.')
      return
    }

    setPhase(PHASE.SAVING)
    setError('')
    try {
      let audioBlob = null
      if (hasVoice && recordVoice) {
        const resp = await fetch(mediaBlobUrl)
        audioBlob  = await resp.blob()
      }

      const { data } = await studentRegister(
        regForm.name,
        regForm.roll_number,
        capturedBlob,
        audioBlob,
      )

      const student = data.student
      setStudent(student)
      toast(`Registered! Welcome, ${student.name}! 🎉`, 'success')

      // If a join-code was in the URL, auto-enroll the newly registered student
      if (joinCode) {
        try {
          await enrollStudent(student.student_id, joinCode)
          toast(`Enrolled with code "${joinCode}" ✅`, 'success')
        } catch {
          toast('Could not auto-enroll — join the subject from your dashboard.', 'warning')
        }
      }

      navigate('/student/dashboard', { replace: true })
    } catch (err) {
      setPhase(PHASE.UNRECOGNIZED)
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    }
  }

  // ── Render ────────────────────────────────────────────────────

  return (
    <div className="auth-layout">
      <Header variant="auth" />
      <main className="auth-main">
        <div className={`auth-card ${phase === PHASE.UNRECOGNIZED || phase === PHASE.REGISTER || phase === PHASE.SAVING ? 'auth-card--wide' : ''}`}>

          {/* Mascot + title */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
            <img
              src="https://i.ibb.co/nspSQFy/mascot-student.png"
              alt="Student mascot"
              style={{ height: 80, objectFit: 'contain', filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.4))' }}
            />
          </div>

          <h1 className="auth-card__title">Student Login</h1>
          <p className="auth-card__sub">
            {joinCode
              ? `Join code detected: ${joinCode} — look into the camera to log in or register`
              : 'Look into the camera and capture your photo to log in'}
          </p>

          <hr className="divider" style={{ marginBottom: 'var(--space-lg)' }} />

          {/* PHASE: IDLE / LOADING — just the webcam */}
          {(phase === PHASE.IDLE || phase === PHASE.LOADING) && (
            <div style={{ maxWidth: 480, margin: '0 auto' }}>
              <WebcamCapture
                onCapture={handleCapture}
                capturedImage={capturedUrl}
                onRetake={handleRetake}
              />

              {capturedUrl && (
                <button
                  id="face-login-btn"
                  className="btn btn--primary btn--stretch btn--lg mt-md"
                  onClick={handleFaceLogin}
                  disabled={phase === PHASE.LOADING}
                  style={{ marginTop: 'var(--space-md)' }}
                >
                  {phase === PHASE.LOADING
                    ? <><span className="spinner-sm" /> Identifying…</>
                    : '🔍 Login with Face'}
                </button>
              )}

              {error && <div className="alert alert--error" style={{ marginTop: 'var(--space-md)' }}>{error}</div>}
            </div>
          )}

          {/* PHASE: UNRECOGNIZED / REGISTER / SAVING — two columns */}
          {(phase === PHASE.UNRECOGNIZED || phase === PHASE.SAVING) && (
            <div className="auth-cols">
              {/* Left: captured photo */}
              <div>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>
                  Your Photo
                </p>
                <WebcamCapture
                  onCapture={handleCapture}
                  capturedImage={capturedUrl}
                  onRetake={handleRetake}
                />
              </div>

              {/* Right: registration form */}
              <div>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', marginBottom: 'var(--space-xs)' }}>
                  Register Account
                </h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-lg)' }}>
                  {error}
                </p>

                <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="s-name">Full Name</label>
                    <input
                      id="s-name"
                      className="form-input"
                      placeholder="Riya Sharma"
                      value={regForm.name}
                      onChange={e => updateReg('name', e.target.value)}
                      autoFocus
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="s-roll">Roll Number</label>
                    <input
                      id="s-roll"
                      className="form-input"
                      placeholder="2024CS001"
                      value={regForm.roll_number}
                      onChange={e => updateReg('roll_number', e.target.value)}
                    />
                  </div>

                  {/* Optional voice enrollment */}
                  <div style={{
                    background: 'var(--color-surface-hi)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-md)',
                    border: '1px solid var(--color-border)',
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', cursor: 'pointer', fontSize: '0.9rem' }}>
                      <input
                        type="checkbox"
                        checked={recordVoice}
                        onChange={e => {
                          setRecordVoice(e.target.checked)
                          if (!e.target.checked) clearBlobUrl()
                        }}
                        style={{ accentColor: 'var(--color-success)' }}
                      />
                      Also enroll voice for voice attendance (optional)
                    </label>

                    {recordVoice && (
                      <div style={{ marginTop: 'var(--space-md)', textAlign: 'center' }}>
                        {isRecording ? (
                          <>
                            <div style={{
                              width: 48, height: 48, borderRadius: '50%',
                              background: 'var(--color-error)', margin: '0 auto var(--space-sm)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '1.25rem', animation: 'pulse 1s ease-in-out infinite',
                            }}>🎙️</div>
                            <p style={{ color: 'var(--color-error)', fontWeight: 600, fontSize: '0.85rem', marginBottom: 'var(--space-sm)' }}>Recording…</p>
                            <button type="button" className="btn btn--danger btn--sm" onClick={stopRecording}>
                              ⏹ Stop
                            </button>
                          </>
                        ) : hasVoice ? (
                          <>
                            <p style={{ color: 'var(--color-success)', fontSize: '0.85rem', marginBottom: 'var(--space-sm)' }}>✅ Voice sample ready</p>
                            <audio controls src={mediaBlobUrl} style={{ width: '100%', marginBottom: 'var(--space-sm)' }} />
                            <button type="button" className="btn btn--ghost btn--sm" onClick={clearBlobUrl}>🔄 Re-record</button>
                          </>
                        ) : (
                          <button type="button" className="btn btn--ghost btn--sm" onClick={startRecording}>
                            ● Record Voice Sample
                          </button>
                        )}
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    id="student-register-btn"
                    className="btn btn--primary btn--stretch btn--lg"
                    disabled={phase === PHASE.SAVING}
                  >
                    {phase === PHASE.SAVING ? <><span className="spinner-sm" /> Registering…</> : '✨ Register & Login'}
                  </button>

                  <button
                    type="button"
                    className="btn btn--ghost btn--stretch"
                    onClick={handleRetake}
                    disabled={phase === PHASE.SAVING}
                  >
                    ← Retake Photo
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.85; }
        }
      `}</style>
    </div>
  )
}
