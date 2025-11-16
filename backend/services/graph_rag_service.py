"""
GraphRAG Service for Knowledge Graph Management

Uses Neo4j to build and query a knowledge graph for wellness information
Connects user symptoms, conditions, supplements, foods, and interventions
"""
from typing import List, Dict, Any, Optional
import logging
import json
import os

try:
    from neo4j import GraphDatabase, AsyncGraphDatabase
except ImportError:
    GraphDatabase = None
    AsyncGraphDatabase = None

logger = logging.getLogger(__name__)


class GraphRAGService:
    """Service for managing wellness knowledge graph in Neo4j"""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection"""
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")

        if GraphDatabase is None:
            logger.warning("Neo4j driver not available. GraphRAG features disabled.")
            self.driver = None
            return

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    async def initialize_knowledge_graph(self):
        """
        Initialize the knowledge graph with wellness domain knowledge

        Creates nodes and relationships for:
        - Symptoms (stress, anxiety, fatigue, etc.)
        - Conditions (poor sleep, high stress, etc.)
        - Supplements (ashwagandha, magnesium, etc.)
        - Foods (leafy greens, nuts, fish, etc.)
        - Interventions (meditation, exercise, etc.)
        - Research (PubMed citations, etc.)
        """
        if not self.driver:
            logger.warning("Neo4j driver not available. Skipping graph initialization.")
            return

        try:
            with self.driver.session() as session:
                # Clear existing data (for development)
                # session.run("MATCH (n) DETACH DELETE n")

                # Create constraints and indexes
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (sup:Supplement) REQUIRE sup.name IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS FOR (s:Symptom) ON (s.category)
                """)

                # Load knowledge from files
                await self._load_symptoms(session)
                await self._load_supplements(session)
                await self._load_foods(session)
                await self._load_interventions(session)
                await self._create_relationships(session)

                logger.info("Knowledge graph initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing knowledge graph: {e}")
            raise

    async def _load_symptoms(self, session):
        """Load symptom nodes"""
        symptoms = [
            {"name": "Stress", "category": "mental", "severity_scale": "0-1"},
            {"name": "Anxiety", "category": "mental", "severity_scale": "0-1"},
            {"name": "Poor Sleep", "category": "physical", "severity_scale": "hours"},
            {"name": "Fatigue", "category": "physical", "severity_scale": "0-1"},
            {"name": "Low Focus", "category": "cognitive", "severity_scale": "0-1"},
            {"name": "Brain Fog", "category": "cognitive", "severity_scale": "0-1"},
            {"name": "Low Energy", "category": "physical", "severity_scale": "0-1"},
            {"name": "Irritability", "category": "mental", "severity_scale": "0-1"},
        ]

        for symptom in symptoms:
            session.run("""
                MERGE (s:Symptom {name: $name})
                SET s.category = $category, s.severity_scale = $severity_scale
            """, **symptom)

    async def _load_supplements(self, session):
        """Load supplement nodes from knowledge base"""
        kb_path = "/home/user/Wellnessapp/knowledge_base/supplements/supplements_db.json"

        supplements_data = {}
        if os.path.exists(kb_path):
            with open(kb_path, 'r') as f:
                supplements_data = json.load(f)

        for supp_id, supp in supplements_data.items():
            session.run("""
                MERGE (sup:Supplement {name: $name})
                SET sup.category = $category,
                    sup.dosage = $dosage,
                    sup.safety_rating = $safety_rating,
                    sup.description = $description
            """,
                name=supp.get("name", ""),
                category=supp.get("category", ""),
                dosage=supp.get("typical_dosage", ""),
                safety_rating=supp.get("safety_rating", ""),
                description=supp.get("description", "")
            )

    async def _load_foods(self, session):
        """Load food nodes"""
        foods = [
            {"name": "Leafy Greens", "category": "vegetable", "nutrients": "magnesium,iron,vitamins"},
            {"name": "Salmon", "category": "fish", "nutrients": "omega-3,protein,vitamin-d"},
            {"name": "Nuts", "category": "protein", "nutrients": "magnesium,healthy-fats,protein"},
            {"name": "Berries", "category": "fruit", "nutrients": "antioxidants,vitamin-c,fiber"},
            {"name": "Whole Grains", "category": "grain", "nutrients": "fiber,b-vitamins,complex-carbs"},
            {"name": "Dark Chocolate", "category": "treat", "nutrients": "magnesium,antioxidants"},
            {"name": "Green Tea", "category": "beverage", "nutrients": "l-theanine,antioxidants"},
        ]

        for food in foods:
            session.run("""
                MERGE (f:Food {name: $name})
                SET f.category = $category, f.nutrients = $nutrients
            """, **food)

    async def _load_interventions(self, session):
        """Load intervention nodes"""
        interventions = [
            {"name": "Meditation", "type": "practice", "duration": "10-20 minutes", "difficulty": "easy"},
            {"name": "Breathing Exercises", "type": "practice", "duration": "5-10 minutes", "difficulty": "easy"},
            {"name": "Yoga", "type": "exercise", "duration": "20-60 minutes", "difficulty": "medium"},
            {"name": "Aerobic Exercise", "type": "exercise", "duration": "30 minutes", "difficulty": "medium"},
            {"name": "Cold Shower", "type": "practice", "duration": "2-5 minutes", "difficulty": "medium"},
            {"name": "Journaling", "type": "practice", "duration": "10-15 minutes", "difficulty": "easy"},
            {"name": "Nature Walk", "type": "activity", "duration": "20-30 minutes", "difficulty": "easy"},
        ]

        for intervention in interventions:
            session.run("""
                MERGE (i:Intervention {name: $name})
                SET i.type = $type, i.duration = $duration, i.difficulty = $difficulty
            """, **intervention)

    async def _create_relationships(self, session):
        """Create relationships between nodes"""

        # Supplements -> Helps -> Symptoms
        relationships = [
            # Ashwagandha
            ("Supplement", "Ashwagandha", "HELPS_WITH", "Symptom", "Stress", {"evidence": "RCT", "confidence": 0.9}),
            ("Supplement", "Ashwagandha", "HELPS_WITH", "Symptom", "Anxiety", {"evidence": "Meta-analysis", "confidence": 0.85}),
            ("Supplement", "Ashwagandha", "HELPS_WITH", "Symptom", "Poor Sleep", {"evidence": "Study", "confidence": 0.75}),

            # Magnesium
            ("Supplement", "Magnesium", "HELPS_WITH", "Symptom", "Stress", {"evidence": "Study", "confidence": 0.75}),
            ("Supplement", "Magnesium", "HELPS_WITH", "Symptom", "Poor Sleep", {"evidence": "RCT", "confidence": 0.8}),
            ("Supplement", "Magnesium", "HELPS_WITH", "Symptom", "Anxiety", {"evidence": "Study", "confidence": 0.7}),

            # L-Theanine
            ("Supplement", "L-Theanine", "HELPS_WITH", "Symptom", "Stress", {"evidence": "RCT", "confidence": 0.8}),
            ("Supplement", "L-Theanine", "HELPS_WITH", "Symptom", "Low Focus", {"evidence": "Study", "confidence": 0.75}),

            # Omega-3
            ("Supplement", "Omega-3 (EPA/DHA)", "HELPS_WITH", "Symptom", "Brain Fog", {"evidence": "Meta-analysis", "confidence": 0.75}),
            ("Supplement", "Omega-3 (EPA/DHA)", "HELPS_WITH", "Symptom", "Low Focus", {"evidence": "Study", "confidence": 0.7}),

            # Foods -> Contains -> Supplement/Nutrient
            ("Food", "Salmon", "CONTAINS", "Supplement", "Omega-3 (EPA/DHA)", {"amount": "high"}),
            ("Food", "Leafy Greens", "CONTAINS", "Supplement", "Magnesium", {"amount": "high"}),
            ("Food", "Nuts", "CONTAINS", "Supplement", "Magnesium", {"amount": "high"}),
            ("Food", "Green Tea", "CONTAINS", "Supplement", "L-Theanine", {"amount": "moderate"}),

            # Interventions -> Helps -> Symptoms
            ("Intervention", "Meditation", "HELPS_WITH", "Symptom", "Stress", {"evidence": "Meta-analysis", "confidence": 0.9}),
            ("Intervention", "Meditation", "HELPS_WITH", "Symptom", "Anxiety", {"evidence": "RCT", "confidence": 0.85}),
            ("Intervention", "Meditation", "HELPS_WITH", "Symptom", "Low Focus", {"evidence": "Study", "confidence": 0.8}),

            ("Intervention", "Breathing Exercises", "HELPS_WITH", "Symptom", "Stress", {"evidence": "Study", "confidence": 0.85}),
            ("Intervention", "Breathing Exercises", "HELPS_WITH", "Symptom", "Anxiety", {"evidence": "Study", "confidence": 0.8}),

            ("Intervention", "Aerobic Exercise", "HELPS_WITH", "Symptom", "Fatigue", {"evidence": "Meta-analysis", "confidence": 0.85}),
            ("Intervention", "Aerobic Exercise", "HELPS_WITH", "Symptom", "Poor Sleep", {"evidence": "RCT", "confidence": 0.8}),
            ("Intervention", "Aerobic Exercise", "HELPS_WITH", "Symptom", "Low Energy", {"evidence": "Study", "confidence": 0.9}),

            ("Intervention", "Yoga", "HELPS_WITH", "Symptom", "Stress", {"evidence": "Meta-analysis", "confidence": 0.85}),
            ("Intervention", "Yoga", "HELPS_WITH", "Symptom", "Poor Sleep", {"evidence": "RCT", "confidence": 0.75}),
        ]

        for start_label, start_name, rel_type, end_label, end_name, properties in relationships:
            session.run(f"""
                MATCH (start:{start_label} {{name: $start_name}})
                MATCH (end:{end_label} {{name: $end_name}})
                MERGE (start)-[r:{rel_type}]->(end)
                SET r += $properties
            """, start_name=start_name, end_name=end_name, properties=properties)

    def get_recommendations_for_symptoms(
        self,
        symptoms: List[str],
        recommendation_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations based on symptoms using graph traversal

        Args:
            symptoms: List of symptom names (e.g., ["Stress", "Poor Sleep"])
            recommendation_types: Types to include ["supplements", "foods", "interventions"]

        Returns:
            Dictionary with recommended supplements, foods, and interventions
        """
        if not self.driver:
            logger.warning("Neo4j driver not available. Returning empty recommendations.")
            return {"supplements": [], "foods": [], "interventions": []}

        if recommendation_types is None:
            recommendation_types = ["supplements", "foods", "interventions"]

        recommendations = {
            "supplements": [],
            "foods": [],
            "interventions": []
        }

        try:
            with self.driver.session() as session:
                # Find supplements that help with the symptoms
                if "supplements" in recommendation_types:
                    result = session.run("""
                        MATCH (s:Symptom)-[r:HELPS_WITH]-(sup:Supplement)
                        WHERE s.name IN $symptoms
                        RETURN DISTINCT sup.name AS name, sup.dosage AS dosage,
                               AVG(r.confidence) AS confidence
                        ORDER BY confidence DESC
                        LIMIT 5
                    """, symptoms=symptoms)

                    for record in result:
                        recommendations["supplements"].append({
                            "name": record["name"],
                            "dosage": record["dosage"],
                            "confidence": record["confidence"]
                        })

                # Find interventions
                if "interventions" in recommendation_types:
                    result = session.run("""
                        MATCH (s:Symptom)<-[r:HELPS_WITH]-(i:Intervention)
                        WHERE s.name IN $symptoms
                        RETURN DISTINCT i.name AS name, i.type AS type,
                               i.duration AS duration, i.difficulty AS difficulty,
                               AVG(r.confidence) AS confidence
                        ORDER BY confidence DESC
                        LIMIT 5
                    """, symptoms=symptoms)

                    for record in result:
                        recommendations["interventions"].append({
                            "name": record["name"],
                            "type": record["type"],
                            "duration": record["duration"],
                            "difficulty": record["difficulty"],
                            "confidence": record["confidence"]
                        })

                # Find foods (through supplements they contain)
                if "foods" in recommendation_types:
                    result = session.run("""
                        MATCH (s:Symptom)<-[:HELPS_WITH]-(sup:Supplement)<-[:CONTAINS]-(f:Food)
                        WHERE s.name IN $symptoms
                        RETURN DISTINCT f.name AS name, f.category AS category,
                               f.nutrients AS nutrients, COUNT(DISTINCT sup) AS num_beneficial_nutrients
                        ORDER BY num_beneficial_nutrients DESC
                        LIMIT 5
                    """, symptoms=symptoms)

                    for record in result:
                        recommendations["foods"].append({
                            "name": record["name"],
                            "category": record["category"],
                            "nutrients": record["nutrients"],
                            "beneficial_nutrients": record["num_beneficial_nutrients"]
                        })

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations from graph: {e}")
            return {"supplements": [], "foods": [], "interventions": []}

    def find_connections(self, entity1: str, entity2: str) -> List[Dict[str, Any]]:
        """
        Find all paths connecting two entities in the graph

        Useful for explaining WHY a recommendation is made
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (n1)-[*1..3]-(n2)
                    WHERE (n1.name = $entity1 OR n1.name = $entity2)
                      AND (n2.name = $entity1 OR n2.name = $entity2)
                      AND n1 <> n2
                    RETURN [node IN nodes(path) | node.name] AS nodes,
                           [rel IN relationships(path) | type(rel)] AS relationships
                    LIMIT 5
                """, entity1=entity1, entity2=entity2)

                paths = []
                for record in result:
                    paths.append({
                        "nodes": record["nodes"],
                        "relationships": record["relationships"]
                    })

                return paths

        except Exception as e:
            logger.error(f"Error finding connections: {e}")
            return []


# Global instance
graph_rag = GraphRAGService()
