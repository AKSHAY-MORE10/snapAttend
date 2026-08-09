import { useState } from 'react'
import Modal from '../Modal'
import { enrollStudent } from '../../api/client'
import { useToast } from '../../context/ToastContext'

export default function EnrollModal({ studentId, onClose, onEnrolled }) {
  const toast = useToast()
  const [code,    setCode]    = useState('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const handleEnroll = async (e) => {
    e.preventDefault()
    if (!code.trim()) {
      setError('Please enter a subject code.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { data } = await enrollStudent(studentId, code.trim().toUpperCase())
      toast(`Enrolled in ${data.subject.name}!`, 'success')
      onEnrolled?.()
      onClose()
    } catch (err) {
      const msg = err.response?.data?.detail
      if (err.response?.status === 404) setError('Subject code not found. Check with your teacher.')
      else if (err.response?.status === 409) setError('You are already enrolled in this subject.')
      else setError(msg || 'Enrollment failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Enroll in Subject" onClose={onClose}>
      <p style={{ marginBottom: 'var(--space-lg)' }}>
        Enter the subject code provided by your teacher.
      </p>
      <form onSubmit={handleEnroll} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <div className="form-group">
          <label className="form-label" htmlFor="enroll-code">Subject Code</label>
          <input
            id="enroll-code"
            className="form-input"
            placeholder="E.g. CS101"
            value={code}
            onChange={e => setCode(e.target.value.toUpperCase())}
            autoFocus
            style={{ textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '1.3rem', textAlign: 'center', fontWeight: 700 }}
          />
        </div>

        {error && <div className="alert alert--error">{error}</div>}

        <div className="flex gap-md mt-md">
          <button type="button" className="btn btn--ghost btn--stretch" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button
            type="submit"
            id="enroll-submit-btn"
            className="btn btn--primary btn--stretch"
            disabled={loading || !code.trim()}
          >
            {loading ? <><span className="spinner-sm" /> Enrolling…</> : '✓ Enroll Now'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
