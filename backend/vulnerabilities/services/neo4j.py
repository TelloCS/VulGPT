import logging
from neo4j import GraphDatabase
from django.conf import settings

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
