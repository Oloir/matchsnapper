import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { usersApi, type UserMe } from '../api/users'
import { matchingApi, type SimilarityResponse } from '../api/matching'

const WEIGHT_COLOR: Record<string, string> = {
  S: 'bg-purple-100 text-purple-700',
  A: 'bg-blue-100 text-blue-700',
  B: 'bg-green-100 text-green-700',
  C: 'bg-yellow-100 text-yellow-700',
  D: 'bg-gray-100 text-gray-600',
}

interface SnapshotItem {
  tag_id: string
  tag_name: string
  weight: string
}

export function UserProfilePage() {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()

  const [user, setUser] = useState<UserMe | null>(null)
  const [similarity, setSimilarity] = useState<SimilarityResponse | null>(null)
  const [snapshot, setSnapshot] = useState<SnapshotItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [infoOpen, setInfoOpen] = useState(false)
  const [contactSent, setContactSent] = useState(false)
  const [contactLoading, setContactLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    Promise.all([
      usersApi.getPublic(userId),
      matchingApi.getSimilarity(userId),
      usersApi.getPublicSnapshot(userId),
    ])
      .then(([u, sim, snap]) => {
        setUser(u)
        setSimilarity(sim)
        setSnapshot(snap.items)
      })
      .catch(() => setError('Не удалось загрузить профиль'))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-24 text-gray-400">Загружаем…</div>
      </Layout>
    )
  }

  if (error || !user || !similarity) {
    return (
      <Layout>
        <div className="text-center py-24 text-gray-400">{error || 'Пользователь не найден'}</div>
      </Layout>
    )
  }

  const pct = Math.round(similarity.score * 100)

  async function handleContact() {
    setContactLoading(true)
    try {
      await usersApi.sendContact(user.id)
      setContactSent(true)
    } catch {
      setContactSent(true) // 409 = already sent
    } finally {
      setContactLoading(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-lg mx-auto flex flex-col gap-5">
        <button
          onClick={() => navigate(-1)}
          className="self-start text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          ← Назад
        </button>

        {/* Шапка профиля */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 flex items-center gap-5">
          <div className="w-20 h-20 rounded-full bg-indigo-100 overflow-hidden flex-shrink-0">
            {user.avatar_url ? (
              <img src={user.avatar_url} alt={user.username} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-3xl font-semibold text-indigo-400">
                {user.username[0].toUpperCase()}
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-lg font-semibold text-gray-800">@{user.username}</p>
            {user.bio
              ? <p className="mt-1 text-sm text-gray-500">{user.bio}</p>
              : <p className="mt-1 text-sm text-gray-300 italic">Нет описания</p>
            }
            <button
              onClick={handleContact}
              disabled={contactLoading || contactSent}
              className="mt-3 px-4 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {contactSent ? 'Запрос отправлен ✓' : 'Написать'}
            </button>
          </div>
        </div>

        {/* Совместимость */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <h2 className="text-sm font-semibold text-gray-700">Совместимость</h2>
              <div
                className="relative"
                onMouseEnter={() => setInfoOpen(true)}
                onMouseLeave={() => setInfoOpen(false)}
              >
                <div className="w-4 h-4 rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600 text-[10px] font-bold flex items-center justify-center cursor-default transition-colors">
                  ?
                </div>
                {infoOpen && (
                  <div className="absolute left-0 top-6 z-20 w-64 bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-xs text-gray-500 leading-relaxed">
                    Показатель рассчитывается по косинусному сходству слепков: каждый тег — это ось, вес (S=5, A=4, B=3, C=2, D=1) — значение. Чем ближе направления двух векторов интересов, тем выше процент. 100% — полное совпадение всех тегов и весов.
                  </div>
                )}
              </div>
            </div>
            <span className="text-2xl font-bold text-indigo-600">{pct}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-400 rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>

          {similarity.common_tags.length > 0 ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400">Общие интересы</p>
                <p className="text-xs text-gray-300">Мой / {user.username}</p>
              </div>
              <div className="flex flex-col divide-y divide-gray-50">
                {similarity.common_tags.map(ct => (
                  <div key={ct.tag} className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-700">{ct.tag}</span>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-bold px-1.5 py-0.5 rounded ${WEIGHT_COLOR[ct.weight_mine] ?? ''}`}>
                        {ct.weight_mine}
                      </span>
                      <span className="text-gray-300">/</span>
                      <span className={`font-bold px-1.5 py-0.5 rounded ${WEIGHT_COLOR[ct.weight_theirs] ?? ''}`}>
                        {ct.weight_theirs}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400">Общих интересов нет</p>
          )}
        </div>

        {/* Слепок пользователя */}
        {snapshot.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-5 flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-gray-700">Слепок @{user.username}</h2>
            <div className="flex flex-col divide-y divide-gray-50">
              {snapshot.map(i => (
                <div key={i.tag_id} className="flex items-center justify-between py-2">
                  <span className="text-sm text-gray-700">{i.tag_name}</span>
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${WEIGHT_COLOR[i.weight] ?? ''}`}>
                    {i.weight}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
