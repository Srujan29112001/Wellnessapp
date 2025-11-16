"""
GraphRAG - Knowledge Graph for Wellness Domain

Uses Neo4j to create and query a knowledge graph connecting:
- Supplements → Benefits → Conditions
- Symptoms → Causes → Interventions
- Doshas → Imbalances → Foods/Herbs
- EEG states → Recommendations → Mechanisms
"""
from neo4j import GraphDatabase
from typing import List, Dict, Optional, Tuple
import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GraphRAGService:
    """
    Knowledge Graph for complex wellness reasoning

    Benefits over flat RAG:
    - Multi-hop reasoning (A causes B causes C)
    - Discover non-obvious connections
    - Contraindication checking (drug interactions)
    - Personalized traversal (filter by user's dosha/conditions)
    """

    def __init__(
        self,
        uri: str = None,
        user: str = "neo4j",
        password: str = None
    ):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
        """
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        password = password or os.getenv("NEO4J_PASSWORD", "wellness_graph")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.warning(f"Could not connect to Neo4j: {e}. GraphRAG will not be available.")
            self.driver = None

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def init_schema(self):
        """Initialize graph schema and constraints"""
        if not self.driver:
            return

        with self.driver.session() as session:
            # Create constraints (ensures uniqueness)
            constraints = [
                "CREATE CONSTRAINT supplement_name IF NOT EXISTS FOR (s:Supplement) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT condition_name IF NOT EXISTS FOR (c:Condition) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT dosha_name IF NOT EXISTS FOR (d:Dosha) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT food_name IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE",
                "CREATE CONSTRAINT herb_name IF NOT EXISTS FOR (h:Herb) REQUIRE h.name IS UNIQUE",
                "CREATE CONSTRAINT mechanism_name IF NOT EXISTS FOR (m:Mechanism) REQUIRE m.name IS UNIQUE"
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists or error: {e}")

    def load_knowledge_graph(self):
        """Load knowledge base into graph"""
        if not self.driver:
            logger.warning("Neo4j not connected, skipping graph load")
            return

        logger.info("Loading knowledge graph...")

        self.init_schema()

        # Load supplements
        self._load_supplements_graph()

        # Load Ayurveda doshas
        self._load_doshas_graph()

        # Load symptom→condition→intervention chains
        self._load_symptom_chains()

        # Load interactions
        self._load_interactions()

        logger.info("Knowledge graph loaded")

    def _load_supplements_graph(self):
        """Load supplement knowledge into graph"""
        supp_path = Path("knowledge_base/supplements/supplements_db.json")
        if not supp_path.exists():
            logger.warning(f"Supplement file not found: {supp_path}")
            return

        with open(supp_path) as f:
            data = json.load(f)

        supplements = data.get("supplements", [])

        with self.driver.session() as session:
            for supp in supplements:
                # Create supplement node
                session.run("""
                    MERGE (s:Supplement {name: $name})
                    SET s.description = $description,
                        s.category = $category
                """, name=supp["name"],
                    description=supp.get("description", ""),
                    category=supp.get("category", "general"))

                # Create benefit nodes and relationships
                for benefit in supp.get("benefits", [])[:5]:
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (b:Benefit {name: $benefit})
                        MERGE (s)-[:PROVIDES]->(b)
                    """, supp_name=supp["name"], benefit=benefit)

                # Create mechanism nodes
                for mechanism in supp.get("mechanisms", [])[:3]:
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (m:Mechanism {name: $mechanism})
                        MERGE (s)-[:WORKS_VIA]->(m)
                    """, supp_name=supp["name"], mechanism=mechanism)

                # Create contraindication relationships
                for contra in supp.get("contraindications", [])[:5]:
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (c:Condition {name: $contra})
                        MERGE (s)-[:CONTRAINDICATED_FOR]->(c)
                    """, supp_name=supp["name"], contra=contra)

                # Create interaction warnings
                for interaction in supp.get("interactions", [])[:5]:
                    session.run("""
                        MERGE (s:Supplement {name: $supp_name})
                        MERGE (i:Substance {name: $interaction})
                        MERGE (s)-[:INTERACTS_WITH]->(i)
                    """, supp_name=supp["name"], interaction=interaction)

        logger.info(f"Loaded {len(supplements)} supplements into graph")

    def _load_doshas_graph(self):
        """Load Ayurvedic dosha knowledge"""
        dosha_path = Path("knowledge_base/ayurveda/doshas.json")
        if not dosha_path.exists():
            return

        with open(dosha_path) as f:
            doshas_data = json.load(f)

        with self.driver.session() as session:
            for dosha_name, dosha_data in doshas_data.items():
                # Create dosha node
                session.run("""
                    MERGE (d:Dosha {name: $name})
                    SET d.description = $description,
                        d.element = $element
                """, name=dosha_name,
                    description=dosha_data.get("description", ""),
                    element=dosha_data.get("element", ""))

                # Imbalance symptoms
                for symptom in dosha_data.get("imbalance_signs", [])[:10]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha})
                        MERGE (s:Symptom {name: $symptom})
                        MERGE (d)-[:IMBALANCE_CAUSES]->(s)
                    """, dosha=dosha_name, symptom=symptom)

                # Balancing foods
                for food in dosha_data.get("balancing_foods", [])[:15]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha})
                        MERGE (f:Food {name: $food})
                        MERGE (f)-[:BALANCES]->(d)
                    """, dosha=dosha_name, food=food)

                # Balancing herbs
                for herb in dosha_data.get("herbs", [])[:10]:
                    session.run("""
                        MERGE (d:Dosha {name: $dosha})
                        MERGE (h:Herb {name: $herb_name})
                        SET h.properties = $properties
                        MERGE (h)-[:BALANCES]->(d)
                    """, dosha=dosha_name,
                        herb_name=herb.get("name", ""),
                        properties=herb.get("properties", ""))

        logger.info(f"Loaded {len(doshas_data)} doshas into graph")

    def _load_symptom_chains(self):
        """Load symptom → condition → intervention chains"""
        # Common wellness symptom chains
        chains = [
            {
                "symptom": "Poor sleep",
                "causes": ["High cortisol", "Magnesium deficiency", "Circadian disruption"],
                "interventions": ["Magnesium supplementation", "Sleep hygiene", "Morning sunlight"]
            },
            {
                "symptom": "High stress",
                "causes": ["Elevated cortisol", "Sympathetic overdrive", "Vata imbalance"],
                "interventions": ["Ashwagandha", "Breathing exercises", "Meditation"]
            },
            {
                "symptom": "Brain fog",
                "causes": ["Poor sleep", "Inflammation", "Nutrient deficiency"],
                "interventions": ["Omega-3", "B vitamins", "Exercise"]
            },
            {
                "symptom": "Low energy",
                "causes": ["Iron deficiency", "B12 deficiency", "Thyroid dysfunction", "Poor sleep"],
                "interventions": ["Iron supplementation", "B-complex", "Thyroid check", "Sleep optimization"]
            },
            {
                "symptom": "Anxiety",
                "causes": ["GABA deficiency", "High cortisol", "Vata imbalance", "Magnesium deficiency"],
                "interventions": ["L-theanine", "Magnesium", "Ashwagandha", "Meditation"]
            }
        ]

        with self.driver.session() as session:
            for chain in chains:
                symptom = chain["symptom"]

                # Create symptom node
                session.run("MERGE (s:Symptom {name: $name})", name=symptom)

                # Create causes
                for cause in chain["causes"]:
                    session.run("""
                        MERGE (s:Symptom {name: $symptom})
                        MERGE (c:Cause {name: $cause})
                        MERGE (c)-[:LEADS_TO]->(s)
                    """, symptom=symptom, cause=cause)

                # Create interventions
                for intervention in chain["interventions"]:
                    session.run("""
                        MERGE (s:Symptom {name: $symptom})
                        MERGE (i:Intervention {name: $intervention})
                        MERGE (i)-[:ADDRESSES]->(s)
                    """, symptom=symptom, intervention=intervention)

        logger.info(f"Loaded {len(chains)} symptom chains")

    def _load_interactions(self):
        """Load supplement interaction matrix"""
        interactions = [
            ("Ashwagandha", "Sedatives", "POTENTIATES", "May increase sedation"),
            ("St. John's Wort", "Antidepressants", "CONTRAINDICATES", "Serotonin syndrome risk"),
            ("Fish oil", "Blood thinners", "CAUTION", "May increase bleeding risk"),
            ("Magnesium", "Calcium", "COMPETES", "Take separately for absorption"),
            ("Iron", "Calcium", "COMPETES", "Take separately"),
            ("Vitamin D", "Magnesium", "SYNERGIZES", "Magnesium aids vitamin D activation"),
            ("Curcumin", "Black pepper", "ENHANCES", "Piperine increases absorption 2000%")
        ]

        with self.driver.session() as session:
            for item1, item2, rel_type, note in interactions:
                session.run(f"""
                    MERGE (a:Substance {{name: $item1}})
                    MERGE (b:Substance {{name: $item2}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    SET r.note = $note
                """, item1=item1, item2=item2, note=note)

    def find_supplement_for_symptom(
        self,
        symptom: str,
        user_conditions: List[str] = None,
        user_supplements: List[str] = None
    ) -> List[Dict]:
        """
        Find supplements that address a symptom

        Checks contraindications and interactions

        Args:
            symptom: User's symptom
            user_conditions: User's medical conditions
            user_supplements: Current supplements user is taking

        Returns:
            List of recommended supplements with reasoning
        """
        if not self.driver:
            return []

        user_conditions = user_conditions or []
        user_supplements = user_supplements or []

        with self.driver.session() as session:
            # Find supplements that address the symptom
            # Multi-hop: Intervention→addresses→Symptom, Supplement→provides→Benefit
            result = session.run("""
                MATCH (i:Intervention)-[:ADDRESSES]->(s:Symptom {name: $symptom})
                OPTIONAL MATCH (supp:Supplement)-[:PROVIDES]->(b:Benefit)
                WHERE toLower(b.name) CONTAINS toLower(i.name) OR toLower(i.name) CONTAINS toLower(supp.name)
                OPTIONAL MATCH (supp)-[:CONTRAINDICATED_FOR]->(c:Condition)
                OPTIONAL MATCH (supp)-[int:INTERACTS_WITH]->(sub:Substance)
                RETURN DISTINCT
                    supp.name AS supplement,
                    i.name AS intervention,
                    COLLECT(DISTINCT b.name) AS benefits,
                    COLLECT(DISTINCT c.name) AS contraindications,
                    COLLECT(DISTINCT {substance: sub.name, type: type(int)}) AS interactions
                LIMIT 10
            """, symptom=symptom)

            recommendations = []
            for record in result:
                supp_name = record["supplement"]
                if not supp_name:
                    continue

                # Check contraindications
                contras = record["contraindications"]
                has_contra = any(c.lower() in [uc.lower() for uc in user_conditions] for c in contras if c)

                # Check interactions
                interactions = record["interactions"]
                has_interaction = any(
                    i["substance"] and i["substance"].lower() in [us.lower() for us in user_supplements]
                    for i in interactions if i["substance"]
                )

                recommendations.append({
                    "supplement": supp_name,
                    "intervention": record["intervention"],
                    "benefits": [b for b in record["benefits"] if b],
                    "contraindicated": has_contra,
                    "contraindications": contras,
                    "has_interaction": has_interaction,
                    "interactions": [i for i in interactions if i["substance"]],
                    "safe": not has_contra and not has_interaction
                })

            # Sort by safety
            recommendations.sort(key=lambda x: (x["safe"], len(x["benefits"])), reverse=True)

            return recommendations

    def find_dosha_balancing_foods(
        self,
        dosha: str,
        food_preferences: List[str] = None
    ) -> List[Dict]:
        """
        Find foods that balance a specific dosha

        Args:
            dosha: Dosha type (Vata, Pitta, Kapha)
            food_preferences: User's food preferences (vegetarian, etc.)

        Returns:
            List of balancing foods
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run("""
                MATCH (f:Food)-[:BALANCES]->(d:Dosha {name: $dosha})
                RETURN f.name AS food
                LIMIT 20
            """, dosha=dosha)

            foods = [{"food": record["food"]} for record in result]
            return foods

    def get_supplement_interactions(
        self,
        supplements: List[str]
    ) -> List[Dict]:
        """
        Check for interactions between supplements

        Args:
            supplements: List of supplement names

        Returns:
            List of interactions found
        """
        if not self.driver or len(supplements) < 2:
            return []

        with self.driver.session() as session:
            result = session.run("""
                UNWIND $supplements AS supp1
                UNWIND $supplements AS supp2
                MATCH (s1:Supplement {name: supp1})-[r]->(s2:Supplement {name: supp2})
                WHERE s1 <> s2
                RETURN DISTINCT
                    s1.name AS supplement1,
                    s2.name AS supplement2,
                    type(r) AS interaction_type,
                    r.note AS note
            """, supplements=supplements)

            interactions = []
            for record in result:
                interactions.append({
                    "supplement1": record["supplement1"],
                    "supplement2": record["supplement2"],
                    "type": record["interaction_type"],
                    "note": record["note"]
                })

            return interactions

    def explain_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 4
    ) -> List[List[str]]:
        """
        Find and explain paths between two concepts

        Args:
            start_node: Starting concept
            end_node: Target concept
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of node names)
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            # Find shortest paths
            result = session.run("""
                MATCH path = shortestPath(
                    (start)-[*..{max_depth}]-(end)
                )
                WHERE (start.name = $start OR start.name CONTAINS $start)
                  AND (end.name = $end OR end.name CONTAINS $end)
                RETURN [node IN nodes(path) | node.name] AS path_nodes,
                       [rel IN relationships(path) | type(rel)] AS relationships
                LIMIT 5
            """.replace("{max_depth}", str(max_depth)),
                start=start_node,
                end=end_node
            )

            paths = []
            for record in result:
                nodes = record["path_nodes"]
                rels = record["relationships"]

                # Format path nicely
                path_str = []
                for i, node in enumerate(nodes):
                    path_str.append(node)
                    if i < len(rels):
                        path_str.append(f"--[{rels[i]}]-->")

                paths.append(path_str)

            return paths


# Global instance
_graph_rag_instance = None

def get_graph_rag() -> GraphRAGService:
    """Get or create GraphRAG singleton"""
    global _graph_rag_instance
    if _graph_rag_instance is None:
        _graph_rag_instance = GraphRAGService()
        # Load knowledge graph on first init
        try:
            _graph_rag_instance.load_knowledge_graph()
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {e}")

    return _graph_rag_instance
