"""
LLM Wellness Coach Service with RAG and GraphRAG

This service implements a conversational AI wellness coach that:
- Uses RAG to retrieve relevant knowledge from wellness knowledge base
- Uses GraphRAG with Neo4j to traverse health relationships
- Maintains long-term memory of user conversations
- Provides evidence-based, personalized wellness advice
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.schema import Document

from neo4j import GraphDatabase


class WellnessKnowledgeBase:
    """Manages the wellness knowledge base with vector and graph storage"""

    def __init__(
        self,
        knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base",
        vector_store_path: str = "/home/user/Wellnessapp/data/vector_store",
        neo4j_uri: str = "bolt://neo4j:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "wellness123"
    ):
        self.kb_path = Path(knowledge_base_path)
        self.vector_store_path = Path(vector_store_path)

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}  # Use GPU if available
        )

        # Initialize or load vector store
        self.vector_store = self._init_vector_store()

        # Initialize Neo4j for GraphRAG
        try:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
        except Exception as e:
            print(f"Neo4j connection failed: {e}. GraphRAG features will be limited.")
            self.neo4j_driver = None

    def _init_vector_store(self) -> Chroma:
        """Initialize or load the vector store"""
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Check if vector store already exists
        if (self.vector_store_path / "chroma.sqlite3").exists():
            print("Loading existing vector store...")
            return Chroma(
                persist_directory=str(self.vector_store_path),
                embedding_function=self.embeddings
            )

        # Create new vector store from knowledge base
        print("Creating new vector store from knowledge base...")
        documents = self._load_knowledge_base()

        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(self.vector_store_path)
        )
        vector_store.persist()

        return vector_store

    def _load_knowledge_base(self) -> List[Document]:
        """Load all knowledge base documents"""
        documents = []

        # Load Ayurveda knowledge
        ayurveda_path = self.kb_path / "ayurveda" / "doshas.json"
        if ayurveda_path.exists():
            with open(ayurveda_path) as f:
                doshas_data = json.load(f)

            for dosha_name, dosha_info in doshas_data.items():
                # Create documents for each aspect of dosha
                documents.append(Document(
                    page_content=f"Dosha: {dosha_name}\n"
                                f"Description: {dosha_info.get('description', '')}\n"
                                f"Characteristics: {json.dumps(dosha_info.get('characteristics', {}))}",
                    metadata={"source": "ayurveda", "type": "dosha", "name": dosha_name}
                ))

                # Foods
                if "balancing_foods" in dosha_info:
                    documents.append(Document(
                        page_content=f"For {dosha_name} dosha imbalance, favor: "
                                    f"{', '.join(dosha_info['balancing_foods']['favor'])}. "
                                    f"Avoid: {', '.join(dosha_info['balancing_foods']['avoid'])}.",
                        metadata={"source": "ayurveda", "type": "diet", "dosha": dosha_name}
                    ))

                # Herbs
                if "herbs" in dosha_info:
                    for herb in dosha_info["herbs"]:
                        documents.append(Document(
                            page_content=f"{herb['name']}: {herb.get('properties', '')} "
                                        f"Benefits for {dosha_name}: {herb.get('benefits', '')}",
                            metadata={"source": "ayurveda", "type": "herb", "dosha": dosha_name}
                        ))

        # Load supplement database
        supplements_path = self.kb_path / "supplements" / "supplements_db.json"
        if supplements_path.exists():
            with open(supplements_path) as f:
                supplements_data = json.load(f)

            for supplement in supplements_data.get("supplements", []):
                # Main supplement info
                documents.append(Document(
                    page_content=f"Supplement: {supplement['name']}\n"
                                f"Type: {supplement.get('type', '')}\n"
                                f"Benefits: {', '.join(supplement.get('benefits', []))}\n"
                                f"Mechanism: {supplement.get('mechanism', '')}\n"
                                f"Dosage: {supplement.get('dosage', {}).get('typical', '')}\n"
                                f"Contraindications: {', '.join(supplement.get('contraindications', []))}",
                    metadata={"source": "supplements", "name": supplement['name']}
                ))

                # Evidence
                if "evidence" in supplement:
                    for study in supplement["evidence"]:
                        documents.append(Document(
                            page_content=f"Study on {supplement['name']}: {study.get('summary', '')}",
                            metadata={
                                "source": "pubmed",
                                "supplement": supplement['name'],
                                "link": study.get('link', '')
                            }
                        ))

        print(f"Loaded {len(documents)} documents into knowledge base")
        return documents

    def semantic_search(self, query: str, k: int = 5) -> List[Dict]:
        """Perform semantic search on knowledge base"""
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            }
            for doc, score in results
        ]

    def graph_traverse(self, user_state: Dict, issue: str) -> List[str]:
        """
        Traverse the knowledge graph to find relevant interventions

        Example: high_stress + poor_sleep -> magnesium + breathwork
        """
        if not self.neo4j_driver:
            return []

        recommendations = []

        # Simple graph query example
        query = """
        MATCH (state:MentalState {name: $state_name})
        -[:CAN_BE_HELPED_BY]->(intervention:Intervention)
        RETURN intervention.name as name, intervention.description as description
        LIMIT 5
        """

        try:
            with self.neo4j_driver.session() as session:
                # This would need the graph to be populated first
                # For now, return empty list
                pass
        except Exception as e:
            print(f"Graph traversal error: {e}")

        return recommendations


class WellnessCoach:
    """AI Wellness Coach with RAG and conversational memory"""

    def __init__(
        self,
        knowledge_base: WellnessKnowledgeBase,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7
    ):
        self.kb = knowledge_base

        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if anthropic_key:
            self.llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=temperature,
                anthropic_api_key=anthropic_key
            )
        elif api_key:
            self.llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                openai_api_key=api_key
            )
        else:
            # Fallback to local model (would need to be configured)
            raise ValueError("No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

        # Create the wellness coach prompt
        self.system_prompt = PromptTemplate(
            template="""You are a compassionate and knowledgeable AI wellness coach specializing in holistic health.
You integrate modern science with traditional wisdom (Ayurveda, mindfulness) to provide personalized guidance.

Your approach:
- Be empathetic and encouraging
- Provide evidence-based advice with sources when possible
- Consider the user's whole context (mind, body, lifestyle)
- Suggest actionable steps that are realistic
- Always include a disclaimer that you're not replacing professional medical advice

Context about the user:
{user_context}

Relevant knowledge:
{knowledge_context}

User's question: {question}

Provide a thoughtful, personalized response that addresses their concern with specific, actionable recommendations.
Include references to studies or traditional wisdom when applicable.""",
            input_variables=["user_context", "knowledge_context", "question"]
        )

        # User conversation memories (in-memory for now, should be in DB)
        self.user_memories: Dict[str, ConversationBufferMemory] = {}

    def get_or_create_memory(self, user_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for user"""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return self.user_memories[user_id]

    async def chat(
        self,
        user_id: str,
        message: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Process a chat message and generate response

        Returns:
            {
                "message": str,
                "context_used": List[str],
                "recommendations": List[str],
                "sources": List[str]
            }
        """
        # Get user context (health metrics, profile, etc.)
        if user_context is None:
            user_context = await self._get_user_context(user_id)

        # Retrieve relevant knowledge using RAG
        knowledge_results = self.kb.semantic_search(message, k=5)

        # Format knowledge context
        knowledge_text = "\n\n".join([
            f"[{r['metadata'].get('source', 'unknown')}] {r['content']}"
            for r in knowledge_results
        ])

        # Build context strings
        user_context_str = self._format_user_context(user_context)

        # Generate response using LLM
        prompt = self.system_prompt.format(
            user_context=user_context_str,
            knowledge_context=knowledge_text,
            question=message
        )

        response = self.llm.predict(prompt)

        # Extract structured information from response
        context_used = self._extract_context_used(knowledge_results, user_context)
        recommendations = self._extract_recommendations(response)
        sources = self._extract_sources(knowledge_results)

        # Store in memory
        memory = self.get_or_create_memory(user_id)
        memory.chat_memory.add_user_message(message)
        memory.chat_memory.add_ai_message(response)

        return {
            "message": response,
            "context_used": context_used,
            "recommendations": recommendations,
            "sources": sources
        }

    async def _get_user_context(self, user_id: str) -> Dict:
        """Get user's recent health data and profile"""
        # TODO: Query database for user context
        # This would include: recent EEG, sleep, stress levels, goals, etc.
        return {
            "recent_stress": "high",
            "sleep_hours": 5.5,
            "dosha_type": "vata_pitta",
            "goals": ["reduce stress", "improve sleep"],
            "dietary_restrictions": ["vegetarian"]
        }

    def _format_user_context(self, context: Dict) -> str:
        """Format user context for prompt"""
        lines = []
        if "recent_stress" in context:
            lines.append(f"Recent stress level: {context['recent_stress']}")
        if "sleep_hours" in context:
            lines.append(f"Recent sleep: {context['sleep_hours']} hours")
        if "dosha_type" in context:
            lines.append(f"Ayurvedic constitution: {context['dosha_type']}")
        if "goals" in context:
            lines.append(f"Health goals: {', '.join(context['goals'])}")
        if "dietary_restrictions" in context:
            lines.append(f"Dietary restrictions: {', '.join(context['dietary_restrictions'])}")

        return "\n".join(lines)

    def _extract_context_used(self, knowledge_results: List[Dict], user_context: Dict) -> List[str]:
        """Extract what context was used in the response"""
        context_used = []

        # Add top knowledge sources
        for result in knowledge_results[:3]:
            source = result['metadata'].get('source', 'knowledge base')
            context_used.append(f"Knowledge from {source}")

        # Add user data used
        if user_context.get("recent_stress"):
            context_used.append("Recent stress levels")
        if user_context.get("sleep_hours"):
            context_used.append("Sleep data")

        return context_used

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        # Simple extraction - look for numbered lists or bullet points
        recommendations = []

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            # Look for numbered items (1., 2., etc.) or bullet points (-, *, •)
            if line and (
                line[0].isdigit() or
                line.startswith('-') or
                line.startswith('*') or
                line.startswith('•')
            ):
                # Clean up
                clean = line.lstrip('0123456789.-*• ').strip()
                if clean and len(clean) > 10:  # Skip very short items
                    recommendations.append(clean)

        return recommendations[:5]  # Top 5

    def _extract_sources(self, knowledge_results: List[Dict]) -> List[str]:
        """Extract source citations"""
        sources = []

        for result in knowledge_results:
            metadata = result['metadata']

            if metadata.get('source') == 'pubmed' and metadata.get('link'):
                sources.append(f"PubMed study: {metadata['link']}")
            elif metadata.get('source') == 'ayurveda':
                sources.append(f"Ayurvedic principle: {metadata.get('type', '')}")
            elif metadata.get('source') == 'supplements':
                sources.append(f"Supplement database: {metadata.get('name', '')}")

        return sources[:5]  # Top 5


# Global instances (would be managed by dependency injection in production)
_knowledge_base: Optional[WellnessKnowledgeBase] = None
_coach: Optional[WellnessCoach] = None


def get_knowledge_base() -> WellnessKnowledgeBase:
    """Get or create knowledge base instance"""
    global _knowledge_base

    if _knowledge_base is None:
        _knowledge_base = WellnessKnowledgeBase()

    return _knowledge_base


def get_coach() -> WellnessCoach:
    """Get or create coach instance"""
    global _coach

    if _coach is None:
        kb = get_knowledge_base()
        _coach = WellnessCoach(kb)

    return _coach


async def generate_proactive_check_in(user_id: str, current_data: Dict) -> Dict:
    """
    Generate proactive check-in based on user's current state

    This is the "agentic AI" behavior - the system takes initiative
    """
    coach = get_coach()

    # Analyze current data for triggers
    triggers = []
    suggestions = []

    if current_data.get("hours_since_break", 0) > 2:
        triggers.append("Long time without break")
        suggestions.append("Take a 5-minute stretch break")

    if current_data.get("stress_level", 0) > 0.7:
        triggers.append("Elevated stress detected")
        suggestions.append("Try a breathing exercise")

    if current_data.get("focus_level", 0) < 0.4:
        triggers.append("Declining focus")
        suggestions.append("Short walk or hydration")

    if not triggers:
        return None  # No check-in needed

    # Generate personalized message
    message = f"I noticed: {', '.join(triggers)}. "
    message += f"Would you like to try: {suggestions[0]}?"

    return {
        "message": message,
        "triggers": triggers,
        "suggestions": suggestions,
        "urgency": "medium" if len(triggers) > 1 else "low"
    }
