#!/usr/bin/env python3
"""
Populate Neo4j Knowledge Graph

This script loads knowledge base data into Neo4j for GraphRAG capabilities.
Creates nodes for supplements, symptoms, conditions, and their relationships.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


class Neo4jKnowledgeGraph:
    """Manages Neo4j knowledge graph population"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships (for fresh start)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared")

    def create_constraints(self):
        """Create uniqueness constraints"""
        with self.driver.session() as session:
            # Constraints for unique nodes
            constraints = [
                "CREATE CONSTRAINT supp_name IF NOT EXISTS FOR (s:Supplement) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT condition_name IF NOT EXISTS FOR (c:Condition) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT dosha_name IF NOT EXISTS FOR (d:Dosha) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT food_name IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint might already exist
                    pass

        print("✓ Constraints created")

    def load_supplements(self, supplements_data: Dict):
        """Load supplements into graph"""
        supplements = supplements_data.get("supplements", [])

        with self.driver.session() as session:
            for supp in supplements:
                # Create Supplement node
                session.run("""
                    MERGE (s:Supplement {name: $name})
                    SET s.category = $category,
                        s.description = $description,
                        s.mechanism = $mechanism,
                        s.dosage_typical = $dosage_typical,
                        s.dosage_range = $dosage_range
                """, {
                    "name": supp["name"],
                    "category": supp["category"],
                    "description": supp["description"],
                    "mechanism": supp["mechanism_of_action"],
                    "dosage_typical": supp["dosage"]["typical"],
                    "dosage_range": supp["dosage"]["range"]
                })

                # Create relationships for benefits
                for benefit in supp["benefits"]:
                    # Extract condition/symptom from benefit text
                    # For simplicity, use the whole benefit as a condition
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (c:Condition {name: $condition})
                        MERGE (s)-[:HELPS_WITH {strength: 'moderate'}]->(c)
                    """, {
                        "supp_name": supp["name"],
                        "condition": benefit
                    })

                # Create interactions
                for interaction in supp["drug_interactions"]:
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (d:Drug {name: $drug})
                        MERGE (s)-[:INTERACTS_WITH {type: 'negative'}]->(d)
                    """, {
                        "supp_name": supp["name"],
                        "drug": interaction
                    })

                # Link to doshas
                dosha_effect = supp["ayurvedic"]["dosha_effect"]
                for dosha, effect in dosha_effect.items():
                    if effect in ["balances", "pacifies"]:
                        session.run("""
                            MERGE (s:Supplement {name: $supp_name})
                            MERGE (d:Dosha {name: $dosha})
                            MERGE (s)-[:BALANCES {effect: $effect}]->(d)
                        """, {
                            "supp_name": supp["name"],
                            "dosha": dosha.capitalize(),
                            "effect": effect
                        })

        print(f"✓ Loaded {len(supplements)} supplements")

    def load_doshas(self, doshas_data: Dict):
        """Load Ayurvedic doshas into graph"""
        doshas = doshas_data.get("doshas", [])

        with self.driver.session() as session:
            for dosha in doshas:
                # Create Dosha node
                session.run("""
                    MERGE (d:Dosha {name: $name})
                    SET d.description = $description,
                        d.primary_element = $primary_element,
                        d.secondary_element = $secondary_element
                """, {
                    "name": dosha["name"],
                    "description": dosha["description"],
                    "primary_element": dosha["primary_element"],
                    "secondary_element": dosha["secondary_element"]
                })

                # Create relationships for imbalance symptoms
                for symptom in dosha["imbalance_signs"]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha_name})
                        MERGE (s:Symptom {name: $symptom})
                        MERGE (d)-[:CAUSES_WHEN_IMBALANCED]->(s)
                    """, {
                        "dosha_name": dosha["name"],
                        "symptom": symptom
                    })

                # Create relationships for balancing foods
                for food in dosha["balancing_foods"]["favor"]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha_name})
                        MERGE (f:Food {name: $food})
                        MERGE (f)-[:BALANCES {type: 'favor'}]->(d)
                    """, {
                        "dosha_name": dosha["name"],
                        "food": food
                    })

                for food in dosha["balancing_foods"]["avoid"]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha_name})
                        MERGE (f:Food {name: $food})
                        MERGE (f)-[:AGGRAVATES]->(d)
                    """, {
                        "dosha_name": dosha["name"],
                        "food": food
                    })

                # Link recommended herbs
                for herb in dosha["recommended_herbs"]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha_name})
                        MERGE (h:Supplement {name: $herb_name})
                        SET h.properties = $properties
                        MERGE (h)-[:BALANCES]->(d)
                    """, {
                        "dosha_name": dosha["name"],
                        "herb_name": herb["name"],
                        "properties": herb["properties"]
                    })

        print(f"✓ Loaded {len(doshas)} doshas")

    def create_symptom_chains(self):
        """Create common symptom -> condition -> intervention chains"""
        with self.driver.session() as session:
            # Stress pathway
            session.run("""
                MERGE (s:Symptom {name: 'High stress'})
                MERGE (c:Condition {name: 'Chronic stress'})
                MERGE (i1:Intervention {name: 'Meditation', type: 'lifestyle'})
                MERGE (i2:Intervention {name: 'Breathing exercises', type: 'practice'})
                MERGE (s)-[:INDICATES]->(c)
                MERGE (c)-[:TREATED_BY]->(i1)
                MERGE (c)-[:TREATED_BY]->(i2)
            """)

            # Sleep pathway
            session.run("""
                MERGE (s:Symptom {name: 'Poor sleep'})
                MERGE (c:Condition {name: 'Insomnia'})
                MERGE (i:Intervention {name: 'Sleep hygiene', type: 'lifestyle'})
                MERGE (s)-[:INDICATES]->(c)
                MERGE (c)-[:TREATED_BY]->(i)
            """)

            # Anxiety pathway
            session.run("""
                MERGE (s:Symptom {name: 'High beta waves'})
                MERGE (c:Condition {name: 'Anxiety'})
                MERGE (s)-[:INDICATES]->(c)
            """)

        print("✓ Created symptom chains")


def populate_graph():
    """Main function to populate Neo4j graph"""

    print("=" * 60)
    print("Populating Neo4j Knowledge Graph")
    print("=" * 60)

    # Get Neo4j credentials
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "wellness123")

    print(f"\nConnecting to Neo4j at {uri}...")

    try:
        graph = Neo4jKnowledgeGraph(uri, user, password)
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("Make sure Neo4j is running and credentials are correct.")
        return False

    # Clear existing data
    print("\n1. Clearing existing data...")
    graph.clear_database()

    # Create constraints
    print("\n2. Creating constraints...")
    graph.create_constraints()

    # Load knowledge base
    kb_path = PROJECT_ROOT / "knowledge_base"

    # Load supplements
    print("\n3. Loading supplements...")
    supplements_file = kb_path / "supplements" / "supplements_db.json"
    if supplements_file.exists():
        with open(supplements_file, 'r') as f:
            supplements_data = json.load(f)
        graph.load_supplements(supplements_data)
    else:
        print(f"Warning: {supplements_file} not found")

    # Load doshas
    print("\n4. Loading Ayurvedic doshas...")
    doshas_file = kb_path / "ayurveda" / "doshas.json"
    if doshas_file.exists():
        with open(doshas_file, 'r') as f:
            doshas_data = json.load(f)
        graph.load_doshas(doshas_data)
    else:
        print(f"Warning: {doshas_file} not found")

    # Create symptom chains
    print("\n5. Creating symptom chains...")
    graph.create_symptom_chains()

    # Get statistics
    with graph.driver.session() as session:
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
        """)

        print("\n" + "=" * 60)
        print("✓ Knowledge graph populated successfully!")
        print("\nNode Statistics:")
        for record in result:
            print(f"  {record['type']}: {record['count']}")

        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = rel_result.single()["count"]
        print(f"  Total Relationships: {rel_count}")
        print("=" * 60)

    graph.close()
    return True


if __name__ == "__main__":
    success = populate_graph()
    sys.exit(0 if success else 1)
