"""
Vector Database Service for RAG (Retrieval Augmented Generation)

Manages embeddings and similarity search for wellness knowledge base
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    Manages vector embeddings for RAG

    Uses ChromaDB for vector storage and sentence-transformers for embeddings
    """

    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize vector database

        Args:
            persist_directory: Path to persist ChromaDB data
            model_name: HuggingFace model for embeddings
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)

        # Create collections
        self._init_collections()

    def _init_collections(self):
        """Initialize ChromaDB collections"""
        # Wellness knowledge collection
        try:
            self.wellness_collection = self.client.get_collection("wellness_knowledge")
        except:
            self.wellness_collection = self.client.create_collection(
                name="wellness_knowledge",
                metadata={"description": "General wellness, nutrition, Ayurveda knowledge"}
            )

        # Supplement knowledge collection
        try:
            self.supplement_collection = self.client.get_collection("supplements")
        except:
            self.supplement_collection = self.client.create_collection(
                name="supplements",
                metadata={"description": "Supplement database with interactions"}
            )

        # Research papers collection
        try:
            self.research_collection = self.client.get_collection("research")
        except:
            self.research_collection = self.client.create_collection(
                name="research",
                metadata={"description": "Scientific research and PubMed articles"}
            )

        # User context collection (per-user memories)
        try:
            self.user_context_collection = self.client.get_collection("user_contexts")
        except:
            self.user_context_collection = self.client.create_collection(
                name="user_contexts",
                metadata={"description": "User-specific health context and memories"}
            )

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        collection_name: str = "wellness_knowledge",
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to vector database

        Args:
            documents: List of text documents
            metadatas: Metadata for each document
            collection_name: Target collection
            ids: Optional document IDs
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()

        # Select collection
        collection = self._get_collection(collection_name)

        # Add to ChromaDB
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(documents)} documents to {collection_name}")

    def search(
        self,
        query: str,
        collection_name: str = "wellness_knowledge",
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search for relevant documents

        Args:
            query: Search query
            collection_name: Collection to search
            n_results: Number of results
            filter_metadata: Metadata filters

        Returns:
            List of {document, metadata, distance} dicts
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]

        # Select collection
        collection = self._get_collection(collection_name)

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'id': results['ids'][0][i]
            })

        return formatted_results

    def add_user_memory(
        self,
        user_id: str,
        memory: str,
        metadata: Dict
    ) -> None:
        """
        Add user-specific memory for personalization

        Args:
            user_id: User ID
            memory: Memory text
            metadata: Memory metadata (timestamp, type, etc.)
        """
        metadata['user_id'] = user_id

        embedding = self.embedding_model.encode([memory]).tolist()[0]

        self.user_context_collection.add(
            embeddings=[embedding],
            documents=[memory],
            metadatas=[metadata],
            ids=[f"{user_id}_{metadata.get('timestamp', 'memory')}"]
        )

    def retrieve_user_context(
        self,
        user_id: str,
        query: str,
        n_results: int = 3
    ) -> List[Dict]:
        """
        Retrieve relevant user context for query

        Args:
            user_id: User ID
            query: Current query
            n_results: Number of memories to retrieve

        Returns:
            List of relevant user memories
        """
        return self.search(
            query=query,
            collection_name="user_contexts",
            n_results=n_results,
            filter_metadata={"user_id": user_id}
        )

    def load_knowledge_base(self) -> None:
        """
        Load knowledge base from JSON files into vector DB
        """
        logger.info("Loading knowledge base into vector database...")

        # Load Ayurveda doshas
        self._load_ayurveda_knowledge()

        # Load supplement database
        self._load_supplement_knowledge()

        # Load general wellness knowledge
        self._load_wellness_knowledge()

        logger.info("Knowledge base loaded successfully")

    def _load_ayurveda_knowledge(self):
        """Load Ayurveda dosha knowledge"""
        dosha_path = Path("knowledge_base/ayurveda/doshas.json")
        if not dosha_path.exists():
            logger.warning(f"Dosha file not found: {dosha_path}")
            return

        with open(dosha_path) as f:
            doshas_data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for dosha_name, dosha_data in doshas_data.items():
            # Main dosha description
            doc = f"{dosha_name} dosha: {dosha_data.get('description', '')}. "
            doc += f"Characteristics: {', '.join(dosha_data.get('characteristics', {}).get('physical', []))}. "
            doc += f"Mental traits: {', '.join(dosha_data.get('characteristics', {}).get('mental', []))}. "
            doc += f"Imbalance signs: {', '.join(dosha_data.get('imbalance_signs', []))}."

            documents.append(doc)
            metadatas.append({
                "source": "ayurveda",
                "type": "dosha",
                "dosha": dosha_name
            })
            ids.append(f"dosha_{dosha_name}")

            # Balancing foods
            if "balancing_foods" in dosha_data:
                foods_doc = f"Foods that balance {dosha_name} dosha: {', '.join(dosha_data['balancing_foods'][:10])}"
                documents.append(foods_doc)
                metadatas.append({
                    "source": "ayurveda",
                    "type": "diet",
                    "dosha": dosha_name
                })
                ids.append(f"dosha_{dosha_name}_foods")

            # Herbs
            if "herbs" in dosha_data:
                for herb in dosha_data["herbs"][:5]:
                    herb_doc = f"{herb['name']}: {herb.get('properties', '')}. Benefits: {herb.get('benefits', '')}. Good for {dosha_name} dosha."
                    documents.append(herb_doc)
                    metadatas.append({
                        "source": "ayurveda",
                        "type": "herb",
                        "dosha": dosha_name,
                        "herb_name": herb['name']
                    })
                    ids.append(f"herb_{dosha_name}_{herb['name'].replace(' ', '_')}")

        self.add_documents(documents, metadatas, "wellness_knowledge", ids)
        logger.info(f"Loaded {len(documents)} Ayurveda documents")

    def _load_supplement_knowledge(self):
        """Load supplement database"""
        supp_path = Path("knowledge_base/supplements/supplements_db.json")
        if not supp_path.exists():
            logger.warning(f"Supplement file not found: {supp_path}")
            return

        with open(supp_path) as f:
            supplements_data = json.load(f)

        supplements = supplements_data.get("supplements", [])

        documents = []
        metadatas = []
        ids = []

        for supp in supplements:
            # Main supplement info
            doc = f"{supp['name']}: {supp.get('description', '')}. "
            doc += f"Benefits: {', '.join(supp.get('benefits', [])[:5])}. "
            doc += f"Mechanisms: {', '.join(supp.get('mechanisms', [])[:3])}. "

            if "dosage" in supp:
                doc += f"Typical dosage: {supp['dosage'].get('typical', 'varies')}. "

            if "contraindications" in supp:
                doc += f"Contraindications: {', '.join(supp['contraindications'][:3])}."

            documents.append(doc)
            metadatas.append({
                "source": "supplement_db",
                "type": "supplement",
                "supplement_name": supp['name']
            })
            ids.append(f"supp_{supp['name'].replace(' ', '_')}")

        self.add_documents(documents, metadatas, "supplements", ids)
        logger.info(f"Loaded {len(documents)} supplement documents")

    def _load_wellness_knowledge(self):
        """Load general wellness knowledge"""
        # General wellness tips
        wellness_tips = [
            {
                "content": "Sleep: Adults need 7-9 hours per night. Poor sleep increases stress hormones (cortisol), impairs cognitive function, and weakens immune response. Magnesium, melatonin, and L-theanine can support sleep quality.",
                "type": "sleep",
                "category": "lifestyle"
            },
            {
                "content": "Stress management: Chronic stress elevates cortisol, causes inflammation, and impairs digestion. Effective techniques include breathwork (4-7-8 breathing), meditation, yoga, and adaptogenic herbs like Ashwagandha.",
                "type": "stress",
                "category": "mental_health"
            },
            {
                "content": "Nutrition: Whole foods rich in omega-3 (fish, nuts), antioxidants (berries, leafy greens), and fiber support brain health, reduce inflammation, and stabilize blood sugar. Avoid processed foods and excess sugar.",
                "type": "nutrition",
                "category": "diet"
            },
            {
                "content": "Exercise: 150 minutes moderate aerobic activity per week improves cardiovascular health, reduces anxiety/depression, enhances sleep, and boosts cognitive function. Resistance training builds muscle and bone density.",
                "type": "exercise",
                "category": "fitness"
            },
            {
                "content": "Hydration: Aim for 8-10 glasses water daily. Dehydration impairs cognitive performance, mood, and physical endurance. Add electrolytes if exercising intensely.",
                "type": "hydration",
                "category": "nutrition"
            },
            {
                "content": "Gut health: Probiotics and prebiotics support healthy microbiome. Good gut bacteria produce neurotransmitters (serotonin, GABA) that affect mood and cognition. Fermented foods, fiber-rich vegetables are beneficial.",
                "type": "gut_health",
                "category": "nutrition"
            },
            {
                "content": "Cognitive performance: Omega-3 DHA supports brain structure, B vitamins aid neurotransmitter synthesis, and antioxidants protect against oxidative stress. Regular mental stimulation and learning enhance neuroplasticity.",
                "type": "cognitive",
                "category": "brain_health"
            },
            {
                "content": "Inflammation reduction: Chronic inflammation linked to depression, anxiety, and cognitive decline. Anti-inflammatory foods: turmeric, ginger, omega-3, green tea. Reduce processed foods, excess sugar, trans fats.",
                "type": "inflammation",
                "category": "nutrition"
            }
        ]

        documents = [tip['content'] for tip in wellness_tips]
        metadatas = [{"source": "wellness_general", **{k: v for k, v in tip.items() if k != 'content'}}
                     for tip in wellness_tips]
        ids = [f"wellness_{tip['type']}" for tip in wellness_tips]

        self.add_documents(documents, metadatas, "wellness_knowledge", ids)
        logger.info(f"Loaded {len(documents)} general wellness documents")

    def _get_collection(self, collection_name: str):
        """Get collection by name"""
        collection_map = {
            "wellness_knowledge": self.wellness_collection,
            "supplements": self.supplement_collection,
            "research": self.research_collection,
            "user_contexts": self.user_context_collection
        }

        collection = collection_map.get(collection_name)
        if collection is None:
            raise ValueError(f"Unknown collection: {collection_name}")

        return collection

    def reset_database(self):
        """Reset all collections (use with caution)"""
        self.client.reset()
        self._init_collections()
        logger.warning("Vector database reset")


# Global instance
_vector_db_instance = None

def get_vector_db() -> VectorDBService:
    """Get or create vector DB singleton"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDBService()
        # Load knowledge base on first initialization
        try:
            _vector_db_instance.load_knowledge_base()
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")

    return _vector_db_instance
