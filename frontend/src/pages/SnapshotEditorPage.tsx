import { useEffect, useRef, useState } from 'react'
import { Layout } from '../components/Layout'
import { SnapshotItem } from '../components/SnapshotEditor/SnapshotItem'
import { TagSearch } from '../components/SnapshotEditor/TagSearch'
import { snapshotsApi, type SnapshotItemOut } from '../api/snapshots'
import type { Tag } from '../api/matching'

const WEIGHT_ORDER: Record<string, number> = { S: 0, A: 1, B: 2, C: 3, D: 4 }
const ORDER_KEY = 'snapshot_tag_order'

function loadOrder(): string[] {
  try { return JSON.parse(localStorage.getItem(ORDER_KEY) ?? '[]') } catch { return [] }
}

function persistOrder(items: SnapshotItemOut[]) {
  localStorage.setItem(ORDER_KEY, JSON.stringify(items.map(i => i.tag_id)))
}

function applyOrder(items: SnapshotItemOut[], order: string[]): SnapshotItemOut[] {
  if (order.length === 0) return items
  const map = new Map(items.map(i => [i.tag_id, i]))
  const known = order.flatMap(id => map.has(id) ? [map.get(id)!] : [])
  const rest = items.filter(i => !order.includes(i.tag_id))
  return [...known, ...rest]
}

export function SnapshotEditorPage() {
  const [items, setItems] = useState<SnapshotItemOut[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [sortByPriority, setSortByPriority] = useState(false)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const dragIndexRef = useRef<number | null>(null)

  useEffect(() => {
    snapshotsApi.get().then(data => {
      const ordered = applyOrder(data.items, loadOrder())
      setItems(ordered)
      setLoading(false)
    })
  }, [])

  const existingTagIds = new Set(items.map(i => i.tag_id))

  async function handleWeightChange(tagId: string, weight: string) {
    setSaving(true)
    try {
      await snapshotsApi.upsertItem(tagId, weight)
      setItems(prev => prev.map(i => i.tag_id === tagId ? { ...i, weight } : i))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(tagId: string) {
    setSaving(true)
    try {
      await snapshotsApi.deleteItem(tagId)
      setItems(prev => {
        const next = prev.filter(i => i.tag_id !== tagId)
        persistOrder(next)
        return next
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleAddTag(tag: Tag) {
    setSaving(true)
    try {
      await snapshotsApi.upsertItem(tag.id, 'B')
      setItems(prev => {
        const next = [...prev, { tag_id: tag.id, tag_name: tag.name, weight: 'B' }]
        persistOrder(next)
        return next
      })
    } finally {
      setSaving(false)
    }
  }

  function handleDragStart(index: number) {
    dragIndexRef.current = index
    setDragIndex(index)
  }

  function handleDragOver(e: React.DragEvent, overIndex: number) {
    e.preventDefault()
    const from = dragIndexRef.current
    if (from === null || from === overIndex) return
    dragIndexRef.current = overIndex
    setDragIndex(overIndex)
    setItems(prev => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(overIndex, 0, moved)
      return next
    })
  }

  function handleDragEnd() {
    dragIndexRef.current = null
    setDragIndex(null)
    setItems(prev => {
      persistOrder(prev)
      return prev
    })
  }

  const displayed = sortByPriority
    ? [...items].sort((a, b) => (WEIGHT_ORDER[a.weight] ?? 9) - (WEIGHT_ORDER[b.weight] ?? 9))
    : items

  return (
    <Layout>
      <div className="max-w-lg mx-auto flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-800">Мой слепок</h1>
          <div className="flex items-center gap-3">
            {saving && <span className="text-xs text-gray-400">Сохраняем…</span>}
            {items.length > 1 && (
              <button
                onClick={() => setSortByPriority(v => !v)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  sortByPriority
                    ? 'border-indigo-300 bg-indigo-50 text-indigo-600'
                    : 'border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600'
                }`}
              >
                {sortByPriority ? 'По приоритету ✓' : 'По приоритету'}
              </button>
            )}
          </div>
        </div>

        <p className="text-sm text-gray-500">
          Добавьте теги и расставьте веса: S — главный интерес, D — слабый.
        </p>

        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-sm text-gray-400">Загружаем…</div>
          ) : displayed.length === 0 ? (
            <div className="p-8 text-center text-sm text-gray-400">
              Слепок пуст — добавьте первый тег ниже
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {displayed.map((item, index) => (
                <SnapshotItem
                  key={item.tag_id}
                  item={item}
                  index={index}
                  dragging={!sortByPriority && dragIndex === index}
                  onWeightChange={handleWeightChange}
                  onDelete={handleDelete}
                  onDragStart={sortByPriority ? () => {} : handleDragStart}
                  onDragOver={sortByPriority ? e => e.preventDefault() : handleDragOver}
                  onDragEnd={sortByPriority ? () => {} : handleDragEnd}
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
