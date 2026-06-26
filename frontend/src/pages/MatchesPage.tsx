import { useEffect, useState } from 'react'
import { Layout } from '../components/Layout'
import { MatchCard } from '../components/MatchCard'
import { matchingApi, type MatchList } from '../api/matching'

export function MatchesPage() {
  const [data, setData] = useState<MatchList | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    matchingApi.list(page).then(d => {
      setData(d)
      setLoading(false)
    })
  }, [page])

  return (
    <Layout>
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-800">Матчи</h1>
          {data && (
            <span className="text-sm text-gray-400">{data.total} пользователей</span>
          )}
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400">Загружаем…</div>
        ) : data?.results.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg mb-2">Нет матчей</p>
            <p className="text-sm">Заполните слепок, чтобы найти похожих людей</p>
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              {data?.results.map(result => (
                <MatchCard key={result.user.id} result={result} />
              ))}
            </div>

            {data && data.pages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ←
                </button>
                <span className="text-sm text-gray-500">
                  {page} / {data.pages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
