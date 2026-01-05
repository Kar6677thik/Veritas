#!/usr/bin/env python3
"""
Demo Runner for Research Verification System

This script demonstrates the multi-agent research verification pipeline
using sample data. It runs all agents sequentially and displays the results.

Usage:
    python run_demo.py [--paper PATH] [--logs DIR] [--scripts DIR] [--bib PATH]
    
Example:
    python run_demo.py --paper sample_data/sample_paper.txt
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))


def setup_environment():
    """Load environment variables and check for API key."""
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment.")
        print("   Please set your API key in a .env file:")
        print("   GOOGLE_API_KEY=your_api_key_here")
        print()
        return False
    return True


def print_banner():
    """Print the demo banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║     Research Verification System - Multi-Agent Pipeline         ║
║                                                                  ║
║   Powered by Google ADK (Agent Development Kit)                 ║
╠══════════════════════════════════════════════════════════════════╣
║   Agents:                                                        ║
║   1. PaperParserAgent       - Extract claims & results          ║
║   2. ReproducibilityAgent   - Check reproducibility info        ║
║   3. ExperimentEvidenceAgent- Map results to evidence           ║
║   4. StatisticalAuditorAgent- Audit statistical validity        ║
║   5. RelatedWorkBaselineAgent- Analyze citations & baselines    ║
║   6. ReviewerSimulationAgent- Simulate reviewer feedback        ║
║   7. VerdictAgent           - Final verdict & action items      ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def get_default_paths():
    """Get default paths for sample data."""
    sample_dir = project_root / "sample_data"
    
    return {
        "paper": sample_dir / "sample_paper.txt",
        "logs": [str(sample_dir / "experiment_logs" / "training_log.csv")],
        "scripts": [str(sample_dir / "scripts" / "train.py")],
        "bib": sample_dir / "references.bib"
    }


async def run_agent_pipeline(paper_path: str, log_paths: list, script_paths: list, bib_path: str):
    """
    Run the full agent pipeline.
    
    This function demonstrates how the agents communicate through ADK's
    state mechanism using output_key.
    """
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
    from google.genai import types
    from research_verifier.agent import root_agent
    
    print("\n🚀 Starting Research Verification Pipeline...\n")
    print(f"   📄 Paper: {paper_path}")
    print(f"   📊 Logs: {log_paths}")
    print(f"   📝 Scripts: {script_paths}")
    print(f"   📚 BibTeX: {bib_path}")
    print()
    
    # Create session service
    session_service = InMemorySessionService()
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="research_verifier",
        session_service=session_service
    )
    
    # Prepare the user message with all file paths
    user_message_text = f"""Please analyze this research paper and provide a comprehensive verification report.

**Paper Path**: {paper_path}
**Experiment Logs**: {', '.join(log_paths) if log_paths else 'None provided'}
**Experiment Scripts**: {', '.join(script_paths) if script_paths else 'None provided'}
**BibTeX File**: {bib_path if bib_path else 'None provided'}

Please run the full verification pipeline:
1. Parse the paper and extract claims, results, datasets, and metrics
2. Check reproducibility information in the scripts and logs
3. Map reported results to experimental evidence
4. Audit the statistical validity of claims
5. Analyze citations and baseline comparisons
6. Simulate likely reviewer comments
7. Produce a final verdict with prioritized action items

Provide detailed, actionable feedback that would help improve the paper before submission.
"""
    
    # Create proper Content object for ADK
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message_text)]
    )
    
    # Run the pipeline
    print("=" * 70)
    print("Running agents...")
    print("=" * 70)
    
    # Create a new session
    session = await session_service.create_session(
        app_name="research_verifier",
        user_id="demo_user"
    )
    
    # Run the agent with retry logic for rate limits
    final_response = None
    agent_outputs = {}
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async for event in runner.run_async(
                user_id="demo_user",
                session_id=session.id,
                new_message=user_message
            ):
                # Print agent progress
                if hasattr(event, 'author') and event.author:
                    agent_name = event.author
                    if agent_name not in agent_outputs:
                        agent_outputs[agent_name] = True
                        print(f"\n✅ {agent_name} completed")
                
                # Capture the final response
                if hasattr(event, 'content') and event.content:
                    final_response = event.content
            
            # If we get here, execution was successful
            break
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 20 * retry_count  # Exponential backoff: 20s, 40s, 60s
                    print(f"\n⚠️  Rate limit hit. Waiting {wait_time} seconds before retry {retry_count}/{max_retries}...")
                    import time
                    time.sleep(wait_time)
                else:
                    print("\n❌ Rate limit exceeded after all retries.")
                    print("   Options:")
                    print("   1. Wait a few minutes and try again")
                    print("   2. Run standalone demo: python run_demo.py")
                    print("   3. Upgrade your API key to a paid tier")
                    print("   4. Use a different API key")
                    return None
            else:
                # Re-raise non-rate-limit errors
                raise
    
    # Print the final response
    if final_response:
        print("\n" + "=" * 70)
        print("📋 FINAL VERIFICATION REPORT")
        print("=" * 70)
        if isinstance(final_response, types.Content):
            for part in final_response.parts:
                if hasattr(part, 'text'):
                    print(part.text)
        else:
            print(final_response)
    
    print("\n" + "=" * 70)
    print("✅ Pipeline completed!")
    print("=" * 70)
    
    return final_response


def run_standalone_demo(paper_path: str, log_paths: list, script_paths: list, bib_path: str):
    """
    Run a standalone demo without full ADK runner.
    
    This demonstrates the tool functions and shows sample output.
    """
    print("\n🔍 Running Standalone Analysis Demo...\n")
    
    # Import tools
    from research_verifier.tools.pdf_parser import parse_pdf
    from research_verifier.tools.latex_parser import parse_latex
    from research_verifier.tools.log_analyzer import analyze_training_logs, extract_reproducibility_info
    from research_verifier.tools.bib_parser import get_citation_info
    
    results = {}
    
    # 1. Parse paper
    print("📄 Step 1: Parsing paper...")
    if paper_path and os.path.exists(paper_path):
        ext = os.path.splitext(paper_path)[1].lower()
        if ext == '.pdf':
            paper_result = parse_pdf(paper_path)
        elif ext in ['.tex', '.latex']:
            paper_result = parse_latex(paper_path)
        else:
            # Plain text
            with open(paper_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            paper_result = {"status": "success", "full_text": content}
        
        results["paper"] = paper_result
        if paper_result.get("status") == "success":
            text_len = len(paper_result.get("full_text", ""))
            print(f"   ✅ Parsed paper: {text_len} characters")
        else:
            print(f"   ❌ Failed to parse paper: {paper_result.get('error_message')}")
    else:
        print("   ⚠️  No paper file provided or file not found")
    
    # 2. Analyze logs
    print("\n📊 Step 2: Analyzing experiment logs...")
    if log_paths:
        for log_path in log_paths:
            if os.path.exists(log_path):
                log_result = analyze_training_logs(log_path)
                results[f"log_{os.path.basename(log_path)}"] = log_result
                
                if log_result.get("status") == "success":
                    metrics = log_result.get("metrics", {})
                    print(f"   ✅ Analyzed {log_path}")
                    print(f"      Metrics found: {list(metrics.keys())}")
                else:
                    print(f"   ❌ Failed to analyze {log_path}")
            else:
                print(f"   ⚠️  Log file not found: {log_path}")
    else:
        print("   ⚠️  No log files provided")
    
    # 3. Check reproducibility
    print("\n📝 Step 3: Checking reproducibility info...")
    if script_paths:
        for script_path in script_paths:
            if os.path.exists(script_path):
                repro_result = extract_reproducibility_info(script_path)
                results[f"repro_{os.path.basename(script_path)}"] = repro_result
                
                if repro_result.get("status") == "success":
                    print(f"   ✅ Analyzed {script_path}")
                    print(f"      Seeds found: {repro_result.get('seeds', [])}")
                    print(f"      Hyperparameters: {list(repro_result.get('hyperparameters', {}).keys())}")
                    print(f"      Missing items: {repro_result.get('missing_items', [])}")
                else:
                    print(f"   ❌ Failed to analyze {script_path}")
            else:
                print(f"   ⚠️  Script not found: {script_path}")
    else:
        print("   ⚠️  No script files provided")
    
    # 4. Analyze citations
    print("\n📚 Step 4: Analyzing citations...")
    if bib_path and os.path.exists(bib_path):
        bib_result = get_citation_info(bib_path)
        results["citations"] = bib_result
        
        if bib_result.get("status") == "success":
            count = bib_result.get("count", 0)
            print(f"   ✅ Analyzed {count} citations")
            if bib_result.get("issues"):
                print(f"      Issues: {bib_result.get('issues')}")
        else:
            print(f"   ❌ Failed to parse BibTeX: {bib_result.get('error_message')}")
    else:
        print("   ⚠️  No BibTeX file provided")
    
    # 5. Generate sample output
    print("\n" + "=" * 70)
    print("📋 SAMPLE VERIFICATION REPORT")
    print("=" * 70)
    
    sample_report = {
        "critical_issues": [
            "Result '94.7% success rate on Gibson' cannot be verified from logs",
            "Log shows val_accuracy of 91.01%, paper claims 94.7% - discrepancy detected",
            "No standard deviation reported for main results"
        ],
        "reviewer_risks": [
            "Missing comparison to recent SOTA methods (2023-2024)",
            "No reproducibility section or code availability statement",
            "Statistical significance of improvements not verified"
        ],
        "reproducibility_gaps": [
            "Random seed not explicitly set in training script",
            "Library versions not pinned",
            "GPU/hardware specifications missing"
        ],
        "action_items": [
            {
                "action": "Verify and align reported results with experiment logs",
                "priority": "URGENT",
                "category": "experiments",
                "effort": "medium"
            },
            {
                "action": "Add experiments with multiple random seeds (5+)",
                "priority": "HIGH",
                "category": "experiments",
                "effort": "high"
            },
            {
                "action": "Add explicit seed setting: torch.manual_seed(42)",
                "priority": "HIGH", 
                "category": "code",
                "effort": "low"
            },
            {
                "action": "Compare against ResNet baseline (missing from CV benchmarks)",
                "priority": "HIGH",
                "category": "experiments",
                "effort": "medium"
            },
            {
                "action": "Create requirements.txt with pinned versions",
                "priority": "MEDIUM",
                "category": "code",
                "effort": "low"
            },
            {
                "action": "Add reproducibility appendix with full hyperparameters",
                "priority": "MEDIUM",
                "category": "writing",
                "effort": "low"
            }
        ],
        "overall_verdict": "Paper shows promising contributions but has significant gaps in experimental rigor and reproducibility. Major revisions recommended before submission.",
        "submission_readiness": "NOT READY - Major revisions needed",
        "estimated_time_to_fix": "2-3 weeks"
    }
    
    print(json.dumps(sample_report, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Demo completed!")
    print("=" * 70)
    
    print("\n📌 To run with full ADK agent orchestration:")
    print("   1. Set GOOGLE_API_KEY in .env file")
    print("   2. Run: adk web research_verifier")
    print("   3. Or run: python run_demo.py --full")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Research Verification System Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_demo.py                    # Run with sample data
  python run_demo.py --paper my_paper.pdf
  python run_demo.py --full             # Run full ADK pipeline (requires API key)
        """
    )
    
    parser.add_argument("--paper", type=str, help="Path to research paper (PDF/LaTeX/txt)")
    parser.add_argument("--logs", type=str, nargs="+", help="Paths to experiment log files")
    parser.add_argument("--scripts", type=str, nargs="+", help="Paths to experiment scripts")
    parser.add_argument("--bib", type=str, help="Path to BibTeX file")
    parser.add_argument("--full", action="store_true", help="Run full ADK pipeline")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Get paths
    defaults = get_default_paths()
    
    paper_path = args.paper or str(defaults["paper"])
    log_paths = args.logs or defaults["logs"]
    script_paths = args.scripts or defaults["scripts"]
    bib_path = args.bib or str(defaults["bib"])
    
    if args.full:
        # Run full ADK pipeline
        has_key = setup_environment()
        if not has_key:
            print("Cannot run full pipeline without API key. Running standalone demo instead.\n")
            run_standalone_demo(paper_path, log_paths, script_paths, bib_path)
        else:
            asyncio.run(run_agent_pipeline(paper_path, log_paths, script_paths, bib_path))
    else:
        # Run standalone demo
        run_standalone_demo(paper_path, log_paths, script_paths, bib_path)


if __name__ == "__main__":
    main()
