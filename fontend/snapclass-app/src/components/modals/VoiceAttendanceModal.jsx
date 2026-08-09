import { useState, useRef } from 'react'
import { useReactMediaRecorder } from 'react-media-recorder'
import Modal from '../Modal'
import { runVoiceAttendance, saveAttendance } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import AttendanceResultModal from './AttendanceResultModal'

export default function VoiceAttendanceModal({ subjectId, onClose, onSaved }) {
  const toast = useToast()
  const [analyzing, setAnalyzing] = useState(false)
  const [report,    setReport]    = useState(null)
  const [error,     setError]     = useState('')

  const { status, startRecording, stopRecording, mediaBlobUrl, clearBlobUrl } =
    useReactMediaRecorder({ audio: true, blobPropertyBag: { type: 'audio/wav' } })

  const isRecording = status === 'recording'
  const hasAudio    = !!mediaBlobUrl && status !== 'recording'

  const handleAnalyze = async () => {
    if (!mediaBlobUrl) {
      setError('Please record audio first.')
      return
    }
    setAnalyzing(true)
    setError('')
    try {
      const resp = await fetch(mediaBlobUrl)
      const blob = await resp.blob()
      const { data } = await runVoiceAttendance(subjectId, blob)
      setReport(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Voice analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleReset = () => {
    clearBlobUrl()
    setReport(null)
    setError('')
  }

  // If we have a report show the result modal inside
  if (report) {
    return (
      <AttendanceResultModal
        report={report}
        onClose={onClose}
        onSaved={() => { onSaved?.(); onClose() }}
      />
    )
  }

  return (
    <Modal title="Voice Attendance" onClose={onClose}>
      <p style={{ marginBottom: 'var(--space-lg)' }}>
        Record classroom audio of students saying "I am present". AI will recognise each voice.
      </p>

      {/* Recorder UI */}
      <div style={{
        background: 'var(--color-surface-hi)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-xl)',
        textAlign: 'center',
        border: `2px solid ${isRecording ? 'var(--color-error)' : 'var(--color-border)'}`,
        transition: 'border-color 0.2s',
        marginBottom: 'var(--space-lg)',
      }}>
        {isRecording ? (
          <>
            <div style={{
              width: 60, height: 60, borderRadius: '50%',
              background: 'var(--color-error)',
              margin: '0 auto var(--space-md)',
              animation: 'pulse 1s ease-in-out infinite',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.5rem',
            }}>🎙️</div>
            <p style={{ color: 'var(--color-error)', fontWeight: 600 }}>Recording…</p>
            <button
              id="stop-recording-btn"
              className="btn btn--danger btn--stretch mt-md"
              onClick={stopRecording}
            >
              ⏹ Stop Recording
            </button>
          </>
        ) : hasAudio ? (
          <>
            <p style={{ marginBottom: 'var(--space-md)', color: 'var(--color-success)' }}>✅ Recording ready</p>
            <audio controls src={mediaBlobUrl} style={{ width: '100%', marginBottom: 'var(--space-md)' }} />
            <button className="btn btn--ghost btn--sm" onClick={handleReset}>
              🔄 Re-record
            </button>
          </>
        ) : (
          <>
            <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>🎙️</div>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
              Click to start recording
            </p>
            <button
              id="start-recording-btn"
              className="btn btn--primary btn--stretch"
              onClick={startRecording}
            >
              ● Start Recording
            </button>
          </>
        )}
      </div>

      {error && <div className="alert alert--error" style={{ marginBottom: 'var(--space-md)' }}>{error}</div>}

      <div className="flex gap-md">
        <button className="btn btn--ghost btn--stretch" onClick={onClose} disabled={analyzing}>
          Cancel
        </button>
        <button
          id="analyze-audio-btn"
          className="btn btn--primary btn--stretch"
          onClick={handleAnalyze}
          disabled={!hasAudio || analyzing}
        >
          {analyzing
            ? <><span className="spinner-sm" /> Analysing…</>
            : '🔍 Analyse Audio'}
        </button>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.85; }
        }
      `}</style>
    </Modal>
  )
}
