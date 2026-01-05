# Veritas

**Enterprise Research Verification System**

![Veritas Badge](https://img.shields.io/badge/Veritas-Enterprise_Grade-indigo.svg)
![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/frontend-React_18-cyan.svg)
![Google ADK](https://img.shields.io/badge/agent_engine-Google_ADK-orange.svg)

Veritas is an autonomous, multi-agent system designed to audit scientific manuscripts for reproducibility, statistical validity, and submission readiness. By deploying a swarm of specialized AI agents, Veritas provides a rigorous, pre-submission peer review that catches critical issues before they reach human reviewers.

---

## 🚀 Key Features

- **Autonomous Agent Swarm**: Seven specialized AI agents working in concert to analyze different facets of a research paper.
- **Evidence-Backed Verification**: claims are traceably mapped to specific lines in experiment logs and source code.
- **Premium Enterprise UI**: A sleek, dark-mode interface built with React and Tailwind CSS for a professional user experience.
- **Real-time Pipeline Visualization**: Watch the verification graph execute in real-time as agents collaborate.
- **Comprehensive Reporting**: Generates a detailed audit covering reproducibility, statistics, citations, and more.

## 🏗️ Architecture

Veritas utilizes a modern decoupled architecture:

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + Framer Motion
- **Visualization**: React Flow (for agent graph) & Lucide Icons
- **Routing**: React Router DOM

### Backend
- **API Server**: FastAPI (Python)
- **Agent Engine**: Google Agent Development Kit (ADK)
- **Model**: Google Gemini Pro 1.5
- **Orchestration**: Sequential Agent Pipeline

### The 7-Agent Swarm

| Agent | Icon | Responsibility |
|-------|------|----------------|
| **PaperParserAgent** | 📄 | High-fidelity extraction of claims, datasets, and metrics from PDF/LaTeX. |
| **ReproducibilityAgent** | 🔄 | Scans for random seeds, hardware specs, and library versions. |
| **ExperimentEvidenceAgent** | 🧪 | Maps every paper claim to specific evidence in execution logs. |
| **StatisticalAuditorAgent** | 📈 | Detects p-hacking, variance issues, and weak statistical claims. |
| **RelatedWorkBaselineAgent** | 📚 | Identifies missing baselines and citation coverage gaps. |
| **ReviewerSimulationAgent** | 👨‍🔬 | Simulates a harsh Tier-1 conference reviewer to predict rejection reasons. |
| **VerdictAgent** | ⚖️ | Synthesizes all analysis into a final Go/No-Go verdict and compliance report. |

---

## 🛠️ Installation & Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- Google AI API Key

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-org/veritas.git
cd veritas

# Create virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

**Run the Backend Server:**
```bash
python web_api.py
```
*Server runs on http://localhost:8000*

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run Development Server
npm run dev
```
*Application runs on http://localhost:5173*

---

## 📖 Usage Guide

1.  **Launch**: Open `http://localhost:5173/` in your browser.
2.  **Landing Page**: Click **"Get Started"** to enter the analysis dashboard.
3.  **Upload Assets**:
    *   **Research Paper**: Upload your PDF draft.
    *   **Logs (Optional)**: Upload `.csv` or `.log` files from your experiments.
    *   **Scripts (Optional)**: Upload `.py` training scripts for reproducibility checks.
4.  **Analyze**: Click **"Start Analysis"**.
5.  **Monitor**: Watch the agent graph light up as each agent processes its task.
6.  **Review**: Once complete, review the detailed report, critical issues, and reproducibility score.

---

## 📂 Project Structure

```
veritas/
├── frontend/                 # React Application
│   ├── src/
│   │   ├── components/       # AgentNode, AnimatedEdge, etc.
│   │   ├── Analyzer.tsx      # Main Application Logic
│   │   ├── LandingPage.tsx   # Corporate Landing Page
│   │   └── App.tsx           # Router Configuration
│   └── ...
├── research_verifier/        # Python ADK Package
│   ├── agents/               # Individual Agent Definitions
│   │   ├── paper_parser.py
│   │   ├── verdict.py
│   │   └── ...
│   ├── tools/                # Analysis Tools (PDF, Logs)
│   └── agent.py              # Pipeline Orchestrator
├── web_api.py                # FastAPI Backend & Agent Aggregator
├── requirements.txt          # Python Dependencies
└── README.md                 # Documentation
```

## 🤝 Contributing

We welcome contributions! Please fork the repository and submit a Pull Request.

## 📄 License

MIT License. Copyright © 2026 Veritas Logic Inc.

---

*Powered by Google ADK and Gemini Models.*
