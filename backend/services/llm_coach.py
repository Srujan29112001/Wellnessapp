"""
LangChain-based Wellness Coach with RAG and Long-term Memory
Implements the conversational AI coach with knowledge base integration
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import Document, HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool, StructuredTool
from langchain.callbacks import get_openai_callback
from pydantic import BaseModel, Field

from config.settings import settings
from backend.services.graph_rag import get_knowledge_graph

logger = logging.getLogger(__name__)


class WellnessCoach:
    """
    AI Wellness Coach with RAG, long-term memory, and agentic capabilities
    """

    def __init__(
        self,
        use_local_llm: bool = False,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the Wellness Coach

        Args:
            use_local_llm: Whether to use local LLM (HuggingFace) or API (OpenAI/Anthropic)
            model_name: Specific model to use
            temperature: Temperature for generation (0.0-1.0)
        """
        self.use_local_llm = use_local_llm or settings.USE_LOCAL_LLM
        self.temperature = temperature

        # Initialize LLM
        if self.use_local_llm:
            # Local HuggingFace model (requires loading)
            logger.info("Using local LLM (not fully implemented - falling back to OpenAI)")
            self.llm = self._init_openai_llm(model_name)
        else:
            # Use OpenAI or Anthropic
            if settings.ANTHROPIC_API_KEY and "claude" in (model_name or "").lower():
                self.llm = self._init_anthropic_llm(model_name)
            else:
                self.llm = self._init_openai_llm(model_name)

        # Initialize embeddings
        if settings.USE_LOCAL_LLM:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            self.embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL
            )

        # Initialize vector store for RAG
        self.vector_store = self._init_vector_store()

        # Load knowledge base into vector store
        self._load_knowledge_base()

        # Conversational memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # Create the conversational chain
        self.chain = self._create_conversational_chain()

        # Create tools for agentic behavior
        self.tools = self._create_tools()

        # Agent for proactive recommendations
        self.agent = None  # Will be initialized when needed

        # Knowledge Graph for GraphRAG
        self.knowledge_graph = None  # Will be initialized when needed

        logger.info("Wellness Coach initialized successfully")

    async def _ensure_graph_connected(self):
        """Ensure knowledge graph is connected"""
        if self.knowledge_graph is None:
            self.knowledge_graph = await get_knowledge_graph()

    def _init_openai_llm(self, model_name: Optional[str] = None):
        """Initialize OpenAI LLM"""
        return ChatOpenAI(
            model=model_name or settings.OPENAI_MODEL,
            temperature=self.temperature,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=True,
        )

    def _init_anthropic_llm(self, model_name: Optional[str] = None):
        """Initialize Anthropic Claude LLM"""
        return ChatAnthropic(
            model=model_name or settings.ANTHROPIC_MODEL,
            temperature=self.temperature,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            streaming=True,
        )

    def _init_vector_store(self) -> Chroma:
        """Initialize ChromaDB vector store for RAG"""
        persist_directory = str(Path(settings.DATA_DIR) / "chroma_db")

        vector_store = Chroma(
            collection_name="wellness_knowledge",
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

        logger.info(f"Vector store initialized at {persist_directory}")
        return vector_store

    def _load_knowledge_base(self):
        """Load knowledge base documents into vector store"""
        # Check if already loaded
        if self.vector_store._collection.count() > 0:
            logger.info(f"Vector store already contains {self.vector_store._collection.count()} documents")
            return

        logger.info("Loading knowledge base into vector store...")

        documents = []

        # Load Ayurveda knowledge
        ayurveda_path = Path(settings.KB_DIR) / "ayurveda" / "doshas.json"
        if ayurveda_path.exists():
            with open(ayurveda_path) as f:
                ayurveda_data = json.load(f)

            for dosha_name, dosha_info in ayurveda_data.items():
                # Create document for each dosha
                doc_text = f"""
Ayurvedic Dosha: {dosha_name}

Characteristics: {', '.join(dosha_info.get('characteristics', []))}

Signs of Imbalance: {', '.join(dosha_info.get('imbalance_signs', []))}

Balancing Foods to Include: {', '.join(dosha_info.get('balancing_foods', []))}

Foods to Avoid: {', '.join(dosha_info.get('avoid_foods', []))}

Recommended Herbs: {json.dumps(dosha_info.get('herbs', []), indent=2)}

Lifestyle Recommendations: {', '.join(dosha_info.get('lifestyle', []))}
"""
                documents.append(
                    Document(
                        page_content=doc_text,
                        metadata={
                            "source": "ayurveda",
                            "dosha": dosha_name,
                            "type": "ayurvedic_knowledge"
                        }
                    )
                )

        # Load Supplement knowledge
        supplements_path = Path(settings.KB_DIR) / "supplements" / "supplements_db.json"
        if supplements_path.exists():
            with open(supplements_path) as f:
                supplements_data = json.load(f)

            for supplement_name, supp_info in supplements_data.items():
                # Create document for each supplement
                doc_text = f"""
Supplement: {supplement_name}

Benefits: {', '.join(supp_info.get('benefits', []))}

Mechanism: {supp_info.get('mechanism', 'Not specified')}

Dosage: {supp_info.get('dosage', {}).get('typical', 'Not specified')}

Contraindications: {', '.join(supp_info.get('contraindications', []))}

Drug Interactions: {', '.join(supp_info.get('drug_interactions', []))}

Evidence: {', '.join(supp_info.get('evidence', []))}
"""
                documents.append(
                    Document(
                        page_content=doc_text,
                        metadata={
                            "source": "supplements",
                            "supplement": supplement_name,
                            "type": "supplement_knowledge"
                        }
                    )
                )

        # Add documents to vector store
        if documents:
            self.vector_store.add_documents(documents)
            logger.info(f"Loaded {len(documents)} documents into vector store")
        else:
            logger.warning("No documents found to load into vector store")

    def _create_conversational_chain(self) -> ConversationalRetrievalChain:
        """Create the conversational retrieval chain"""

        # Custom prompt for wellness coaching
        system_template = """You are a compassionate and knowledgeable holistic wellness coach with expertise in:
- Modern health science and nutrition
- Ayurvedic medicine and principles
- Stress management and mental health
- Preventive healthcare and lifestyle optimization

Your role is to provide personalized, evidence-based guidance that integrates:
- Scientific research and clinical evidence
- Traditional wellness practices (Ayurveda, yoga, meditation)
- The user's unique health profile, goals, and preferences

Guidelines:
1. Always provide empathetic, encouraging responses
2. Base recommendations on evidence when possible, citing sources from the knowledge base
3. Consider the user's entire health context (physical, mental, lifestyle)
4. Suggest actionable, practical steps
5. Encourage professional medical consultation for serious concerns
6. Respect cultural and personal beliefs
7. Focus on prevention and holistic wellness

Use the following pieces of context to answer the user's question. If you don't know the answer, admit it honestly.

Context from knowledge base:
{context}

Previous conversation:
{chat_history}

Current question: {question}

Provide a thoughtful, personalized response:"""

        prompt = PromptTemplate(
            template=system_template,
            input_variables=["context", "chat_history", "question"]
        )

        # Create the chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=True,
        )

        return chain

    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent (for agentic behavior)"""

        # Tool to query user's health data
        def get_user_health_summary(user_id: str) -> str:
            """Get a summary of user's recent health metrics"""
            # This would query the database in production
            return f"User {user_id}: Recent stress levels elevated, sleep quality decreased in past week"

        # Tool to generate recommendations
        def generate_recommendation(context: str) -> str:
            """Generate a personalized recommendation based on context"""
            # This would use the recommendation engine in production
            return f"Recommendation: {context}"

        # Tool to schedule a guided session
        def schedule_session(session_type: str) -> str:
            """Schedule a guided wellness session"""
            return f"Scheduled {session_type} session"

        tools = [
            Tool(
                name="GetUserHealth",
                func=get_user_health_summary,
                description="Get user's recent health metrics and trends. Input should be user_id."
            ),
            Tool(
                name="GenerateRecommendation",
                func=generate_recommendation,
                description="Generate a personalized wellness recommendation. Input should be the context/reason."
            ),
            Tool(
                name="ScheduleSession",
                func=schedule_session,
                description="Schedule a guided wellness session (breathing, meditation, etc.). Input should be session type."
            ),
        ]

        return tools

    async def chat(
        self,
        user_message: str,
        user_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response

        Args:
            user_message: The user's message/question
            user_id: Optional user ID for personalization
            user_context: Optional additional context (recent health data, goals, etc.)

        Returns:
            Dictionary with response, sources, and metadata
        """
        try:
            # Add user context to the question if provided
            enhanced_question = user_message
            if user_context:
                context_str = f"\nUser Context: {json.dumps(user_context, indent=2)}\n"
                enhanced_question = context_str + user_message

            # Run the chain
            with get_openai_callback() as cb:
                result = await self.chain.acall({"question": enhanced_question})

                response = {
                    "answer": result["answer"],
                    "sources": [
                        {
                            "content": doc.page_content[:200] + "...",
                            "metadata": doc.metadata,
                        }
                        for doc in result.get("source_documents", [])
                    ],
                    "metadata": {
                        "tokens_used": cb.total_tokens,
                        "cost": cb.total_cost,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                }

            logger.info(f"Generated response for user {user_id}: {cb.total_tokens} tokens used")
            return response

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "answer": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "sources": [],
                "metadata": {"error": str(e)}
            }

    async def get_proactive_recommendations(
        self,
        user_id: str,
        user_health_data: Dict[str, Any],
    ) -> List[str]:
        """
        Generate proactive recommendations based on user's health patterns
        (Agentic behavior)

        Args:
            user_id: User ID
            user_health_data: User's recent health metrics and trends

        Returns:
            List of proactive recommendations
        """
        prompt = f"""Based on the following user health data, generate 2-3 proactive wellness recommendations:

{json.dumps(user_health_data, indent=2)}

Focus on actionable suggestions that address concerning trends or optimize wellness.
Format as a numbered list."""

        try:
            response = await self.llm.apredict(prompt)
            recommendations = [
                line.strip()
                for line in response.split("\n")
                if line.strip() and any(line.startswith(str(i)) for i in range(1, 10))
            ]
            return recommendations
        except Exception as e:
            logger.error(f"Error generating proactive recommendations: {e}")
            return []

    async def get_graph_enhanced_recommendations(
        self,
        user_id: str,
        symptoms: List[str],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get recommendations enhanced with GraphRAG reasoning

        Uses knowledge graph to find interventions and explanation paths
        """
        await self._ensure_graph_connected()

        # Find interventions using graph traversal
        interventions = await self.knowledge_graph.find_interventions_for_symptoms(
            symptoms=symptoms,
            user_dosha=user_context.get("ayurvedic_dosha"),
            limit=5
        )

        # Get explanation paths for top interventions
        explanations = []
        for intervention in interventions[:3]:
            for symptom in symptoms[:2]:  # Top 2 symptoms
                path = await self.knowledge_graph.get_explanation_path(
                    symptom=symptom,
                    intervention=intervention["name"]
                )
                if path:
                    explanations.append({
                        "symptom": symptom,
                        "intervention": intervention["name"],
                        "path": path
                    })

        # Format for LLM context
        graph_context = {
            "interventions": interventions,
            "explanations": explanations,
            "reasoning": f"Found {len(interventions)} interventions through knowledge graph traversal"
        }

        return graph_context

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")

    def save_conversation(self, user_id: str, filepath: str):
        """Save conversation history to file"""
        try:
            history = self.memory.load_memory_variables({})
            with open(filepath, 'w') as f:
                json.dump(history, f, indent=2, default=str)
            logger.info(f"Conversation saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    def load_conversation(self, filepath: str):
        """Load conversation history from file"""
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            # Reconstruct memory
            # This is simplified - in production, properly reconstruct message objects
            logger.info(f"Conversation loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")


# Singleton instance
_coach_instance: Optional[WellnessCoach] = None


def get_wellness_coach() -> WellnessCoach:
    """Get or create the wellness coach singleton instance"""
    global _coach_instance
    if _coach_instance is None:
        _coach_instance = WellnessCoach()
    return _coach_instance
