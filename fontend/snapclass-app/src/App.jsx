import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'

import HomePage         from './pages/HomePage'
import TeacherLogin     from './pages/TeacherLogin'
import TeacherDashboard from './pages/TeacherDashboard'
import StudentLogin     from './pages/StudentLogin'
import StudentDashboard from './pages/StudentDashboard'

function AuthRouter() {
  const { loginType, isLoggedIn, teacherData, studentData } = useAuth()
  const [searchParams] = useSearchParams()
  const joinCode = searchParams.get('join-code')

  // If student arrives with join-code but not logged in → force student login
  if (joinCode && loginType !== 'student') {
    return <Navigate to="/student" replace />
  }

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      {/* Teacher routes */}
      <Route path="/teacher" element={
        isLoggedIn && teacherData ? <Navigate to="/teacher/dashboard" replace /> : <TeacherLogin />
      } />
      <Route path="/teacher/dashboard" element={
        isLoggedIn && teacherData ? <TeacherDashboard /> : <Navigate to="/teacher" replace />
      } />

      {/* Student routes */}
      <Route path="/student" element={
        isLoggedIn && studentData ? <Navigate to="/student/dashboard" replace /> : <StudentLogin />
      } />
      <Route path="/student/dashboard" element={
        isLoggedIn && studentData ? <StudentDashboard /> : <Navigate to="/student" replace />
      } />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <AuthRouter />
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  )
}
