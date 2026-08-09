import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min — AI inference can be slow
})

// ─── Auth ────────────────────────────────────────────────────

export const teacherLogin = (username, password) =>
  api.post('/auth/teacher/login', { username, password })

export const teacherRegister = (username, name, password, confirm) =>
  api.post('/auth/teacher/register', { username, name, password, confirm })

export const studentFaceLogin = (imageBlob) => {
  const fd = new FormData()
  fd.append('image', imageBlob, 'face.jpg')
  return api.post('/auth/student/face-login', fd)
}

export const studentRegister = (name, rollNumber, imageBlob, audioBlob = null) => {
  const fd = new FormData()
  fd.append('name', name)
  fd.append('roll_number', rollNumber)
  fd.append('image', imageBlob, 'face.jpg')
  if (audioBlob) fd.append('audio', audioBlob, 'voice.wav')
  return api.post('/auth/student/register', fd)
}

// ─── Subjects ────────────────────────────────────────────────

export const getTeacherSubjects = (teacherId) =>
  api.get(`/teachers/${teacherId}/subjects`)

export const createSubject = (teacherId, name, subjectCode, section) =>
  api.post('/subjects', { teacher_id: teacherId, name, subject_code: subjectCode, section })

export const deleteSubject = (subjectId) =>
  api.delete(`/subjects/${subjectId}`)

// ─── Enrollment ──────────────────────────────────────────────

export const enrollStudent = (studentId, subjectCode) =>
  api.post('/enroll', { student_id: studentId, subject_code: subjectCode })

export const unenrollStudent = (studentId, subjectId) =>
  api.delete(`/students/${studentId}/subjects/${subjectId}`)

export const getStudentSubjects = (studentId) =>
  api.get(`/students/${studentId}/subjects`)

export const getStudentAttendance = (studentId) =>
  api.get(`/students/${studentId}/attendance`)

// ─── Attendance ───────────────────────────────────────────────

export const runFaceAttendance = (subjectId, imageFiles, threshold = 0.6) => {
  const fd = new FormData()
  fd.append('subject_id', subjectId)
  fd.append('threshold', threshold)
  imageFiles.forEach((f) => fd.append('images', f))
  return api.post('/attendance/face', fd)
}

export const runVoiceAttendance = (subjectId, audioBlob, threshold = 0.65) => {
  const fd = new FormData()
  fd.append('subject_id', subjectId)
  fd.append('threshold', threshold)
  fd.append('audio', audioBlob, 'classroom.wav')
  return api.post('/attendance/voice', fd)
}

export const saveAttendance = (subjectId, timestamp, results) =>
  api.post('/attendance/save', { subject_id: subjectId, timestamp, results })

export const getTeacherAttendance = (teacherId) =>
  api.get(`/teachers/${teacherId}/attendance`)

export default api
