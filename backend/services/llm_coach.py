"""
AI Wellness Coach Service

Implements LangChain-based conversational AI with:
- RAG (Retrieval Augmented Generation)
- Long-term memory
- Context-aware responses
- Knowledge base integration
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.tools import tool
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from backend.models.postgres_models import User, HealthMetric, EEGAnalysis, Recommendation
from backend.database.mongo import get_mongo_db
from backend.database.postgres import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WellnessCoach:
    """
    AI Wellness Coach with memory, context awareness, and knowledge base
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.db = get_mongo_db()

        # Initialize LLM
        if settings.USE_LOCAL_LLM:
            # Use HuggingFace local model
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            from langchain.llms import HuggingFacePipeline

            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    settings.LOCAL_LLM_MODEL,
                    cache_dir=settings.MODEL_CACHE_DIR
                )
                model = AutoModelForCausalLM.from_pretrained(
                    settings.LOCAL_LLM_MODEL,
                    cache_dir=settings.MODEL_CACHE_DIR,
                    device_map="auto",
                    load_in_4bit=settings.USE_QUANTIZATION if settings.QUANTIZATION_BITS == 4 else False
                )

                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.95,
                )

                self.llm = HuggingFacePipeline(pipeline=pipe)
                logger.info(f"Loaded local LLM: {settings.LOCAL_LLM_MODEL}")

            except Exception as e:
                logger.error(f"Failed to load local LLM: {e}")
                logger.info("Falling back to OpenAI API")
                self.llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY or "sk-dummy-key-for-testing",
                    temperature=0.7
                )
        else:
            # Use OpenAI API
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY or "sk-dummy-key-for-testing",
                temperature=0.7
            )

        # Initialize embeddings
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=settings.MODEL_CACHE_DIR
            )

        # Initialize vector store for RAG
        self.vector_store = self._init_vector_store()

        # System prompt
        self.system_prompt = """You are a compassionate AI wellness coach specializing in holistic health.
You combine modern science with traditional wisdom (Ayurveda, yoga) to provide personalized guidance.

Your goals:
- Help users manage stress, improve sleep, and optimize mental/physical health
- Provide evidence-based recommendations for diet, supplements, and lifestyle
- Be empathetic, encouraging, and non-judgmental
- Cite sources when making claims
- Always remind users to consult healthcare professionals for medical decisions

You have access to:
- User's health data (EEG, heart rate, sleep, etc.)
- Wellness knowledge base (nutrition, supplements, Ayurveda)
- Conversation history

When responding:
1. Consider the user's context (dosha type, health goals, current state)
2. Provide actionable, specific advice
3. Explain the reasoning behind recommendations
4. Cite evidence from the knowledge base
5. Ask clarifying questions when needed
"""

    def _init_vector_store(self) -> Chroma:
        """Initialize or load vector store for RAG"""
        try:
            # Try to load existing vector store
            vector_store = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name="wellness_knowledge"
            )

            # Check if it has documents
            if vector_store._collection.count() == 0:
                # Populate with knowledge base
                self._populate_knowledge_base(vector_store)

            return vector_store

        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            # Create new vector store
            vector_store = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name="wellness_knowledge"
            )
            self._populate_knowledge_base(vector_store)
            return vector_store

    def _populate_knowledge_base(self, vector_store: Chroma):
        """Populate vector store with knowledge base documents"""
        import json
        from langchain.schema import Document

        documents = []

        # Load Ayurveda doshas
        try:
            with open("knowledge_base/ayurveda/doshas.json", "r") as f:
                doshas = json.load(f)

            for dosha_name, dosha_info in doshas.items():
                content = f"Ayurvedic Dosha: {dosha_name}\n\n"
                content += f"Description: {dosha_info.get('description', '')}\n\n"

                if "characteristics" in dosha_info:
                    content += "Characteristics:\n"
                    chars = dosha_info["characteristics"]
                    content += f"Physical: {', '.join(chars.get('physical', []))}\n"
                    content += f"Mental: {', '.join(chars.get('mental', []))}\n\n"

                if "balancing_foods" in dosha_info:
                    content += f"Balancing Foods: {', '.join(dosha_info['balancing_foods'])}\n\n"

                if "recommended_herbs" in dosha_info:
                    content += "Recommended Herbs:\n"
                    for herb in dosha_info["recommended_herbs"]:
                        content += f"- {herb.get('name', '')}: {herb.get('properties', '')}\n"

                documents.append(Document(
                    page_content=content,
                    metadata={"source": "ayurveda", "dosha": dosha_name}
                ))

        except Exception as e:
            logger.error(f"Error loading doshas: {e}")

        # Load supplements
        try:
            with open("knowledge_base/supplements/supplements_db.json", "r") as f:
                supp_data = json.load(f)

            for supp in supp_data.get("supplements", []):
                content = f"Supplement: {supp.get('name', '')}\n\n"
                content += f"Category: {supp.get('category', '')}\n\n"
                content += f"Description: {supp.get('description', '')}\n\n"

                content += f"Benefits: {', '.join(supp.get('benefits', []))}\n\n"

                if "dosage" in supp:
                    dosage = supp["dosage"]
                    content += f"Typical Dosage: {dosage.get('typical', '')}\n"
                    content += f"Range: {dosage.get('range', '')}\n"
                    content += f"Timing: {dosage.get('timing', '')}\n\n"

                if "contraindications" in supp:
                    content += f"Contraindications: {', '.join(supp['contraindications'])}\n\n"

                if "evidence" in supp:
                    content += "Scientific Evidence:\n"
                    for ev in supp["evidence"]:
                        content += f"- {ev.get('claim', '')}: {ev.get('source', '')}\n"

                documents.append(Document(
                    page_content=content,
                    metadata={"source": "supplements", "name": supp.get("name", "")}
                ))

        except Exception as e:
            logger.error(f"Error loading supplements: {e}")

        # Add documents to vector store
        if documents:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            split_docs = text_splitter.split_documents(documents)
            vector_store.add_documents(split_docs)
            vector_store.persist()
            logger.info(f"Added {len(split_docs)} documents to vector store")

    async def get_user_context(self) -> Dict[str, Any]:
        """Retrieve comprehensive user context"""
        context = {}

        async with AsyncSessionLocal() as session:
            # Get user profile
            result = await session.execute(
                select(User).where(User.id == self.user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                context["user"] = {
                    "name": user.name,
                    "age": user.age,
                    "dosha": user.dosha_type.value if user.dosha_type else None,
                    "health_goals": user.health_goals,
                    "dietary_restrictions": user.dietary_restrictions,
                    "medical_conditions": user.medical_conditions
                }

            # Get recent health metrics (last 7 days)
            week_ago = datetime.now().date() - timedelta(days=7)
            result = await session.execute(
                select(HealthMetric)
                .where(and_(
                    HealthMetric.user_id == self.user_id,
                    HealthMetric.date >= week_ago
                ))
                .order_by(HealthMetric.date.desc())
                .limit(7)
            )
            metrics = result.scalars().all()

            if metrics:
                context["recent_health"] = {
                    "avg_sleep": sum(m.sleep_hours or 0 for m in metrics) / len(metrics),
                    "avg_stress": sum(m.stress_level or 0 for m in metrics) / len(metrics),
                    "avg_steps": sum(m.steps or 0 for m in metrics) / len(metrics),
                    "latest_date": str(metrics[0].date)
                }

            # Get latest EEG analysis
            result = await session.execute(
                select(EEGAnalysis)
                .where(EEGAnalysis.user_id == self.user_id)
                .order_by(EEGAnalysis.timestamp.desc())
                .limit(1)
            )
            eeg = result.scalar_one_or_none()

            if eeg:
                context["latest_eeg"] = {
                    "mental_state": eeg.mental_state.value,
                    "stress_level": eeg.stress_level,
                    "focus_level": eeg.focus_level,
                    "timestamp": str(eeg.timestamp)
                }

            # Get active recommendations
            result = await session.execute(
                select(Recommendation)
                .where(and_(
                    Recommendation.user_id == self.user_id,
                    Recommendation.completed == False
                ))
                .order_by(Recommendation.created_at.desc())
                .limit(3)
            )
            recommendations = result.scalars().all()

            if recommendations:
                context["active_recommendations"] = [
                    {"category": r.category, "title": r.title}
                    for r in recommendations
                ]

        # Get user context from MongoDB
        user_ctx = await self.db.user_context.find_one({"user_id": self.user_id})
        if user_ctx:
            context["patterns"] = user_ctx.get("patterns", {})
            context["preferred_interventions"] = user_ctx.get("preferred_interventions", [])

        return context

    async def chat(
        self,
        message: str,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with the wellness coach

        Returns:
            Dict with keys: message, context_used, recommendations, sources
        """
        try:
            # Get user context
            context = await self.get_user_context() if include_context else {}

            # Retrieve relevant knowledge from vector store
            relevant_docs = self.vector_store.similarity_search(
                message,
                k=3
            )

            # Build context string
            context_str = "User Context:\n"
            if "user" in context:
                user_info = context["user"]
                context_str += f"- Name: {user_info.get('name')}\n"
                context_str += f"- Dosha Type: {user_info.get('dosha')}\n"
                context_str += f"- Health Goals: {', '.join(user_info.get('health_goals', []))}\n"

            if "recent_health" in context:
                health = context["recent_health"]
                context_str += f"\nRecent Health (past week):\n"
                context_str += f"- Average Sleep: {health.get('avg_sleep', 0):.1f} hours\n"
                context_str += f"- Average Stress: {health.get('avg_stress', 0):.1%}\n"
                context_str += f"- Average Steps: {health.get('avg_steps', 0):.0f}\n"

            if "latest_eeg" in context:
                eeg = context["latest_eeg"]
                context_str += f"\nLatest Brain Activity:\n"
                context_str += f"- Mental State: {eeg.get('mental_state')}\n"
                context_str += f"- Stress: {eeg.get('stress_level', 0):.1%}\n"
                context_str += f"- Focus: {eeg.get('focus_level', 0):.1%}\n"

            # Add retrieved knowledge
            knowledge_str = "\n\nRelevant Knowledge:\n"
            for i, doc in enumerate(relevant_docs, 1):
                knowledge_str += f"\n{i}. {doc.page_content[:300]}...\n"

            # Get conversation history
            history = await self._get_chat_history(limit=5)

            # Build messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context_str + knowledge_str),
            ]

            # Add conversation history
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            # Add current message
            messages.append(HumanMessage(content=message))

            # Generate response
            response = await self.llm.agenerate([messages])
            assistant_message = response.generations[0][0].text

            # Save conversation to MongoDB
            await self._save_message("user", message)
            await self._save_message("assistant", assistant_message, context_used=[
                f"Dosha: {context.get('user', {}).get('dosha')}",
                f"Recent sleep: {context.get('recent_health', {}).get('avg_sleep', 0):.1f}h"
            ])

            # Extract any recommendations from the response
            recommendations = self._extract_recommendations(assistant_message)

            # Extract sources
            sources = [doc.metadata.get("source", "knowledge_base") for doc in relevant_docs]

            return {
                "message": assistant_message,
                "context_used": [
                    f"User profile (dosha: {context.get('user', {}).get('dosha')})",
                    f"Recent health data ({len(context.get('recent_health', {}))} days)",
                    f"Knowledge base ({len(relevant_docs)} relevant articles)"
                ],
                "recommendations": recommendations,
                "sources": list(set(sources))
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request. Please try again.",
                "context_used": [],
                "recommendations": [],
                "sources": []
            }

    async def _get_chat_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent chat history from MongoDB"""
        cursor = self.db.chat_messages.find(
            {"user_id": self.user_id}
        ).sort("timestamp", -1).limit(limit)

        messages = []
        async for msg in cursor:
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content")
            })

        return list(reversed(messages))

    async def _save_message(
        self,
        role: str,
        content: str,
        context_used: Optional[List[str]] = None
    ):
        """Save message to MongoDB"""
        message = {
            "user_id": self.user_id,
            "timestamp": datetime.now(),
            "role": role,
            "content": content,
            "context_used": context_used or [],
            "sources": [],
            "created_at": datetime.now()
        }

        await self.db.chat_messages.insert_one(message)

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from AI response"""
        # Simple extraction - look for numbered lists or bullet points
        recommendations = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Look for numbered items (1., 2., etc.) or bullet points (-, *, etc.)
            if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '-', '*', '•']):
                # Clean up the line
                for prefix in ['1.', '2.', '3.', '-', '*', '•']:
                    line = line.replace(prefix, '', 1).strip()
                if line and len(line) > 10:  # Only meaningful recommendations
                    recommendations.append(line)

        return recommendations[:5]  # Max 5 recommendations


# Global coach instances cache
_coach_cache: Dict[str, WellnessCoach] = {}


def get_wellness_coach(user_id: str) -> WellnessCoach:
    """Get or create wellness coach instance for user"""
    if user_id not in _coach_cache:
        _coach_cache[user_id] = WellnessCoach(user_id)
    return _coach_cache[user_id]
