"""Individual agent implementations for the research verification system."""

from .paper_parser import paper_parser_agent
from .experiment_evidence import experiment_evidence_agent
from .statistical_auditor import statistical_auditor_agent
from .related_work import related_work_agent
from .reviewer_simulation import reviewer_simulation_agent
from .reproducibility import reproducibility_agent
from .verdict import verdict_agent

__all__ = [
    "paper_parser_agent",
    "experiment_evidence_agent",
    "statistical_auditor_agent",
    "related_work_agent",
    "reviewer_simulation_agent",
    "reproducibility_agent",
    "verdict_agent",
]
