"""
Personality Assessment Service - Big Five (OCEAN) Personality Test

Implements the IPIP-NEO-120 (shortened 44-item version) for personality assessment
"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from enum import Enum


class PersonalityTrait(str, Enum):
    """Big Five personality traits"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class PersonalityScore(BaseModel):
    """Personality scores for Big Five"""
    openness: float  # 0-1
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float


class PersonalityProfile(BaseModel):
    """Complete personality profile"""
    scores: PersonalityScore
    primary_trait: PersonalityTrait
    trait_descriptions: Dict[str, str]
    wellness_recommendations: List[str]
    meal_preferences: List[str]
    exercise_preferences: List[str]


class BigFiveAssessment:
    """Big Five Personality Assessment (44-item IPIP-NEO)"""

    # 44-item questionnaire (shortened from IPIP-NEO-120)
    # Format: (question_text, trait, reverse_scored)
    QUESTIONS = [
        # Openness (11 questions)
        ("I have a vivid imagination", PersonalityTrait.OPENNESS, False),
        ("I enjoy creative activities like art, music, or writing", PersonalityTrait.OPENNESS, False),
        ("I am interested in abstract ideas and theories", PersonalityTrait.OPENNESS, False),
        ("I like to try new and exotic foods", PersonalityTrait.OPENNESS, False),
        ("I enjoy discussing philosophical questions", PersonalityTrait.OPENNESS, False),
        ("I am not interested in theoretical discussions", PersonalityTrait.OPENNESS, True),
        ("I have difficulty understanding abstract ideas", PersonalityTrait.OPENNESS, True),
        ("I prefer routine and familiar experiences", PersonalityTrait.OPENNESS, True),
        ("I am curious about many different things", PersonalityTrait.OPENNESS, False),
        ("I appreciate beauty in art and nature", PersonalityTrait.OPENNESS, False),
        ("I enjoy learning about new cultures", PersonalityTrait.OPENNESS, False),

        # Conscientiousness (9 questions)
        ("I am always prepared and organized", PersonalityTrait.CONSCIENTIOUSNESS, False),
        ("I pay attention to details", PersonalityTrait.CONSCIENTIOUSNESS, False),
        ("I get tasks done right away without procrastinating", PersonalityTrait.CONSCIENTIOUSNESS, False),
        ("I follow a schedule and stick to plans", PersonalityTrait.CONSCIENTIOUSNESS, False),
        ("I leave my belongings lying around", PersonalityTrait.CONSCIENTIOUSNESS, True),
        ("I often forget to put things back in their proper place", PersonalityTrait.CONSCIENTIOUSNESS, True),
        ("I shirk my duties and responsibilities", PersonalityTrait.CONSCIENTIOUSNESS, True),
        ("I strive for excellence in everything I do", PersonalityTrait.CONSCIENTIOUSNESS, False),
        ("I complete tasks successfully and on time", PersonalityTrait.CONSCIENTIOUSNESS, False),

        # Extraversion (8 questions)
        ("I am the life of the party and enjoy being the center of attention", PersonalityTrait.EXTRAVERSION, False),
        ("I feel comfortable around people and make friends easily", PersonalityTrait.EXTRAVERSION, False),
        ("I start conversations with strangers", PersonalityTrait.EXTRAVERSION, False),
        ("I don't talk a lot in social situations", PersonalityTrait.EXTRAVERSION, True),
        ("I keep in the background and prefer to observe", PersonalityTrait.EXTRAVERSION, True),
        ("I have little to say to others", PersonalityTrait.EXTRAVERSION, True),
        ("I enjoy being around lots of people", PersonalityTrait.EXTRAVERSION, False),
        ("I feel energized by social interactions", PersonalityTrait.EXTRAVERSION, False),

        # Agreeableness (8 questions)
        ("I am interested in other people's problems and feelings", PersonalityTrait.AGREEABLENESS, False),
        ("I sympathize with others and try to help", PersonalityTrait.AGREEABLENESS, False),
        ("I have a soft heart and am easily moved", PersonalityTrait.AGREEABLENESS, False),
        ("I take time out for others without expecting anything in return", PersonalityTrait.AGREEABLENESS, False),
        ("I am not really interested in others' problems", PersonalityTrait.AGREEABLENESS, True),
        ("I insult people and can be rude", PersonalityTrait.AGREEABLENESS, True),
        ("I feel little concern for others", PersonalityTrait.AGREEABLENESS, True),
        ("I trust others and assume the best in people", PersonalityTrait.AGREEABLENESS, False),

        # Neuroticism (8 questions)
        ("I get stressed out easily and worry a lot", PersonalityTrait.NEUROTICISM, False),
        ("I am easily disturbed and upset", PersonalityTrait.NEUROTICISM, False),
        ("I change my mood frequently", PersonalityTrait.NEUROTICISM, False),
        ("I have frequent mood swings and emotional ups and downs", PersonalityTrait.NEUROTICISM, False),
        ("I get irritated and angry easily", PersonalityTrait.NEUROTICISM, False),
        ("I am relaxed most of the time and not easily bothered", PersonalityTrait.NEUROTICISM, True),
        ("I seldom feel blue or sad", PersonalityTrait.NEUROTICISM, True),
        ("I remain calm under pressure", PersonalityTrait.NEUROTICISM, True),
    ]

    @classmethod
    def get_questions(cls) -> List[Dict]:
        """Get all questions for the assessment"""
        questions = []
        for idx, (text, trait, reverse) in enumerate(cls.QUESTIONS, 1):
            questions.append({
                'id': idx,
                'text': text,
                'trait': trait.value,
                'reverse_scored': reverse
            })
        return questions

    @classmethod
    def calculate_scores(cls, responses: Dict[int, int]) -> PersonalityScore:
        """
        Calculate Big Five scores from responses

        Args:
            responses: Dict mapping question_id (1-44) to response (1-5 scale)
                      1 = Strongly Disagree, 5 = Strongly Agree

        Returns:
            PersonalityScore with normalized scores (0-1)
        """
        # Initialize trait sums
        trait_sums = {trait: [] for trait in PersonalityTrait}

        # Score each question
        for idx, (text, trait, reverse) in enumerate(cls.QUESTIONS, 1):
            if idx in responses:
                score = responses[idx]

                # Reverse scoring if needed (1->5, 2->4, 3->3, 4->2, 5->1)
                if reverse:
                    score = 6 - score

                trait_sums[trait].append(score)

        # Calculate average scores for each trait and normalize to 0-1
        # (since responses are 1-5, normalize by subtracting 1 and dividing by 4)
        scores = {}
        for trait, values in trait_sums.items():
            if values:
                avg_score = sum(values) / len(values)
                normalized = (avg_score - 1) / 4  # Convert 1-5 scale to 0-1
                scores[trait.value] = round(normalized, 3)
            else:
                scores[trait.value] = 0.5  # Default middle value

        return PersonalityScore(**scores)

    @classmethod
    def generate_profile(cls, scores: PersonalityScore) -> PersonalityProfile:
        """Generate complete personality profile with recommendations"""

        # Determine primary trait (highest score)
        score_dict = scores.dict()
        primary_trait = PersonalityTrait(max(score_dict, key=score_dict.get))

        # Trait descriptions
        descriptions = {
            "openness": cls._describe_openness(scores.openness),
            "conscientiousness": cls._describe_conscientiousness(scores.conscientiousness),
            "extraversion": cls._describe_extraversion(scores.extraversion),
            "agreeableness": cls._describe_agreeableness(scores.agreeableness),
            "neuroticism": cls._describe_neuroticism(scores.neuroticism)
        }

        # Wellness recommendations based on profile
        recommendations = cls._generate_wellness_recommendations(scores)

        # Meal preferences
        meal_prefs = cls._generate_meal_preferences(scores)

        # Exercise preferences
        exercise_prefs = cls._generate_exercise_preferences(scores)

        return PersonalityProfile(
            scores=scores,
            primary_trait=primary_trait,
            trait_descriptions=descriptions,
            wellness_recommendations=recommendations,
            meal_preferences=meal_prefs,
            exercise_preferences=exercise_prefs
        )

    @staticmethod
    def _describe_openness(score: float) -> str:
        if score > 0.7:
            return "Very High - You are extremely creative, curious, and open to new experiences. You enjoy abstract thinking and appreciate art and beauty."
        elif score > 0.5:
            return "High - You are open-minded and enjoy exploring new ideas, cultures, and experiences."
        elif score > 0.3:
            return "Moderate - You balance openness to new experiences with appreciation for familiar routines."
        else:
            return "Low - You prefer familiar experiences and practical thinking over abstract ideas."

    @staticmethod
    def _describe_conscientiousness(score: float) -> str:
        if score > 0.7:
            return "Very High - You are extremely organized, disciplined, and detail-oriented. You plan ahead and follow through on commitments."
        elif score > 0.5:
            return "High - You are organized and reliable, preferring structure and planning."
        elif score > 0.3:
            return "Moderate - You balance organization with flexibility."
        else:
            return "Low - You tend to be more spontaneous and flexible, less focused on detailed planning."

    @staticmethod
    def _describe_extraversion(score: float) -> str:
        if score > 0.7:
            return "Very High - You are extremely outgoing and social. You gain energy from being around people."
        elif score > 0.5:
            return "High - You enjoy social interactions and feel comfortable in groups."
        elif score > 0.3:
            return "Moderate - You balance social time with alone time (ambivert)."
        else:
            return "Low - You are more introverted, preferring quiet environments and smaller social circles."

    @staticmethod
    def _describe_agreeableness(score: float) -> str:
        if score > 0.7:
            return "Very High - You are extremely compassionate, cooperative, and trusting. You prioritize harmony in relationships."
        elif score > 0.5:
            return "High - You are kind, empathetic, and considerate of others."
        elif score > 0.3:
            return "Moderate - You balance compassion with assertiveness."
        else:
            return "Low - You tend to be more competitive and direct, prioritizing honesty over harmony."

    @staticmethod
    def _describe_neuroticism(score: float) -> str:
        if score > 0.7:
            return "Very High - You experience stress and emotional ups and downs frequently. Focus on stress management is important."
        elif score > 0.5:
            return "High - You are more sensitive to stress and may experience mood fluctuations."
        elif score > 0.3:
            return "Moderate - You experience average levels of stress and emotional stability."
        else:
            return "Low - You are emotionally stable and resilient, remaining calm under pressure."

    @staticmethod
    def _generate_wellness_recommendations(scores: PersonalityScore) -> List[str]:
        """Generate personalized wellness recommendations"""
        recs = []

        # High Neuroticism -> stress management
        if scores.neuroticism > 0.6:
            recs.append("Practice daily meditation and breathing exercises to manage stress")
            recs.append("Consider adaptogenic herbs like Ashwagandha for emotional balance")
            recs.append("Maintain consistent sleep schedule to support emotional regulation")

        # High Conscientiousness -> avoid burnout
        if scores.conscientiousness > 0.7:
            recs.append("Schedule regular breaks to prevent burnout from overworking")
            recs.append("Practice self-compassion and allow flexibility in your routines")

        # Low Conscientiousness -> structure support
        if scores.conscientiousness < 0.4:
            recs.append("Use meal prep and planning tools to build healthy eating habits")
            recs.append("Set small, achievable daily goals to build consistency")

        # High Openness -> variety
        if scores.openness > 0.6:
            recs.append("Explore diverse cuisines and food experiences for meal enjoyment")
            recs.append("Try varied exercise modalities like yoga, dance, and martial arts")

        # High Extraversion -> social wellness
        if scores.extraversion > 0.6:
            recs.append("Join group fitness classes or meditation groups for motivation")
            recs.append("Cook and share meals with friends for social wellbeing")

        # Low Extraversion -> solitary practices
        if scores.extraversion < 0.4:
            recs.append("Focus on individual practices like solo meditation and journaling")
            recs.append("Create peaceful home environments for recharging")

        return recs or ["Continue your balanced approach to wellness"]

    @staticmethod
    def _generate_meal_preferences(scores: PersonalityScore) -> List[str]:
        """Generate meal preferences based on personality"""
        prefs = []

        if scores.openness > 0.6:
            prefs.append("Experimental flavors and exotic cuisines")
            prefs.append("Colorful, visually appealing meals")

        if scores.conscientiousness > 0.6:
            prefs.append("Meal prep and planned menus")
            prefs.append("Structured eating schedule")

        if scores.extraversion > 0.6:
            prefs.append("Social dining experiences")
            prefs.append("Cooking for groups")

        if scores.neuroticism > 0.6:
            prefs.append("Comfort foods for emotional balance")
            prefs.append("Calming herbal teas and warm meals")

        return prefs or ["Balanced, nutritious meals"]

    @staticmethod
    def _generate_exercise_preferences(scores: PersonalityScore) -> List[str]:
        """Generate exercise preferences"""
        prefs = []

        if scores.openness > 0.6:
            prefs.append("Varied workout routines with new challenges")
            prefs.append("Dance, martial arts, or adventurous activities")

        if scores.conscientiousness > 0.6:
            prefs.append("Structured workout programs with clear goals")
            prefs.append("Tracking progress and metrics")

        if scores.extraversion > 0.6:
            prefs.append("Group fitness classes and team sports")

        if scores.extraversion < 0.4:
            prefs.append("Solo activities like running, yoga, or swimming")

        if scores.neuroticism > 0.6:
            prefs.append("Gentle exercises like yoga and tai chi for stress relief")

        return prefs or ["Moderate, balanced exercise routine"]


# Singleton access
_big_five_assessment = BigFiveAssessment()


def get_big_five_assessment() -> BigFiveAssessment:
    """Get Big Five Assessment instance"""
    return _big_five_assessment
