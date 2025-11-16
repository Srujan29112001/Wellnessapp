"""
LLM-Powered Wellness Coach Service

Implements conversational AI coaching with:
- LangChain integration
- RAG (Retrieval Augmented Generation) with knowledge base
- Long-term memory of user interactions
- Context-aware recommendations
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from config.settings import settings

logger = logging.getLogger(__name__)


class WellnessCoachService:
    """
    AI Wellness Coach powered by LLM

    Features:
    - Conversational interface with empathy
    - Knowledge base retrieval (Ayurveda, supplements, wellness practices)
    - Personalized advice based on user health data
    - Long-term memory of user preferences and progress
    """

    def __init__(self):
        self.llm = None
        self.vectorstore = None
        self.embeddings = None
        self.memory = {}  # Per-user memory
        self._initialize_components()

    def _initialize_components(self):
        """Initialize LLM, embeddings, and vector store"""
        try:
            logger.info("Initializing Wellness Coach components...")

            # Initialize embeddings
            logger.info("Loading embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            # Initialize vector store for knowledge base
            logger.info("Initializing vector store...")
            self._initialize_knowledge_base()

            # Initialize LLM
            if settings.USE_LOCAL_LLM:
                logger.info(f"Loading local LLM: {settings.LOCAL_LLM_MODEL}")
                self._initialize_local_llm()
            else:
                logger.info("Using OpenAI API")
                self._initialize_openai_llm()

            logger.info("Wellness Coach initialized successfully!")

        except Exception as e:
            logger.error(f"Error initializing Wellness Coach: {e}")
            logger.warning("Falling back to simple response mode")

    def _initialize_local_llm(self):
        """Initialize local Llama-2 or similar model with quantization"""
        try:
            from transformers import BitsAndBytesConfig

            # Quantization config for memory efficiency
            quantization_config = None
            if settings.USE_QUANTIZATION:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

            # For demo, use a smaller model (TinyLlama or similar)
            model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto",
                cache_dir=settings.MODEL_CACHE_DIR,
                low_cpu_mem_usage=True
            )

            # Create pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15
            )

            self.llm = HuggingFacePipeline(pipeline=pipe)
            logger.info("Local LLM initialized successfully")

        except Exception as e:
            logger.error(f"Error loading local LLM: {e}")
            self.llm = None

    def _initialize_openai_llm(self):
        """Initialize OpenAI LLM"""
        try:
            from langchain_openai import ChatOpenAI

            if not settings.OPENAI_API_KEY:
                logger.warning("No OpenAI API key provided")
                return

            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info("OpenAI LLM initialized")

        except Exception as e:
            logger.error(f"Error initializing OpenAI LLM: {e}")

    def _initialize_knowledge_base(self):
        """Load and index knowledge base documents"""
        try:
            # Load knowledge base files
            kb_dir = "knowledge_base"
            documents = []

            # Load Ayurveda knowledge
            ayurveda_path = os.path.join(kb_dir, "ayurveda", "doshas.json")
            if os.path.exists(ayurveda_path):
                with open(ayurveda_path, 'r') as f:
                    ayurveda_data = json.load(f)
                    for dosha_name, dosha_info in ayurveda_data.get('doshas', {}).items():
                        doc_text = f"Dosha: {dosha_name}\n"
                        doc_text += f"Characteristics: {', '.join(dosha_info.get('characteristics', {}).get('physical', []))}\n"
                        doc_text += f"Balancing foods: {', '.join(dosha_info.get('balancing_foods', []))}\n"
                        doc_text += f"Herbs: {', '.join([h['name'] for h in dosha_info.get('herbs', [])])}\n"
                        documents.append(doc_text)

            # Load supplement knowledge
            supplements_path = os.path.join(kb_dir, "supplements", "supplements_db.json")
            if os.path.exists(supplements_path):
                with open(supplements_path, 'r') as f:
                    supplements_data = json.load(f)
                    for supp in supplements_data.get('supplements', []):
                        doc_text = f"Supplement: {supp['name']}\n"
                        doc_text += f"Benefits: {', '.join(supp.get('benefits', []))}\n"
                        doc_text += f"Dosage: {supp.get('dosage', {}).get('typical', 'Not specified')}\n"
                        doc_text += f"Contraindications: {', '.join(supp.get('contraindications', []))}\n"
                        documents.append(doc_text)

            if documents:
                # Create vector store
                self.vectorstore = Chroma.from_texts(
                    texts=documents,
                    embedding=self.embeddings,
                    persist_directory=settings.CHROMA_PERSIST_DIR
                )
                logger.info(f"Knowledge base indexed: {len(documents)} documents")
            else:
                logger.warning("No knowledge base documents found")

        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")

    async def chat(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process user message and generate coach response

        Args:
            user_id: User identifier
            message: User's message
            context: Optional context (health data, recent analyses)

        Returns:
            Response dict with message, sources, recommendations
        """
        try:
            # Retrieve relevant knowledge
            context_docs = []
            if self.vectorstore:
                retrieved_docs = self.vectorstore.similarity_search(message, k=3)
                context_docs = [doc.page_content for doc in retrieved_docs]

            # Build context string
            context_str = ""
            if context:
                if context.get('latest_eeg'):
                    eeg = context['latest_eeg']
                    context_str += f"\nRecent EEG Analysis: Stress {eeg.get('stress', 0):.2f}, "
                    context_str += f"Focus {eeg.get('focus', 0):.2f}, Mental State: {eeg.get('mental_state', 'unknown')}"

                if context.get('health_goals'):
                    context_str += f"\nUser's Health Goals: {', '.join(context['health_goals'])}"

            # Create prompt
            system_prompt = """You are a compassionate and knowledgeable wellness coach specializing in holistic health.
            You have expertise in:
            - Stress management and mental wellness
            - Nutrition and dietary recommendations
            - Ayurvedic principles and herbal remedies
            - Sleep optimization
            - Mindfulness and meditation practices

            Your responses should be:
            - Empathetic and supportive
            - Evidence-based when possible
            - Personalized to the user's current state
            - Actionable and practical
            - Encouraging and positive

            Always consider the user's current physiological state (stress levels, sleep, etc.) when giving advice.
            """

            if context_docs:
                system_prompt += f"\n\nRelevant Knowledge:\n" + "\n".join(context_docs)

            if context_str:
                system_prompt += f"\n\nUser Context:{context_str}"

            # Generate response
            if self.llm:
                try:
                    # Use LLM for response
                    full_prompt = f"{system_prompt}\n\nUser: {message}\n\nWellness Coach:"
                    response = self.llm(full_prompt)

                    # Extract text from response
                    if isinstance(response, str):
                        ai_response = response
                    else:
                        ai_response = str(response)

                    # Clean up response
                    if "Wellness Coach:" in ai_response:
                        ai_response = ai_response.split("Wellness Coach:")[-1].strip()
                    if "User:" in ai_response:
                        ai_response = ai_response.split("User:")[0].strip()

                except Exception as e:
                    logger.error(f"LLM generation error: {e}")
                    ai_response = self._generate_fallback_response(message, context)
            else:
                ai_response = self._generate_fallback_response(message, context)

            return {
                "message": ai_response,
                "context_used": context_docs[:2] if context_docs else [],
                "recommendations": self._extract_recommendations(ai_response),
                "sources": ["Knowledge Base", "Ayurvedic Principles"] if context_docs else []
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Could you please rephrase your question?",
                "context_used": [],
                "recommendations": [],
                "sources": []
            }

    def _generate_fallback_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate rule-based response when LLM is unavailable"""
        message_lower = message.lower()

        # Stress-related queries
        if any(word in message_lower for word in ['stress', 'anxious', 'anxiety', 'worried']):
            response = "I understand you're experiencing stress. Here are some evidence-based suggestions:\n\n"
            response += "1. **Deep Breathing**: Try box breathing (4-4-4-4) to activate your parasympathetic nervous system\n"
            response += "2. **Ashwagandha**: This adaptogenic herb has been shown to reduce cortisol levels\n"
            response += "3. **Mindful Meditation**: Even 5-10 minutes can significantly reduce stress markers\n\n"

            if context and context.get('latest_eeg'):
                stress_level = context['latest_eeg'].get('stress', 0)
                if stress_level > 0.7:
                    response += f"Your recent EEG shows elevated stress ({stress_level:.0%}). Consider taking a short break now."

            return response

        # Sleep-related queries
        elif any(word in message_lower for word in ['sleep', 'insomnia', 'tired', 'fatigue']):
            response = "Sleep is crucial for wellness. Here are some recommendations:\n\n"
            response += "1. **Sleep Hygiene**: Keep your bedroom cool (65-68°F), dark, and quiet\n"
            response += "2. **Magnesium**: Helps relax muscles and promote sleep (300-400mg before bed)\n"
            response += "3. **Wind-Down Routine**: Stop screens 1 hour before bed\n\n"
            return response

        # Focus/concentration
        elif any(word in message_lower for word in ['focus', 'concentration', 'productivity']):
            response = "Let's enhance your focus:\n\n"
            response += "1. **L-Theanine**: Promotes calm focus without jitters (100-200mg)\n"
            response += "2. **Pomodoro Technique**: 25-minute focused work sessions with 5-minute breaks\n"
            response += "3. **Omega-3s**: Support cognitive function (EPA/DHA 1000mg daily)\n\n"
            return response

        # General wellness
        else:
            response = "I'm here to support your holistic wellness journey. I can help with:\n\n"
            response += "• Stress management and relaxation techniques\n"
            response += "• Sleep optimization\n"
            response += "• Nutrition and supplementation guidance\n"
            response += "• Ayurvedic principles and dosha balancing\n"
            response += "• Mindfulness and meditation practices\n\n"
            response += "What specific area would you like to focus on?"
            return response

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        recommendations = []

        # Simple extraction based on numbered lists
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the line
                clean_line = line.lstrip('0123456789.-•*) ').strip()
                if len(clean_line) > 10:  # Meaningful recommendation
                    recommendations.append(clean_line)

        return recommendations[:5]  # Top 5 recommendations


# Global coach instance
_coach_instance = None


def get_wellness_coach() -> WellnessCoachService:
    """Get or create wellness coach instance"""
    global _coach_instance
    if _coach_instance is None:
        _coach_instance = WellnessCoachService()
    return _coach_instance
