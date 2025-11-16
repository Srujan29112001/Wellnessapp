"""
AI Wellness Coach Service

Implements the LLM-based conversational AI coach with RAG and GraphRAG
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import os

# LangChain imports
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.tools import BaseTool

from backend.database.mongo import get_collection
from backend.models.mongo_schemas import COLLECTION_CHAT_MESSAGES, ChatMessage
from backend.services.user_service import UserService
from backend.services.health_service import HealthService

logger = logging.getLogger(__name__)


class WellnessCoachService:
    """AI Wellness Coach with LLM, RAG, and long-term memory"""

    def __init__(self):
        """Initialize the wellness coach"""
        # Use local HuggingFace embeddings for privacy (or OpenAI if API key available)
        use_openai = os.getenv("OPENAI_API_KEY") is not None

        if use_openai:
            self.embeddings = OpenAIEmbeddings()
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=500
            )
        else:
            # Use local models for privacy
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            # For local LLM, you could use HuggingFacePipeline or Ollama
            # For now, we'll use a mock for demonstration
            self.llm = None  # Would integrate Ollama/LocalLLM here

        self.knowledge_base = None
        self._init_knowledge_base()

    def _init_knowledge_base(self):
        """Initialize vector store with wellness knowledge"""
        try:
            # Load knowledge base documents
            kb_path = "/home/user/Wellnessapp/knowledge_base"

            docs = []

            # Load Ayurveda knowledge
            ayurveda_file = os.path.join(kb_path, "ayurveda/ayurveda_doshas.json")
            if os.path.exists(ayurveda_file):
                with open(ayurveda_file, 'r') as f:
                    ayurveda_data = json.load(f)
                    for dosha, data in ayurveda_data.items():
                        docs.append(f"Dosha: {dosha}\nCharacteristics: {data.get('characteristics', '')}\n")
                        docs.append(f"Foods for {dosha}: {', '.join(data.get('foods', []))}\n")
                        docs.append(f"Herbs for {dosha}: {', '.join(data.get('herbs', []))}\n")

            # Load supplements knowledge
            supps_file = os.path.join(kb_path, "supplements/supplements_db.json")
            if os.path.exists(supps_file):
                with open(supps_file, 'r') as f:
                    supps_data = json.load(f)
                    for supp_id, supp in supps_data.items():
                        name = supp.get('name', '')
                        benefits = ', '.join(supp.get('benefits', []))
                        dosage = supp.get('typical_dosage', '')
                        docs.append(f"Supplement: {name}\nBenefits: {benefits}\nDosage: {dosage}\n")

            # Add general wellness knowledge
            docs.extend([
                "Stress Management: High beta wave activity in EEG indicates stress. Recommend breathing exercises, meditation, or ashwagandha supplement.",
                "Sleep Quality: Poor sleep correlates with higher stress. Recommend magnesium supplements, reducing screen time before bed, and consistent sleep schedule.",
                "Focus Enhancement: Alpha waves indicate relaxation. L-theanine and caffeine combination can improve focus. Meditation increases alpha waves.",
                "Exercise Benefits: Regular physical activity reduces stress hormones, improves sleep quality, and enhances mood through endorphin release.",
                "Nutrition for Mental Health: Omega-3 fatty acids, B vitamins, vitamin D, and magnesium are crucial for brain health and mood regulation.",
                "Mindfulness Practice: Daily meditation for 10-15 minutes can reduce anxiety, improve focus, and enhance overall well-being."
            ])

            if not docs:
                logger.warning("No knowledge base documents loaded")
                return

            # Create vector store
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = text_splitter.create_documents(docs)

            # Initialize ChromaDB
            self.knowledge_base = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory="/home/user/Wellnessapp/data/chroma_db"
            )

            logger.info(f"Knowledge base initialized with {len(docs)} documents")

        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
            self.knowledge_base = None

    async def chat(
        self,
        user_id: str,
        message: str,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Process a chat message from the user

        Args:
            user_id: User ID
            message: User's message
            db_session: Database session for retrieving user data

        Returns:
            Response dictionary with AI reply, sources, and metadata
        """
        try:
            # Store user message
            await self._store_message(user_id, "user", message)

            # Get user context and recent history
            context = await self._get_user_context(user_id, db_session)
            chat_history = await self._get_chat_history(user_id, limit=10)

            # Retrieve relevant knowledge
            relevant_knowledge = []
            if self.knowledge_base:
                results = self.knowledge_base.similarity_search(message, k=3)
                relevant_knowledge = [doc.page_content for doc in results]

            # Generate response
            response = await self._generate_response(
                user_id=user_id,
                message=message,
                context=context,
                chat_history=chat_history,
                relevant_knowledge=relevant_knowledge
            )

            # Store AI response
            await self._store_message(
                user_id,
                "assistant",
                response["content"],
                context_used=response.get("context_used", []),
                sources=response.get("sources", [])
            )

            return response

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "content": "I apologize, but I encountered an error. Please try again or rephrase your question.",
                "sources": [],
                "error": str(e)
            }

    async def _get_user_context(self, user_id: str, db_session) -> Dict[str, Any]:
        """
        Gather comprehensive user context for personalized responses

        Includes: recent health data, EEG analysis, user profile, etc.
        """
        context = {
            "user_profile": {},
            "recent_health": {},
            "recent_eeg": {},
            "goals": [],
            "preferences": {}
        }

        try:
            # Get user context from MongoDB
            user_context = await UserService.get_user_context(user_id)
            if user_context:
                context["goals"] = user_context.get("active_goals", [])
                context["preferences"] = user_context.get("preferred_interventions", [])
                context["patterns"] = user_context.get("patterns", {})

            # Get recent health metrics (if db_session available)
            if db_session:
                from datetime import date
                recent_metrics = await HealthService.get_health_metrics(
                    db_session,
                    user_id,
                    start_date=date.today() - timedelta(days=7),
                    limit=7
                )

                if recent_metrics:
                    latest = recent_metrics[0]
                    context["recent_health"] = {
                        "date": str(latest.date),
                        "sleep_hours": latest.sleep_hours,
                        "stress_level": latest.stress_level,
                        "focus_level": latest.focus_level,
                        "steps": latest.steps,
                        "weight_kg": latest.weight_kg
                    }

                    # Calculate trends
                    if len(recent_metrics) >= 2:
                        stress_trend = "increasing" if recent_metrics[0].stress_level and recent_metrics[-1].stress_level and recent_metrics[0].stress_level > recent_metrics[-1].stress_level else "decreasing"
                        context["trends"] = {
                            "stress": stress_trend
                        }

        except Exception as e:
            logger.error(f"Error getting user context: {e}")

        return context

    async def _get_chat_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent chat history"""
        try:
            collection = get_collection(COLLECTION_CHAT_MESSAGES)

            cursor = collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)

            messages = await cursor.to_list(length=limit)

            # Reverse to chronological order and format
            history = []
            for msg in reversed(messages):
                history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            return history

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def _generate_response(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any],
        chat_history: List[Dict[str, str]],
        relevant_knowledge: List[str]
    ) -> Dict[str, Any]:
        """
        Generate AI response using LLM with context and knowledge

        This is where the magic happens!
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Build context string
        context_str = ""

        if relevant_knowledge:
            context_str += "\n**Relevant Knowledge:**\n" + "\n".join(relevant_knowledge)

        if context.get("recent_health"):
            health = context["recent_health"]
            context_str += f"\n\n**User's Recent Health Data:**\n"
            if health.get("stress_level"):
                context_str += f"- Stress Level: {health['stress_level']:.2f}/1.0\n"
            if health.get("sleep_hours"):
                context_str += f"- Sleep: {health['sleep_hours']} hours\n"
            if health.get("steps"):
                context_str += f"- Activity: {health['steps']} steps\n"

        if context.get("goals"):
            context_str += f"\n**User's Goals:** {', '.join(context['goals'])}\n"

        # Format chat history
        history_str = ""
        for msg in chat_history[-6:]:  # Last 3 exchanges
            history_str += f"{msg['role'].title()}: {msg['content']}\n"

        # If no LLM available, use rule-based responses
        if not self.llm:
            response_content = self._generate_rule_based_response(
                message, context, relevant_knowledge
            )

            return {
                "content": response_content,
                "context_used": relevant_knowledge,
                "sources": ["Knowledge Base", "User Health Data"],
                "model": "rule-based"
            }

        # Use LLM to generate response
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Context:\n{context_str}\n\nPrevious conversation:\n{history_str}\n\nUser: {message}\n\nProvide a helpful, empathetic response:")
            ]

            response = self.llm(messages)

            return {
                "content": response.content,
                "context_used": relevant_knowledge,
                "sources": ["Knowledge Base", "User Health Data"],
                "model": "gpt-3.5-turbo"
            }

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to rule-based
            response_content = self._generate_rule_based_response(
                message, context, relevant_knowledge
            )

            return {
                "content": response_content,
                "context_used": relevant_knowledge,
                "sources": ["Knowledge Base"],
                "model": "rule-based-fallback"
            }

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt for the AI coach"""
        return """You are a compassionate and knowledgeable wellness AI coach. Your role is to:

1. Provide personalized health and wellness guidance based on the user's data
2. Recommend evidence-based interventions for stress, sleep, nutrition, and mental health
3. Incorporate holistic approaches including Ayurveda, supplements, meditation, and lifestyle changes
4. Be empathetic, encouraging, and supportive
5. Always cite your sources and reasoning
6. Encourage users to consult healthcare professionals for medical concerns

Communication style:
- Be warm and personable, not clinical
- Use "I" statements and build rapport
- Celebrate progress and provide encouragement
- Ask clarifying questions when needed
- Provide actionable, specific recommendations

Remember: You're a coach and companion on their wellness journey, not a replacement for medical professionals."""

    def _generate_rule_based_response(
        self,
        message: str,
        context: Dict[str, Any],
        relevant_knowledge: List[str]
    ) -> str:
        """
        Generate rule-based response when LLM is not available

        This is a fallback that uses pattern matching and context
        """
        message_lower = message.lower()

        # Stress-related
        if any(word in message_lower for word in ["stress", "stressed", "anxious", "anxiety"]):
            response = "I understand you're feeling stressed. Based on your recent data, "

            if context.get("recent_health", {}).get("stress_level", 0) > 0.7:
                response += "your stress levels have been elevated. "

            response += "\n\nHere are some evidence-based strategies:\n\n"
            response += "1. **Breathing Exercise**: Try box breathing - inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat for 5 minutes.\n\n"
            response += "2. **Supplement**: Consider Ashwagandha (300-500mg daily), an adaptogenic herb shown to reduce cortisol levels.\n\n"
            response += "3. **Lifestyle**: Take short breaks every hour. Even 2-3 minutes of stretching or walking helps.\n\n"

            if context.get("recent_health", {}).get("sleep_hours", 8) < 6:
                response += "I also notice your sleep has been limited. Poor sleep amplifies stress - let's work on that too.\n"

            return response

        # Sleep-related
        elif any(word in message_lower for word in ["sleep", "insomnia", "tired", "fatigue"]):
            response = "Sleep is crucial for overall wellness. "

            if context.get("recent_health", {}).get("sleep_hours"):
                hours = context["recent_health"]["sleep_hours"]
                response += f"You're averaging {hours} hours. "

                if hours < 7:
                    response += "Most adults need 7-9 hours for optimal function.\n\n"

            response += "**Recommendations:**\n\n"
            response += "1. **Sleep Hygiene**: Consistent bedtime, dark cool room, no screens 1 hour before bed\n\n"
            response += "2. **Magnesium**: 200-400mg before bed can improve sleep quality. Found in leafy greens, nuts, or as a supplement.\n\n"
            response += "3. **Relaxation**: Try a 10-minute body scan meditation before bed.\n\n"
            response += "4. **Avoid**: Caffeine after 2pm, large meals before bed, alcohol (disrupts sleep cycles)\n"

            return response

        # Nutrition/diet
        elif any(word in message_lower for word in ["eat", "food", "diet", "nutrition", "meal"]):
            response = "Great that you're focusing on nutrition! Food is foundational to wellness.\n\n"

            # Use knowledge if available
            if relevant_knowledge:
                response += "Based on wellness principles:\n\n"
                response += relevant_knowledge[0][:200] + "...\n\n"

            response += "**General Guidance:**\n\n"
            response += "- **Whole Foods**: Focus on vegetables, fruits, lean proteins, whole grains\n\n"
            response += "- **Brain Health**: Omega-3 (fish, walnuts), B vitamins, leafy greens\n\n"
            response += "- **Energy**: Balance protein, complex carbs, healthy fats at each meal\n\n"
            response += "- **Hydration**: Aim for 8 glasses of water daily\n\n"
            response += "Would you like specific meal ideas or help with a particular dietary goal?"

            return response

        # Focus/productivity
        elif any(word in message_lower for word in ["focus", "concentrate", "productivity", "distracted"]):
            response = "Improving focus involves both mind and body. Here's what can help:\n\n"
            response += "**Immediate:**\n"
            response += "- Pomodoro Technique: 25 min focused work, 5 min break\n"
            response += "- Eliminate distractions: Phone away, close unnecessary tabs\n"
            response += "- Natural light: Improves alertness and focus\n\n"

            response += "**Supplements:**\n"
            response += "- L-Theanine (100-200mg) + Caffeine: Smooth focus without jitters\n"
            response += "- Omega-3: Supports cognitive function\n\n"

            response += "**Lifestyle:**\n"
            response += "- Morning exercise: Boosts BDNF (brain growth factor)\n"
            response += "- Meditation: 10 min daily improves attention span\n"
            response += "- Quality sleep: Non-negotiable for cognitive performance\n"

            return response

        # General wellness/how are you
        elif any(word in message_lower for word in ["how", "feel", "doing", "energy"]):
            response = "I'm here to support your wellness journey! "

            if context.get("recent_health"):
                health = context["recent_health"]

                if health.get("stress_level") and health["stress_level"] > 0.6:
                    response += "\n\nI notice your stress levels have been a bit high. "

                if health.get("sleep_hours") and health["sleep_hours"] < 7:
                    response += "Your sleep could use some attention too. "

                response += "\n\nWould you like to work on stress management, sleep quality, nutrition, or something else?"

            else:
                response += "\n\nTo give you the best guidance, I'd love to know more about how you're feeling and what you'd like to focus on. What's on your mind today?"

            return response

        # Goals
        elif any(word in message_lower for word in ["goal", "want to", "improve", "better"]):
            response = "Setting wellness goals is a powerful first step! I'm here to help you achieve them.\n\n"
            response += "Common wellness goals I can support:\n"
            response += "- Reduce stress and anxiety\n"
            response += "- Improve sleep quality\n"
            response += "- Boost energy and focus\n"
            response += "- Better nutrition habits\n"
            response += "- Regular exercise routine\n"
            response += "- Meditation practice\n\n"
            response += "What specific goal would you like to focus on?"

            return response

        # Default response
        else:
            response = "I'm here to help with your health and wellness! I can provide guidance on:\n\n"
            response += "- **Stress Management**: Techniques, supplements, lifestyle changes\n"
            response += "- **Sleep Optimization**: Sleep hygiene, supplements, routines\n"
            response += "- **Nutrition**: Healthy eating, meal planning, supplements\n"
            response += "- **Mental Wellness**: Meditation, mindfulness, cognitive health\n"
            response += "- **Energy & Focus**: Productivity tips, nootropics, exercise\n\n"

            if context.get("recent_health"):
                response += "I can also review your health data to provide personalized recommendations. "

            response += "\n\nWhat would you like to explore?"

            return response

    async def _store_message(
        self,
        user_id: str,
        role: str,
        content: str,
        context_used: List[str] = None,
        sources: List[str] = None
    ):
        """Store chat message in MongoDB"""
        try:
            collection = get_collection(COLLECTION_CHAT_MESSAGES)

            message = {
                "user_id": user_id,
                "timestamp": datetime.now(),
                "role": role,
                "content": content,
                "context_used": context_used,
                "sources": sources,
                "created_at": datetime.now()
            }

            await collection.insert_one(message)

        except Exception as e:
            logger.error(f"Error storing message: {e}")

    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return await self._get_chat_history(user_id, limit=limit)

    async def clear_conversation(self, user_id: str):
        """Clear conversation history"""
        try:
            collection = get_collection(COLLECTION_CHAT_MESSAGES)
            await collection.delete_many({"user_id": user_id})
            logger.info(f"Cleared conversation for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")


# Global instance
wellness_coach = WellnessCoachService()
