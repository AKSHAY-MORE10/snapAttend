import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import {
  getStudentSubjects,
  getStudentAttendance,
  unenrollStudent,
  enrollStudent,
} from '../api/client'
import Header from '../components/Header'
import Footer from '../components/Footer'
import SubjectCard from '../components/SubjectCard'
import EnrollModal from '../components/modals/EnrollModal'

export default function StudentDashboard() {
  const { studentData }   = useAuth()
  const toast             = useToast()
  const [searchParams]    = useSearchParams()

  const [subjects,  setSubjects]  = useState([])
  const [records,   setRecords]   = useState([])
  const [loading,   setLoading]   = useState(true)
  const [showEnroll, setShowEnroll] = useState(false)

  const studentId = studentData?.student_id

  // ── Loaders ───────────────────────────────────────────────────

  const loadSubjects = useCallback(async () => {
    if (!studentId) return
    setLoading(true)
    try {
      const [subRes, attRes] = await Promise.all([
        getStudentSubjects(studentId),
        getStudentAttendance(studentId),
      ])
      setSubjects(subRes.data.subjects  || [])
      setRecords(attRes.data.records    || [])
    } catch {
      toast('Failed to load your subjects', 'error')
    } finally {
      setLoading(false)
    }
  }, [studentId, toast])

  useEffect(() => { loadSubjects() }, [loadSubjects])

  // ── Auto-enroll via join-code URL param ───────────────────────
  // (join-code is handled during StudentLogin; here we support deep links after login)
  const joinCode = searchParams.get('join-code')
  useEffect(() => {
    if (joinCode && studentId) {
      enrollStudent(studentId, joinCode)
        .then(() => {
          toast(`Enrolled with code "${joinCode}" ✅`, 'success')
          loadSubjects()
        })
        .catch(err => {
          const msg = err.response?.data?.detail || 'Could not enroll'
          if (msg.toLowerCase().includes('already')) {
            toast('Already enrolled in that subject.', 'warning')
          } else {
            toast(msg, 'error')
          }
        })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [joinCode, studentId])

  // ── Unenroll ──────────────────────────────────────────────────

  const handleUnenroll = async (subjectId, name) => {
    if (!window.confirm(`Leave "${name}"? Your attendance records will remain.`)) return
    try {
      await unenrollStudent(studentId, subjectId)
      toast(`Left "${name}"`, 'success')
      loadSubjects()
    } catch (err) {
      toast(err.response?.data?.detail || 'Could not unenroll', 'error')
    }
  }

  // ── Attendance stats per subject ──────────────────────────────

  const statsForSubject = (subjectId) => {
    const subRecords = records.filter(r => r.subject_id === subjectId)
    const total      = subRecords.length
    const present    = subRecords.filter(r => r.is_present).length
    const pct        = total > 0 ? Math.round((present / total) * 100) : null
    return { total, present, absent: total - present, pct }
  }

  // ── Render ────────────────────────────────────────────────────

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Header />

        <main style={{ flex: 1, maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-xl) var(--space-md)', width: '100%' }}>

          {/* Page heading */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
            <div>
              <h1 style={{ fontSize: 'clamp(1.6rem, 4vw, 2.4rem)', marginBottom: 'var(--space-xs)' }}>
                Student Dashboard
              </h1>
              <p style={{ color: 'var(--color-text-muted)' }}>
                Welcome, {studentData?.name} 👋
              </p>
            </div>
            <button
              id="enroll-subject-btn"
              className="btn btn--primary"
              onClick={() => setShowEnroll(true)}
            >
              + Enroll in Subject
            </button>
          </div>

          {/* Quick stats banner */}
          {!loading && subjects.length > 0 && (
            <div style={{
              display: 'flex',
              gap: 'var(--space-md)',
              marginBottom: 'var(--space-xl)',
              padding: 'var(--space-lg)',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              flexWrap: 'wrap',
            }}>
              {[
                { icon: '📚', label: 'Subjects', value: subjects.length },
                { icon: '✅', label: 'Present', value: records.filter(r => r.is_present).length },
                { icon: '❌', label: 'Absent', value: records.filter(r => !r.is_present).length },
                { icon: '📊', label: 'Overall %',
                  value: records.length > 0
                    ? `${Math.round((records.filter(r => r.is_present).length / records.length) * 100)}%`
                    : 'N/A',
                },
              ].map(({ icon, label, value }) => (
                <div key={label} style={{ flex: 1, minWidth: 100, textAlign: 'center' }}>
                  <p style={{ fontSize: '1.6rem', fontWeight: 700, margin: 0 }}>{icon} {value}</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: 'var(--space-xs)' }}>{label}</p>
                </div>
              ))}
            </div>
          )}

          {/* Subjects grid */}
          {loading ? (
            <div className="loading-state">Loading your subjects…</div>
          ) : subjects.length === 0 ? (
            <div className="empty-state">
              <p>You haven't enrolled in any subjects yet.</p>
              <button className="btn btn--primary" onClick={() => setShowEnroll(true)}>
                Enroll in a Subject →
              </button>
            </div>
          ) : (
            <div className="card-grid">
              {subjects.map(sub => {
                const { total, present, absent, pct } = statsForSubject(sub.subject_id)
                return (
                  <SubjectCard
                    key={sub.subject_id}
                    name={sub.name}
                    code={sub.subject_code}
                    section={sub.section}
                    stats={total > 0 ? [
                      { icon: '✅', label: 'Present', value: present },
                      { icon: '❌', label: 'Absent',  value: absent  },
                      { icon: '📊', label: 'Attendance', value: `${pct}%` },
                    ] : []}
                    footer={
                      <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                          {total} session{total !== 1 ? 's' : ''}
                        </span>
                        <button
                          id={`unenroll-${sub.subject_id}`}
                          className="btn btn--ghost btn--sm"
                          onClick={() => handleUnenroll(sub.subject_id, sub.name)}
                        >
                          Leave Subject
                        </button>
                      </div>
                    }
                  />
                )
              })}
            </div>
          )}

          {/* Attendance Records Table */}
          {!loading && records.length > 0 && (
            <div style={{ marginTop: 'var(--space-3xl)' }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', marginBottom: 'var(--space-lg)' }}>
                📋 Attendance History
              </h2>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Subject</th>
                      <th>Date / Time</th>
                      <th>Status</th>
                      <th>Detected Via</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r, i) => (
                      <tr key={i}>
                        <td>{r.subject_name || r.subject_id}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                          {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
                        </td>
                        <td>
                          <span className={`badge ${r.is_present ? 'badge--present' : 'badge--absent'}`}>
                            {r.is_present ? '✅ Present' : '❌ Absent'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.82rem', color: 'var(--color-text-dim)' }}>
                          {r.sources?.join(', ') || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>

        <Footer />
      </div>

      {showEnroll && (
        <EnrollModal
          studentId={studentId}
          onClose={() => setShowEnroll(false)}
          onEnrolled={loadSubjects}
        />
      )}
    </>
  )
}
