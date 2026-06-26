import type { SnapshotItemOut } from '../../api/snapshots'
import { WeightSelector } from './WeightSelector'

interface Props {
  item: SnapshotItemOut
  index: number
  dragging?: boolean
  onWeightChange: (tagId: string, weight: string) => void
  onDelete: (tagId: string) => void
  onDragStart: (index: number) => void
  onDragOver: (e: React.DragEvent, index: number) => void
  onDragEnd: () => void
}

export function SnapshotItem({ item, index, dragging, onWeightChange, onDelete, onDragStart, onDragOver, onDragEnd }: Props) {
  return (
    <div
      draggable
      onDragStart={() => onDragStart(index)}
      onDragOver={e => onDragOver(e, index)}
      onDragEnd={onDragEnd}
      className={`flex items-center gap-2 py-2 px-3 hover:bg-gray-50 transition-opacity ${dragging ? 'opacity-40' : ''}`}
    >
      <span className="text-gray-300 cursor-grab active:cursor-grabbing select-none px-1 text-base leading-none">
        ⠿
      </span>
      <span className="flex-1 text-sm text-gray-700">{item.tag_name}</span>
      <WeightSelector
        value={item.weight}
        onChange={w => onWeightChange(item.tag_id, w)}
      />
      <button
        onClick={() => onDelete(item.tag_id)}
        className="w-6 h-6 flex items-center justify-center rounded text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
      >
        ×
      </button>
    </div>
  )
}
