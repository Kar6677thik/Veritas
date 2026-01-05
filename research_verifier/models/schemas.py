"""
Pydantic schemas for structured agent communication.

These models define the input/output structures for each agent,
enabling type-safe message passing through ADK's state mechanism.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class Severity(str, Enum):
    """Severity levels for issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    """Priority levels for action items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ========================
# PaperParserAgent Schemas
# ========================

class ReportedResult(BaseModel):
    """A result reported in the paper."""
    metric_name: str = Field(description="Name of the metric (e.g., accuracy, F1)")
    value: str = Field(description="The reported value")
    location: str = Field(description="Where in the paper (e.g., Table 1, Section 4.2)")
    context: Optional[str] = Field(default=None, description="Additional context about the result")


class PaperParserOutput(BaseModel):
    """Output from the PaperParserAgent."""
    claims: List[str] = Field(default_factory=list, description="Main claims made in the paper")
    reported_results: List[ReportedResult] = Field(default_factory=list, description="Numerical results reported")
    datasets: List[str] = Field(default_factory=list, description="Datasets mentioned")
    metrics: List[str] = Field(default_factory=list, description="Evaluation metrics used")
    baselines: List[str] = Field(default_factory=list, description="Baseline methods mentioned")
    paper_title: Optional[str] = Field(default=None, description="Title of the paper if found")
    abstract: Optional[str] = Field(default=None, description="Abstract if found")


# ================================
# ExperimentEvidenceAgent Schemas
# ================================

class ExperimentMapping(BaseModel):
    """Mapping of a claim/result to its experimental evidence."""
    claimed_result: str = Field(description="The claimed result from the paper")
    log_file: Optional[str] = Field(default=None, description="Associated log file if found")
    script_file: Optional[str] = Field(default=None, description="Associated script if found")
    evidence_strength: str = Field(default="none", description="none/weak/moderate/strong")
    notes: Optional[str] = Field(default=None, description="Additional notes about the mapping")


class ExperimentEvidenceOutput(BaseModel):
    """Output from the ExperimentEvidenceAgent."""
    experiment_map: Dict[str, ExperimentMapping] = Field(
        default_factory=dict, 
        description="Mapping of results to their experimental evidence"
    )
    untraceable_results: List[str] = Field(
        default_factory=list, 
        description="Results that cannot be traced to experiments"
    )
    missing_experiments: List[str] = Field(
        default_factory=list,
        description="Expected experiments that are missing"
    )


# ===============================
# StatisticalAuditorAgent Schemas
# ===============================

class WeakClaim(BaseModel):
    """A statistically weak claim identified in the paper."""
    claim: str = Field(description="The claim that is statistically weak")
    reason: str = Field(description="Why the claim is considered weak")
    severity: Severity = Field(default=Severity.MEDIUM, description="Severity of the issue")
    recommendation: Optional[str] = Field(default=None, description="How to strengthen the claim")


class StatisticalAuditOutput(BaseModel):
    """Output from the StatisticalAuditorAgent."""
    weak_claims: List[WeakClaim] = Field(default_factory=list, description="Claims with statistical issues")
    variance_issues: List[str] = Field(default_factory=list, description="Issues with variance/std reporting")
    significance_issues: List[str] = Field(default_factory=list, description="Statistical significance concerns")
    metric_misuse: List[str] = Field(default_factory=list, description="Cases of metric misuse")


# ================================
# RelatedWorkBaselineAgent Schemas
# ================================

class RelatedWorkOutput(BaseModel):
    """Output from the RelatedWorkBaselineAgent."""
    missing_baselines: List[str] = Field(
        default_factory=list, 
        description="Standard baselines that should be compared against"
    )
    related_work_gaps: List[str] = Field(
        default_factory=list, 
        description="Gaps in related work coverage"
    )
    weak_comparisons: List[str] = Field(
        default_factory=list,
        description="Comparisons that are incomplete or unfair"
    )
    citation_issues: List[str] = Field(
        default_factory=list,
        description="Issues with citations (missing, outdated, etc.)"
    )


# ==================================
# ReviewerSimulationAgent Schemas
# ==================================

class ReviewerComment(BaseModel):
    """A simulated reviewer comment."""
    comment: str = Field(description="The reviewer's comment")
    category: str = Field(description="Category: methodology/results/clarity/novelty/reproducibility")
    severity: Severity = Field(default=Severity.MEDIUM, description="How critical this comment is")
    section: Optional[str] = Field(default=None, description="Which section this relates to")


class ReviewerSimulationOutput(BaseModel):
    """Output from the ReviewerSimulationAgent."""
    reviewer_comments: List[ReviewerComment] = Field(
        default_factory=list, 
        description="Simulated reviewer comments"
    )
    overall_assessment: Optional[str] = Field(
        default=None, 
        description="Overall assessment summary"
    )
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weaknesses")


# =============================
# ReproducibilityAgent Schemas
# =============================

class ReproducibilityOutput(BaseModel):
    """Output from the ReproducibilityAgent."""
    missing_reproducibility_items: List[str] = Field(
        default_factory=list, 
        description="Missing reproducibility information"
    )
    found_seeds: List[str] = Field(default_factory=list, description="Random seeds found")
    found_hardware: List[str] = Field(default_factory=list, description="Hardware specifications found")
    found_library_versions: Dict[str, str] = Field(
        default_factory=dict, 
        description="Library versions found"
    )
    reproducibility_score: Optional[float] = Field(
        default=None, 
        description="Estimated reproducibility score 0-100"
    )


# =====================
# VerdictAgent Schemas
# =====================

class ActionItem(BaseModel):
    """An action item for the researcher."""
    action: str = Field(description="What needs to be done")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    category: str = Field(description="Category of the action")
    estimated_effort: Optional[str] = Field(default=None, description="Estimated effort (low/medium/high)")


class VerdictOutput(BaseModel):
    """Final output from the VerdictAgent."""
    critical_issues: List[str] = Field(
        default_factory=list, 
        description="Critical issues that must be addressed"
    )
    reviewer_risks: List[str] = Field(
        default_factory=list, 
        description="Likely points of reviewer criticism"
    )
    reproducibility_gaps: List[str] = Field(
        default_factory=list, 
        description="Reproducibility information gaps"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list, 
        description="Prioritized list of actions"
    )
    overall_verdict: Optional[str] = Field(
        default=None, 
        description="Overall assessment of paper readiness"
    )
    confidence_score: Optional[float] = Field(
        default=None, 
        description="Confidence in the analysis 0-100"
    )


# =====================
# Input Schemas
# =====================

class ResearchInputs(BaseModel):
    """Input configuration for the research verification system."""
    paper_path: Optional[str] = Field(default=None, description="Path to paper PDF or LaTeX file")
    paper_text: Optional[str] = Field(default=None, description="Raw paper text if already extracted")
    experiment_logs: List[str] = Field(default_factory=list, description="Paths to experiment log files")
    experiment_scripts: List[str] = Field(default_factory=list, description="Paths to experiment scripts")
    bibtex_path: Optional[str] = Field(default=None, description="Path to .bib file")
    target_venue: Optional[str] = Field(default=None, description="Target venue for submission")
    claimed_contributions: List[str] = Field(default_factory=list, description="Claimed contributions")
