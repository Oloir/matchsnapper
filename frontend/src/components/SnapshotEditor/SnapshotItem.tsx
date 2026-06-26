import type { SnapshotItemOut } from '../../api/snapshots'
import { WeightSelector } from './WeightSelector'

interface Props {
  item: SnapshotItemOut
  onWeightChange: (tagId: string, weight: string) => void
  onDelete: (tagId: string) => void
}

export function SnapshotItem({ item, onWeightChange, onDelete }: Props) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-gray-50">
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
