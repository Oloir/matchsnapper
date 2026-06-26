import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/matches" className="text-xl font-bold text-indigo-600 tracking-tight">
            MatchSnapper
          </Link>
          {user && (
            <nav className="flex items-center gap-6 text-sm">
              <Link to="/matches" className="text-gray-600 hover:text-indigo-600 transition-colors">
                Матчи
              </Link>
              <Link to="/snapshot" className="text-gray-600 hover:text-indigo-600 transition-colors">
                Слепок
              </Link>
              <Link to="/profile" className="text-gray-600 hover:text-indigo-600 transition-colors">
                Профиль
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                Выйти
              </button>
            </nav>
          )}
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-6">{children}</main>
    </div>
  )
}
