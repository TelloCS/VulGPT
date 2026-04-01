from ninja import Schema
from typing import List, Optional, Dict


class VulnerabilitySchema(Schema):
    cve_id: str
    summary: Optional[str] = None
    classification: str
    safe_versions: Optional[str] = None
    github_references: List[str] = []


class ScanStatsSchema(Schema):
    status: str
    total_packages: int
    processed_packages: int
    created_at: Optional[int]
    completed_at: Optional[int]
    total_vulnerabilities: int
    breakdown: Dict[str, int]


class UploadResponseSchema(Schema):
    message: str
    scan_id: str


class ErrorSchema(Schema):
    error: str
