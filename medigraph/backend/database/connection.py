"""
Neo4j Database Connection
"""
from neo4j import GraphDatabase
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file at module import
load_dotenv()


def _get_config():
    """Get config from environment - reads fresh each time."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password"),
    }


class Neo4jConnection:
    _instance: Optional["Neo4jConnection"] = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        if self._driver is None:
            config = _get_config()
            self._driver = GraphDatabase.driver(
                config["uri"],
                auth=(config["user"], config["password"])
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        try:
            config = _get_config()
            driver = GraphDatabase.driver(
                config["uri"],
                auth=(config["user"], config["password"])
            )
            driver.verify_connectivity()
            driver.close()
            return True
        except Exception:
            return False

    def execute_query(self, query: str, params: Optional[dict] = None):
        config = _get_config()
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["user"], config["password"])
        )
        with driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]


def get_db() -> Neo4jConnection:
    db = Neo4jConnection()
    db.connect()
    return db
