const WEIGHTS = ['S', 'A', 'B', 'C', 'D'] as const
const WEIGHT_STYLE: Record<string, string> = {
  S: 'bg-purple-500 text-white',
  A: 'bg-blue-500 text-white',
  B: 'bg-green-500 text-white',
  C: 'bg-yellow-500 text-white',
  D: 'bg-gray-400 text-white',
}
const WEIGHT_HOVER: Record<string, string> = {
  S: 'hover:bg-purple-100 hover:text-purple-700',
  A: 'hover:bg-blue-100 hover:text-blue-700',
  B: 'hover:bg-green-100 hover:text-green-700',
  C: 'hover:bg-yellow-100 hover:text-yellow-700',
  D: 'hover:bg-gray-100 hover:text-gray-700',
}

interface Props {
  value: string
  onChange: (w: string) => void
}

export function WeightSelector({ value, onChange }: Props) {
  return (
    <div className="flex gap-1">
      {WEIGHTS.map(w => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`w-7 h-7 rounded text-xs font-bold transition-colors ${
            value === w ? WEIGHT_STYLE[w] : `bg-gray-50 text-gray-400 border border-gray-200 ${WEIGHT_HOVER[w]}`
          }`}
        >
          {w}
        </button>
      ))}
    </div>
  )
}
