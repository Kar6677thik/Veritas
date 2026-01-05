import { useState, useCallback, useEffect, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from '@xyflow/react'
import type { Node, Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, 
  Play, 
  FileText, 
  ChevronDown, 
  CheckCircle2, 
  AlertCircle, 
  Zap, 
  X,
  FileSearch,
  RefreshCw,
  FlaskConical,
  BarChart3,
  BookOpen,
  UserCheck,
  Scale
} from 'lucide-react'
import AgentNode from './components/AgentNode'
import AnimatedEdge from './components/AnimatedEdge'
import './App.css'

const nodeTypes = { agent: AgentNode }
const edgeTypes = { animated: AnimatedEdge }

// Agent configuration with icons
const AGENT_CONFIG = {
  paper: { label: 'Paper Parser', Icon: FileSearch },
  repro: { label: 'Reproducibility', Icon: RefreshCw },
  evidence: { label: 'Evidence Mapper', Icon: FlaskConical },
  stats: { label: 'Stats Auditor', Icon: BarChart3 },
  related: { label: 'Related Work', Icon: BookOpen },
  reviewer: { label: 'Reviewer Sim', Icon: UserCheck },
  verdict: { label: 'Final Verdict', Icon: Scale },
} as const

// Helper to render agent icon
const AgentIcon = ({ agentId, className = "w-5 h-5" }: { agentId: string; className?: string }) => {
  const config = AGENT_CONFIG[agentId as keyof typeof AGENT_CONFIG]
  if (!config) return null
  const IconComponent = config.Icon
  return <IconComponent className={className} />
}

// Initial node positions
const createInitialNodes = (): Node[] => [
  { id: 'paper', type: 'agent', position: { x: 400, y: 50 }, data: { label: 'Paper Parser', iconId: 'paper', status: 'idle' } },
  { id: 'repro', type: 'agent', position: { x: 150, y: 200 }, data: { label: 'Reproducibility', iconId: 'repro', status: 'idle' } },
  { id: 'evidence', type: 'agent', position: { x: 400, y: 200 }, data: { label: 'Evidence Mapper', iconId: 'evidence', status: 'idle' } },
  { id: 'stats', type: 'agent', position: { x: 650, y: 200 }, data: { label: 'Stats Auditor', iconId: 'stats', status: 'idle' } },
  { id: 'related', type: 'agent', position: { x: 150, y: 350 }, data: { label: 'Related Work', iconId: 'related', status: 'idle' } },
  { id: 'reviewer', type: 'agent', position: { x: 400, y: 350 }, data: { label: 'Reviewer Sim', iconId: 'reviewer', status: 'idle' } },
  { id: 'verdict', type: 'agent', position: { x: 400, y: 500 }, data: { label: 'Final Verdict', iconId: 'verdict', status: 'idle' } },
]

const createInitialEdges = (): Edge[] => [
  { id: 'e1', source: 'paper', target: 'repro', type: 'animated', data: { active: false } },
  { id: 'e2', source: 'paper', target: 'evidence', type: 'animated', data: { active: false } },
  { id: 'e3', source: 'paper', target: 'stats', type: 'animated', data: { active: false } },
  { id: 'e4', source: 'repro', target: 'related', type: 'animated', data: { active: false } },
  { id: 'e5', source: 'evidence', target: 'reviewer', type: 'animated', data: { active: false } },
  { id: 'e6', source: 'stats', target: 'reviewer', type: 'animated', data: { active: false } },
  { id: 'e7', source: 'related', target: 'reviewer', type: 'animated', data: { active: false } },
  { id: 'e8', source: 'reviewer', target: 'verdict', type: 'animated', data: { active: false } },
]

interface LogEntry {
  time: string
  agent: string
  msg: string
  type: 'info' | 'success' | 'warn' | 'error'
}

interface ReviewerComment {
  severity: string
  comment: string
}

interface AnalysisResults {
  paper_analysis?: {
    claims?: string[]
    datasets?: string[]
    paper_title?: string
    metrics?: string[]
  }
  reproducibility?: {
    reproducibility_score?: number
    missing_items?: string[]
    missing_reproducibility_items?: string[] // Alternate key
    found_seeds?: string[]
    found_hardware?: string[]
    found_library_versions?: Record<string, string>
    recommendations?: string[]
  }
  experiment_evidence?: {
    issues?: string[]
    experiment_map?: Record<string, { claimed_result: string; log_file: string; evidence_strength: string }>
    untraceable_results?: string[]
    missing_experiments?: string[]
    logs_analyzed?: unknown[]
  }
  statistical_audit?: {
    weak_claims?: string[]
    variance_issues?: string[]
    recommendations?: string[]
    valid_claims?: string[] // In case available
  }
  related_work?: {
    citations_found?: number
    issues?: string[]
    missing_baselines?: string[]
    related_work_gaps?: string[]
    weak_comparisons?: string[]
    citation_issues?: string[]
  }
  reviewer_simulation?: {
    comments?: ReviewerComment[]
    strengths?: string[]
    weaknesses?: string[]
    overall_assessment?: string
  }
  verdict?: {
    submission_readiness?: string
    overall_verdict?: string
    confidence_score?: number
    reproducibility_score?: number
  }
}

interface AgentResult {
  id: string
  name: string
  iconId: string
  status: 'success' | 'warning' | 'error'
  summary: string
  findings: string[]
}

function Analyzer() {
  const API_URL = import.meta.env.VITE_API_URL || ''
  const [nodes, setNodes, onNodesChange] = useNodesState(createInitialNodes())
  const [edges, setEdges, onEdgesChange] = useEdgesState(createInitialEdges())
  const [stage, setStage] = useState<'upload' | 'processing' | 'results'>('upload')
  const [files, setFiles] = useState<{ paper?: File; logs?: File[]; scripts?: File[]; bibtex?: File }>({})
  const [preview, setPreview] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [results, setResults] = useState<AnalysisResults | null>(null)
  const [agentResults, setAgentResults] = useState<AgentResult[]>([])
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs])

  const addLog = useCallback((agent: string, msg: string, type: LogEntry['type'] = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [...prev, { time, agent, msg, type }])
  }, [])

  const mapAgentName = (name: string): string => {
    const map: Record<string, string> = {
      'PaperParserAgent': 'paper',
      'ReproducibilityAgent': 'repro',
      'ExperimentEvidenceAgent': 'evidence',
      'StatisticalAuditorAgent': 'stats',
      'RelatedWorkBaselineAgent': 'related',
      'ReviewerSimulationAgent': 'reviewer',
      'VerdictAgent': 'verdict',
    }
    return map[name] || name
  }

  const updateNodeStatus = useCallback((nodeId: string, status: string) => {
    setNodes(nds => nds.map(n => 
      n.id === nodeId ? { ...n, data: { ...n.data, status } } : n
    ))
  }, [setNodes])

  const updateEdgeActive = useCallback((targetId: string, active: boolean) => {
    setEdges(eds => eds.map(e => 
      e.target === targetId ? { ...e, data: { ...e.data, active } } : e
    ))
  }, [setEdges])

  const buildAgentResults = (data: AnalysisResults): AgentResult[] => {
    const results: AgentResult[] = []

    // Paper Parser
    const paperFindings: string[] = []
    if (data.paper_analysis?.claims?.length) {
      paperFindings.push(`Extracted ${data.paper_analysis.claims.length} claims`)
      data.paper_analysis.claims.forEach(claim => claim && paperFindings.push(`Claim: ${claim.slice(0, 100)}${claim.length > 100 ? '...' : ''}`))
    }
    if (data.paper_analysis?.datasets?.length) {
      paperFindings.push(`Datasets: ${data.paper_analysis.datasets.join(', ')}`)
    }
    if (data.paper_analysis?.metrics?.length) {
      paperFindings.push(`Metrics: ${data.paper_analysis.metrics.join(', ')}`)
    }
    results.push({
      id: 'paper',
      name: 'Paper Parser',
      iconId: 'paper',
      status: data.paper_analysis?.claims?.length ? 'success' : 'warning',
      summary: `${data.paper_analysis?.claims?.length || 0} claims extracted`,
      findings: paperFindings.length > 0 ? paperFindings : ['No claims parsed']
    })

    // Reproducibility
    const reproFindings: string[] = []
    const missingItems = data.reproducibility?.missing_items || data.reproducibility?.missing_reproducibility_items || []
    if (missingItems.length) {
      missingItems.forEach(item => item && reproFindings.push(`Missing: ${item}`))
    }
    if (data.reproducibility?.found_seeds?.length) {
      reproFindings.push(`Seeds found: ${data.reproducibility.found_seeds.join(', ')}`)
    }
    if (data.reproducibility?.found_hardware?.length) {
      reproFindings.push(`Hardware identified: ${data.reproducibility.found_hardware.join(', ')}`)
    }
    if (data.reproducibility?.recommendations?.length) {
      data.reproducibility.recommendations.forEach(rec => rec && reproFindings.push(`Recommendation: ${rec}`))
    }
    if (reproFindings.length === 0) reproFindings.push('Basic reproducibility checks passed')
    results.push({
      id: 'repro',
      name: 'Reproducibility',
      iconId: 'repro',
      status: (data.reproducibility?.reproducibility_score || 0) > 50 ? 'success' : 'warning',
      summary: `Score: ${data.reproducibility?.reproducibility_score || 0}%`,
      findings: reproFindings
    })

    // Evidence Mapper
    const evidenceFindings: string[] = []
    const expMap = data.experiment_evidence?.experiment_map
    if (expMap) {
      Object.entries(expMap).forEach(([, val]) => {
        evidenceFindings.push(`Verified: ${val.claimed_result} -> ${val.log_file} (${val.evidence_strength})`)
      })
    }
    if (data.experiment_evidence?.untraceable_results?.length) {
      data.experiment_evidence.untraceable_results.forEach(res => res && evidenceFindings.push(`Untraceable: ${res}`))
    }
    if (data.experiment_evidence?.missing_experiments?.length) {
      data.experiment_evidence.missing_experiments.forEach(exp => exp && evidenceFindings.push(`Missing Experiment: ${exp}`))
    }
    // Fallback if no detailed structured data but issues array exists
    if (data.experiment_evidence?.issues?.length && evidenceFindings.length === 0) {
       data.experiment_evidence.issues.forEach(i => i && evidenceFindings.push(i))
    }
    if (evidenceFindings.length === 0) evidenceFindings.push('No evidence mapping data available')
    results.push({
      id: 'evidence',
      name: 'Evidence Mapper',
      iconId: 'evidence',
      status: (data.experiment_evidence?.untraceable_results?.length || 0) > 0 ? 'warning' : 'success',
      summary: `${Object.keys(expMap || {}).length} results verified`,
      findings: evidenceFindings
    })

    // Stats Auditor
    const statsFindings: string[] = []
    if (data.statistical_audit?.weak_claims?.length) {
      data.statistical_audit.weak_claims.forEach(claim => claim && statsFindings.push(`Weak claim: ${claim}`))
    }
    if (data.statistical_audit?.variance_issues?.length) {
      data.statistical_audit.variance_issues.forEach(issue => issue && statsFindings.push(`Variance: ${issue}`))
    }
    if (data.statistical_audit?.valid_claims?.length) {
       // Assuming there might be a field for valid claims in future or if added
       data.statistical_audit.valid_claims.forEach(claim => claim && statsFindings.push(`Valid: ${claim}`))
    }
    if (data.statistical_audit?.recommendations?.length) {
      data.statistical_audit.recommendations.forEach(rec => rec && statsFindings.push(`Tip: ${rec}`))
    }
    if (statsFindings.length === 0) statsFindings.push('Statistical audit found no critical issues')
    results.push({
      id: 'stats',
      name: 'Stats Auditor',
      iconId: 'stats',
      status: data.statistical_audit?.weak_claims?.length ? 'warning' : 'success',
      summary: statsFindings.length > 0 ? `${statsFindings.length} items logged` : 'Pass',
      findings: statsFindings
    })

    // Related Work
    const relatedFindings: string[] = []
    const gaps = [...(data.related_work?.missing_baselines || []), ...(data.related_work?.related_work_gaps || []), ...(data.related_work?.citation_issues || [])]
    if (gaps.length) {
      gaps.forEach(gap => gap && relatedFindings.push(`Gap: ${gap}`))
    } else {
      relatedFindings.push('No significant coverage gaps found')
    }
    if (data.related_work?.weak_comparisons?.length) {
       data.related_work.weak_comparisons.forEach(wc => wc && relatedFindings.push(`Weak Comparison: ${wc}`))
    }
    results.push({
      id: 'related',
      name: 'Related Work',
      iconId: 'related',
      status: gaps.length > 0 ? 'warning' : 'success',
      summary: `${gaps.length} gaps identified`,
      findings: relatedFindings
    })

    // Reviewer Simulation
    const reviewerFindings: string[] = []
    if (data.reviewer_simulation?.overall_assessment) {
      reviewerFindings.push(`Assessment: ${data.reviewer_simulation.overall_assessment}`)
    }
    if (data.reviewer_simulation?.strengths?.length) {
      data.reviewer_simulation.strengths.forEach(s => s && reviewerFindings.push(`[STRENGTH] ${s}`))
    }
    if (data.reviewer_simulation?.weaknesses?.length) {
      data.reviewer_simulation.weaknesses.forEach(w => w && reviewerFindings.push(`[WEAKNESS] ${w}`))
    }
    if (data.reviewer_simulation?.comments?.length) {
      data.reviewer_simulation.comments.forEach(c => {
        if (c?.comment) {
          const prefix = c.severity === 'major' ? '[MAJOR] ' : c.severity === 'minor' ? '[MINOR] ' : ''
          reviewerFindings.push(`${prefix}${c.comment}`)
        }
      })
    }
    results.push({
      id: 'reviewer',
      name: 'Reviewer Simulation',
      iconId: 'reviewer',
      status: (data.reviewer_simulation?.weaknesses?.length || 0) > 0 ? 'warning' : 'success',
      summary: `${(data.reviewer_simulation?.strengths?.length || 0) + (data.reviewer_simulation?.weaknesses?.length || 0)} points`,
      findings: reviewerFindings.length > 0 ? reviewerFindings : ['Review simulation detailed no specific points']
    })

    // Final Verdict
    if (data.verdict?.overall_verdict) {
      results.push({
        id: 'verdict',
        name: 'Final Verdict',
        iconId: 'verdict',
        status: data.verdict?.submission_readiness?.includes('READY') && !data.verdict?.submission_readiness?.includes('NOT') ? 'success' : 'error',
        summary: data.verdict?.submission_readiness || 'Complete',
        findings: [data.verdict.overall_verdict]
      })
    }

    return results
  }

  // Poll for status
  useEffect(() => {
    if (!sessionId || stage !== 'processing') return
    let lastAgent = ''

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/status/${sessionId}`)
        const data = await res.json()
        setProgress(data.progress || 0)

        if (data.current_agent) {
          const agentId = mapAgentName(data.current_agent)
          if (agentId !== lastAgent) {
            if (lastAgent) {
              updateNodeStatus(lastAgent, 'success')
              updateEdgeActive(lastAgent, false)
              addLog(lastAgent, '✓ Complete', 'success')
            }
            updateNodeStatus(agentId, 'running')
            updateEdgeActive(agentId, true)
            addLog(agentId, 'Processing...', 'info')
            lastAgent = agentId
          }
        }

        if (data.status === 'completed') {
          clearInterval(interval)
          createInitialNodes().forEach(n => updateNodeStatus(n.id, 'success'))
          createInitialEdges().forEach(e => updateEdgeActive(e.target, false))
          addLog('system', '✓ Analysis complete', 'success')
          setResults(data.results)
          setAgentResults(buildAgentResults(data.results))
          setTimeout(() => setStage('results'), 800)
        }

        if (data.status === 'error') {
          clearInterval(interval)
          setError(data.error)
          addLog('error', data.error, 'error')
        }
      } catch (err) {
        console.error(err)
      }
    }, 800)

    return () => clearInterval(interval)
  }, [sessionId, stage, addLog, updateNodeStatus, updateEdgeActive])

  const handleUpload = async () => {
    if (!files.paper) return
    setStage('processing')
    setLogs([])
    createInitialNodes().forEach(n => updateNodeStatus(n.id, 'idle'))
    
    addLog('system', '▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓', 'info')
    addLog('system', 'Veritas Verification System', 'info')
    addLog('system', '▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓', 'info')
    addLog('system', 'Initializing agents...', 'info')

    const formData = new FormData()
    formData.append('paper', files.paper)
    files.logs?.forEach(f => formData.append('logs', f))
    files.scripts?.forEach(f => formData.append('scripts', f))
    if (files.bibtex) formData.append('bibtex', files.bibtex)

    try {
      const res = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      setSessionId(data.session_id)
      addLog('system', `Session: ${data.session_id.slice(0, 8)}`, 'success')
    } catch {
      setError('Upload failed')
    }
  }

  const reset = () => {
    setStage('upload')
    setFiles({})
    setPreview('')
    setSessionId(null)
    setProgress(0)
    setLogs([])
    setResults(null)
    setAgentResults([])
    setExpandedAgent(null)
    setError(null)
    setNodes(createInitialNodes())
    setEdges(createInitialEdges())
  }

  const readPreview = (file: File) => {
    if (file.name.endsWith('.pdf')) {
      setPreview('[PDF - content extracted during analysis]')
    } else {
      const reader = new FileReader()
      reader.onload = e => setPreview((e.target?.result as string).slice(0, 3000))
      reader.readAsText(file)
    }
  }

  return (
    <div className="h-screen w-screen bg-black flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-12 border-b border-zinc-800 bg-black/80 backdrop-blur-sm flex items-center justify-between px-4 shrink-0 z-50">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-500" />
          <span className="font-semibold text-sm">Veritas</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>7 Agents Ready</span>
        </div>
      </header>

      <PanelGroup orientation="horizontal" className="flex-1">
        {/* Left Panel - Upload / Results */}
        <Panel defaultSize={30} minSize={20} className="bg-zinc-950">
          <div className="h-full relative overflow-hidden">
            <AnimatePresence mode="wait">
              {stage === 'upload' && (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex flex-col p-4 gap-4 overflow-auto"
                >
                  <h2 className="text-lg font-semibold">Upload Files</h2>
                  
                  <div
                    className={`flex-1 min-h-[150px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer transition-all ${
                      files.paper ? 'border-green-500/50 bg-green-500/5' : 'border-zinc-700 hover:border-indigo-500/50 hover:bg-indigo-500/5'
                    }`}
                    onClick={() => document.getElementById('paper')?.click()}
                  >
                    <input id="paper" type="file" className="hidden" accept=".pdf,.tex,.txt,.md"
                      onChange={e => { const f = e.target.files?.[0]; if (f) { setFiles(fs => ({...fs, paper: f})); readPreview(f) } }} />
                    {files.paper ? (
                      <>
                        <CheckCircle2 className="w-8 h-8 text-green-500" />
                        <span className="text-sm font-medium">{files.paper.name}</span>
                        <span className="text-xs text-zinc-500">{(files.paper.size/1024).toFixed(1)} KB</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-8 h-8 text-zinc-500" />
                        <span className="text-sm text-zinc-400">Drop paper here</span>
                        <span className="text-xs text-zinc-600">PDF, LaTeX, or Text</span>
                      </>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: 'logs', iconId: 'stats', label: 'Logs', accept: '.csv,.json,.txt,.log', multi: true },
                      { id: 'scripts', iconId: 'evidence', label: 'Scripts', accept: '.py', multi: true },
                      { id: 'bibtex', iconId: 'related', label: 'BibTeX', accept: '.bib', multi: false },
                    ].map(item => (
                      <div
                        key={item.id}
                        className={`p-3 rounded-lg border cursor-pointer text-center text-xs transition-all ${
                          (files as Record<string, File | File[] | undefined>)[item.id] ? 'border-green-500/50 bg-green-500/5' : 'border-zinc-800 hover:border-indigo-500/50'
                        }`}
                        onClick={() => document.getElementById(item.id)?.click()}
                      >
                        <input id={item.id} type="file" className="hidden" accept={item.accept} multiple={item.multi}
                          onChange={e => setFiles(f => ({...f, [item.id]: item.multi ? Array.from(e.target.files || []) : e.target.files?.[0]}))} />
                        <div className="flex justify-center mb-1">
                          <AgentIcon agentId={item.iconId} className="w-5 h-5 text-zinc-400" />
                        </div>
                        <div className="text-zinc-400">{item.label}</div>
                      </div>
                    ))}
                  </div>

                  {preview && (
                    <div className="border border-zinc-800 rounded-lg overflow-hidden">
                      <div className="px-3 py-2 bg-zinc-900 border-b border-zinc-800 text-xs text-zinc-400 flex items-center gap-2">
                        <FileText className="w-3 h-3" /> Preview
                      </div>
                      <pre className="p-3 text-[10px] text-zinc-500 overflow-auto max-h-32 font-mono">{preview}</pre>
                    </div>
                  )}

                  <button
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all"
                    disabled={!files.paper}
                    onClick={handleUpload}
                  >
                    <Play className="w-4 h-4" /> Start Analysis
                  </button>
                </motion.div>
              )}

              {stage === 'processing' && (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex flex-col p-4 gap-4 overflow-y-auto"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Analyzing...</h2>
                    <span className="text-xs text-indigo-400">{progress}%</span>
                  </div>
                  
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <motion.div 
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>

                  <div className="flex flex-col gap-2 flex-1">
                    {[
                      { id: 'paper', name: 'Paper Parser' },
                      { id: 'repro', name: 'Reproducibility' },
                      { id: 'evidence', name: 'Evidence Mapper' },
                      { id: 'stats', name: 'Stats Auditor' },
                      { id: 'related', name: 'Related Work' },
                      { id: 'reviewer', name: 'Reviewer Sim' },
                      { id: 'verdict', name: 'Final Verdict' },
                    ].map((agent) => {
                      const nodeData = nodes.find(n => n.id === agent.id)?.data as { status?: string }
                      const isRunning = nodeData?.status === 'running'
                      const isDone = nodeData?.status === 'success'
                      return (
                        <div
                          key={agent.id}
                          className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                            isRunning ? 'border-indigo-500 bg-indigo-500/10' :
                            isDone ? 'border-green-500/30 bg-green-500/5' :
                            'border-zinc-800 bg-zinc-900/50'
                          }`}
                        >
                          <div className="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center shrink-0">
                            <AgentIcon agentId={agent.id} className="w-5 h-5 text-indigo-400" />
                          </div>
                          <div className="flex-1">
                            <div className="text-sm font-medium">{agent.name}</div>
                            <div className="text-xs text-zinc-500">
                              {isRunning ? 'Processing...' : isDone ? 'Complete' : 'Waiting...'}
                            </div>
                          </div>
                          {isRunning && (
                            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                          )}
                          {isDone && (
                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                          )}
                        </div>
                      )
                    })}
                  </div>
                </motion.div>
              )}

              {stage === 'results' && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex flex-col p-4 gap-4"
                >
                  <div className="flex items-center justify-between shrink-0">
                    <h2 className="text-lg font-semibold">Results</h2>
                    <button onClick={reset} className="text-xs text-zinc-400 hover:text-white">New Analysis</button>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                    {/* Overall Verdict Card */}
                    <div className={`p-4 rounded-xl border shrink-0 ${
                      results?.verdict?.submission_readiness?.includes('NOT') ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'
                    }`}>
                      <div className={`inline-block px-3 py-1 rounded-full text-xs font-medium mb-2 ${
                        results?.verdict?.submission_readiness?.includes('NOT') ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                      }`}>
                        {results?.verdict?.submission_readiness || 'Complete'}
                      </div>
                      <p className="text-sm text-zinc-300 line-clamp-3">{results?.verdict?.overall_verdict}</p>
                      <div className="flex gap-6 mt-3">
                        <div>
                          <div className="text-2xl font-bold text-indigo-400">{results?.verdict?.confidence_score || 0}%</div>
                          <div className="text-[10px] text-zinc-500 uppercase">Confidence</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-indigo-400">{results?.verdict?.reproducibility_score || 0}%</div>
                          <div className="text-[10px] text-zinc-500 uppercase">Reproducibility</div>
                        </div>
                      </div>
                    </div>

                    {/* Agent Results - Show each agent with findings */}
                    <div className="flex flex-col gap-3">
                      {agentResults
                        .filter(agent => agent.findings.length > 0 && agent.findings.some(f => f && f.trim() !== ''))
                        .map(agent => (
                        <div
                          key={agent.id}
                          className={`border rounded-lg overflow-hidden transition-all ${
                            agent.status === 'success' ? 'border-green-500/30' :
                            agent.status === 'warning' ? 'border-yellow-500/30' : 'border-red-500/30'
                          } bg-zinc-900/50`}
                        >
                          {/* Agent Header */}
                          <div 
                            className="flex items-center gap-3 p-3 cursor-pointer hover:bg-zinc-900"
                            onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
                          >
                            <div className="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center shrink-0">
                              <AgentIcon agentId={agent.iconId} className="w-5 h-5 text-indigo-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium">{agent.name}</div>
                              <div className="text-xs text-zinc-500">{agent.summary}</div>
                            </div>
                            <div className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                              agent.status === 'success' ? 'bg-green-500/20 text-green-400' :
                              agent.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                              {agent.status === 'success' ? 'OK' : agent.status === 'warning' ? 'WARN' : 'ISSUE'}
                            </div>
                            <motion.div animate={{ rotate: expandedAgent === agent.id ? 180 : 0 }}>
                              <ChevronDown className="w-4 h-4 text-zinc-500" />
                            </motion.div>
                          </div>

                          {/* Agent Findings */}
                          <AnimatePresence>
                            {expandedAgent === agent.id && (
                              <motion.div 
                                initial={{ height: 0 }} 
                                animate={{ height: 'auto' }} 
                                exit={{ height: 0 }} 
                                className="overflow-hidden"
                              >
                                <div className="px-3 pb-3 pt-2 border-t border-zinc-800 bg-zinc-900">
                                  {agent.findings
                                    .filter(f => f && f.trim() !== '')
                                    .map((finding, i) => (
                                    <div 
                                      key={i} 
                                      className="text-xs text-zinc-300 py-2 border-b border-zinc-800/50 last:border-0 leading-relaxed"
                                    >
                                      <span className="text-zinc-500 mr-2">•</span>
                                      {finding}
                                    </div>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Panel>

        <PanelResizeHandle className="w-1 bg-zinc-800 hover:bg-indigo-500/50 transition-colors" />

        {/* Center - React Flow Canvas */}
        <Panel defaultSize={50} minSize={30}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            minZoom={0.3}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#222" />
            <Controls />
            <MiniMap
              nodeColor={node => {
                const nodeData = node.data as { status?: string }
                const status = nodeData?.status
                if (status === 'running') return '#6366f1'
                if (status === 'success') return '#22c55e'
                if (status === 'error') return '#ef4444'
                return '#333'
              }}
              maskColor="rgba(0,0,0,0.8)"
            />
          </ReactFlow>
        </Panel>

        <PanelResizeHandle className="w-1 bg-zinc-800 hover:bg-indigo-500/50 transition-colors" />

        {/* Right Panel - Terminal */}
        <Panel defaultSize={20} minSize={15} className="bg-black">
          <div className="h-full flex flex-col">
            <div className="h-10 border-b border-zinc-800 flex items-center gap-2 px-3 shrink-0">
              <div className="flex gap-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <span className="text-xs text-zinc-500 ml-2">Agent Logs</span>
            </div>
            <div ref={terminalRef} className="flex-1 p-3 overflow-auto font-mono text-[11px] leading-relaxed">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-zinc-600 w-16 shrink-0">{log.time}</span>
                  <span className="text-indigo-400 w-20 shrink-0">{log.agent}</span>
                  <span className={
                    log.type === 'success' ? 'text-green-400' :
                    log.type === 'warn' ? 'text-yellow-400' :
                    log.type === 'error' ? 'text-red-400' : 'text-emerald-400'
                  }>{log.msg}</span>
                </div>
              ))}
              <span className="text-emerald-400 animate-pulse">█</span>
            </div>
            {stage === 'processing' && (
              <div className="h-8 border-t border-zinc-800 flex items-center px-3 gap-2 shrink-0">
                <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div className="h-full bg-indigo-500" animate={{ width: `${progress}%` }} />
                </div>
                <span className="text-xs text-indigo-400 font-medium">{progress}%</span>
              </div>
            )}
          </div>
        </Panel>
      </PanelGroup>

      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-3 bg-zinc-900 border border-red-500/50 rounded-lg text-sm z-50">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-red-400">{error}</span>
          <button onClick={() => setError(null)}><X className="w-4 h-4 text-zinc-500" /></button>
        </div>
      )}
    </div>
  )
}

export default Analyzer
