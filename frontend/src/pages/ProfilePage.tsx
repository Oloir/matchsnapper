import { useEffect, useState } from 'react'
import { AvatarUpload } from '../components/AvatarUpload'
import { Layout } from '../components/Layout'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'

export function ProfilePage() {
  const { user, setUser } = useAuthStore()
  const [bio, setBio] = useState(user?.bio ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!user) {
      usersApi.getMe().then(setUser)
    }
  }, [])

  useEffect(() => {
    setBio(user?.bio ?? '')
  }, [user?.bio])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setSaved(false)
    try {
      const updated = await usersApi.patchMe(bio || null)
      setUser(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto flex flex-col gap-6">
        <h1 className="text-xl font-semibold text-gray-800">Профиль</h1>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col items-center gap-4">
          <AvatarUpload />
          <div className="text-center">
            <p className="font-semibold text-gray-800">@{user?.username}</p>
            <p className="text-sm text-gray-400">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-gray-600">О себе</h2>
          <textarea
            value={bio}
            onChange={e => setBio(e.target.value)}
            rows={3}
            placeholder="Расскажите о своих интересах…"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400 resize-none"
          />
          <button
            type="submit"
            disabled={saving}
            className="self-end px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {saving ? 'Сохраняем…' : saved ? 'Сохранено ✓' : 'Сохранить'}
          </button>
        </form>
      </div>
    </Layout>
  )
}
