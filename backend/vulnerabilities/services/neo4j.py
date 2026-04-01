import logging
from neo4j import GraphDatabase
from django.conf import settings
from typing import Optional

logger = logging.getLogger(__name__)

_driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)


class GraphService:
    def __init__(self):
        self.driver = _driver

    def insert_vulnerabilities(self, neo4j_batch: list):
        cypher_query = """
            UNWIND $batch AS data
            MERGE (v:Vulnerability {cve_id: data.cve_id})
            SET v.summary = data.summary,
                v.safe_versions = data.safe_versions,
                v.classification = data.classification
            WITH v, data
                UNWIND data.github_urls AS gh_url
                MERGE (g:GitHubNode {url: gh_url})
                MERGE (v)-[:HAS_REFERENCE]->(g)
            WITH v, data
                WHERE data.scan_id IS NOT NULL
                MERGE (s:ScanReport {uuid: data.scan_id})
                MERGE (v)-[:FOUND_IN_SCAN]->(s)
        """
        with self.driver.session() as session:
            session.run(cypher_query, batch=neo4j_batch)

    def increment_scan_progress(self, scan_id):
        increment_query = """
            MATCH (s:ScanReport {uuid: $scan_id})
            SET s.processed_packages = COALESCE(s.processed_packages, 0) + 1
            WITH s
            WHERE s.processed_packages >= s.total_packages
            SET s.status = 'COMPLETED',
                s.completed_at = timestamp()
        """
        with self.driver.session() as session:
            session.run(increment_query, scan_id=scan_id)

    def get_vulnerabilities(self, search: Optional[str] = None, classification: Optional[str] = None):
        where_clauses = []
        params = {}

        if search:
            where_clauses.append(
                """(toLower(v.cve_id) CONTAINS toLower($search) OR
                    toLower(v.summary) CONTAINS toLower($search))"""
            )
            params["search"] = search

        if classification and classification != "All":
            where_clauses.append("v.classification = $classification")
            params["classification"] = classification

        where_stmt = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            MATCH (v:Vulnerability)
            {where_stmt}
            OPTIONAL MATCH (v)-[:HAS_REFERENCE]->(g:GitHubNode)
            RETURN v.cve_id AS cve_id, v.summary AS summary,
                COALESCE(v.classification, 'Pending Analysis') AS classification,
                v.safe_versions AS safe_versions, collect(g.url) AS github_references
            ORDER BY cve_id DESC
        """
        with self.driver.session() as session:
            return [record.data() for record in session.run(query, **params)]

    def get_scan_stats(self, scan_id: str):
        query = """
        MATCH (s:ScanReport {uuid: $scan_id})
        CALL {
            WITH s
            OPTIONAL MATCH (s)<-[:FOUND_IN_SCAN]-(v:Vulnerability)
            WITH COALESCE(v.classification, 'Pending Analysis') AS cat, count(v) AS catCount
            WHERE catCount > 0
            RETURN collect({label: cat, count: catCount}) AS categories, sum(catCount) AS total_found
        }
        RETURN {
            status: s.status,
            total_packages: s.total_packages,
            processed_packages: s.processed_packages,
            created_at: s.created_at,
            completed_at: s.completed_at,
            breakdown: categories,
            total_vulnerabilities: total_found
        } AS stats
        """
        with self.driver.session() as session:
            result = session.run(query, scan_id=scan_id)
            record = result.single()
            return record["stats"] if record else None

    def get_scan_results(self, scan_id: str):
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
        with self.driver.session() as session:
            results = session.run(query, scan_id=scan_id)
            return [record.data() for record in results]

    def create_scan_report(self, scan_id: str, total_packages: int):
        query = """
            MERGE (s:ScanReport {uuid: $scan_id})
            SET s.status = 'PROCESSING',
                s.total_packages = $total,
                s.processed_packages = 0,
                s.created_at = timestamp()
        """
        with self.driver.session() as session:
            session.run(query, scan_id=scan_id, total=total_packages)
