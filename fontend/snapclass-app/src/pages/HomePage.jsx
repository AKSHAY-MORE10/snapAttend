import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import Footer from '../components/Footer'
import './HomePage.css'

export default function HomePage() {
  const navigate  = useNavigate()
  const { setLoginType } = useAuth()

  const go = (type) => {
    setLoginType(type)
    navigate(`/${type}`)
  }

  return (
    <div className="home-layout">
      <Header variant="home" />

      <main className="home-main">
        {/* Hero */}
        <section className="home-hero">
          <p className="home-hero__label">AI-Powered Attendance</p>
          <h1 className="home-hero__title">
            Making Attendance<br />
            <span className="home-hero__accent">Faster with AI</span>
          </h1>
          <p className="home-hero__sub">
            Face recognition · Voice recognition · Instant results
          </p>
        </section>

        {/* Portal Selection */}
        <section className="home-portals">
          <div
            id="student-portal-card"
            className="portal-card portal-card--student"
            onClick={() => go('student')}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && go('student')}
          >
            <div className="portal-card__mascot">
              <img
                src="https://i.ibb.co/844D9Lrt/mascot-student.png"
                alt="Student mascot"
              />
            </div>
            <div className="portal-card__body">
              <p className="portal-card__role">I'm a</p>
              <h2 className="portal-card__title">Student</h2>
              <p className="portal-card__desc">
                Login with face recognition. View your subjects and attendance records.
              </p>
              <button className="btn btn--primary portal-card__btn">
                Student Portal →
              </button>
            </div>
          </div>

          <div
            id="teacher-portal-card"
            className="portal-card portal-card--teacher"
            onClick={() => go('teacher')}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && go('teacher')}
          >
            <div className="portal-card__mascot">
              <img
                src="https://i.ibb.co/CsmQQV6X/mascot-prof.png"
                alt="Teacher mascot"
              />
            </div>
            <div className="portal-card__body">
              <p className="portal-card__role">I'm a</p>
              <h2 className="portal-card__title">Teacher</h2>
              <p className="portal-card__desc">
                Manage subjects, run AI attendance via face or voice, and review records.
              </p>
              <button className="btn btn--primary portal-card__btn">
                Teacher Portal →
              </button>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
