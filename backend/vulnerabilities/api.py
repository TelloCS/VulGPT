import uuid
import csv
from django.http import HttpResponse
from ninja import NinjaAPI, File
from ninja.files import UploadedFile
from ninja.pagination import paginate
from typing import List, Optional
from vulnerabilities.schemas import (
    VulnerabilitySchema,
    UploadResponseSchema,
    ErrorSchema
)
from vulnerabilities.utils.parse import parse_manifest
from vulnerabilities.tasks import ingest_osv_data
from vulnerabilities.services.neo4j import GraphService

api = NinjaAPI()
db = GraphService()


@api.get("/vulnerabilities/", response=List[VulnerabilitySchema])
@paginate
def get_vulnerabilities(request, search: Optional[str] = None, classification: Optional[str] = None):
    results = db.get_vulnerabilities(search=search, classification=classification)
    return results


@api.post("/upload-manifest/", response={200: UploadResponseSchema, 400: ErrorSchema})
def upload_manifest(request, file: UploadedFile = File(...)):
    if file.size > 1024 * 1024:
        return 400, {"error": "File exceeds 1MB limit."}

    try:
        filename = file.name.lower()
        content = file.read().decode('utf-8')
        queued_packages = parse_manifest(filename=filename, content=content)

        if queued_packages is None:
            return 400, {"error": "Unsupported file."}
        if not queued_packages:
            return 400, {"error": "No dependencies found."}

        scan_id = str(uuid.uuid4())
        db.create_scan_report(scan_id, len(queued_packages))

        for ecosystem, package in queued_packages:
            ingest_osv_data.delay(ecosystem=ecosystem, package_name=package, scan_id=scan_id)

        return 200, {
            "message": f"Successfully queued {len(queued_packages)} packages for scanning.",
            "scan_id": scan_id
        }

    except Exception as e:
        return 400, {"error": f"Failed to parse file: {str(e)}"}


@api.get("/scans/{scan_id}/", response=List[VulnerabilitySchema])
@paginate
def get_scan_results(request, scan_id: str):
    results = db.get_scan_results(scan_id=scan_id)

    if not results:
        return api.create_response(request, {"error": "Scan results not found"}, status=404)

    return results


@api.get("/scans/{scan_id}/stats/", response=dict)
def get_scan_stats(request, scan_id: str):
    stats = db.get_scan_stats(scan_id)

    if not stats:
        return api.create_response(request, {"error": "Scan not found"}, status=404)

    return stats


@api.get("/scans/{scan_id}/export/")
def export_scan_csv(request, scan_id: str):
    results = db.get_scan_results(scan_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'inline; filename="vulgpt_scan_{scan_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['CVE ID', 'Classification', 'Safe Version', 'Summary', 'GitHub References'])

    for record in results:
        writer.writerow([
            record['cve_id'],
            record['classification'],
            record['safe_versions'],
            record['summary'],
            ", ".join(record['github_references'])
        ])

    return response
