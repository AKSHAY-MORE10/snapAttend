import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import {
  getTeacherSubjects,
  getTeacherAttendance,
  deleteSubject,
} from '../api/client'
import Header from '../components/Header'
import Footer from '../components/Footer'
import SubjectCard from '../components/SubjectCard'
import CreateSubjectModal  from '../components/modals/CreateSubjectModal'
import ShareSubjectModal   from '../components/modals/ShareSubjectModal'
import AddPhotosModal      from '../components/modals/AddPhotosModal'
import VoiceAttendanceModal from '../components/modals/VoiceAttendanceModal'

// ─── Tab IDs ──────────────────────────────────────────────────
const TABS = ['take-attendance', 'manage-subjects', 'attendance-records']
const TAB_LABELS = {
  'take-attendance':     '📸 Take Attendance',
  'manage-subjects':     '📚 Manage Subjects',
  'attendance-records':  '📋 Records',
}

export default function TeacherDashboard() {
  const { teacherData } = useAuth()
  const toast           = useToast()

  const [activeTab, setActiveTab]   = useState('take-attendance')
  const [subjects,  setSubjects]    = useState([])
  const [records,   setRecords]     = useState([])
  const [loadingSubjects, setLS]    = useState(true)
  const [loadingRecords,  setLR]    = useState(false)

  // Modal state — only one open at a time
  const [modal, setModal] = useState(null)
  // modal = { type: 'create' | 'share' | 'face' | 'voice', subjectId?, subjectCode? }

  const closeModal = () => setModal(null)

  // ── Data loaders ──────────────────────────────────────────────

  const loadSubjects = useCallback(async () => {
    if (!teacherData?.teacher_id) return
    setLS(true)
    try {
      const { data } = await getTeacherSubjects(teacherData.teacher_id)
      setSubjects(data.subjects || [])
    } catch {
      toast('Failed to load subjects', 'error')
    } finally {
      setLS(false)
    }
  }, [teacherData?.teacher_id, toast])

  const loadRecords = useCallback(async () => {
    if (!teacherData?.teacher_id) return
    setLR(true)
    try {
      const { data } = await getTeacherAttendance(teacherData.teacher_id)
      setRecords(data.records || [])
    } catch {
      toast('Failed to load attendance records', 'error')
    } finally {
      setLR(false)
    }
  }, [teacherData?.teacher_id, toast])

  useEffect(() => { loadSubjects() }, [loadSubjects])

  useEffect(() => {
    if (activeTab === 'attendance-records') loadRecords()
  }, [activeTab, loadRecords])

  // ── Delete subject ─────────────────────────────────────────────

  const handleDelete = async (subjectId, name) => {
    if (!window.confirm(`Delete "${name}"? This will remove all attendance records.`)) return
    try {
      await deleteSubject(subjectId)
      toast(`"${name}" deleted`, 'success')
      loadSubjects()
    } catch (err) {
      toast(err.response?.data?.detail || 'Delete failed', 'error')
    }
  }

  // ── Render ────────────────────────────────────────────────────

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Header />

        <main style={{ flex: 1, maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-xl) var(--space-md)', width: '100%' }}>

          {/* Page heading */}
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <h1 style={{ fontSize: 'clamp(1.6rem, 4vw, 2.4rem)', marginBottom: 'var(--space-xs)' }}>
              Teacher Dashboard
            </h1>
            <p style={{ color: 'var(--color-text-muted)' }}>
              Welcome, {teacherData?.name} 👋
            </p>
          </div>

          {/* Tabs */}
          <div className="tabs" style={{ marginBottom: 'var(--space-xl)' }}>
            {TABS.map(tab => (
              <button
                key={tab}
                id={`tab-${tab}`}
                className={`tab-btn${activeTab === tab ? ' tab-btn--active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {TAB_LABELS[tab]}
              </button>
            ))}
          </div>

          {/* ── TAB: Take Attendance ────────────────────────────── */}
          {activeTab === 'take-attendance' && (
            <div>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-xl)' }}>
                Select a subject, then run face or voice attendance.
              </p>

              {loadingSubjects ? (
                <div className="loading-state">Loading subjects…</div>
              ) : subjects.length === 0 ? (
                <div className="empty-state">
                  <p>No subjects yet.</p>
                  <button className="btn btn--primary" onClick={() => setActiveTab('manage-subjects')}>
                    Go to Manage Subjects →
                  </button>
                </div>
              ) : (
                <div className="card-grid">
                  {subjects.map(sub => (
                    <SubjectCard
                      key={sub.subject_id}
                      name={sub.name}
                      code={sub.subject_code}
                      section={sub.section}
                      footer={
                        <div className="flex gap-sm" style={{ flexWrap: 'wrap' }}>
                          <button
                            id={`face-attend-${sub.subject_id}`}
                            className="btn btn--primary btn--sm"
                            onClick={() => setModal({ type: 'face', subjectId: sub.subject_id })}
                          >
                            📸 Face Attendance
                          </button>
                          <button
                            id={`voice-attend-${sub.subject_id}`}
                            className="btn btn--ghost btn--sm"
                            onClick={() => setModal({ type: 'voice', subjectId: sub.subject_id })}
                          >
                            🎙️ Voice Attendance
                          </button>
                        </div>
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── TAB: Manage Subjects ────────────────────────────── */}
          {activeTab === 'manage-subjects' && (
            <div>
              <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xl)' }}>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem' }}>Your Subjects</h2>
                <button
                  id="create-subject-btn"
                  className="btn btn--primary"
                  onClick={() => setModal({ type: 'create' })}
                >
                  + New Subject
                </button>
              </div>

              {loadingSubjects ? (
                <div className="loading-state">Loading subjects…</div>
              ) : subjects.length === 0 ? (
                <div className="empty-state">
                  <p>No subjects yet. Create one to get started!</p>
                </div>
              ) : (
                <div className="card-grid">
                  {subjects.map(sub => (
                    <SubjectCard
                      key={sub.subject_id}
                      name={sub.name}
                      code={sub.subject_code}
                      section={sub.section}
                      footer={
                        <div className="flex gap-sm" style={{ flexWrap: 'wrap' }}>
                          <button
                            id={`share-${sub.subject_id}`}
                            className="btn btn--ghost btn--sm"
                            onClick={() => setModal({ type: 'share', subjectCode: sub.subject_code, subjectName: sub.name })}
                          >
                            🔗 Share Code
                          </button>
                          <button
                            id={`delete-${sub.subject_id}`}
                            className="btn btn--danger btn--sm"
                            onClick={() => handleDelete(sub.subject_id, sub.name)}
                          >
                            🗑 Delete
                          </button>
                        </div>
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── TAB: Attendance Records ─────────────────────────── */}
          {activeTab === 'attendance-records' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', marginBottom: 'var(--space-xl)' }}>
                Attendance Records
              </h2>

              {loadingRecords ? (
                <div className="loading-state">Loading records…</div>
              ) : records.length === 0 ? (
                <div className="empty-state">
                  <p>No attendance records yet.</p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Date / Time</th>
                        <th>Present</th>
                        <th>Absent</th>
                        <th>Total</th>
                        <th>% Present</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((r, i) => {
                        const pct = r.total > 0 ? Math.round((r.present / r.total) * 100) : 0
                        return (
                          <tr key={i}>
                            <td>{r.subject_name || r.subject_id}</td>
                            <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                              {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
                            </td>
                            <td style={{ color: 'var(--color-success)', fontWeight: 600 }}>{r.present ?? r.present_count ?? '—'}</td>
                            <td style={{ color: 'var(--color-error)', fontWeight: 600 }}>{r.absent ?? r.absent_count ?? '—'}</td>
                            <td>{r.total ?? (r.present_count + r.absent_count) ?? '—'}</td>
                            <td>
                              <span className={`badge ${pct >= 75 ? 'badge--present' : 'badge--absent'}`}>
                                {pct}%
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </main>

        <Footer />
      </div>

      {/* ── Modals ── */}
      {modal?.type === 'create' && (
        <CreateSubjectModal
          teacherId={teacherData?.teacher_id}
          onClose={closeModal}
          onCreated={loadSubjects}
        />
      )}
      {modal?.type === 'share' && (
        <ShareSubjectModal
          subjectCode={modal.subjectCode}
          subjectName={modal.subjectName}
          onClose={closeModal}
        />
      )}
      {modal?.type === 'face' && (
        <AddPhotosModal
          subjectId={modal.subjectId}
          onClose={closeModal}
          onSaved={loadRecords}
        />
      )}
      {modal?.type === 'voice' && (
        <VoiceAttendanceModal
          subjectId={modal.subjectId}
          onClose={closeModal}
          onSaved={loadRecords}
        />
      )}
    </>
  )
}
