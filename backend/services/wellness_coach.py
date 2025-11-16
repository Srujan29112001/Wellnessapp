"""
Wellness Coach Service - LangChain-based AI Coach with RAG

This service implements a comprehensive AI wellness coach that:
- Uses LangChain for conversation management
- Implements RAG for knowledge retrieval
- Maintains long-term memory of user interactions
- Provides personalized, evidence-based recommendations
"""

import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import JSONLoader, TextLoader
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.tools import BaseTool

# Database
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Local imports
from backend.models.mongo_schemas import ChatMessage as ChatMessageSchema
from backend.models.postgres_models import HealthMetric, EEGAnalysis, Recommendation
from backend.database.mongo import get_mongo_db
from backend.database.postgres import get_db


class WellnessCoach:
    """
    AI Wellness Coach with RAG and long-term memory
    """

    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",  # Can use local models with Ollama
        temperature: float = 0.7,
        knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base"
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.knowledge_base_path = Path(knowledge_base_path)

        # Initialize embeddings (using local HuggingFace model)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize vector store
        self.vector_store = None
        self._initialize_vector_store()

        # Initialize LLM (can switch to local Ollama/HuggingFace model)
        self.llm = None
        self._initialize_llm()

        # Memory stores (per user)
        self.user_memories: Dict[str, ConversationBufferWindowMemory] = {}

        # System prompt
        self.system_prompt = self._create_system_prompt()

    def _initialize_llm(self):
        """Initialize the language model"""
        try:
            # Try OpenAI first (if API key available)
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your-openai-api-key-here":
                self.llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=self.temperature,
                    openai_api_key=api_key
                )
            else:
                # Fallback to local model (would need Ollama or HuggingFace)
                from langchain.llms import HuggingFacePipeline
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

                # Use a small local model for demonstration
                model_id = "microsoft/DialoGPT-medium"
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForCausalLM.from_pretrained(model_id)

                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=512,
                    temperature=self.temperature
                )

                self.llm = HuggingFacePipeline(pipeline=pipe)

        except Exception as e:
            print(f"Error initializing LLM: {e}")
            # Create a mock LLM for development
            self.llm = None

    def _initialize_vector_store(self):
        """Initialize vector store with knowledge base"""
        try:
            # Load all knowledge base documents
            documents = []

            # Load Ayurvedic doshas
            ayurveda_file = self.knowledge_base_path / "ayurveda" / "doshas.json"
            if ayurveda_file.exists():
                with open(ayurveda_file) as f:
                    doshas_data = json.load(f)
                    for dosha in doshas_data.get("doshas", []):
                        text = self._format_dosha_for_rag(dosha)
                        documents.append({
                            "page_content": text,
                            "metadata": {"source": "ayurveda", "type": "dosha", "name": dosha["name"]}
                        })

            # Load supplements database
            supplements_file = self.knowledge_base_path / "supplements" / "supplements_db.json"
            if supplements_file.exists():
                with open(supplements_file) as f:
                    supplements_data = json.load(f)
                    for supp in supplements_data.get("supplements", []):
                        text = self._format_supplement_for_rag(supp)
                        documents.append({
                            "page_content": text,
                            "metadata": {"source": "supplements", "type": "supplement", "name": supp["name"]}
                        })

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            # Create documents for vector store
            from langchain.schema import Document
            docs = [Document(page_content=doc["page_content"], metadata=doc["metadata"])
                   for doc in documents]

            # Create vector store
            persist_directory = "/home/user/Wellnessapp/data/chroma_db"
            os.makedirs(persist_directory, exist_ok=True)

            self.vector_store = Chroma.from_documents(
                documents=docs,
                embedding=self.embeddings,
                persist_directory=persist_directory
            )

            print(f"✅ Vector store initialized with {len(docs)} documents")

        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.vector_store = None

    def _format_dosha_for_rag(self, dosha: Dict) -> str:
        """Format dosha data for RAG retrieval"""
        text = f"AYURVEDIC DOSHA: {dosha['name']}\n\n"
        text += f"Description: {dosha.get('description', '')}\n\n"

        if "characteristics" in dosha:
            chars = dosha["characteristics"]
            text += f"Physical Characteristics: {', '.join(chars.get('physical', []))}\n"
            text += f"Mental Characteristics: {', '.join(chars.get('mental', []))}\n\n"

        if "imbalance_signs" in dosha:
            text += f"Signs of Imbalance: {', '.join(dosha['imbalance_signs'])}\n\n"

        if "balancing_foods" in dosha:
            text += f"Balancing Foods: {', '.join(dosha['balancing_foods'])}\n"
            text += f"Foods to Avoid: {', '.join(dosha.get('avoid_foods', []))}\n\n"

        if "recommended_herbs" in dosha:
            herbs = [f"{h['name']} ({h['benefit']})" for h in dosha["recommended_herbs"]]
            text += f"Recommended Herbs: {', '.join(herbs)}\n\n"

        return text

    def _format_supplement_for_rag(self, supplement: Dict) -> str:
        """Format supplement data for RAG retrieval"""
        text = f"SUPPLEMENT: {supplement['name']}\n\n"
        text += f"Category: {supplement.get('category', '')}\n"
        text += f"Origin: {supplement.get('origin', '')}\n\n"

        text += f"Benefits: {', '.join(supplement.get('benefits', []))}\n\n"
        text += f"Mechanisms: {', '.join(supplement.get('mechanisms', []))}\n\n"

        if "dosage" in supplement:
            dos = supplement["dosage"]
            text += f"Typical Dosage: {dos.get('typical', '')}\n"
            text += f"Dosage Range: {dos.get('range', '')}\n"
            text += f"Timing: {dos.get('timing', '')}\n\n"

        if "contraindications" in supplement:
            text += f"Contraindications: {', '.join(supplement['contraindications'])}\n\n"

        if "interactions" in supplement:
            text += f"Drug Interactions: {', '.join(supplement['interactions'])}\n\n"

        return text

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI coach"""
        return """You are a compassionate and knowledgeable AI Wellness Coach specializing in holistic health.

Your expertise includes:
- Modern nutritional science and evidence-based wellness practices
- Traditional Ayurvedic medicine (doshas, herbs, lifestyle)
- Stress management and mental health support
- Sleep optimization and circadian rhythm
- Supplement science and recommendations
- Personalized health interventions

Guidelines for your responses:
1. EMPATHY: Always be warm, encouraging, and supportive
2. EVIDENCE: Ground recommendations in science and cite sources when possible
3. PERSONALIZATION: Consider the user's unique history, dosha type, and current state
4. SAFETY: Always include appropriate medical disclaimers and recommend professional consultation for serious issues
5. ACTIONABLE: Provide specific, practical steps the user can take
6. HOLISTIC: Consider mind, body, and lifestyle factors together

You have access to:
- User's health metrics (EEG stress levels, sleep data, diet logs)
- Ayurvedic knowledge base (doshas, herbs, practices)
- Supplement database (benefits, dosages, interactions, contraindications)
- Conversation history with this user

Format your responses with:
- Clear, conversational language
- Specific recommendations with rationale
- Citations when referencing studies or traditional wisdom
- Safety warnings where appropriate
- Follow-up questions to better understand the user's needs

Remember: You are not a substitute for professional medical care. Always encourage users to consult healthcare providers for serious concerns."""

    def _get_user_memory(self, user_id: str) -> ConversationBufferWindowMemory:
        """Get or create memory for a user"""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationBufferWindowMemory(
                k=10,  # Remember last 10 exchanges
                memory_key="chat_history",
                return_messages=True
            )
        return self.user_memories[user_id]

    async def get_user_context(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Retrieve user context from database"""
        context = {
            "recent_metrics": [],
            "recent_eeg": None,
            "sleep_average": None,
            "stress_trend": None,
            "preferences": {},
            "dosha_type": None
        }

        try:
            # Get recent health metrics (last 7 days)
            from sqlalchemy import desc
            result = await db.execute(
                select(HealthMetric)
                .where(HealthMetric.user_id == user_id)
                .order_by(desc(HealthMetric.date))
                .limit(7)
            )
            metrics = result.scalars().all()

            if metrics:
                context["recent_metrics"] = [
                    {
                        "date": m.date.isoformat(),
                        "steps": m.steps,
                        "sleep_hours": m.sleep_hours,
                        "heart_rate": m.heart_rate_avg,
                        "stress_level": m.stress_level
                    }
                    for m in metrics
                ]

                # Calculate averages
                sleep_hours = [m.sleep_hours for m in metrics if m.sleep_hours]
                if sleep_hours:
                    context["sleep_average"] = sum(sleep_hours) / len(sleep_hours)

                stress_levels = [m.stress_level for m in metrics if m.stress_level]
                if stress_levels:
                    context["stress_trend"] = "increasing" if stress_levels[0] > stress_levels[-1] else "decreasing"

            # Get latest EEG analysis
            result = await db.execute(
                select(EEGAnalysis)
                .where(EEGAnalysis.user_id == user_id)
                .order_by(desc(EEGAnalysis.timestamp))
                .limit(1)
            )
            eeg = result.scalar_one_or_none()
            if eeg:
                context["recent_eeg"] = {
                    "timestamp": eeg.timestamp.isoformat(),
                    "stress_level": eeg.stress_level,
                    "focus_level": eeg.focus_level,
                    "relaxation_level": eeg.relaxation_level,
                    "mental_state": eeg.mental_state
                }

        except Exception as e:
            print(f"Error retrieving user context: {e}")

        return context

    def _create_context_string(self, context: Dict[str, Any]) -> str:
        """Create a formatted context string for the LLM"""
        parts = ["CURRENT USER CONTEXT:\n"]

        if context.get("dosha_type"):
            parts.append(f"- Ayurvedic Constitution: {context['dosha_type']}")

        if context.get("sleep_average"):
            parts.append(f"- Average Sleep (7 days): {context['sleep_average']:.1f} hours")

        if context.get("stress_trend"):
            parts.append(f"- Stress Trend: {context['stress_trend']}")

        if context.get("recent_eeg"):
            eeg = context["recent_eeg"]
            parts.append(f"- Latest Brain State (EEG): {eeg['mental_state']}")
            parts.append(f"  - Stress: {eeg['stress_level']:.2f}, Focus: {eeg['focus_level']:.2f}, Relaxation: {eeg['relaxation_level']:.2f}")

        if context.get("recent_metrics"):
            latest = context["recent_metrics"][0]
            parts.append(f"- Today's Activity: {latest.get('steps', 0)} steps, {latest.get('sleep_hours', 0)} hours sleep")

        return "\n".join(parts)

    async def chat(
        self,
        user_id: str,
        message: str,
        db: AsyncSession,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response

        Args:
            user_id: User ID
            message: User's message
            db: Database session
            include_context: Whether to include user health data context

        Returns:
            Dict with response, sources, and recommendations
        """
        try:
            # Get user context
            context = {}
            if include_context:
                context = await self.get_user_context(user_id, db)

            context_string = self._create_context_string(context)

            # Retrieve relevant knowledge from vector store
            relevant_docs = []
            sources = []
            if self.vector_store:
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                relevant_docs = retriever.get_relevant_documents(message)
                sources = [doc.metadata.get("name", doc.metadata.get("source", "Knowledge Base"))
                          for doc in relevant_docs]

            # Build knowledge context
            knowledge_context = "\n\n".join([doc.page_content for doc in relevant_docs[:3]])

            # Get conversation memory
            memory = self._get_user_memory(user_id)

            # If LLM is available, generate response
            if self.llm:
                # Create prompt
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("system", f"\n{context_string}\n\nRELEVANT KNOWLEDGE:\n{knowledge_context}"),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ])

                # Simple chain
                from langchain.chains import LLMChain
                chain = LLMChain(
                    llm=self.llm,
                    prompt=prompt,
                    memory=memory
                )

                response = chain.predict(input=message)

            else:
                # Fallback: rule-based response with retrieved knowledge
                response = self._generate_fallback_response(message, context, relevant_docs)

            # Extract recommendations from response (simple heuristic)
            recommendations = self._extract_recommendations(response)

            # Store conversation in MongoDB
            await self._store_conversation(user_id, message, response, context)

            return {
                "message": response,
                "context_used": [k for k, v in context.items() if v],
                "recommendations": recommendations,
                "sources": sources[:3]  # Top 3 sources
            }

        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request. Could you please rephrase or try again?",
                "context_used": [],
                "recommendations": [],
                "sources": []
            }

    def _generate_fallback_response(
        self,
        message: str,
        context: Dict,
        relevant_docs: List
    ) -> str:
        """Generate a rule-based response when LLM is not available"""
        message_lower = message.lower()

        # Detect intent
        if any(word in message_lower for word in ["stress", "anxious", "anxiety", "worried"]):
            response = "I understand you're feeling stressed and anxious. "

            # Check context
            if context.get("recent_eeg") and context["recent_eeg"]["stress_level"] > 0.6:
                response += "Your recent EEG analysis confirms elevated stress levels. "

            if context.get("sleep_average") and context["sleep_average"] < 6.5:
                response += f"I notice you've been averaging {context['sleep_average']:.1f} hours of sleep, which may be contributing to your stress. "

            response += "\n\nHere's what I recommend:\n\n"
            response += "1. **Breathing Exercise**: Try box breathing - inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Do this for 5 minutes.\n\n"
            response += "2. **Magnesium-Rich Foods**: Include nuts, leafy greens, and dark chocolate in your diet. Magnesium helps regulate stress response.\n\n"
            response += "3. **Ashwagandha**: Consider this Ayurvedic adaptogen (300-600mg daily). Research shows it can reduce cortisol by up to 28%. Always consult your doctor first.\n\n"
            response += "4. **Sleep Priority**: Aim for 7-8 hours tonight. Good sleep is crucial for stress management.\n\n"

            if relevant_docs:
                response += f"\n💡 I found relevant information from our knowledge base about {relevant_docs[0].metadata.get('name', 'stress management')}."

            response += "\n\n⚠️ If stress persists or worsens, please consult a healthcare professional."

        elif any(word in message_lower for word in ["sleep", "insomnia", "tired", "fatigue"]):
            response = "Let's work on improving your sleep quality. "

            if context.get("sleep_average"):
                response += f"You've been averaging {context['sleep_average']:.1f} hours of sleep over the last week. "

            response += "\n\nHere's a comprehensive sleep improvement plan:\n\n"
            response += "1. **Sleep Hygiene**:\n"
            response += "   - Go to bed and wake up at the same time daily\n"
            response += "   - Keep bedroom cool (60-67°F), dark, and quiet\n"
            response += "   - No screens 1 hour before bed\n\n"
            response += "2. **Evening Routine**:\n"
            response += "   - Warm bath or shower 90 minutes before bed\n"
            response += "   - Light reading or meditation\n"
            response += "   - Chamomile or passionflower tea\n\n"
            response += "3. **Supplements to Consider** (consult your doctor):\n"
            response += "   - Magnesium Glycinate: 200-400mg before bed\n"
            response += "   - L-Theanine: 200mg for relaxation\n"
            response += "   - Melatonin: 0.5-3mg (start low) 30 mins before bed\n\n"
            response += "4. **Ayurvedic Approach**:\n"
            response += "   - Self-massage with warm sesame oil before shower\n"
            response += "   - Avoid stimulating activities in evening (balance Vata)\n\n"

        elif any(word in message_lower for word in ["focus", "concentrate", "distracted", "adhd"]):
            response = "Let's enhance your focus and concentration. "

            response += "\n\nHere are evidence-based strategies:\n\n"
            response += "1. **Nutrition for Focus**:\n"
            response += "   - Omega-3 fatty acids (fish, walnuts, flax)\n"
            response += "   - Blueberries (antioxidants for brain health)\n"
            response += "   - Green tea (L-theanine + caffeine for alert calmness)\n\n"
            response += "2. **Cognitive Enhancers**:\n"
            response += "   - Brahmi (Bacopa monnieri): 300mg daily for memory\n"
            response += "   - Lion's Mane mushroom: 500-1000mg for cognitive function\n"
            response += "   - L-Theanine + Caffeine: 200mg + 100mg for focus without jitters\n\n"
            response += "3. **Focus Techniques**:\n"
            response += "   - Pomodoro: 25 min focused work, 5 min break\n"
            response += "   - Single-tasking: One thing at a time\n"
            response += "   - Morning sunlight exposure (helps circadian rhythm)\n\n"

        elif any(word in message_lower for word in ["energy", "low energy", "lethargy"]):
            response = "Let's boost your energy levels naturally. "

            response += "\n\nEnergy Enhancement Protocol:\n\n"
            response += "1. **Rule Out Deficiencies** (get tested):\n"
            response += "   - Vitamin D, B12, Iron, Thyroid function\n\n"
            response += "2. **Energy-Boosting Foods**:\n"
            response += "   - Complex carbs (oats, quinoa, sweet potato)\n"
            response += "   - Protein at each meal (stabilizes blood sugar)\n"
            response += "   - Stay hydrated (dehydration causes fatigue)\n\n"
            response += "3. **Strategic Supplementation**:\n"
            response += "   - Vitamin B-Complex: Supports energy production\n"
            response += "   - Coenzyme Q10: 100-200mg for cellular energy\n"
            response += "   - Rhodiola or Cordyceps: Adaptogenic energy support\n\n"
            response += "4. **Lifestyle**:\n"
            response += "   - Exercise (even 10-min walk boosts energy)\n"
            response += "   - Power nap: 20 minutes max (not too late)\n"
            response += "   - Cold shower in morning (activates sympathetic system)\n\n"

        else:
            # General wellness response
            response = "Thank you for reaching out! I'm here to help with your holistic wellness journey.\n\n"
            response += "I can assist you with:\n"
            response += "- Stress and anxiety management\n"
            response += "- Sleep optimization\n"
            response += "- Focus and cognitive enhancement\n"
            response += "- Nutrition and supplement guidance\n"
            response += "- Ayurvedic wellness practices\n"
            response += "- Personalized health recommendations based on your data\n\n"
            response += "What specific area would you like to focus on today?"

        return response

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        recommendations = []
        lines = response.split('\n')

        for line in lines:
            # Look for numbered points or bullet points
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the line
                clean_line = line.lstrip('0123456789.-•* ').strip()
                if len(clean_line) > 10:  # Meaningful recommendation
                    # Extract the main point (before colon if exists)
                    main_point = clean_line.split(':')[0].strip()
                    if main_point:
                        recommendations.append(main_point)

        return recommendations[:5]  # Top 5 recommendations

    async def _store_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        context: Dict
    ):
        """Store conversation in MongoDB"""
        try:
            mongo_db = await get_mongo_db()
            chat_collection = mongo_db["chat_messages"]

            await chat_collection.insert_one({
                "user_id": user_id,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message,
                        "timestamp": datetime.utcnow()
                    },
                    {
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.utcnow()
                    }
                ],
                "context_snapshot": context,
                "created_at": datetime.utcnow()
            })
        except Exception as e:
            print(f"Error storing conversation: {e}")

    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Retrieve chat history from MongoDB"""
        try:
            mongo_db = await get_mongo_db()
            chat_collection = mongo_db["chat_messages"]

            cursor = chat_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)

            messages = []
            async for doc in cursor:
                for msg in doc.get("messages", []):
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"]
                    })

            return list(reversed(messages))  # Chronological order

        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []


# Global instance
_coach_instance = None

def get_wellness_coach() -> WellnessCoach:
    """Get or create wellness coach singleton"""
    global _coach_instance
    if _coach_instance is None:
        _coach_instance = WellnessCoach()
    return _coach_instance
