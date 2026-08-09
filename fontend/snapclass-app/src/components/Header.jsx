import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Header.css'

export default function Header({ variant = 'home' }) {
  const { teacherData, studentData, isLoggedIn, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  const userName = teacherData?.name || studentData?.name || ''

  return (
    <header className="header">
      <a href="/" className="header__brand" onClick={e => { e.preventDefault(); navigate('/') }}>
        <img
          src="https://i.ibb.co/YTYGn5qV/logo.png"
          alt="SnapClass logo"
          className="header__logo"
        />
        <span className="header__name">SnapClass</span>
      </a>

      {isLoggedIn && (
        <div className="header__right">
          {userName && (
            <span className="header__greeting">
              👋 {userName}
            </span>
          )}
          <button className="btn btn--ghost btn--sm" onClick={handleLogout}>
            Logout
          </button>
        </div>
      )}

      {!isLoggedIn && variant === 'auth' && (
        <button
          className="btn btn--ghost btn--sm"
          onClick={() => navigate('/')}
        >
          ← Home
        </button>
      )}
    </header>
  )
}
