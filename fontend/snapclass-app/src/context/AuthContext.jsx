import { createContext, useContext, useReducer, useEffect } from 'react'

const AuthContext = createContext(null)

const initialState = {
  loginType: null,       // 'teacher' | 'student' | null
  teacherData: null,
  studentData: null,
  isLoggedIn: false,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_TEACHER':
      return {
        ...state,
        loginType: 'teacher',
        teacherData: action.payload,
        isLoggedIn: true,
        studentData: null,
      }
    case 'SET_STUDENT':
      return {
        ...state,
        loginType: 'student',
        studentData: action.payload,
        isLoggedIn: true,
        teacherData: null,
      }
    case 'SET_LOGIN_TYPE':
      return { ...state, loginType: action.payload }
    case 'LOGOUT':
      return { ...initialState }
    default:
      return state
  }
}

function loadFromStorage() {
  try {
    const saved = localStorage.getItem('snapclass_auth')
    return saved ? JSON.parse(saved) : initialState
  } catch {
    return initialState
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState, loadFromStorage)

  // Persist to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem('snapclass_auth', JSON.stringify(state))
  }, [state])

  const setTeacher  = (data)  => dispatch({ type: 'SET_TEACHER',    payload: data })
  const setStudent  = (data)  => dispatch({ type: 'SET_STUDENT',    payload: data })
  const setLoginType = (type) => dispatch({ type: 'SET_LOGIN_TYPE', payload: type })
  const logout      = ()      => {
    localStorage.removeItem('snapclass_auth')
    dispatch({ type: 'LOGOUT' })
  }

  return (
    <AuthContext.Provider value={{ ...state, setTeacher, setStudent, setLoginType, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
