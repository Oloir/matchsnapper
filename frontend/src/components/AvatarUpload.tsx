import { useRef, useState } from 'react'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'

export function AvatarUpload() {
  const { user, setUser } = useAuthStore()
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const { avatar_url } = await usersApi.uploadAvatar(file)
      if (user) setUser({ ...user, avatar_url })
    } catch {
      setError('Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    setLoading(true)
    setError('')
    try {
      await usersApi.deleteAvatar()
      if (user) setUser({ ...user, avatar_url: null })
    } catch {
      setError('Ошибка удаления')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className="w-24 h-24 rounded-full bg-indigo-100 overflow-hidden cursor-pointer border-2 border-indigo-200 hover:border-indigo-400 transition-colors"
        onClick={() => inputRef.current?.click()}
      >
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-3xl text-indigo-400">
            {user?.username?.[0]?.toUpperCase() ?? '?'}
          </div>
        )}
      </div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
      <div className="flex gap-2">
        <button
          onClick={() => inputRef.current?.click()}
          disabled={loading}
          className="text-xs px-3 py-1 rounded bg-indigo-50 text-indigo-600 hover:bg-indigo-100 disabled:opacity-50"
        >
          {loading ? '...' : 'Сменить'}
        </button>
        {user?.avatar_url && (
          <button
            onClick={handleDelete}
            disabled={loading}
            className="text-xs px-3 py-1 rounded bg-red-50 text-red-500 hover:bg-red-100 disabled:opacity-50"
          >
            Удалить
          </button>
        )}
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
