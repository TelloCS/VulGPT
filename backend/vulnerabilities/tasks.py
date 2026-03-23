import os
import asyncio
from celery import shared_task
from .services.neo4j import GraphService
from .utils.solver import compute_minimal_safe_version
from .utils.llm import classify_vulnerability
from .utils.network import fetch_all_github_patches, fetch_osv_data


def run_async(coro):
    """
    Helper to run async code within a synchronous Celery worker.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:

        # Fallback if a loop is already running in this thread
        return asyncio.get_event_loop().run_until_complete(coro)


@shared_task
def ingest_osv_data(ecosystem="PyPI", package_name="django", scan_id=None):
    """
    The main background worker process.
    It fetches data, analyzes it, and updates the graph database.
    """
    graph_service = GraphService()

    try:
        github_token = os.environ.get("GITHUB_TOKEN")
        osv_data = run_async(fetch_osv_data(ecosystem, package_name))
        vulns = osv_data.get("vulns", [])

        neo4j_batch = []

        for vuln in vulns:
            # Prefer standard CVE aliases, fallback to OSV ID
            cve_id = next((alias for alias in vuln.get("aliases", []) if alias.startswith("CVE-")), vuln.get("id"))

            # Extract valid GitHub commit URLs
            github_urls = [
                ref["url"] for ref in vuln.get("references", [])
                if "github.com" in ref["url"] and "commit" in ref["url"]
            ]

            # Fetch patch context and limit size for LLM context window
            patches = run_async(fetch_all_github_patches(github_urls, github_token))
            combined_patch_text = "\n".join(patches)[:1500]

            # Run Local LLM Classification
            llm_context = f"Summary: {vuln.get('summary')}\nCode Context:\n{combined_patch_text}"
            classification = classify_vulnerability(llm_context)

            # Parse affected ranges to find vulnerable version windows
            parsed_ranges = []
            for affected in vuln.get("affected", []):
                for pkg_range in affected.get("ranges", []):
                    events = pkg_range.get("events", [])
                    current_intro = "0.0.0"
                    for event in events:
                        if "introduced" in event:
                            current_intro = event["introduced"]
                        elif "fixed" in event:
                            parsed_ranges.append((current_intro, event["fixed"]))

            # Calculate minimal safe version path using OR-Tools math solver
            # (Note: In a production setting, 'available_versions_list' would be fetched dynamically from PyPI/NPM)
            safe_versions = compute_minimal_safe_version(
                current_version_str="1.0.0",
                available_versions_list=["1.0.0", "1.1.0", "1.2.0", "1.11.29", "2.0.0"],
                vulnerable_ranges=parsed_ranges
            )

            # Prepare the data dictionary for bulk Neo4j insertion
            neo4j_batch.append({
                "cve_id": cve_id,
                "summary": vuln.get("summary", "No summary provided"),
                "classification": classification,
                "github_urls": github_urls,
                "safe_versions": safe_versions,
                "scan_id": scan_id
            })

        # Insert vulnerabilities into the Graph Database
        if neo4j_batch:
            graph_service.insert_vulnerabilities(neo4j_batch)

    except Exception as e:
        print(f"Error processing {ecosystem}:{package_name} - {str(e)}")

    finally:
        if scan_id:
            graph_service.increment_scan_progress(scan_id)

    return f"Finished processing package: {package_name}"
