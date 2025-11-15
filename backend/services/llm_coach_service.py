"""
LLM Wellness Coach Service with RAG and Long-term Memory

Implements a conversational AI wellness coach using:
- LangChain for orchestration
- RAG (Retrieval Augmented Generation) for knowledge retrieval
- Vector database (ChromaDB) for long-term memory
- Knowledge base (Ayurveda, supplements, wellness practices)
"""
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_openai_functions_agent, Tool
from langchain.schema import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.postgres_models import Recommendation, Priority
from backend.models.mongo_schemas import ChatMessage, UserContext, COLLECTION_CHAT_MESSAGES, COLLECTION_USER_CONTEXT
from backend.database.mongo import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)


class WellnessCoachService:
    """AI Wellness Coach with RAG and memory"""

    def __init__(self):
        """Initialize the wellness coach"""
        self.knowledge_base_path = "/home/user/Wellnessapp/knowledge_base"
        self.vector_store_path = "/home/user/Wellnessapp/data/vector_store"

        # Use local embeddings for privacy
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize or load vector store
        self.vector_store = self._initialize_vector_store()

        # Initialize LLM (use OpenAI or local model)
        self.llm = self._initialize_llm()

        # Create wellness coach system prompt
        self.system_prompt = self._create_system_prompt()

    def _initialize_llm(self):
        """Initialize the LLM - use OpenAI or local model"""
        try:
            if os.getenv("OPENAI_API_KEY"):
                return ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_tokens=500
                )
            else:
                # Use local model (Hugging Face)
                from langchain.llms import HuggingFacePipeline
                from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

                logger.info("Using local Hugging Face model for LLM")
                model_id = "microsoft/DialoGPT-medium"  # Small conversational model
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForCausalLM.from_pretrained(model_id)

                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=256,
                    temperature=0.7
                )

                return HuggingFacePipeline(pipeline=pipe)
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            # Fallback to mock for development
            return None

    def _initialize_vector_store(self):
        """Initialize or load vector store with knowledge base"""
        os.makedirs(self.vector_store_path, exist_ok=True)

        try:
            # Try to load existing vector store
            vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )

            # Check if it has data
            if vector_store._collection.count() > 0:
                logger.info(f"Loaded existing vector store with {vector_store._collection.count()} documents")
                return vector_store
        except:
            pass

        # Create new vector store and populate with knowledge base
        logger.info("Creating new vector store and indexing knowledge base...")
        documents = self._load_knowledge_base()

        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.vector_store_path
        )
        vector_store.persist()

        logger.info(f"Created vector store with {len(documents)} documents")
        return vector_store

    def _load_knowledge_base(self) -> List[Document]:
        """Load and prepare knowledge base documents"""
        documents = []

        # Load supplements database
        supplements_path = os.path.join(self.knowledge_base_path, "supplements", "supplements_db.json")
        if os.path.exists(supplements_path):
            with open(supplements_path, 'r') as f:
                supplements = json.load(f)
                for supp_id, supp_data in supplements.items():
                    content = f"Supplement: {supp_data['name']}\n"
                    content += f"Category: {supp_data.get('category', 'Unknown')}\n"
                    content += f"Benefits: {', '.join(supp_data.get('benefits', []))}\n"
                    content += f"Description: {supp_data.get('description', '')}\n"
                    if 'dosage' in supp_data:
                        content += f"Typical Dosage: {supp_data['dosage']}\n"
                    if 'warnings' in supp_data:
                        content += f"Warnings: {', '.join(supp_data.get('warnings', []))}\n"

                    documents.append(Document(
                        page_content=content,
                        metadata={"source": "supplements", "id": supp_id, "name": supp_data['name']}
                    ))

        # Load Ayurveda doshas
        doshas_path = os.path.join(self.knowledge_base_path, "ayurveda", "doshas.json")
        if os.path.exists(doshas_path):
            with open(doshas_path, 'r') as f:
                doshas = json.load(f)
                for dosha_name, dosha_data in doshas.items():
                    content = f"Ayurvedic Dosha: {dosha_name}\n"
                    content += f"Characteristics: {', '.join(dosha_data.get('characteristics', []))}\n"
                    content += f"Balanced State: {dosha_data.get('balanced', '')}\n"
                    content += f"Imbalanced State: {dosha_data.get('imbalanced', '')}\n"
                    content += f"Balancing Foods: {', '.join(dosha_data.get('balancing_foods', []))}\n"
                    content += f"Lifestyle Recommendations: {', '.join(dosha_data.get('lifestyle', []))}\n"

                    documents.append(Document(
                        page_content=content,
                        metadata={"source": "ayurveda", "dosha": dosha_name}
                    ))

        # Load general wellness practices
        practices_path = os.path.join(self.knowledge_base_path, "practices")
        if os.path.exists(practices_path):
            for filename in os.listdir(practices_path):
                if filename.endswith('.txt') or filename.endswith('.md'):
                    with open(os.path.join(practices_path, filename), 'r') as f:
                        content = f.read()
                        documents.append(Document(
                            page_content=content,
                            metadata={"source": "practices", "file": filename}
                        ))

        return documents

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the wellness coach"""
        return """You are an empathetic and knowledgeable AI wellness coach specializing in holistic health.

Your role is to:
- Provide personalized wellness guidance based on the user's health data (EEG, sleep, activity, etc.)
- Recommend evidence-based interventions from nutrition, supplements, Ayurveda, and lifestyle practices
- Be supportive, encouraging, and non-judgmental
- Always cite sources and explain your reasoning
- Suggest actionable steps the user can take
- Recognize when professional medical help may be needed

When analyzing the user's data:
- Consider patterns and correlations (e.g., stress vs sleep)
- Provide context-aware recommendations
- Remember previous conversations and track progress
- Be proactive in checking in on the user's goals

Always prioritize user safety and well-being. If you detect serious mental or physical health concerns, encourage seeking professional help."""

    async def chat(
        self,
        db: AsyncSession,
        user_id: str,
        message: str,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with the wellness coach

        Args:
            db: Database session
            user_id: User ID
            message: User's message
            include_context: Whether to retrieve user context and health data

        Returns:
            Coach's response with context and recommendations
        """
        try:
            # Store user message
            await self._store_message(user_id, "user", message)

            # Get conversation history
            history = await self._get_recent_history(user_id, limit=10)

            # Build context if requested
            context_docs = []
            context_summary = []

            if include_context:
                # Get user's recent health data
                user_context = await self._get_user_context(db, user_id)
                if user_context:
                    context_summary.extend(user_context['summary'])
                    context_docs.append(Document(
                        page_content=user_context['text'],
                        metadata={"source": "user_health_data"}
                    ))

                # Retrieve relevant knowledge from vector store
                knowledge_docs = self.vector_store.similarity_search(message, k=3)
                context_docs.extend(knowledge_docs)
                context_summary.extend([f"Knowledge: {doc.metadata.get('source', 'unknown')}" for doc in knowledge_docs])

            # Generate response using LLM
            if self.llm is None:
                # Fallback mock response for development
                response_text = self._generate_mock_response(message, context_summary)
            else:
                response_text = await self._generate_llm_response(
                    message,
                    history,
                    context_docs
                )

            # Extract recommendations from response
            recommendations = self._extract_recommendations(response_text)

            # Store assistant message
            await self._store_message(
                user_id,
                "assistant",
                response_text,
                context_used=context_summary
            )

            # Store recommendations in database if any
            if recommendations:
                await self._store_recommendations(db, user_id, recommendations)

            return {
                "message": response_text,
                "context_used": context_summary,
                "recommendations": recommendations,
                "sources": [doc.metadata.get('source') for doc in context_docs if 'source' in doc.metadata]
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "message": "I apologize, I'm having trouble processing your request right now. Please try again.",
                "context_used": [],
                "recommendations": [],
                "sources": []
            }

    async def _get_user_context(self, db: AsyncSession, user_id: str) -> Optional[Dict]:
        """Get user's health context for the conversation"""
        from backend.models.postgres_models import HealthMetric, EEGAnalysis, User
        from datetime import date, timedelta

        context = {
            "summary": [],
            "text": "User Context:\n"
        }

        # Get user profile
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            context["text"] += f"Name: {user.name}\n"
            if user.dosha_type:
                context["text"] += f"Ayurvedic Dosha: {user.dosha_type.value}\n"
                context["summary"].append(f"Dosha: {user.dosha_type.value}")
            if user.health_goals:
                context["text"] += f"Health Goals: {', '.join(user.health_goals)}\n"
                context["summary"].append("User health goals")

        # Get recent health metrics
        week_ago = date.today() - timedelta(days=7)
        stmt = select(HealthMetric).where(
            HealthMetric.user_id == user_id,
            HealthMetric.date >= week_ago
        ).order_by(HealthMetric.date.desc()).limit(7)
        result = await db.execute(stmt)
        metrics = list(result.scalars().all())

        if metrics:
            recent = metrics[0]
            context["text"] += f"\nRecent Health Data (last 7 days):\n"
            if recent.sleep_hours:
                avg_sleep = sum(m.sleep_hours for m in metrics if m.sleep_hours) / len([m for m in metrics if m.sleep_hours])
                context["text"] += f"Average Sleep: {avg_sleep:.1f} hours\n"
                context["summary"].append(f"Sleep: {avg_sleep:.1f}h avg")
            if recent.stress_level:
                context["text"] += f"Stress Level: {recent.stress_level:.2f}\n"
                context["summary"].append(f"Stress: {recent.stress_level:.2f}")

        # Get recent EEG analysis
        cutoff = datetime.now() - timedelta(hours=24)
        stmt = select(EEGAnalysis).where(
            EEGAnalysis.user_id == user_id,
            EEGAnalysis.timestamp >= cutoff
        ).order_by(EEGAnalysis.timestamp.desc()).limit(3)
        result = await db.execute(stmt)
        eeg_analyses = list(result.scalars().all())

        if eeg_analyses:
            latest = eeg_analyses[0]
            context["text"] += f"\nLatest EEG Analysis:\n"
            context["text"] += f"Mental State: {latest.mental_state.value}\n"
            context["text"] += f"Stress: {latest.stress_level:.2f}, Focus: {latest.focus_level:.2f}\n"
            context["summary"].append(f"EEG: {latest.mental_state.value}")

        return context if context["summary"] else None

    async def _generate_llm_response(
        self,
        message: str,
        history: List[Dict],
        context_docs: List[Document]
    ) -> str:
        """Generate response using LLM with context"""
        # Build context string
        context_str = "\n\n".join([doc.page_content for doc in context_docs])

        # Build conversation history
        history_str = "\n".join([
            f"{'User' if h['role'] == 'user' else 'Coach'}: {h['content']}"
            for h in history[-6:]  # Last 3 exchanges
        ])

        # Create prompt
        prompt = f"""{self.system_prompt}

Context Information:
{context_str}

Conversation History:
{history_str}

User: {message}

Coach:"""

        # Generate response
        response = self.llm(prompt)
        return response.strip()

    def _generate_mock_response(self, message: str, context: List[str]) -> str:
        """Generate mock response for development (when LLM not available)"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['stress', 'anxious', 'worried', 'anxiety']):
            return ("I understand you're feeling stressed. Based on your recent data, I can see your stress levels have been elevated. "
                   "I recommend trying a 10-minute breathing exercise to activate your parasympathetic nervous system. "
                   "Additionally, magnesium-rich foods like nuts and leafy greens can help promote relaxation. "
                   "Consider practicing meditation for 5-10 minutes before bed to improve sleep quality. "
                   "Would you like me to guide you through a breathing exercise now?")

        elif any(word in message_lower for word in ['sleep', 'tired', 'fatigue', 'energy']):
            return ("Sleep and energy are closely connected. Based on your health data, I notice you might benefit from improving your sleep hygiene. "
                   "Try maintaining a consistent sleep schedule, avoiding screens 1 hour before bed, and keeping your bedroom cool and dark. "
                   "Consider supplements like magnesium or melatonin (consult your doctor first). "
                   "Regular exercise during the day can also improve sleep quality. "
                   "Would you like me to create a personalized sleep improvement plan?")

        elif any(word in message_lower for word in ['focus', 'concentration', 'distract']):
            return ("For better focus and concentration, try the Pomodoro Technique: work in 25-minute focused sessions with 5-minute breaks. "
                   "Your EEG data suggests you might benefit from practices that promote alpha wave activity, such as mindfulness meditation. "
                   "Consider L-theanine (found in green tea) which can enhance focus without jitters. "
                   "Ensure you're getting adequate sleep and staying hydrated. "
                   "Would you like specific techniques to improve your concentration?")

        else:
            return (f"Thank you for sharing that with me. Based on your health data ({', '.join(context) if context else 'no recent data'}), "
                   f"I'm here to support your wellness journey. Could you tell me more about what specific aspect of your health "
                   f"you'd like to focus on today? I can help with stress management, sleep improvement, nutrition, exercise, or mental wellness.")

    def _extract_recommendations(self, response_text: str) -> List[str]:
        """Extract actionable recommendations from the response"""
        recommendations = []

        # Simple extraction - look for recommendation keywords
        lines = response_text.split('.')
        keywords = ['recommend', 'suggest', 'try', 'consider', 'should', 'would help', 'beneficial']

        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                recommendation = line.strip()
                if len(recommendation) > 20:  # Avoid too short fragments
                    recommendations.append(recommendation)

        return recommendations[:5]  # Limit to 5 recommendations

    async def _store_message(
        self,
        user_id: str,
        role: str,
        content: str,
        context_used: Optional[List[str]] = None
    ):
        """Store chat message in MongoDB"""
        collection = get_collection(COLLECTION_CHAT_MESSAGES)

        message_doc = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "role": role,
            "content": content,
            "context_used": context_used,
            "created_at": datetime.now()
        }

        await collection.insert_one(message_doc)

    async def _get_recent_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent chat history"""
        collection = get_collection(COLLECTION_CHAT_MESSAGES)

        cursor = collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        messages = await cursor.to_list(length=limit)
        messages.reverse()  # Chronological order

        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

    async def _store_recommendations(
        self,
        db: AsyncSession,
        user_id: str,
        recommendations: List[str]
    ):
        """Store recommendations in PostgreSQL"""
        for rec_text in recommendations:
            # Determine category from text
            category = "lifestyle"
            if any(word in rec_text.lower() for word in ['eat', 'food', 'diet', 'nutrition']):
                category = "diet"
            elif any(word in rec_text.lower() for word in ['supplement', 'vitamin', 'magnesium']):
                category = "supplement"
            elif any(word in rec_text.lower() for word in ['exercise', 'walk', 'yoga']):
                category = "exercise"
            elif any(word in rec_text.lower() for word in ['sleep', 'rest']):
                category = "sleep"
            elif any(word in rec_text.lower() for word in ['stress', 'anxiety', 'meditat']):
                category = "stress"

            recommendation = Recommendation(
                user_id=user_id,
                category=category,
                title=rec_text[:100],  # First 100 chars as title
                description=rec_text,
                reasoning="Generated by AI wellness coach based on your health data",
                priority=Priority.MEDIUM
            )

            db.add(recommendation)

        await db.commit()
