"""
GraphRAG Service - Knowledge Graph-based Retrieval Augmented Generation

This service implements GraphRAG for complex reasoning across:
- Supplement interactions and contraindications
- Ayurvedic dosha relationships
- Symptom-treatment pathways
- Health metrics correlations

Uses Neo4j for the knowledge graph.
"""

import json
import os
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable


class GraphRAG:
    """
    Graph-based Retrieval Augmented Generation
    """

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base"
    ):
        # Neo4j connection
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "neo4j_password")

        self.driver = None
        self._connect()

        self.knowledge_base_path = Path(knowledge_base_path)

    def _connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            print(f"✅ Connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print("GraphRAG will operate in limited mode without graph database")
            self.driver = None
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            self.driver = None

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def initialize_knowledge_graph(self):
        """
        Initialize the knowledge graph with:
        - Supplements and their properties
        - Interactions between supplements
        - Ayurvedic doshas and relationships
        - Symptoms and treatments
        """
        if not self.driver:
            print("Cannot initialize graph: No database connection")
            return

        with self.driver.session() as session:
            # Clear existing data (for fresh start)
            session.run("MATCH (n) DETACH DELETE n")

            # Create constraints
            session.run("""
                CREATE CONSTRAINT supplement_name IF NOT EXISTS
                FOR (s:Supplement) REQUIRE s.name IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT dosha_name IF NOT EXISTS
                FOR (d:Dosha) REQUIRE d.name IS UNIQUE
            """)

            # Load supplements
            self._load_supplements(session)

            # Load doshas
            self._load_doshas(session)

            # Create symptom-treatment pathways
            self._create_symptom_pathways(session)

            print("✅ Knowledge graph initialized")

    def _load_supplements(self, session):
        """Load supplements into knowledge graph"""
        supplements_file = self.knowledge_base_path / "supplements" / "supplements_db.json"

        if not supplements_file.exists():
            return

        with open(supplements_file) as f:
            data = json.load(f)

        for supp in data.get("supplements", []):
            # Create supplement node
            session.run("""
                CREATE (s:Supplement {
                    id: $id,
                    name: $name,
                    category: $category,
                    origin: $origin,
                    evidence_level: $evidence_level
                })
            """, {
                "id": supp["id"],
                "name": supp["name"],
                "category": supp.get("category", "unknown"),
                "origin": supp.get("origin", "unknown"),
                "evidence_level": supp.get("evidence_level", "moderate")
            })

            # Create benefit nodes and relationships
            for benefit in supp.get("benefits", []):
                session.run("""
                    MERGE (b:Benefit {name: $benefit})
                    WITH b
                    MATCH (s:Supplement {name: $supp_name})
                    MERGE (s)-[:PROVIDES]->(b)
                """, {"benefit": benefit, "supp_name": supp["name"]})

            # Create condition nodes (from contraindications)
            for contraindication in supp.get("contraindications", []):
                session.run("""
                    MERGE (c:Contraindication {name: $condition})
                    WITH c
                    MATCH (s:Supplement {name: $supp_name})
                    MERGE (s)-[:CONTRAINDICATED_FOR]->(c)
                """, {"condition": contraindication, "supp_name": supp["name"]})

        # Create supplement interactions
        self._create_supplement_interactions(session, data.get("supplements", []))

    def _create_supplement_interactions(self, session, supplements: List[Dict]):
        """Create interaction relationships between supplements"""
        # Define some known interactions (in a real system, this would be from a database)
        interactions = [
            {
                "supp1": "Ashwagandha",
                "supp2": "Magnesium",
                "type": "SYNERGISTIC",
                "effect": "Enhanced stress reduction and sleep quality"
            },
            {
                "supp1": "Omega-3",
                "supp2": "Turmeric",
                "type": "SYNERGISTIC",
                "effect": "Enhanced anti-inflammatory effects"
            },
            {
                "supp1": "L-Theanine",
                "supp2": "Brahmi",
                "type": "SYNERGISTIC",
                "effect": "Improved focus and mental clarity"
            },
            {
                "supp1": "Magnesium",
                "supp2": "Vitamin D3",
                "type": "SYNERGISTIC",
                "effect": "Magnesium aids vitamin D absorption"
            }
        ]

        for interaction in interactions:
            session.run("""
                MATCH (s1:Supplement {name: $supp1})
                MATCH (s2:Supplement {name: $supp2})
                MERGE (s1)-[r:INTERACTS_WITH {
                    type: $type,
                    effect: $effect
                }]->(s2)
            """, interaction)

    def _load_doshas(self, session):
        """Load Ayurvedic doshas into knowledge graph"""
        doshas_file = self.knowledge_base_path / "ayurveda" / "doshas.json"

        if not doshas_file.exists():
            return

        with open(doshas_file) as f:
            data = json.load(f)

        for dosha in data.get("doshas", []):
            # Create dosha node
            session.run("""
                CREATE (d:Dosha {
                    name: $name,
                    description: $description,
                    element_primary: $elem1,
                    element_secondary: $elem2
                })
            """, {
                "name": dosha["name"],
                "description": dosha.get("description", ""),
                "elem1": dosha.get("elements", [])[0] if len(dosha.get("elements", [])) > 0 else "",
                "elem2": dosha.get("elements", [])[1] if len(dosha.get("elements", [])) > 1 else ""
            })

            # Create balancing food nodes
            for food in dosha.get("balancing_foods", []):
                session.run("""
                    MERGE (f:Food {name: $food})
                    WITH f
                    MATCH (d:Dosha {name: $dosha_name})
                    MERGE (f)-[:BALANCES]->(d)
                """, {"food": food, "dosha_name": dosha["name"]})

            # Link herbs to doshas
            for herb in dosha.get("recommended_herbs", []):
                session.run("""
                    MERGE (h:Herb {name: $herb_name})
                    WITH h
                    MATCH (d:Dosha {name: $dosha_name})
                    MERGE (h)-[:BALANCES {benefit: $benefit}]->(d)
                """, {
                    "herb_name": herb["name"],
                    "dosha_name": dosha["name"],
                    "benefit": herb.get("benefit", "")
                })

    def _create_symptom_pathways(self, session):
        """Create symptom-treatment knowledge graph pathways"""
        # Define symptom-treatment relationships
        pathways = [
            {
                "symptom": "High Stress",
                "treatments": [
                    {"name": "Ashwagandha", "type": "Supplement", "efficacy": 0.85},
                    {"name": "Magnesium", "type": "Supplement", "efficacy": 0.75},
                    {"name": "Breathing Exercises", "type": "Practice", "efficacy": 0.80},
                    {"name": "Meditation", "type": "Practice", "efficacy": 0.75}
                ],
                "related_symptoms": ["Anxiety", "Poor Sleep", "Fatigue"]
            },
            {
                "symptom": "Poor Sleep",
                "treatments": [
                    {"name": "Magnesium", "type": "Supplement", "efficacy": 0.80},
                    {"name": "L-Theanine", "type": "Supplement", "efficacy": 0.70},
                    {"name": "Sleep Hygiene", "type": "Practice", "efficacy": 0.85},
                    {"name": "Evening Routine", "type": "Practice", "efficacy": 0.75}
                ],
                "related_symptoms": ["High Stress", "Fatigue", "Low Focus"]
            },
            {
                "symptom": "Low Focus",
                "treatments": [
                    {"name": "Brahmi", "type": "Supplement", "efficacy": 0.75},
                    {"name": "L-Theanine", "type": "Supplement", "efficacy": 0.80},
                    {"name": "Omega-3", "type": "Supplement", "efficacy": 0.70},
                    {"name": "Pomodoro Technique", "type": "Practice", "efficacy": 0.85}
                ],
                "related_symptoms": ["Poor Sleep", "High Stress"]
            },
            {
                "symptom": "Low Energy",
                "treatments": [
                    {"name": "Vitamin B-Complex", "type": "Supplement", "efficacy": 0.75},
                    {"name": "Vitamin D3", "type": "Supplement", "efficacy": 0.70},
                    {"name": "Exercise", "type": "Practice", "efficacy": 0.85},
                    {"name": "Balanced Diet", "type": "Practice", "efficacy": 0.80}
                ],
                "related_symptoms": ["Poor Sleep", "Low Mood"]
            }
        ]

        for pathway in pathways:
            # Create symptom node
            session.run("""
                MERGE (s:Symptom {name: $symptom})
            """, {"symptom": pathway["symptom"]})

            # Create treatment nodes and relationships
            for treatment in pathway["treatments"]:
                if treatment["type"] == "Supplement":
                    session.run("""
                        MERGE (t:Supplement {name: $name})
                        WITH t
                        MATCH (s:Symptom {name: $symptom})
                        MERGE (t)-[:TREATS {efficacy: $efficacy}]->(s)
                    """, {
                        "name": treatment["name"],
                        "symptom": pathway["symptom"],
                        "efficacy": treatment["efficacy"]
                    })
                else:
                    session.run("""
                        MERGE (t:Practice {name: $name})
                        WITH t
                        MATCH (s:Symptom {name: $symptom})
                        MERGE (t)-[:TREATS {efficacy: $efficacy}]->(s)
                    """, {
                        "name": treatment["name"],
                        "symptom": pathway["symptom"],
                        "efficacy": treatment["efficacy"]
                    })

            # Create relationships between related symptoms
            for related in pathway.get("related_symptoms", []):
                session.run("""
                    MATCH (s1:Symptom {name: $symptom})
                    MERGE (s2:Symptom {name: $related})
                    MERGE (s1)-[:RELATED_TO]->(s2)
                """, {"symptom": pathway["symptom"], "related": related})

    def find_treatments_for_symptoms(
        self,
        symptoms: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find treatments for given symptoms using graph traversal

        Returns treatments ranked by:
        - Efficacy
        - Coverage (how many symptoms they address)
        - Evidence level
        """
        if not self.driver:
            return self._fallback_find_treatments(symptoms)

        with self.driver.session() as session:
            # Complex Cypher query to find best treatments
            result = session.run("""
                UNWIND $symptoms AS symptom_name
                MATCH (s:Symptom {name: symptom_name})
                MATCH (t)-[r:TREATS]->(s)
                WITH t, collect(DISTINCT s.name) AS treated_symptoms, avg(r.efficacy) AS avg_efficacy
                RETURN
                    labels(t)[0] AS type,
                    t.name AS name,
                    treated_symptoms,
                    avg_efficacy,
                    size(treated_symptoms) AS coverage
                ORDER BY coverage DESC, avg_efficacy DESC
                LIMIT $limit
            """, {"symptoms": symptoms, "limit": limit})

            treatments = []
            for record in result:
                treatments.append({
                    "name": record["name"],
                    "type": record["type"],
                    "treated_symptoms": record["treated_symptoms"],
                    "efficacy": round(record["avg_efficacy"], 2),
                    "coverage": record["coverage"]
                })

            return treatments

    def find_supplement_interactions(
        self,
        supplement_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find interactions between given supplements
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run("""
                MATCH (s1:Supplement)-[r:INTERACTS_WITH]->(s2:Supplement)
                WHERE s1.name IN $supplements AND s2.name IN $supplements
                RETURN s1.name AS supplement1, s2.name AS supplement2,
                       r.type AS interaction_type, r.effect AS effect
            """, {"supplements": supplement_names})

            interactions = []
            for record in result:
                interactions.append({
                    "supplement1": record["supplement1"],
                    "supplement2": record["supplement2"],
                    "type": record["interaction_type"],
                    "effect": record["effect"]
                })

            return interactions

    def find_dosha_balancing_recommendations(
        self,
        dosha: str,
        category: str = None  # "food", "herb", or None for all
    ) -> Dict[str, List[str]]:
        """
        Find balancing recommendations for a dosha
        """
        if not self.driver:
            return self._fallback_dosha_recommendations(dosha)

        with self.driver.session() as session:
            # Find foods that balance the dosha
            foods_result = session.run("""
                MATCH (f:Food)-[:BALANCES]->(d:Dosha {name: $dosha})
                RETURN f.name AS name
            """, {"dosha": dosha})

            foods = [record["name"] for record in foods_result]

            # Find herbs that balance the dosha
            herbs_result = session.run("""
                MATCH (h:Herb)-[r:BALANCES]->(d:Dosha {name: $dosha})
                RETURN h.name AS name, r.benefit AS benefit
            """, {"dosha": dosha})

            herbs = [{"name": record["name"], "benefit": record["benefit"]} for record in herbs_result]

            return {
                "dosha": dosha,
                "balancing_foods": foods,
                "recommended_herbs": herbs
            }

    def complex_reasoning_query(
        self,
        user_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform complex reasoning using the knowledge graph

        Example user_state:
        {
            "symptoms": ["High Stress", "Poor Sleep"],
            "current_supplements": ["Magnesium"],
            "dosha": "Vata",
            "contraindications": ["Pregnancy"]
        }
        """
        if not self.driver:
            return self._fallback_complex_reasoning(user_state)

        recommendations = {
            "new_supplements": [],
            "practices": [],
            "dietary_changes": [],
            "warnings": []
        }

        # Find treatments for symptoms
        symptoms = user_state.get("symptoms", [])
        current_supps = user_state.get("current_supplements", [])

        treatments = self.find_treatments_for_symptoms(symptoms)

        # Filter out current supplements and add new ones
        for treatment in treatments:
            if treatment["type"] == "Supplement" and treatment["name"] not in current_supps:
                recommendations["new_supplements"].append(treatment)
            elif treatment["type"] == "Practice":
                recommendations["practices"].append(treatment)

        # Check for interactions with current supplements
        if current_supps and recommendations["new_supplements"]:
            all_supps = current_supps + [s["name"] for s in recommendations["new_supplements"]]
            interactions = self.find_supplement_interactions(all_supps)
            if interactions:
                recommendations["supplement_interactions"] = interactions

        # Get dosha-specific recommendations
        dosha = user_state.get("dosha")
        if dosha:
            dosha_recs = self.find_dosha_balancing_recommendations(dosha)
            recommendations["dietary_changes"] = dosha_recs.get("balancing_foods", [])[:5]

        # Check contraindications
        contraindications = user_state.get("contraindications", [])
        if contraindications and self.driver:
            with self.driver.session() as session:
                for supp in recommendations["new_supplements"]:
                    result = session.run("""
                        MATCH (s:Supplement {name: $supp})-[:CONTRAINDICATED_FOR]->(c:Contraindication)
                        RETURN c.name AS contraindication
                    """, {"supp": supp["name"]})

                    matched_contras = [r["contraindication"] for r in result]
                    for contra in contraindications:
                        if any(contra.lower() in mc.lower() for mc in matched_contras):
                            recommendations["warnings"].append({
                                "supplement": supp["name"],
                                "warning": f"Contraindicated for {contra}"
                            })

        return recommendations

    def _fallback_find_treatments(self, symptoms: List[str]) -> List[Dict]:
        """Fallback when Neo4j is not available"""
        # Simple rule-based fallback
        treatment_map = {
            "High Stress": [
                {"name": "Ashwagandha", "type": "Supplement", "efficacy": 0.85},
                {"name": "Magnesium", "type": "Supplement", "efficacy": 0.75},
                {"name": "Breathing Exercises", "type": "Practice", "efficacy": 0.80}
            ],
            "Poor Sleep": [
                {"name": "Magnesium", "type": "Supplement", "efficacy": 0.80},
                {"name": "L-Theanine", "type": "Supplement", "efficacy": 0.70}
            ],
            "Low Focus": [
                {"name": "Brahmi", "type": "Supplement", "efficacy": 0.75},
                {"name": "L-Theanine", "type": "Supplement", "efficacy": 0.80}
            ]
        }

        treatments = []
        for symptom in symptoms:
            treatments.extend(treatment_map.get(symptom, []))

        # Deduplicate and rank
        unique_treatments = {}
        for t in treatments:
            if t["name"] not in unique_treatments:
                unique_treatments[t["name"]] = t
                unique_treatments[t["name"]]["treated_symptoms"] = [symptom]
                unique_treatments[t["name"]]["coverage"] = 1
            else:
                unique_treatments[t["name"]]["coverage"] += 1

        return sorted(unique_treatments.values(), key=lambda x: (x["coverage"], x["efficacy"]), reverse=True)[:5]

    def _fallback_dosha_recommendations(self, dosha: str) -> Dict:
        """Fallback dosha recommendations"""
        recommendations = {
            "Vata": {
                "balancing_foods": ["Warm soups", "Cooked grains", "Root vegetables", "Ghee", "Nuts"],
                "recommended_herbs": [
                    {"name": "Ashwagandha", "benefit": "Grounding and calming"},
                    {"name": "Brahmi", "benefit": "Mental stability"}
                ]
            },
            "Pitta": {
                "balancing_foods": ["Cooling fruits", "Leafy greens", "Cucumber", "Coconut", "Sweet foods"],
                "recommended_herbs": [
                    {"name": "Turmeric", "benefit": "Anti-inflammatory"},
                    {"name": "Brahmi", "benefit": "Cooling for mind"}
                ]
            },
            "Kapha": {
                "balancing_foods": ["Spicy foods", "Light vegetables", "Legumes", "Ginger", "Honey"],
                "recommended_herbs": [
                    {"name": "Turmeric", "benefit": "Metabolism boost"},
                    {"name": "Ginger", "benefit": "Digestive fire"}
                ]
            }
        }

        return {
            "dosha": dosha,
            **recommendations.get(dosha, {"balancing_foods": [], "recommended_herbs": []})
        }

    def _fallback_complex_reasoning(self, user_state: Dict) -> Dict:
        """Fallback complex reasoning without graph"""
        symptoms = user_state.get("symptoms", [])
        treatments = self._fallback_find_treatments(symptoms)

        current_supps = user_state.get("current_supplements", [])
        new_supplements = [t for t in treatments if t["type"] == "Supplement" and t["name"] not in current_supps]
        practices = [t for t in treatments if t["type"] == "Practice"]

        dosha_recs = {}
        if user_state.get("dosha"):
            dosha_recs = self._fallback_dosha_recommendations(user_state["dosha"])

        return {
            "new_supplements": new_supplements[:3],
            "practices": practices[:3],
            "dietary_changes": dosha_recs.get("balancing_foods", [])[:5],
            "warnings": []
        }


# Global instance
_graph_rag_instance = None

def get_graph_rag() -> GraphRAG:
    """Get or create GraphRAG singleton"""
    global _graph_rag_instance
    if _graph_rag_instance is None:
        _graph_rag_instance = GraphRAG()
        # Initialize knowledge graph on first use
        try:
            _graph_rag_instance.initialize_knowledge_graph()
        except Exception as e:
            print(f"Could not initialize knowledge graph: {e}")
    return _graph_rag_instance
