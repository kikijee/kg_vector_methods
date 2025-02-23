# import { neo4j_driver } from "../models";

# export async def runQuery(query: string, params = {}) {
#     const session = neo4j_driver.session();
#     try {
#         const result = await session.run(query, params);
#         return result.records;
#     } finally {
#         await session.close();
#     }
# }

from ..config import settings
from neo4j import GraphDatabase
from typing import Dict, Any, List


NEO4J_URI = settings.neo4j_uri
NEO4J_USER = settings.neo4j_user
NEO4J_PASSWORD = settings.neo4j_password


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
        print("Data successfully inserted into Neo4j.")
    except Exception as e:
        print(f"Error inserting into Neo4j: {e}")
    finally:
        graph.close()