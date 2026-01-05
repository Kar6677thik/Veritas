import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  FileSearch,
  RefreshCw,
  FlaskConical,
  BarChart3,
  BookOpen,
  UserCheck,
  Scale
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

// Icon mapping for agents
const ICON_MAP: Record<string, LucideIcon> = {
  paper: FileSearch,
  repro: RefreshCw,
  evidence: FlaskConical,
  stats: BarChart3,
  related: BookOpen,
  reviewer: UserCheck,
  verdict: Scale,
}

interface AgentNodeProps {
  data: {
    label: string
    iconId?: string
    icon?: string  // Keep for backwards compatibility
    status: 'idle' | 'running' | 'success' | 'error'
  }
}

const AgentNode = memo(({ data }: AgentNodeProps) => {
  const { label, iconId, status } = data

  const statusStyles: Record<string, string> = {
    idle: 'border-zinc-700 bg-zinc-900/80',
    running: 'border-indigo-500 bg-indigo-950/60 shadow-[0_0_30px_rgba(99,102,241,0.4)]',
    success: 'border-green-500/50 bg-green-950/40',
    error: 'border-red-500/50 bg-red-950/40',
  }

  // Get the icon component
  const IconComponent = iconId ? ICON_MAP[iconId] : null

  return (
    <div
      className={`
        relative px-4 py-3 rounded-xl border backdrop-blur-md
        min-w-[140px] transition-all duration-300
        ${statusStyles[status] || statusStyles.idle}
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-zinc-600 !border-2 !border-zinc-800 !-top-1.5"
      />

      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
          {IconComponent && <IconComponent className="w-5 h-5 text-indigo-400" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white truncate">{label}</div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wide">
            {status === 'running' ? 'Processing...' :
             status === 'success' ? 'Complete' :
             status === 'error' ? 'Error' : 'Ready'}
          </div>
        </div>
        
        <div className="shrink-0">
          {status === 'running' && (
            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
          )}
          {status === 'success' && (
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          )}
          {status === 'error' && (
            <AlertCircle className="w-4 h-4 text-red-400" />
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-zinc-600 !border-2 !border-zinc-800 !-bottom-1.5"
      />

      {status === 'running' && (
        <div className="absolute inset-0 rounded-xl border-2 border-indigo-500 animate-ping opacity-30 pointer-events-none" />
      )}
    </div>
  )
})

AgentNode.displayName = 'AgentNode'

export default AgentNode
