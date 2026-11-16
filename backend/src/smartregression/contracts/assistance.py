"""Snapshot-bound static assistance, distinct from generated explanations."""

from typing import Literal

from pydantic import Field

from smartregression.contracts.explorer import GraphEvidence
from smartregression.contracts.repository import GitHubCommit, WebValue


class ReadingStep(WebValue):
    category: Literal["entrypoint", "module", "data", "tests"]
    path: str
    reason: str
    evidence: GraphEvidence


class ReadingGuide(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    repository_id: str
    commit: GitHubCommit
    config_digest: str
    entrypoint_status: Literal["observed", "unknown"]
    steps: list[ReadingStep]
    limitations: list[str]


class FeatureMatch(WebValue):
    path: str
    symbol: str | None = None
    score: float
    matched_terms: list[str]
    evidence: GraphEvidence


class FeatureSearch(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    repository_id: str
    commit: GitHubCommit
    config_digest: str
    retrieval_version: Literal["web-physical-lexical/1"] = "web-physical-lexical/1"
    query: str
    status: Literal["matched", "no_evidence"]
    items: list[FeatureMatch]
    indexed_chunks: int
    truncated: bool
    limitations: list[str]


class FeatureQuery(WebValue):
    query: str = Field(min_length=1, max_length=600)
    top_k: int = Field(default=10, ge=1, le=10)
