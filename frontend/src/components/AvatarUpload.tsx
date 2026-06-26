import { useRef, useState } from 'react'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'

export function AvatarUpload() {
  const { user, setUser } = useAuthStore()
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
  const MAX_BYTES = 5 * 1024 * 1024

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    if (!ALLOWED_TYPES.has(file.type)) {
      setError('Недопустимый формат. Загрузите JPEG, PNG, WebP или GIF')
      return
    }
    if (file.size > MAX_BYTES) {
      setError('Файл слишком большой. Максимум — 5 МБ')
      return
    }

    setLoading(true)
    setError('')
    try {
      const { avatar_url } = await usersApi.uploadAvatar(file)
      if (user) setUser({ ...user, avatar_url: `${avatar_url}?t=${Date.now()}` })
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
      <div className="relative">
        <div
          className="w-24 h-24 rounded-full bg-indigo-100 overflow-hidden cursor-pointer border-2 border-indigo-200 hover:border-indigo-400 transition-colors"
          onClick={() => inputRef.current?.click()}
        >
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-3xl text-indigo-400">
              {loading ? '…' : (user?.username?.[0]?.toUpperCase() ?? '?')}
            </div>
          )}
        </div>
        {user?.avatar_url && (
          <button
            onClick={handleDelete}
            disabled={loading}
            className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-white border border-gray-200 text-gray-400 hover:text-red-500 hover:border-red-300 flex items-center justify-center text-xs shadow-sm transition-colors disabled:opacity-50"
          >
            ×
          </button>
        )}
      </div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
