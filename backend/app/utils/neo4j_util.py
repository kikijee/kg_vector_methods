from ..config import settings
from neo4j import GraphDatabase
from typing import Dict, Any, List

import logging
import traceback

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


NEO4J_URI = settings.neo4j_uri_1
NEO4J_USER = settings.neo4j_user_1
NEO4J_PASSWORD = settings.neo4j_password_1


class Neo4jGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def insert_data(self, data: List[Dict[str, Any]]):
        with self.driver.session() as session:
            session.execute_write(self._insert_entities, data)
            session.execute_write(self._insert_relationships, data)

    @staticmethod
    def _insert_entities(tx, data: List[Dict[str, Any]]):
        for record in data:
            for entity in record["entities"]:
                query = """
                MERGE (e: {label} {id: $id})
                SET e.summary = $summary, e.text = $text
                """.replace("{label}", entity["label"])
                
                tx.run(query, id=entity["id"], summary=entity.get("summary"), text=entity.get("text"))

    @staticmethod
    def _insert_relationships(tx, data: List[Dict[str, Any]]):
        for record in data:
            for rel in record["relationships"]:
                head, relationship, tail = rel.split("|")
                query = f"""
                MATCH (h {{id: $head}}), (t {{id: $tail}})
                MERGE (h)-[r:{relationship}]->(t)
                """
                tx.run(query, head=head, tail=tail)

# Function to insert the generated results into Neo4j
def save_to_neo4j(results: List[Dict[str, Any]]):
    graph = Neo4jGraph()
    try:
        graph.insert_data(results)
    except Exception as e:
        logger.error(f"Error in save_to_neo4j(): {traceback.format_exc()}")
        raise RuntimeError("Error inserting data into neo4j") from e
    finally:
        graph.close()