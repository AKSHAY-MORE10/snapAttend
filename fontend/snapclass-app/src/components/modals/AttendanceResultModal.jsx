import { useState } from 'react'
import Modal from '../Modal'
import { saveAttendance } from '../../api/client'
import { useToast } from '../../context/ToastContext'

/**
 * AttendanceResultModal
 * Props:
 *   report: { subject_id, timestamp, present_count, absent_count, results[] }
 *   onClose()
 *   onSaved()  — called after successfully saving
 */
export default function AttendanceResultModal({ report, onClose, onSaved }) {
  const toast   = useToast()
  const [saving, setSaving] = useState(false)
  const [saved,  setSaved]  = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveAttendance(report.subject_id, report.timestamp, report.results)
      toast('Attendance saved successfully!', 'success')
      setSaved(true)
      onSaved?.()
      onClose()
    } catch (err) {
      toast(err.response?.data?.detail || 'Failed to save attendance', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDiscard = () => {
    toast('Attendance discarded', 'warning')
    onClose()
  }

  const presentCount = report.results.filter(r => r.is_present).length
  const totalCount   = report.results.length

  return (
    <Modal title="Attendance Report" onClose={onClose} maxWidth="680px">
      {/* Summary stats */}
      <div style={{
        display: 'flex',
        gap: 'var(--space-md)',
        marginBottom: 'var(--space-lg)',
        padding: 'var(--space-md)',
        background: 'var(--color-surface-hi)',
        borderRadius: 'var(--radius-md)',
      }}>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-success)', margin: 0 }}>{presentCount}</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Present</p>
        </div>
        <div style={{ flex: 1, textAlign: 'center', borderLeft: '1px solid var(--color-border)', borderRight: '1px solid var(--color-border)' }}>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-error)', margin: 0 }}>{totalCount - presentCount}</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Absent</p>
        </div>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-accent)', margin: 0 }}>{totalCount}</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Total</p>
        </div>
      </div>

      <p style={{ marginBottom: 'var(--space-md)', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
        Please review before confirming.
      </p>

      {/* Results table */}
      <div style={{ maxHeight: '40vh', overflowY: 'auto', marginBottom: 'var(--space-lg)' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Roll No.</th>
              <th>Detected In</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((r) => (
              <tr key={r.student_id}>
                <td>{r.name}</td>
                <td style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>{r.roll_number}</td>
                <td style={{ fontSize: '0.82rem', color: 'var(--color-text-dim)' }}>
                  {r.sources?.join(', ') || '—'}
                </td>
                <td>
                  <span className={`badge ${r.is_present ? 'badge--present' : 'badge--absent'}`}>
                    {r.is_present ? '✅ Present' : '❌ Absent'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-md">
        <button
          id="discard-attendance-btn"
          className="btn btn--ghost btn--stretch"
          onClick={handleDiscard}
          disabled={saving}
        >
          ✕ Discard
        </button>
        <button
          id="save-attendance-btn"
          className="btn btn--primary btn--stretch"
          onClick={handleSave}
          disabled={saving || saved}
        >
          {saving ? <><span className="spinner-sm" /> Saving…</> : '✓ Confirm & Save'}
        </button>
      </div>
    </Modal>
  )
}
