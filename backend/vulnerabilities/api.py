import json
import uuid
import csv
from django.http import HttpResponse
from django.conf import settings
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from ninja.pagination import paginate
from typing import List, Optional
from neo4j import GraphDatabase
from .tasks import ingest_osv_data

api = NinjaAPI()

driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)


class VulnerabilitySchema(Schema):
    cve_id: str
    summary: Optional[str] = None
    classification: str
    safe_versions: Optional[str] = None
    github_references: List[str] = []


@api.get("/vulnerabilities/", response=List[VulnerabilitySchema])
@paginate
def get_vulnerabilities(request, search: Optional[str] = None, classification: Optional[str] = None):
    match_clause = "MATCH (v:Vulnerability)"
    where_clauses = []
    params = {}

    if search:
        where_clauses.append(
            """(toLower(v.cve_id) CONTAINS toLower($search) OR
            toLower(v.summary) CONTAINS toLower($search))
        """)
        params["search"] = search

    if classification and classification != "All":
        where_clauses.append("v.classification = $classification")
        params["classification"] = classification

    where_stmt = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    {match_clause}
    {where_stmt}
    OPTIONAL MATCH (v)-[:HAS_REFERENCE]->(g:GitHubNode)
    RETURN v.cve_id AS cve_id,
           v.summary AS summary,
           COALESCE(v.classification, 'Pending Analysis') AS classification,
           v.safe_versions AS safe_versions,
           collect(g.url) AS github_references
    ORDER BY cve_id DESC
    """

    with driver.session() as session:
        results = session.run(query, **params)
        return [record.data() for record in results]


@api.post("/upload-manifest/")
def upload_manifest(request, file: UploadedFile = File(...)):
    if file.size > 1024 * 1024:
        return api.create_response(request, {"error": "File exceeds 1MB limit."}, status=400)

    filename = file.name.lower()
    content = file.read().decode('utf-8')
    queued_packages = []

    try:
        if filename == 'package.json':
            data = json.loads(content)
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            queued_packages = [("npm", pkg) for pkg in deps.keys()]

        elif filename.endswith('.txt') or filename.endswith('.in'):
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                    if pkg_name:
                        queued_packages.append(("PyPI", pkg_name))
        else:
            return api.create_response(request, {"error": "Unsupported file."}, status=400)

    except Exception as e:
        return api.create_response(request, {"error": f"Failed to parse file: {str(e)}"}, status=400)

    if not queued_packages:
        return api.create_response(request, {"error": "No dependencies found."}, status=400)

    scan_id = str(uuid.uuid4())

    with driver.session() as session:
        session.run("""
            MERGE (s:ScanReport {uuid: $scan_id})
            SET s.status = 'PROCESSING',
                s.total_packages = $total,
                s.processed_packages = 0,
                s.created_at = timestamp()
        """, scan_id=scan_id, total=len(queued_packages))

    for ecosystem, package in queued_packages:
        ingest_osv_data.delay(ecosystem=ecosystem, package_name=package, scan_id=scan_id)

    return {
        "message": f"Successfully queued {len(queued_packages)} packages for scanning.",
        "scan_id": scan_id
    }


@api.get("/scans/{scan_id}/", response=List[VulnerabilitySchema])
@paginate
def get_scan_results(request, scan_id: str):
    query = """
    MATCH (s:ScanReport {uuid: $scan_id})<-[:FOUND_IN_SCAN]-(v:Vulnerability)
    OPTIONAL MATCH (v)-[:HAS_REFERENCE]->(g:GitHubNode)
    RETURN v.cve_id AS cve_id,
           v.summary AS summary,
           COALESCE(v.classification, 'Pending Analysis') AS classification,
           v.safe_versions AS safe_versions,
           collect(g.url) AS github_references
    ORDER BY cve_id DESC
    """
    with driver.session() as session:
        results = session.run(query, scan_id=scan_id)
        return [record.data() for record in results]


@api.get("/scans/{scan_id}/stats/", response=dict)
def get_scan_stats(request, scan_id: str):
    query = """
    MATCH (s:ScanReport {uuid: $scan_id})
    OPTIONAL MATCH (s)<-[:FOUND_IN_SCAN]-(v:Vulnerability)
    RETURN s.status AS status,
           s.total_packages AS total,
           s.processed_packages AS processed,
           s.created_at AS created_at,
           s.completed_at AS completed_at,
           COALESCE(v.classification, 'Pending Analysis') AS classification,
           count(v) AS count
    """
    with driver.session() as session:
        results = session.run(query, scan_id=scan_id)

        stats = {
            "Total": 0, "Very Promising": 0, "Slightly Promising": 0, "Not Promising": 0,
            "status": "PROCESSING", "total_packages": 0, "processed_packages": 0,
            "created_at": None, "completed_at": None
        }

        for record in results:
            stats.update({
                "status": record["status"],
                "total_packages": record["total"],
                "processed_packages": record["processed"],
                "created_at": record["created_at"],
                "completed_at": record["completed_at"]
            })

            if record["count"] > 0 and record["classification"] is not None:
                stats[record["classification"]] = record["count"]
                stats["Total"] += record["count"]

        return stats


@api.get("/scans/{scan_id}/export/")
def export_scan_csv(request, scan_id: str):
    query = """
    MATCH (s:ScanReport {uuid: $scan_id})<-[:FOUND_IN_SCAN]-(v:Vulnerability)
    OPTIONAL MATCH (v)-[:HAS_REFERENCE]->(g:GitHubNode)
    RETURN v.cve_id AS cve_id,
           v.summary AS summary,
           COALESCE(v.classification, 'Pending Analysis') AS classification,
           v.safe_versions AS safe_versions,
           collect(g.url) AS github_references
    ORDER BY classification DESC, cve_id DESC
    """
    with driver.session() as session:
        results = session.run(query, scan_id=scan_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="vulgpt_scan_{scan_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['CVE ID', 'Classification', 'Safe Version', 'Summary', 'GitHub References'])

        for record in results:
            writer.writerow([
                record['cve_id'],
                record['classification'],
                record['safe_versions'] or 'N/A',
                record['summary'] or 'N/A',
                ", ".join(record['github_references'])
            ])

        return response
