import { useEffect, useRef, useState } from 'react'
import type { Tag } from '../../api/matching'
import { tagsApi } from '../../api/matching'

interface Props {
  existingTagIds: Set<string>
  onSelect: (tag: Tag) => void
}

export function TagSearch({ existingTagIds, onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Tag[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setOpen(false)
      return
    }
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await tagsApi.search(query.trim())
        setResults(data.items.filter(t => !existingTagIds.has(t.id)))
        setOpen(true)
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [query, existingTagIds])

  async function handleCreate() {
    if (!query.trim()) return
    setLoading(true)
    try {
      const tag = await tagsApi.create(query.trim())
      onSelect(tag)
      setQuery('')
      setOpen(false)
    } finally {
      setLoading(false)
    }
  }

  function handleSelect(tag: Tag) {
    onSelect(tag)
    setQuery('')
    setOpen(false)
  }

  const queryNormalized = query.trim().toLowerCase()
  const exactMatch = results.some(t => t.name === queryNormalized)

  return (
    <div className="relative">
      <input
        ref={inputRef}
        value={query}
        onChange={e => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Найти или добавить тег…"
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-indigo-400 bg-white"
      />
      {loading && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">...</span>
      )}
      {open && (results.length > 0 || (!exactMatch && queryNormalized)) && (
        <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
          {results.map(tag => (
            <button
              key={tag.id}
              onMouseDown={() => handleSelect(tag)}
              className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-indigo-50 text-left"
            >
              <span>{tag.name}</span>
              {tag.category && (
                <span className="text-xs text-gray-400">{tag.category}</span>
              )}
            </button>
          ))}
          {!exactMatch && queryNormalized && (
            <button
              onMouseDown={handleCreate}
              className="w-full px-3 py-2 text-sm text-indigo-600 hover:bg-indigo-50 text-left border-t border-gray-100"
            >
              + Создать «{queryNormalized}»
            </button>
          )}
        </div>
      )}
    </div>
  )
}
