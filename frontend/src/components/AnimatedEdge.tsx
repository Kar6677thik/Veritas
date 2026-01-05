import { BaseEdge, getBezierPath, Position } from '@xyflow/react'

interface AnimatedEdgeProps {
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: Position
  targetPosition: Position
  data?: { active?: boolean }
}

export default function AnimatedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: AnimatedEdgeProps) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const isActive = data?.active

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: isActive ? '#6366f1' : '#333',
          strokeWidth: isActive ? 2 : 1.5,
          filter: isActive ? 'drop-shadow(0 0 6px rgba(99, 102, 241, 0.5))' : 'none',
        }}
      />

      {isActive && (
        <path
          d={edgePath}
          fill="none"
          stroke="#818cf8"
          strokeWidth={2}
          strokeDasharray="8 8"
          style={{ animation: 'flow 0.5s linear infinite' }}
        />
      )}

      {isActive && (
        <circle r="4" fill="#6366f1">
          <animateMotion dur="1s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}
    </>
  )
}
