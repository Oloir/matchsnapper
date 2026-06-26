import { useEffect, useState } from 'react'
import { Layout } from '../components/Layout'
import { SnapshotItem } from '../components/SnapshotEditor/SnapshotItem'
import { TagSearch } from '../components/SnapshotEditor/TagSearch'
import { snapshotsApi, type SnapshotItemOut } from '../api/snapshots'
import type { Tag } from '../api/matching'

export function SnapshotEditorPage() {
  const [items, setItems] = useState<SnapshotItemOut[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    snapshotsApi.get().then(data => {
      setItems(data.items)
      setLoading(false)
    })
  }, [])

  const existingTagIds = new Set(items.map(i => i.tag_id))

  async function handleWeightChange(tagId: string, weight: string) {
    setSaving(true)
    try {
      const data = await snapshotsApi.upsertItem(tagId, weight)
      setItems(data.items)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(tagId: string) {
    setSaving(true)
    try {
      await snapshotsApi.deleteItem(tagId)
      setItems(prev => prev.filter(i => i.tag_id !== tagId))
    } finally {
      setSaving(false)
    }
  }

  async function handleAddTag(tag: Tag) {
    setSaving(true)
    try {
      const data = await snapshotsApi.upsertItem(tag.id, 'B')
      setItems(data.items)
    } finally {
      setSaving(false)
    }
  }

  const sorted = [...items].sort((a, b) => {
    const order: Record<string, number> = { S: 0, A: 1, B: 2, C: 3, D: 4 }
    return (order[a.weight] ?? 9) - (order[b.weight] ?? 9)
  })

  return (
    <Layout>
      <div className="max-w-lg mx-auto flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-800">Мой слепок</h1>
          {saving && <span className="text-xs text-gray-400">Сохраняем…</span>}
        </div>

        <p className="text-sm text-gray-500">
          Добавьте теги и расставьте веса: S — главный интерес, D — слабый.
        </p>

        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-sm text-gray-400">Загружаем…</div>
          ) : sorted.length === 0 ? (
            <div className="p-8 text-center text-sm text-gray-400">
              Слепок пуст — добавьте первый тег ниже
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {sorted.map(item => (
                <SnapshotItem
                  key={item.tag_id}
                  item={item}
                  onWeightChange={handleWeightChange}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-4">
          <p className="text-xs text-gray-400 mb-2">Добавить тег</p>
          <TagSearch existingTagIds={existingTagIds} onSelect={handleAddTag} />
        </div>

        <div className="flex gap-2 text-xs text-gray-400">
          {[
            ['S', 'bg-purple-500'],
            ['A', 'bg-blue-500'],
            ['B', 'bg-green-500'],
            ['C', 'bg-yellow-500'],
            ['D', 'bg-gray-400'],
          ].map(([label, cls]) => (
            <span key={label} className="flex items-center gap-1">
              <span className={`w-3 h-3 rounded-sm ${cls}`} />
              {label}
            </span>
          ))}
          <span className="ml-1 text-gray-300">= главный → слабый</span>
        </div>
      </div>
    </Layout>
  )
}
