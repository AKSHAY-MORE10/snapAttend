import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { teacherLogin, teacherRegister } from '../api/client'
import Header from '../components/Header'
import Footer from '../components/Footer'
import './AuthPage.css'

export default function TeacherLogin() {
  const navigate   = useNavigate()
  const { setTeacher } = useAuth()
  const toast      = useToast()

  const [mode,    setMode]    = useState('login')  // 'login' | 'register'
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  // Login fields
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  // Register fields
  const [regForm,   setRegForm]   = useState({ username: '', name: '', password: '', confirm: '' })

  const updateLogin = (k, v) => setLoginForm(f => ({ ...f, [k]: v }))
  const updateReg   = (k, v) => setRegForm(f => ({ ...f, [k]: v }))

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!loginForm.username || !loginForm.password) {
      setError('Username and password are required.')
      return
    }
    setLoading(true); setError('')
    try {
      const { data } = await teacherLogin(loginForm.username, loginForm.password)
      setTeacher(data.teacher)
      toast(`Welcome back, ${data.teacher.name}! 👋`, 'success')
      navigate('/teacher/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.status === 401
        ? 'Invalid username or password.'
        : err.response?.data?.detail || 'Login failed.')
    } finally { setLoading(false) }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!regForm.username || !regForm.name || !regForm.password) {
      setError('All fields are required.')
      return
    }
    if (regForm.password !== regForm.confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true); setError('')
    try {
      const { data } = await teacherRegister(regForm.username, regForm.name, regForm.password, regForm.confirm)
      toast('Account created! Please log in.', 'success')
      setMode('login')
      setLoginForm({ username: regForm.username, password: '' })
      setError('')
    } catch (err) {
      setError(
        err.response?.status === 409 ? 'Username already taken.' :
        err.response?.data?.detail || 'Registration failed.'
      )
    } finally { setLoading(false) }
  }

  return (
    <div className="auth-layout">
      <Header variant="auth" />
      <main className="auth-main">
        <div className="auth-card">
          {/* Mascot */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
            <img
              src="https://i.ibb.co/CsmQQV6X/mascot-prof.png"
              alt="Teacher mascot"
              style={{ height: 90, objectFit: 'contain', filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.4))' }}
            />
          </div>

          <h1 className="auth-card__title">
            {mode === 'login' ? 'Teacher Login' : 'Register Account'}
          </h1>
          <p className="auth-card__sub">
            {mode === 'login' ? 'Login with your password' : 'Create your teacher profile'}
          </p>

          <hr className="divider" />

          {mode === 'login' ? (
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="t-username">Username</label>
                <input
                  id="t-username"
                  className="form-input"
                  placeholder="ananyaroy"
                  value={loginForm.username}
                  onChange={e => updateLogin('username', e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="t-password">Password</label>
                <input
                  id="t-password"
                  type="password"
                  className="form-input"
                  placeholder="Enter password"
                  value={loginForm.password}
                  onChange={e => updateLogin('password', e.target.value)}
                />
              </div>
              {error && <div className="alert alert--error">{error}</div>}
              <button
                type="submit"
                id="teacher-login-btn"
                className="btn btn--primary btn--stretch btn--lg mt-md"
                disabled={loading}
              >
                {loading ? <><span className="spinner-sm" /> Logging in…</> : '🔑 Login'}
              </button>
              <button
                type="button"
                className="btn btn--ghost btn--stretch"
                onClick={() => { setMode('register'); setError('') }}
              >
                No account? Register instead →
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="r-username">Username</label>
                <input
                  id="r-username"
                  className="form-input"
                  placeholder="ananyaroy"
                  value={regForm.username}
                  onChange={e => updateReg('username', e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="r-name">Full Name</label>
                <input
                  id="r-name"
                  className="form-input"
                  placeholder="Ananya Roy"
                  value={regForm.name}
                  onChange={e => updateReg('name', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="r-password">Password</label>
                <input
                  id="r-password"
                  type="password"
                  className="form-input"
                  placeholder="Enter password"
                  value={regForm.password}
                  onChange={e => updateReg('password', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="r-confirm">Confirm Password</label>
                <input
                  id="r-confirm"
                  type="password"
                  className="form-input"
                  placeholder="Confirm password"
                  value={regForm.confirm}
                  onChange={e => updateReg('confirm', e.target.value)}
                />
              </div>
              {error && <div className="alert alert--error">{error}</div>}
              <button
                type="submit"
                id="teacher-register-btn"
                className="btn btn--primary btn--stretch btn--lg mt-md"
                disabled={loading}
              >
                {loading ? <><span className="spinner-sm" /> Registering…</> : '✨ Register Now'}
              </button>
              <button
                type="button"
                className="btn btn--ghost btn--stretch"
                onClick={() => { setMode('login'); setError('') }}
              >
                ← Back to Login
              </button>
            </form>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
