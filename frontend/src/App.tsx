import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProfilePage } from './pages/ProfilePage'
import { SnapshotEditorPage } from './pages/SnapshotEditorPage'
import { MatchesPage } from './pages/MatchesPage'
import { UserProfilePage } from './pages/UserProfilePage'
import { useAuthStore } from './store/authStore'
import { usersApi } from './api/users'

function AuthLoader({ children }: { children: React.ReactNode }) {
  const { accessToken, user, setUser, logout } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (accessToken && !user) {
      usersApi.getMe().then(setUser).catch(() => {
        logout()
        navigate('/login')
      })
    }
  }, [accessToken])

  return <>{children}</>
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.accessToken)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function GuestOnly({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.accessToken)
  if (token) return <Navigate to="/matches" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthLoader>
        <Routes>
          <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
          <Route path="/register" element={<GuestOnly><RegisterPage /></GuestOnly>} />
          <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
          <Route path="/snapshot" element={<RequireAuth><SnapshotEditorPage /></RequireAuth>} />
          <Route path="/matches" element={<RequireAuth><MatchesPage /></RequireAuth>} />
          <Route path="/users/:userId" element={<RequireAuth><UserProfilePage /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/matches" replace />} />
        </Routes>
      </AuthLoader>
    </BrowserRouter>
  )
}
