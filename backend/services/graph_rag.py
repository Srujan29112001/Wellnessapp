"""
GraphRAG Implementation with Neo4j Knowledge Graph
Enables complex reasoning over interconnected wellness knowledge
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, Neo4jError

from config.settings import settings

logger = logging.getLogger(__name__)


class WellnessKnowledgeGraph:
    """
    Knowledge Graph for Wellness Domain using Neo4j

    Graph Structure:
    - User nodes: Profile, preferences, goals
    - Symptom nodes: Stress, anxiety, fatigue, etc.
    - Intervention nodes: Supplements, foods, practices
    - Evidence nodes: Studies, traditional wisdom
    - Relationship: User -> HAS_SYMPTOM -> Symptom
    - Relationship: Symptom -> TREATED_BY -> Intervention
    - Relationship: Intervention -> SUPPORTED_BY -> Evidence
    """

    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD

    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def initialize_schema(self):
        """Create constraints and indexes for the graph"""
        async with self.driver.session() as session:
            # Constraints (ensure uniqueness)
            constraints = [
                "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT intervention_name IF NOT EXISTS FOR (i:Intervention) REQUIRE i.name IS UNIQUE",
                "CREATE CONSTRAINT dosha_name IF NOT EXISTS FOR (d:Dosha) REQUIRE d.name IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint creation error (may already exist): {e}")

            # Indexes for faster queries
            indexes = [
                "CREATE INDEX symptom_severity IF NOT EXISTS FOR (s:Symptom) ON (s.severity)",
                "CREATE INDEX intervention_type IF NOT EXISTS FOR (i:Intervention) ON (i.type)",
            ]

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.warning(f"Index creation error: {e}")

            logger.info("Schema initialized")

    async def load_wellness_knowledge(self):
        """Load wellness knowledge base into graph"""
        logger.info("Loading wellness knowledge into graph...")

        # Load Ayurveda knowledge
        await self._load_ayurveda_knowledge()

        # Load supplement knowledge
        await self._load_supplement_knowledge()

        logger.info("Wellness knowledge loaded successfully")

    async def _load_ayurveda_knowledge(self):
        """Load Ayurvedic doshas and relationships"""
        ayurveda_path = Path(settings.KB_DIR) / "ayurveda" / "doshas.json"

        if not ayurveda_path.exists():
            logger.warning(f"Ayurveda knowledge not found at {ayurveda_path}")
            return

        with open(ayurveda_path) as f:
            doshas_data = json.load(f)

        async with self.driver.session() as session:
            for dosha_name, dosha_info in doshas_data.items():
                # Create Dosha node
                await session.run(
                    """
                    MERGE (d:Dosha {name: $name})
                    SET d.characteristics = $characteristics,
                        d.updated_at = datetime()
                    """,
                    name=dosha_name,
                    characteristics=dosha_info.get("characteristics", [])
                )

                # Create Symptom nodes for imbalances
                for symptom in dosha_info.get("imbalance_signs", []):
                    await session.run(
                        """
                        MERGE (s:Symptom {name: $symptom})
                        SET s.category = 'dosha_imbalance',
                            s.updated_at = datetime()
                        WITH s
                        MATCH (d:Dosha {name: $dosha})
                        MERGE (d)-[r:CAUSES_WHEN_IMBALANCED]->(s)
                        """,
                        symptom=symptom.lower(),
                        dosha=dosha_name
                    )

                # Create Food intervention nodes
                for food in dosha_info.get("balancing_foods", []):
                    await session.run(
                        """
                        MERGE (i:Intervention:Food {name: $food})
                        SET i.type = 'diet',
                            i.category = 'balancing_food',
                            i.updated_at = datetime()
                        WITH i
                        MATCH (d:Dosha {name: $dosha})
                        MERGE (d)-[r:BALANCED_BY]->(i)
                        SET r.strength = 'high'
                        """,
                        food=food.lower(),
                        dosha=dosha_name
                    )

                # Create Herb intervention nodes
                for herb_info in dosha_info.get("herbs", []):
                    herb_name = herb_info.get("name", "")
                    if herb_name:
                        await session.run(
                            """
                            MERGE (i:Intervention:Herb {name: $name})
                            SET i.type = 'supplement',
                                i.category = 'ayurvedic_herb',
                                i.properties = $properties,
                                i.updated_at = datetime()
                            WITH i
                            MATCH (d:Dosha {name: $dosha})
                            MERGE (d)-[r:BALANCED_BY]->(i)
                            SET r.strength = 'high'
                            """,
                            name=herb_name.lower(),
                            properties=herb_info.get("properties", ""),
                            dosha=dosha_name
                        )

        logger.info("Ayurveda knowledge loaded into graph")

    async def _load_supplement_knowledge(self):
        """Load supplement database into graph"""
        supplements_path = Path(settings.KB_DIR) / "supplements" / "supplements_db.json"

        if not supplements_path.exists():
            logger.warning(f"Supplements knowledge not found at {supplements_path}")
            return

        with open(supplements_path) as f:
            supplements_data = json.load(f)

        async with self.driver.session() as session:
            for supp_name, supp_info in supplements_data.items():
                # Create Supplement intervention node
                await session.run(
                    """
                    MERGE (i:Intervention:Supplement {name: $name})
                    SET i.type = 'supplement',
                        i.mechanism = $mechanism,
                        i.dosage = $dosage,
                        i.contraindications = $contraindications,
                        i.updated_at = datetime()
                    """,
                    name=supp_name.lower(),
                    mechanism=supp_info.get("mechanism", ""),
                    dosage=json.dumps(supp_info.get("dosage", {})),
                    contraindications=supp_info.get("contraindications", [])
                )

                # Create relationships to symptoms/conditions it treats
                for benefit in supp_info.get("benefits", []):
                    # Extract condition from benefit (simplified)
                    condition = benefit.lower()
                    await session.run(
                        """
                        MERGE (s:Symptom {name: $symptom})
                        SET s.category = 'health_condition',
                            s.updated_at = datetime()
                        WITH s
                        MATCH (i:Intervention {name: $supplement})
                        MERGE (s)-[r:TREATED_BY]->(i)
                        SET r.evidence_level = 'moderate',
                            r.mechanism = $mechanism
                        """,
                        symptom=condition,
                        supplement=supp_name.lower(),
                        mechanism=supp_info.get("mechanism", "")
                    )

                # Create Evidence nodes for scientific studies
                for evidence in supp_info.get("evidence", []):
                    await session.run(
                        """
                        MERGE (e:Evidence {source: $evidence})
                        SET e.type = 'scientific_study',
                            e.updated_at = datetime()
                        WITH e
                        MATCH (i:Intervention {name: $supplement})
                        MERGE (i)-[r:SUPPORTED_BY]->(e)
                        """,
                        evidence=evidence,
                        supplement=supp_name.lower()
                    )

        logger.info("Supplement knowledge loaded into graph")

    async def create_user_node(self, user_id: str, user_data: Dict[str, Any]):
        """Create or update user node in graph"""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.name = $name,
                    u.age = $age,
                    u.dosha = $dosha,
                    u.goals = $goals,
                    u.dietary_restrictions = $restrictions,
                    u.updated_at = datetime()
                """,
                user_id=user_id,
                name=user_data.get("name", ""),
                age=user_data.get("age"),
                dosha=user_data.get("ayurvedic_dosha"),
                goals=user_data.get("health_goals", []),
                restrictions=user_data.get("dietary_restrictions", [])
            )

            # Link user to their dosha
            if user_data.get("ayurvedic_dosha"):
                await session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (d:Dosha {name: $dosha})
                    MERGE (u)-[r:HAS_DOSHA]->(d)
                    """,
                    user_id=user_id,
                    dosha=user_data["ayurvedic_dosha"]
                )

        logger.info(f"User node created/updated for {user_id}")

    async def add_user_symptom(
        self,
        user_id: str,
        symptom: str,
        severity: float,
        context: Optional[Dict] = None
    ):
        """Add a symptom relationship for user"""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (u:User {id: $user_id})
                MERGE (s:Symptom {name: $symptom})
                MERGE (u)-[r:HAS_SYMPTOM]->(s)
                SET r.severity = $severity,
                    r.reported_at = datetime(),
                    r.context = $context
                """,
                user_id=user_id,
                symptom=symptom.lower(),
                severity=severity,
                context=json.dumps(context or {})
            )

    async def find_interventions_for_symptoms(
        self,
        symptoms: List[str],
        user_dosha: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find relevant interventions for given symptoms using graph traversal

        This is the core of GraphRAG - we traverse the knowledge graph to find
        interventions connected to the symptoms, considering evidence and user dosha
        """
        async with self.driver.session() as session:
            # Complex graph query to find interventions
            query = """
            // Match symptoms
            UNWIND $symptoms AS symptom_name
            MATCH (s:Symptom)
            WHERE toLower(s.name) CONTAINS toLower(symptom_name)

            // Find interventions that treat this symptom
            OPTIONAL MATCH (s)-[treats:TREATED_BY]->(i:Intervention)

            // Find dosha-based interventions if dosha provided
            OPTIONAL MATCH (d:Dosha {name: $dosha})-[:BALANCED_BY]->(dosha_intervention:Intervention)
            WHERE $dosha IS NOT NULL

            // Collect all relevant interventions
            WITH collect(DISTINCT i) + collect(DISTINCT dosha_intervention) AS interventions
            UNWIND interventions AS intervention

            // Get evidence for each intervention
            OPTIONAL MATCH (intervention)-[:SUPPORTED_BY]->(e:Evidence)

            // Aggregate and score
            WITH intervention,
                 count(DISTINCT e) as evidence_count,
                 collect(DISTINCT e.source)[0..3] as evidence_samples
            WHERE intervention IS NOT NULL

            RETURN intervention.name as name,
                   intervention.type as type,
                   intervention.mechanism as mechanism,
                   intervention.dosage as dosage,
                   evidence_count,
                   evidence_samples
            ORDER BY evidence_count DESC
            LIMIT $limit
            """

            result = await session.run(
                query,
                symptoms=symptoms,
                dosha=user_dosha,
                limit=limit
            )

            interventions = []
            async for record in result:
                interventions.append({
                    "name": record["name"],
                    "type": record["type"],
                    "mechanism": record["mechanism"],
                    "dosage": record["dosage"],
                    "evidence_count": record["evidence_count"],
                    "evidence": record["evidence_samples"]
                })

            return interventions

    async def get_user_wellness_graph(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user's complete wellness graph (symptoms, interventions, dosha)
        for visualization and analysis
        """
        async with self.driver.session() as session:
            query = """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:HAS_SYMPTOM]->(s:Symptom)
            OPTIONAL MATCH (u)-[:HAS_DOSHA]->(d:Dosha)
            OPTIONAL MATCH (s)-[:TREATED_BY]->(i:Intervention)

            RETURN u,
                   collect(DISTINCT s) as symptoms,
                   collect(DISTINCT d) as doshas,
                   collect(DISTINCT i) as interventions
            """

            result = await session.run(query, user_id=user_id)
            record = await result.single()

            if not record:
                return {}

            return {
                "user": dict(record["u"]),
                "symptoms": [dict(s) for s in record["symptoms"] if s],
                "doshas": [dict(d) for d in record["doshas"] if d],
                "interventions": [dict(i) for i in record["interventions"] if i]
            }

    async def find_similar_users(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find users with similar symptoms/dosha for collaborative insights
        """
        async with self.driver.session() as session:
            query = """
            MATCH (u1:User {id: $user_id})-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(u2:User)
            WHERE u1 <> u2
            WITH u2, count(DISTINCT s) as common_symptoms
            ORDER BY common_symptoms DESC
            LIMIT $limit
            RETURN u2.id as user_id,
                   u2.dosha as dosha,
                   common_symptoms
            """

            result = await session.run(query, user_id=user_id, limit=limit)

            similar_users = []
            async for record in result:
                similar_users.append({
                    "user_id": record["user_id"],
                    "dosha": record["dosha"],
                    "common_symptoms": record["common_symptoms"]
                })

            return similar_users

    async def get_explanation_path(
        self,
        symptom: str,
        intervention: str
    ) -> List[Tuple[str, str, str]]:
        """
        Get the explanation path between a symptom and intervention
        (Why is this intervention recommended for this symptom?)
        """
        async with self.driver.session() as session:
            query = """
            MATCH path = shortestPath(
                (s:Symptom {name: $symptom})-[*..3]-(i:Intervention {name: $intervention})
            )
            RETURN [n in nodes(path) | {type: labels(n)[0], name: n.name}] as nodes,
                   [r in relationships(path) | type(r)] as relationships
            """

            result = await session.run(
                query,
                symptom=symptom.lower(),
                intervention=intervention.lower()
            )

            record = await result.single()
            if not record:
                return []

            # Build explanation path
            nodes = record["nodes"]
            relationships = record["relationships"]

            path = []
            for i in range(len(relationships)):
                path.append((
                    nodes[i]["name"],
                    relationships[i],
                    nodes[i + 1]["name"]
                ))

            return path


# Singleton instance
_graph_instance: Optional[WellnessKnowledgeGraph] = None


async def get_knowledge_graph() -> WellnessKnowledgeGraph:
    """Get or create knowledge graph singleton"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = WellnessKnowledgeGraph()
        await _graph_instance.connect()
        await _graph_instance.initialize_schema()
        await _graph_instance.load_wellness_knowledge()
    return _graph_instance
