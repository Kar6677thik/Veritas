"""
Research Verifier Web API - With Real ADK Agents

FastAPI backend that runs the actual multi-agent pipeline with LLM.
"""

import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

# Load environment variables FIRST (before any ADK imports)
from dotenv import load_dotenv
load_dotenv()

# Verify API key is loaded
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️  WARNING: GOOGLE_API_KEY not found in environment!")
    print("   Make sure your .env file contains: GOOGLE_API_KEY=your_key_here")
else:
    print("✅ GOOGLE_API_KEY loaded successfully")

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import analysis tools for fallback
from research_verifier.tools.pdf_parser import parse_pdf
from research_verifier.tools.latex_parser import parse_latex
from research_verifier.tools.log_analyzer import analyze_training_logs, extract_reproducibility_info
from research_verifier.tools.bib_parser import get_citation_info

app = FastAPI(
    title="Research Verification System",
    description="Multi-Agent Research Paper Analysis with ADK",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = project_root / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Store analysis results in memory
analysis_store: Dict[str, Dict] = {}

# Upload directory
upload_dir = project_root / "uploads"
upload_dir.mkdir(exist_ok=True)


async def save_upload_file(upload_file: UploadFile, session_id: str) -> str:
    """Save uploaded file to disk."""
    session_dir = upload_dir / session_id
    session_dir.mkdir(exist_ok=True)
    
    file_path = session_dir / upload_file.filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)
    
    return str(file_path)


def read_paper_content(file_path: str) -> str:
    """Read paper file and extract text content."""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        result = parse_pdf(file_path)
        if result.get("status") == "success":
            return result.get("full_text", "")
    elif ext in ['.tex', '.latex']:
        result = parse_latex(file_path)
        if result.get("status") == "success":
            return result.get("full_text", "")
    else:
        # Plain text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            pass
    
    return ""


def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON object from text (handling markdown code blocks)."""
    if not text:
        return None
    try:
        # Try finding JSON block
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json.loads(json_match.group(1))
        # Try finding first { and last }
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
    except:
        pass
    return None


async def run_adk_pipeline(session_id: str, paper_path: str, 
                           log_paths: List[str] = None,
                           script_paths: List[str] = None,
                           bib_path: str = None):
    """
    Run the REAL ADK agent pipeline with LLM.
    This calls the actual multi-agent system.
    """
    try:
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai import types
        from research_verifier.agent import root_agent
        
        analysis_store[session_id]["status"] = "running"
        analysis_store[session_id]["progress"] = 5
        analysis_store[session_id]["current_agent"] = "Initializing ADK..."
        
        # Create session service
        session_service = InMemorySessionService()
        
        # Create runner with the root agent
        runner = Runner(
            agent=root_agent,
            app_name="research_verifier",
            session_service=session_service
        )
        
        # Read paper content
        paper_content = read_paper_content(paper_path)
        if not paper_content:
            paper_content = f"[Could not extract text from {paper_path}]"
        
        # Limit paper content to avoid token limits
        if len(paper_content) > 15000:
            paper_content = paper_content[:15000] + "\n\n[... content truncated for analysis ...]"
        
        # Read additional files
        log_content = ""
        if log_paths:
            for lp in log_paths:
                if os.path.exists(lp):
                    try:
                        with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content += f"\n\n--- {os.path.basename(lp)} ---\n"
                            log_content += f.read()[:5000]  # Limit each log
                    except:
                        pass
        
        script_content = ""
        if script_paths:
            for sp in script_paths:
                if os.path.exists(sp):
                    try:
                        with open(sp, 'r', encoding='utf-8', errors='ignore') as f:
                            script_content += f"\n\n--- {os.path.basename(sp)} ---\n"
                            script_content += f.read()[:5000]
                    except:
                        pass
        
        bib_content = ""
        if bib_path and os.path.exists(bib_path):
            try:
                with open(bib_path, 'r', encoding='utf-8', errors='ignore') as f:
                    bib_content = f.read()[:5000]
            except:
                pass
        
        # Prepare comprehensive user message
        user_message_text = f"""Please analyze this research paper and provide a comprehensive verification report.

## PAPER CONTENT:
{paper_content}

## EXPERIMENT LOGS:
{log_content if log_content else 'No experiment logs provided.'}

## EXPERIMENT SCRIPTS:
{script_content if script_content else 'No experiment scripts provided.'}

## BIBTEX REFERENCES:
{bib_content if bib_content else 'No BibTeX file provided.'}

---

Please run the full verification pipeline and provide your analysis in JSON format with these sections:
1. Paper Analysis: claims, results, datasets, metrics extracted
2. Reproducibility Analysis: seeds, hardware, missing items, score
3. Experiment Evidence: log analysis, metric mappings
4. Statistical Audit: weak claims, variance issues
5. Related Work: citation coverage, missing baselines
6. Reviewer Simulation: likely comments and concerns
7. Final Verdict: critical issues, action items, submission readiness

Be specific and reference actual content from the paper in your analysis."""

        # Create ADK Content object
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message_text)]
        )
        
        # Create session
        session = await session_service.create_session(
            app_name="research_verifier",
            user_id=session_id
        )
        
        analysis_store[session_id]["progress"] = 10
        
        # Track agent progress
        completed_agents = []
        agent_progress_map = {
            "PaperParserAgent": 20,
            "ReproducibilityAgent": 35,
            "ExperimentEvidenceAgent": 50,
            "StatisticalAuditorAgent": 65,
            "RelatedWorkBaselineAgent": 75,
            "ReviewerSimulationAgent": 85,
            "VerdictAgent": 95
        }
        
        final_response_text = ""
        
        # Run the agent pipeline
        aggregated_results = {
            "paper_analysis": {"status": "pending", "claims": [], "datasets": [], "metrics": []},
            "reproducibility": {"status": "pending", "missing_items": [], "reproducibility_score": 0},
            "experiment_evidence": {"status": "pending", "issues": [], "experiment_map": {}},
            "statistical_audit": {"status": "pending", "weak_claims": [], "variance_issues": []},
            "related_work": {"status": "pending", "citations_found": 0, "issues": [], "missing_baselines": []},
            "reviewer_simulation": {"status": "pending", "comments": [], "strengths": [], "weaknesses": []},
            "verdict": {
                "status": "pending", 
                "critical_issues": [], 
                "submission_readiness": "Analysis Incomplete", 
                "overall_verdict": "Processing..."
            }
        }

        async for event in runner.run_async(
            user_id=session_id,
            session_id=session.id,
            new_message=user_message
        ):
            # Track agent progress and capture outputs
            if hasattr(event, 'author') and event.author:
                agent_name = event.author
                
                # Update progress
                if agent_name not in completed_agents:
                    completed_agents.append(agent_name)
                    analysis_store[session_id]["current_agent"] = agent_name
                    if agent_name in agent_progress_map:
                        analysis_store[session_id]["progress"] = agent_progress_map[agent_name]

                # Capture Content
                content_text = ""
                if hasattr(event, 'content') and event.content:
                    if isinstance(event.content, types.Content):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                content_text += part.text
                    else:
                        content_text = str(event.content)

                if content_text:
                    # Update aggregated results based on agent
                    json_data = extract_json_from_text(content_text)
                    if json_data:
                        print(f"Captured output from {agent_name}")
                        
                        if agent_name == "PaperParserAgent":
                            aggregated_results["paper_analysis"] = json_data
                            aggregated_results["paper_analysis"]["status"] = "success"
                        
                        elif agent_name == "ReproducibilityAgent":
                            aggregated_results["reproducibility"].update(json_data)
                            aggregated_results["reproducibility"]["status"] = "success"
                            
                        elif agent_name == "ExperimentEvidenceAgent":
                            aggregated_results["experiment_evidence"] = json_data
                            aggregated_results["experiment_evidence"]["status"] = "success"
                            
                        elif agent_name == "StatisticalAuditorAgent":
                            aggregated_results["statistical_audit"] = json_data
                            aggregated_results["statistical_audit"]["status"] = "success"
                            
                        elif agent_name == "RelatedWorkBaselineAgent":
                            aggregated_results["related_work"] = json_data
                            aggregated_results["related_work"]["status"] = "success"
                            
                        elif agent_name == "ReviewerSimulationAgent":
                            # Handle different key names from prompt
                            if "reviewer_comments" in json_data:
                                json_data["comments"] = json_data.pop("reviewer_comments")
                            aggregated_results["reviewer_simulation"] = json_data
                            aggregated_results["reviewer_simulation"]["status"] = "success"
                            
                        elif agent_name == "VerdictAgent":
                            aggregated_results["verdict"] = json_data
                            aggregated_results["verdict"]["status"] = "success"
                            # Also duplicate some scores if missing
                            if "reproducibility_score" in json_data:
                                aggregated_results["reproducibility"]["reproducibility_score"] = json_data["reproducibility_score"]

        # Store results
        analysis_store[session_id]["progress"] = 100
        analysis_store[session_id]["status"] = "completed"
        analysis_store[session_id]["current_agent"] = None
        analysis_store[session_id]["results"] = aggregated_results
        analysis_store[session_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        error_msg = str(e)
        print(f"ADK Pipeline Error: {error_msg}")
        
        # Check if it's a rate limit error
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            analysis_store[session_id]["status"] = "error"
            analysis_store[session_id]["error"] = "API rate limit exceeded. Please wait a few minutes and try again."
        else:
            analysis_store[session_id]["status"] = "error"
            analysis_store[session_id]["error"] = error_msg


def parse_agent_response(response_text: str, paper_path: str) -> Dict:
    """Deprecated: Parsing logic moved to main pipeline loop."""
    return {}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page."""
    html_path = static_dir / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "<h1>Frontend not found</h1>"


@app.post("/api/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    paper: UploadFile = File(...),
    logs: List[UploadFile] = File(default=None),
    scripts: List[UploadFile] = File(default=None),
    bibtex: UploadFile = File(default=None)
):
    """Upload files and start analysis with REAL ADK agents."""
    session_id = str(uuid.uuid4())
    
    # Initialize session
    analysis_store[session_id] = {
        "status": "uploading",
        "progress": 0,
        "current_agent": None,
        "results": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    try:
        # Save paper file
        paper_path = await save_upload_file(paper, session_id)
        
        # Save log files
        log_paths = []
        if logs:
            for log_file in logs:
                if log_file.filename:
                    log_path = await save_upload_file(log_file, session_id)
                    log_paths.append(log_path)
        
        # Save script files
        script_paths = []
        if scripts:
            for script_file in scripts:
                if script_file.filename:
                    script_path = await save_upload_file(script_file, session_id)
                    script_paths.append(script_path)
        
        # Save bibtex file
        bib_path = None
        if bibtex and bibtex.filename:
            bib_path = await save_upload_file(bibtex, session_id)
        
        # Update status
        analysis_store[session_id]["status"] = "processing"
        analysis_store[session_id]["files"] = {
            "paper": paper.filename,
            "logs": [l.filename for l in logs] if logs else [],
            "scripts": [s.filename for s in scripts] if scripts else [],
            "bibtex": bibtex.filename if bibtex else None
        }
        
        # Start REAL ADK pipeline in background
        background_tasks.add_task(
            run_adk_pipeline,
            session_id,
            paper_path,
            log_paths,
            script_paths,
            bib_path
        )
        
        return {"session_id": session_id, "status": "processing"}
        
    except Exception as e:
        analysis_store[session_id]["status"] = "error"
        analysis_store[session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{session_id}")
async def get_analysis_status(session_id: str):
    """Get the status of an analysis session."""
    if session_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return analysis_store[session_id]


@app.get("/api/results/{session_id}")
async def get_analysis_results(session_id: str):
    """Get the full results of an analysis session."""
    if session_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_store[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    return session["results"]


@app.get("/api/raw/{session_id}")
async def get_raw_response(session_id: str):
    """Get the raw LLM response for debugging."""
    if session_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"raw_response": analysis_store[session_id].get("raw_response", "")}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete an analysis session and its files."""
    if session_id in analysis_store:
        del analysis_store[session_id]
    
    # Clean up uploaded files
    session_dir = upload_dir / session_id
    if session_dir.exists():
        import shutil
        shutil.rmtree(session_dir)
    
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("🔬 Research Verifier - Web Interface")
    print("=" * 60)
    print("Server starting at: http://localhost:8000")
    print("This uses the REAL ADK agents with LLM for analysis.")
    print("Make sure GOOGLE_API_KEY is set in your .env file.")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
