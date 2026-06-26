import { useState } from 'react'
import type { MatchResult } from '../api/matching'
import { usersApi } from '../api/users'

const WEIGHT_COLOR: Record<string, string> = {
  S: 'bg-purple-100 text-purple-700',
  A: 'bg-blue-100 text-blue-700',
  B: 'bg-green-100 text-green-700',
  C: 'bg-yellow-100 text-yellow-700',
  D: 'bg-gray-100 text-gray-600',
}

interface Props {
  result: MatchResult
}

export function MatchCard({ result }: Props) {
  const [isViewed, setIsViewed] = useState(result.is_viewed)
  const [contactSent, setContactSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const { user, score, common_tags } = result
  const pct = Math.round(score * 100)

  async function toggleViewed() {
    setLoading(true)
    try {
      if (isViewed) {
        await usersApi.unmarkViewed(user.id)
        setIsViewed(false)
      } else {
        await usersApi.markViewed(user.id)
        setIsViewed(true)
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleContact() {
    setLoading(true)
    try {
      await usersApi.sendContact(user.id)
      setContactSent(true)
    } catch {
      // 409 = already sent
      setContactSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`bg-white rounded-xl border p-4 flex flex-col gap-3 transition-opacity ${isViewed ? 'opacity-75' : ''}`}>
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 rounded-full bg-indigo-100 overflow-hidden flex-shrink-0">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt={user.username} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-lg font-semibold text-indigo-400">
              {user.username[0].toUpperCase()}
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-gray-800">@{user.username}</span>
            <span className="text-sm font-bold text-indigo-600">{pct}%</span>
          </div>
          <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-400 rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          {user.bio && (
            <p className="mt-1 text-sm text-gray-500 truncate">{user.bio}</p>
          )}
        </div>
      </div>

      {common_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {common_tags.map(ct => (
            <span
              key={ct.tag}
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-50 border border-gray-200"
            >
              <span>{ct.tag}</span>
              <span className={`font-bold text-[10px] px-1 rounded ${WEIGHT_COLOR[ct.weight_mine] ?? ''}`}>
                {ct.weight_mine}
              </span>
              <span className="text-gray-300">/</span>
              <span className={`font-bold text-[10px] px-1 rounded ${WEIGHT_COLOR[ct.weight_theirs] ?? ''}`}>
                {ct.weight_theirs}
              </span>
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          onClick={toggleViewed}
          disabled={loading}
          className={`flex-1 text-xs py-1.5 rounded-lg border transition-colors disabled:opacity-50 ${
            isViewed
              ? 'border-gray-200 text-gray-400 hover:bg-gray-50'
              : 'border-indigo-200 text-indigo-600 hover:bg-indigo-50'
          }`}
        >
          {isViewed ? 'Просмотрен ✓' : 'Отметить просмотренным'}
        </button>
        <button
          onClick={handleContact}
          disabled={loading || contactSent}
          className="flex-1 text-xs py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {contactSent ? 'Запрос отправлен ✓' : 'Написать'}
        </button>
      </div>
    </div>
  )
}
