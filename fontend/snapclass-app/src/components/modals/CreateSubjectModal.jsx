import { useState } from 'react'
import Modal from '../Modal'
import { createSubject } from '../../api/client'
import { useToast } from '../../context/ToastContext'

export default function CreateSubjectModal({ teacherId, onClose, onCreated }) {
  const toast = useToast()
  const [form, setForm]     = useState({ name: '', subject_code: '', section: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name || !form.subject_code || !form.section) {
      setError('All fields are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await createSubject(teacherId, form.name, form.subject_code, form.section)
      toast('Subject created successfully!', 'success')
      onCreated()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create subject.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Create New Subject" onClose={onClose}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <div className="form-group">
          <label className="form-label" htmlFor="sub-name">Subject Name</label>
          <input
            id="sub-name"
            className="form-input"
            placeholder="E.g. Introduction to AI"
            value={form.name}
            onChange={e => update('name', e.target.value)}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="sub-code">Subject Code</label>
          <input
            id="sub-code"
            className="form-input"
            placeholder="E.g. AI101"
            value={form.subject_code}
            onChange={e => update('subject_code', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="sub-section">Section</label>
          <input
            id="sub-section"
            className="form-input"
            placeholder="E.g. A / 2026"
            value={form.section}
            onChange={e => update('section', e.target.value)}
          />
        </div>

        {error && <div className="alert alert--error">{error}</div>}

        <div className="flex gap-md mt-md">
          <button type="button" className="btn btn--ghost btn--stretch" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button type="submit" id="create-subject-submit-btn" className="btn btn--primary btn--stretch" disabled={loading}>
            {loading ? <><span className="spinner-sm" /> Creating…</> : '✓ Create Subject'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
