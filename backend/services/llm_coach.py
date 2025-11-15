"""
LLM-based Wellness Coach Service

Uses LangChain with RAG for personalized health coaching
"""
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from typing import List, Dict, Optional, Tuple
import os
from datetime import datetime
import logging
from .vector_db import get_vector_db
from ..database.postgres import get_db
from ..database.mongo import get_mongo_db
from ..models.postgres_models import HealthMetrics, EEGAnalysis, Recommendation
import json

logger = logging.getLogger(__name__)


class WellnessCoach:
    """
    AI Wellness Coach with RAG and long-term memory

    Features:
    - Conversational interface with context
    - RAG over wellness knowledge base
    - Access to user health data
    - Personalized recommendations
    - Memory of past interactions
    """

    def __init__(
        self,
        user_id: str,
        model_provider: str = "openai",  # or "anthropic" or "local"
        model_name: str = "gpt-3.5-turbo"
    ):
        """
        Initialize wellness coach for a specific user

        Args:
            user_id: User ID
            model_provider: LLM provider
            model_name: Model name
        """
        self.user_id = user_id
        self.vector_db = get_vector_db()

        # Initialize LLM
        self.llm = self._init_llm(model_provider, model_name)

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # System prompt
        self.system_prompt = self._create_system_prompt()

        # Initialize tools
        self.tools = self._create_tools()

    def _init_llm(self, provider: str, model_name: str):
        """Initialize LLM based on provider"""
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not set, using mock responses")
                return None
            return ChatOpenAI(
                model=model_name,
                temperature=0.7,
                openai_api_key=api_key
            )
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set")
                return None
            return ChatAnthropic(
                model=model_name,
                temperature=0.7,
                anthropic_api_key=api_key
            )
        else:
            # Local model (would use HuggingFace or Ollama)
            logger.info("Using local model (not fully implemented)")
            return None

    def _create_system_prompt(self) -> str:
        """Create system prompt for wellness coach"""
        return """You are an empathetic AI wellness coach specializing in holistic health.

Your expertise includes:
- Modern nutritional science and supplementation
- Ayurvedic medicine (doshas, herbs, lifestyle)
- Stress management and mental health
- EEG-based mental state analysis
- Personalized lifestyle recommendations

Guidelines:
1. EMPATHY: Always acknowledge the user's feelings and concerns
2. EVIDENCE: Base recommendations on scientific evidence when possible
3. PERSONALIZATION: Use the user's health data, dosha type, and preferences
4. SAFETY: Never diagnose conditions - recommend consulting healthcare providers
5. CITATIONS: Reference sources for major claims
6. ACTIONABLE: Provide specific, actionable steps
7. HOLISTIC: Consider mind-body connections

When analyzing:
- Check user's recent EEG data for stress/focus levels
- Review sleep, diet, and exercise patterns
- Consider Ayurvedic constitution (dosha)
- Look for correlations (e.g., poor sleep → high stress)

Format recommendations as:
1. Immediate actions (breathwork, hydration)
2. Short-term changes (diet, supplements)
3. Long-term practices (sleep hygiene, exercise routine)

Always maintain a supportive, non-judgmental tone."""

    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent to use"""
        tools = [
            Tool(
                name="search_wellness_knowledge",
                func=self._search_wellness_knowledge,
                description="Search wellness knowledge base for information about nutrition, Ayurveda, supplements, stress management, etc. Input should be a search query."
            ),
            Tool(
                name="search_supplements",
                func=self._search_supplements,
                description="Search supplement database for specific supplements, their benefits, dosages, and interactions. Input should be supplement name or benefit."
            ),
            Tool(
                name="get_user_health_metrics",
                func=self._get_user_health_metrics,
                description="Get user's recent health metrics (stress, sleep, activity, vitals). Input should be number of days to retrieve (e.g., '7')."
            ),
            Tool(
                name="get_user_eeg_analysis",
                func=self._get_user_eeg_analysis,
                description="Get user's recent EEG brain analysis results. Shows stress, focus, relaxation levels. Input should be 'latest' or number of records."
            ),
            Tool(
                name="get_user_profile",
                func=self._get_user_profile,
                description="Get user's profile including Ayurvedic dosha type, health goals, medical conditions. Input should be 'profile'."
            )
        ]
        return tools

    def _search_wellness_knowledge(self, query: str) -> str:
        """Search wellness knowledge base"""
        results = self.vector_db.search(
            query=query,
            collection_name="wellness_knowledge",
            n_results=3
        )

        if not results:
            return "No relevant information found."

        output = "Wellness Knowledge:\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['document']}\n"
            output += f"   (Source: {result['metadata'].get('source', 'unknown')})\n\n"

        return output

    def _search_supplements(self, query: str) -> str:
        """Search supplement database"""
        results = self.vector_db.search(
            query=query,
            collection_name="supplements",
            n_results=3
        )

        if not results:
            return "No supplement information found."

        output = "Supplement Information:\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['document']}\n\n"

        return output

    def _get_user_health_metrics(self, days: str) -> str:
        """Get user's recent health metrics"""
        try:
            days_int = int(days)
        except:
            days_int = 7

        # Mock data for now (would query database)
        # TODO: Implement actual database query
        return f"""Recent health metrics (last {days_int} days):
- Average sleep: 6.5 hours (target: 7-9)
- Average stress level: 7.2/10 (elevated)
- Daily steps: 5,200 (target: 10,000)
- Heart rate variability: Low (indicates stress)
- Mood: Mostly anxious/tired"""

    def _get_user_eeg_analysis(self, param: str) -> str:
        """Get user's EEG analysis"""
        # Mock data (would query database)
        return """Latest EEG Analysis:
- Stress level: HIGH (beta waves elevated at 0.68)
- Focus level: MODERATE (0.45)
- Relaxation: LOW (alpha waves at 0.23)
- Fatigue: MODERATE (theta waves at 0.52)

Interpretation: Brain patterns indicate elevated stress and moderate mental fatigue.
Recommend: Breathing exercises, magnesium supplementation, ensure 8 hours sleep."""

    def _get_user_profile(self, param: str) -> str:
        """Get user profile"""
        # Mock data (would query database)
        return """User Profile:
- Ayurvedic Dosha: Vata-Pitta (dual dosha)
- Age: 28
- Gender: Female
- Health Goals: Reduce stress, improve sleep, increase energy
- Medical Conditions: None reported
- Current Medications: None
- Preferences: Prefers natural remedies, vegetarian diet
- Allergies: None known"""

    def chat(
        self,
        message: str,
        include_context: bool = True
    ) -> Dict:
        """
        Chat with wellness coach

        Args:
            message: User message
            include_context: Whether to retrieve relevant context

        Returns:
            Dict with response, context used, recommendations, sources
        """
        # If no LLM configured, return enhanced mock response
        if self.llm is None:
            return self._generate_mock_response(message)

        # Retrieve relevant context from vector DB
        context_docs = []
        if include_context:
            # Search user's conversation history
            user_context = self.vector_db.retrieve_user_context(
                user_id=self.user_id,
                query=message,
                n_results=2
            )
            context_docs.extend([doc['document'] for doc in user_context])

            # Search general wellness knowledge
            wellness_results = self.vector_db.search(
                query=message,
                collection_name="wellness_knowledge",
                n_results=3
            )
            context_docs.extend([doc['document'] for doc in wellness_results])

        # Build prompt with context
        context_str = "\n".join(context_docs) if context_docs else "No additional context."

        full_prompt = f"""Context from knowledge base:
{context_str}

User question: {message}

Provide a compassionate, evidence-based response. Include specific recommendations and cite sources when applicable."""

        # Get LLM response
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=full_prompt)
        ]

        try:
            response = self.llm(messages)
            response_text = response.content

            # Extract recommendations (simple extraction)
            recommendations = self._extract_recommendations(response_text)

            # Store in user memory
            self.vector_db.add_user_memory(
                user_id=self.user_id,
                memory=f"User asked: {message}. Coach responded: {response_text[:200]}...",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation"
                }
            )

            return {
                "message": response_text,
                "context_used": [doc[:100] + "..." for doc in context_docs[:3]],
                "recommendations": recommendations,
                "sources": self._extract_sources(response_text)
            }

        except Exception as e:
            logger.error(f"Error in LLM chat: {e}")
            return self._generate_mock_response(message)

    def _generate_mock_response(self, message: str) -> Dict:
        """Generate intelligent mock response when LLM not available"""
        message_lower = message.lower()

        # Determine response based on keywords
        if any(word in message_lower for word in ['stress', 'anxious', 'worry', 'nervous']):
            response = """I understand you're experiencing stress and anxiety. Based on your recent EEG data showing elevated beta waves (stress indicator) and your sleep log showing only 5-6 hours per night, here's my recommendation:

**Immediate Actions (Today):**
1. Try a 5-minute box breathing exercise (breathe in 4 counts, hold 4, out 4, hold 4)
2. Ensure you're well-hydrated - dehydration worsens stress
3. Step outside for 10 minutes of natural light

**This Week:**
1. **Prioritize Sleep**: Aim for 7.5-8 hours. Set a bedtime alarm.
2. **Magnesium-rich foods**: Almonds, spinach, dark chocolate, pumpkin seeds
3. **Consider Ashwagandha**: An adaptogenic herb that reduces cortisol (stress hormone). Typical dose: 300-500mg daily.

**Long-term:**
1. Regular meditation or yoga (15 min daily)
2. Reduce caffeine after 2 PM
3. Evening routine: warm bath, chamomile tea, no screens 1 hour before bed

Your Vata-Pitta dosha means you're prone to anxiety when imbalanced. Focus on grounding, warm foods and regular routines.

Would you like me to guide you through a breathing exercise now?"""
            recommendations = [
                "Box breathing exercise (4-4-4-4)",
                "Increase sleep to 7-8 hours",
                "Magnesium-rich foods or supplement",
                "Ashwagandha 300-500mg daily",
                "Morning sunlight exposure"
            ]
            sources = [
                "Study: Magnesium and anxiety reduction (PubMed PMID: 28445426)",
                "Ashwagandha for stress: Meta-analysis (J Evid Based Integr Med, 2021)",
                "Ayurvedic principle: Vata dosha and anxiety correlation"
            ]

        elif any(word in message_lower for word in ['sleep', 'insomnia', 'tired', 'fatigue']):
            response = """I see you're struggling with sleep and energy. Your EEG data shows elevated theta waves in the evening (mental fatigue) and your sleep log shows inconsistent sleep times.

**Sleep Hygiene Protocol:**

**Evening (2-3 hours before bed):**
- Dim lights (melatonin production starts)
- Avoid screens or use blue light filters
- Light dinner (heavy meals disrupt sleep)
- Herbal tea: Chamomile, passionflower, or valerian root

**1 Hour Before Bed:**
- Magnesium glycinate: 200-400mg (relaxes muscles, calms nervous system)
- Optional: L-theanine 200mg (promotes relaxation without drowsiness)
- Gentle stretching or yin yoga
- Warm bath with Epsom salts

**Sleep Environment:**
- Cool room (65-68°F)
- Complete darkness (eye mask if needed)
- White noise or silence
- Comfortable mattress

**Morning:**
- Wake same time daily (even weekends)
- 10-15 min sunlight exposure within 1 hour of waking (sets circadian rhythm)

**Supplements to Consider:**
- Magnesium glycinate (better absorbed than oxide)
- Melatonin 0.5-3mg (start low, only if needed)
- Ashwagandha (reduces cortisol that interferes with sleep)

Your Vata dosha tends toward irregular sleep. Establish a consistent routine - Vata thrives on structure.

Track your sleep for 1 week and report back."""
            recommendations = [
                "Consistent sleep schedule (same bedtime daily)",
                "Magnesium glycinate 200-400mg before bed",
                "No screens 1 hour before bed",
                "Morning sunlight exposure",
                "Cool, dark room for sleep"
            ]
            sources = [
                "Sleep Foundation: Sleep hygiene guidelines",
                "Magnesium and sleep quality (Nutrients, 2020)",
                "Circadian rhythm and light exposure (Sleep Medicine Reviews)"
            ]

        elif any(word in message_lower for word in ['focus', 'concentration', 'brain fog', 'clarity']):
            response = """For improved focus and mental clarity, let's optimize your cognitive function:

**Nutrition for Brain Function:**
- **Omega-3 (DHA/EPA)**: Fish oil 1-2g daily or fatty fish 2-3x/week. DHA is structural component of brain.
- **B-Complex**: B6, B9 (folate), B12 support neurotransmitter production
- **Antioxidants**: Blueberries, dark chocolate (cacao 70%+), green tea
- **Hydration**: Even 1-2% dehydration impairs cognition

**Nootropic Supplements:**
1. **L-Theanine + Caffeine**: 200mg L-theanine + 100mg caffeine (green tea provides both). Smooth focus without jitters.
2. **Brahmi (Bacopa monnieri)**: Ayurvedic herb for memory and learning. 300mg daily (takes 4-6 weeks for full effect).
3. **Lion's Mane Mushroom**: Supports nerve growth factor (NGF). 500-1000mg daily.
4. **Rhodiola rosea**: Adaptogen for mental stamina. 200-600mg daily.

**Lifestyle:**
- **Pomodoro Technique**: 25 min focused work, 5 min break
- **Morning exercise**: 20-30 min cardio boosts BDNF (brain-derived neurotrophic factor)
- **Meditation**: 10 min daily improves sustained attention
- **Sleep**: Most important - consolidates memory and clears metabolic waste from brain

**Avoid:**
- Excess sugar (causes energy crashes)
- Multitasking (fragments attention)
- Chronic stress (impairs hippocampus)

Your recent EEG shows moderate focus levels. These interventions should improve it within 2-4 weeks."""
            recommendations = [
                "Omega-3 supplement (1-2g DHA/EPA daily)",
                "L-Theanine + moderate caffeine for focus",
                "Brahmi (Bacopa) 300mg daily",
                "Pomodoro technique for work",
                "Ensure 7-8 hours quality sleep"
            ]
            sources = [
                "Omega-3 and cognitive function (Neurology)",
                "L-Theanine and attention (Nutritional Neuroscience)",
                "Brahmi for memory: Systematic review (J Ethnopharmacol)"
            ]

        else:
            # General wellness response
            response = """I'm here to support your wellness journey! I can help you with:

- **Stress & Anxiety**: Breathing techniques, adaptogenic herbs, lifestyle changes
- **Sleep Optimization**: Sleep hygiene, supplements, circadian rhythm alignment
- **Energy & Focus**: Nootropics, nutrition, cognitive enhancement
- **Nutrition**: Personalized diet based on your dosha and goals
- **Supplements**: Evidence-based recommendations with proper dosing
- **Mind-Body Practices**: Meditation, yoga, breathwork

Based on your profile:
- **Dosha**: Vata-Pitta (prone to stress, needs routine and cooling practices)
- **Recent EEG**: Elevated stress, moderate focus
- **Sleep**: Below optimal (6.5 hrs avg, need 7-9)

What specific area would you like to focus on today?"""
            recommendations = [
                "Focus on one health goal at a time",
                "Track sleep, stress, and energy daily",
                "Stay hydrated (8-10 glasses water)",
                "Daily movement (even 10 min walk helps)"
            ]
            sources = []

        return {
            "message": response,
            "context_used": [
                "User's recent EEG analysis (elevated stress)",
                "User's dosha type (Vata-Pitta)",
                "General wellness knowledge base"
            ],
            "recommendations": recommendations,
            "sources": sources
        }

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract bullet points from response as recommendations"""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                # Clean up the bullet point
                rec = line.lstrip('-•*0123456789. ').strip()
                if rec and len(rec) > 10:  # Avoid very short items
                    recommendations.append(rec[:200])  # Limit length

        return recommendations[:7]  # Return top 7

    def _extract_sources(self, text: str) -> List[str]:
        """Extract citations/sources from response"""
        sources = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['study:', 'research:', 'pubmed', 'source:', 'pmid']):
                sources.append(line.strip())

        return sources[:5]  # Return top 5


# Cache coaches per user
_coach_cache: Dict[str, WellnessCoach] = {}

def get_wellness_coach(user_id: str) -> WellnessCoach:
    """Get or create wellness coach for user"""
    if user_id not in _coach_cache:
        _coach_cache[user_id] = WellnessCoach(user_id)

    return _coach_cache[user_id]
