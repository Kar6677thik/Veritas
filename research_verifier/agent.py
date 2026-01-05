"""
Root Agent - Research Verification Pipeline

This module defines the root agent that orchestrates all sub-agents
using ADK's SequentialAgent workflow.

The pipeline runs the following agents in sequence:
1. PaperParserAgent - Parse paper and extract claims
2. ReproducibilityAgent - Check reproducibility info (parallel with parser)
3. ExperimentEvidenceAgent - Map results to evidence
4. StatisticalAuditorAgent - Audit statistical validity
5. RelatedWorkBaselineAgent - Check citations and baselines
6. ReviewerSimulationAgent - Generate reviewer comments
7. VerdictAgent - Produce final verdict
"""

from google.adk.agents import Agent, SequentialAgent, ParallelAgent

from .agents.paper_parser import paper_parser_agent
from .agents.experiment_evidence import experiment_evidence_agent
from .agents.statistical_auditor import statistical_auditor_agent
from .agents.related_work import related_work_agent
from .agents.reviewer_simulation import reviewer_simulation_agent
from .agents.reproducibility import reproducibility_agent
from .agents.verdict import verdict_agent


# Create the orchestration workflow
# Using SequentialAgent to ensure proper data flow between agents

# The full pipeline runs agents in sequence:
# 1. Parse paper first (foundation for all other analysis)
# 2. Then run experiment evidence and reproducibility (can be parallelized in future)
# 3. Statistical audit (needs experiment evidence)
# 4. Related work analysis (needs paper analysis)
# 5. Reviewer simulation (needs all previous)
# 6. Final verdict (aggregates everything)

root_agent = SequentialAgent(
    name="ResearchVerificationPipeline",
    description="""A multi-agent system for research paper verification and analysis.
    
This pipeline helps researchers detect weaknesses, inconsistencies, and risks
in their research papers before submission. It runs 7 specialized agents:

1. PaperParserAgent - Extracts claims, results, datasets, metrics
2. ReproducibilityAgent - Checks for reproducibility information
3. ExperimentEvidenceAgent - Maps results to experimental evidence
4. StatisticalAuditorAgent - Evaluates statistical validity
5. RelatedWorkBaselineAgent - Analyzes citations and baselines
6. ReviewerSimulationAgent - Simulates reviewer feedback
7. VerdictAgent - Produces final verdict with action items

To use: Provide paths to your paper (PDF/LaTeX/txt), experiment logs, 
scripts, and BibTeX file. The system will analyze and provide actionable feedback.
""",
    sub_agents=[
        paper_parser_agent,
        reproducibility_agent,
        experiment_evidence_agent,
        statistical_auditor_agent,
        related_work_agent,
        reviewer_simulation_agent,
        verdict_agent,
    ]
)


# Alternative: More granular pipeline with parallel initial analysis
def create_parallel_pipeline():
    """
    Create an alternative pipeline with parallel initial analysis.
    
    This version runs paper parsing and reproducibility check in parallel
    for faster execution.
    """
    # Stage 1: Parallel initial analysis
    initial_analysis = ParallelAgent(
        name="InitialAnalysis",
        description="Parallel analysis of paper content and reproducibility",
        sub_agents=[paper_parser_agent, reproducibility_agent]
    )
    
    # Full pipeline with parallel first stage
    parallel_root = SequentialAgent(
        name="ResearchVerificationPipelineParallel",
        description="Research verification with parallel initial analysis",
        sub_agents=[
            initial_analysis,
            experiment_evidence_agent,
            statistical_auditor_agent,
            related_work_agent,
            reviewer_simulation_agent,
            verdict_agent,
        ]
    )
    
    return parallel_root
