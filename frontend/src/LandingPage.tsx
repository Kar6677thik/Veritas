import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  FileSearch, 
  RefreshCw, 
  FlaskConical, 
  BarChart3, 
  BookOpen, 
  UserCheck, 
  Scale, 
  ShieldCheck,
  Zap,
  Play,
  X
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const VideoModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
        onClick={onClose}
      >
        <motion.div 
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="relative w-full max-w-5xl aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-zinc-800"
          onClick={(e) => e.stopPropagation()}
        >
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 text-white transition-colors z-10"
          >
            <X className="w-6 h-6" />
          </button>
          <div className="w-full h-full flex items-center justify-center bg-zinc-900">
             {/* Placeholder for actual video source */}
             <div className="text-center">
                <Play className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
                <p className="text-zinc-500">Promotional Video Placeholder</p>
             </div>
          </div>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
)

const Hero = () => {
  const navigate = useNavigate()
  const [isVideoOpen, setIsVideoOpen] = useState(false)

  return (
    <div className="relative overflow-hidden pt-32 pb-24 lg:pt-48 lg:pb-40 bg-slate-950">
      <VideoModal isOpen={isVideoOpen} onClose={() => setIsVideoOpen(false)} />
      
      {/* Subtle Background - Corporate Style */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-slate-900/50 via-slate-950 to-slate-950" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-8 font-display">
            Research Verification <br />
            <span className="text-slate-400">
              Redefined.
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed font-light">
            Veritas provides enterprise-grade validation for scientific manuscripts using advanced multi-agent architecture.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button 
              onClick={() => navigate('/app')}
              className="px-8 py-4 rounded-lg bg-white text-slate-900 hover:bg-slate-100 font-semibold text-lg transition-all shadow-xl shadow-slate-900/20 w-48"
            >
              Get Started
            </button>
            <button 
              onClick={() => setIsVideoOpen(true)}
              className="px-8 py-4 rounded-lg bg-transparent border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 font-medium text-lg transition-all flex items-center gap-2 group w-48 justify-center"
            >
              <Play className="w-5 h-5 fill-current" />
              Watch Demo
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

const FeatureCard = ({ icon: Icon, title, description }: { icon: LucideIcon, title: string, description: string }) => (
  <div className="p-8 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
    <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center mb-6 text-slate-200">
      <Icon className="w-6 h-6" />
    </div>
    <h3 className="text-xl font-semibold text-white mb-3">{title}</h3>
    <p className="text-slate-400 leading-relaxed text-sm">{description}</p>
  </div>
)

const AgentsGrid = () => {
  const agents = [
    {
      icon: FileSearch,
      title: "Paper Parser",
      description: "Extracts claims and datasets with high-fidelity parsing."
    },
    {
      icon: RefreshCw,
      title: "Reproducibility",
      description: "Validates seeds, hardware, and environment specifications."
    },
    {
      icon: FlaskConical,
      title: "Evidence Mapping",
      description: "Traceably links claims to experimental log data."
    },
    {
      icon: BarChart3,
      title: "Statistical Audit",
      description: "Detects anomalies and variance issues in results."
    },
    {
      icon: BookOpen,
      title: "Citation Analysis",
      description: "Identifies coverage gaps and missing baselines."
    },
    {
      icon: UserCheck,
      title: "Reviewer Simulation",
      description: "Predicts potential rejection criteria prior to submission."
    },
    {
      icon: Scale,
      title: "Compliance Verdict",
      description: "Synthesizes a final readiness report with action items."
    }
  ]

  return (
    <div id="methodology" className="py-32 bg-slate-950 relative border-t border-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-20">
          <h2 className="text-3xl font-bold text-white mb-6">Our Methodology</h2>
          <p className="text-slate-400 max-w-2xl">
            Veritas employs a seven-stage verification pipeline to ensure absolute rigor.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {agents.map((agent, idx) => (
            <FeatureCard key={idx} {...agent} />
          ))}
          <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center text-center">
            <Zap className="w-12 h-12 text-slate-500 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">Automated Pipeline</h3>
            <p className="text-slate-500 text-sm">End-to-end processing.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

const HowItWorks = () => {
  return (
    <div id="features" className="py-32 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-6">Seamless Integration</h2>
                    <p className="text-slate-400 mb-8 text-lg">
                        Designed for research labs and enterprise R&D teams. Simply upload your assets and let Veritas handle the validation.
                    </p>
                    <ul className="space-y-4">
                        {[
                            "Secure Asset Handling",
                            "Comprehensive Logs Analysis",
                            "Instant PDF Generation",
                            "Actionable Feedback"
                        ].map((item, i) => (
                            <li key={i} className="flex items-center gap-3 text-slate-300">
                                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                                {item}
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="relative">
                    <div className="absolute inset-0 bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none" />
                    <div className="relative bg-slate-950 border border-slate-800 rounded-2xl p-8 shadow-2xl">
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 font-bold">1</div>
                                <div>
                                    <h4 className="text-white font-medium">Upload Manuscript</h4>
                                    <p className="text-slate-500 text-sm">PDF or LaTeX format supported.</p>
                                </div>
                            </div>
                            <div className="w-0.5 h-8 bg-slate-800 ml-5" />
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 font-bold">2</div>
                                <div>
                                    <h4 className="text-white font-medium">Connect Data Source</h4>
                                    <p className="text-slate-500 text-sm">Attach logs and training scripts.</p>
                                </div>
                            </div>
                            <div className="w-0.5 h-8 bg-slate-800 ml-5" />
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-emerald-900/20 border border-emerald-900/50 flex items-center justify-center text-emerald-500 font-bold">3</div>
                                <div>
                                    <h4 className="text-white font-medium">Receive Audit</h4>
                                    <p className="text-slate-500 text-sm">Download your verification certificate.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-slate-700">
      <nav className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            <div className="flex items-center gap-3 font-bold text-2xl tracking-tight text-white">
                <div className="w-8 h-8 flex items-center justify-center">
                    <ShieldCheck className="w-8 h-8 text-white" />
                </div>
                Veritas
            </div>
            <div className="hidden md:flex items-center gap-10 text-sm font-medium text-slate-400">
                <a href="#features" className="hover:text-white transition-colors">Features</a>
                <a href="#methodology" className="hover:text-white transition-colors">Methodology</a>
                <a href="#enterprise" className="hover:text-white transition-colors">Enterprise</a>
                <a href="#contact" className="hover:text-white transition-colors">Contact</a>
            </div>
            <div className="w-24"></div> {/* Spacer for balance since Sign In is gone */}
        </div>
      </nav>

      <main>
        <Hero />
        <HowItWorks />
        <AgentsGrid />
      </main>

      <footer className="border-t border-slate-900 py-16 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-8">
                <div className="flex items-center gap-2 text-slate-500 text-sm font-medium">
                    <ShieldCheck className="w-5 h-5" />
                    © 2026 Veritas Logic Inc.
                </div>
                <div className="flex gap-8 text-slate-500 text-sm">
                    <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                    <a href="#" className="hover:text-white transition-colors">Service Terms</a>
                    <a href="#" className="hover:text-white transition-colors">Security</a>
                </div>
            </div>
        </div>
      </footer>
    </div>
  )
}
