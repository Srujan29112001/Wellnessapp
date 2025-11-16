"""
Spiritual Wellness Service - Enhanced spiritual profiling and guided practices

Includes:
- Comprehensive spiritual questionnaire
- Guided meditation scripts
- Breathing exercises
- Yoga flows
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class SpiritualOrientation(str, Enum):
    """Types of spiritual orientations"""
    SECULAR = "secular"  # Non-religious mindfulness
    YOGIC = "yogic"  # Yoga and Eastern philosophy
    BUDDHIST = "buddhist"
    HINDU = "hindu"
    CHRISTIAN = "christian"
    ISLAMIC = "islamic"
    JEWISH = "jewish"
    ECLECTIC = "eclectic"  # Mix of traditions
    NONE = "none"


class MeditationStyle(str, Enum):
    """Meditation preferences"""
    MINDFULNESS = "mindfulness"
    TRANSCENDENTAL = "transcendental"
    LOVING_KINDNESS = "loving_kindness"
    BODY_SCAN = "body_scan"
    VISUALIZATION = "visualization"
    MANTRA = "mantra"
    BREATH_FOCUS = "breath_focus"


class SpiritualProfile(BaseModel):
    """Complete spiritual wellness profile"""
    orientation: SpiritualOrientation
    meditation_experience: str  # beginner, intermediate, advanced
    daily_practice_minutes: int
    preferred_styles: List[MeditationStyle]
    chakra_focus: Optional[List[str]] = None
    astrological_system: str  # vedic, western, chinese, none
    spiritual_goals: List[str]
    practices: List[str]
    sacred_times: Optional[Dict] = None


class GuidedSession(BaseModel):
    """A guided practice session"""
    title: str
    session_type: str  # meditation, breathing, yoga
    duration_minutes: int
    difficulty: str  # beginner, intermediate, advanced
    script: List[str]  # Step-by-step instructions
    benefits: List[str]


class SpiritualAssessment:
    """Enhanced Spiritual Profile Questionnaire"""

    QUESTIONS = [
        {
            'id': 1,
            'text': 'How would you describe your spiritual or philosophical orientation?',
            'type': 'multiple_choice',
            'options': [opt.value for opt in SpiritualOrientation],
            'field': 'orientation'
        },
        {
            'id': 2,
            'text': 'What is your meditation experience level?',
            'type': 'multiple_choice',
            'options': ['beginner', 'intermediate', 'advanced'],
            'field': 'meditation_experience'
        },
        {
            'id': 3,
            'text': 'How many minutes per day do you currently practice meditation or mindfulness?',
            'type': 'number',
            'field': 'daily_practice_minutes'
        },
        {
            'id': 4,
            'text': 'Which meditation styles appeal to you? (Select all that apply)',
            'type': 'multi_select',
            'options': [style.value for style in MeditationStyle],
            'field': 'preferred_styles'
        },
        {
            'id': 5,
            'text': 'Do you work with chakras or energy centers?',
            'type': 'yes_no',
            'field': 'works_with_chakras'
        },
        {
            'id': 6,
            'text': 'Which chakras would you like to focus on? (If applicable)',
            'type': 'multi_select',
            'options': ['root', 'sacral', 'solar_plexus', 'heart', 'throat', 'third_eye', 'crown'],
            'field': 'chakra_focus'
        },
        {
            'id': 7,
            'text': 'Which astrological system do you follow, if any?',
            'type': 'multiple_choice',
            'options': ['vedic', 'western', 'chinese', 'none'],
            'field': 'astrological_system'
        },
        {
            'id': 8,
            'text': 'What are your spiritual or wellness goals? (Select all that apply)',
            'type': 'multi_select',
            'options': [
                'Reduce stress and anxiety',
                'Increase inner peace',
                'Develop intuition',
                'Improve focus and concentration',
                'Cultivate compassion',
                'Connect with higher purpose',
                'Enhance creativity',
                'Improve relationships',
                'Achieve enlightenment/self-realization'
            ],
            'field': 'spiritual_goals'
        },
        {
            'id': 9,
            'text': 'Which spiritual practices do you currently engage in? (Select all)',
            'type': 'multi_select',
            'options': [
                'Meditation',
                'Prayer',
                'Yoga',
                'Journaling',
                'Chanting/Mantras',
                'Energy healing',
                'Breathwork (Pranayama)',
                'Gratitude practice',
                'Nature connection',
                'Fasting/Cleansing',
                'Study of sacred texts'
            ],
            'field': 'practices'
        },
        {
            'id': 10,
            'text': 'Do you observe any sacred times or rituals?',
            'type': 'text',
            'field': 'sacred_times_description'
        }
    ]

    @classmethod
    def get_questions(cls) -> List[Dict]:
        """Return all assessment questions"""
        return cls.QUESTIONS

    @classmethod
    def create_profile(cls, responses: Dict) -> SpiritualProfile:
        """Create spiritual profile from responses"""
        return SpiritualProfile(
            orientation=responses.get('orientation', SpiritualOrientation.SECULAR),
            meditation_experience=responses.get('meditation_experience', 'beginner'),
            daily_practice_minutes=responses.get('daily_practice_minutes', 0),
            preferred_styles=responses.get('preferred_styles', [MeditationStyle.MINDFULNESS]),
            chakra_focus=responses.get('chakra_focus'),
            astrological_system=responses.get('astrological_system', 'none'),
            spiritual_goals=responses.get('spiritual_goals', []),
            practices=responses.get('practices', []),
            sacred_times=responses.get('sacred_times')
        )


class GuidedPracticeLibrary:
    """Library of guided meditation, breathing, and yoga sessions"""

    @staticmethod
    def get_breathing_exercise(duration_minutes: int = 5) -> GuidedSession:
        """Box Breathing Exercise"""
        script = [
            "Find a comfortable seated position with your spine straight.",
            "Close your eyes or soften your gaze downward.",
            "We'll practice box breathing: inhale for 4, hold for 4, exhale for 4, hold for 4.",
            "",
            "Round 1:",
            "Inhale deeply through your nose for 4 counts (1...2...3...4)",
            "Hold your breath for 4 counts (1...2...3...4)",
            "Exhale slowly through your mouth for 4 counts (1...2...3...4)",
            "Hold empty for 4 counts (1...2...3...4)",
            "",
            "Round 2:",
            "Inhale through your nose (1...2...3...4)",
            "Hold (1...2...3...4)",
            "Exhale through your mouth (1...2...3...4)",
            "Hold (1...2...3...4)",
            "",
            "Continue this pattern for the next few minutes...",
            "Notice how your body relaxes with each cycle.",
            "Your mind becomes calmer, more focused.",
            "",
            "Final round:",
            "Inhale (1...2...3...4)",
            "Hold (1...2...3...4)",
            "Exhale (1...2...3...4)",
            "Hold (1...2...3...4)",
            "",
            "Now return to natural breathing.",
            "Notice how you feel - more calm, centered, and present.",
            "When you're ready, slowly open your eyes.",
            "Take this sense of calm with you into your day."
        ]

        return GuidedSession(
            title="Box Breathing for Stress Relief",
            session_type="breathing",
            duration_minutes=duration_minutes,
            difficulty="beginner",
            script=script,
            benefits=[
                "Reduces stress and anxiety",
                "Lowers blood pressure",
                "Improves focus and concentration",
                "Activates parasympathetic nervous system"
            ]
        )

    @staticmethod
    def get_meditation_session(duration_minutes: int = 10, style: str = "mindfulness") -> GuidedSession:
        """Mindfulness Meditation"""
        if style == "mindfulness":
            script = [
                "Find a comfortable seated position.",
                "You can sit on a cushion, chair, or the floor - whatever feels stable.",
                "Lengthen your spine, relax your shoulders.",
                "",
                "Close your eyes or lower your gaze.",
                "Take three deep breaths to settle in.",
                "Inhale... Exhale...",
                "Inhale... Exhale...",
                "Inhale... Exhale...",
                "",
                "Now let your breath return to its natural rhythm.",
                "Simply observe the breath as it flows in and out.",
                "Notice the sensation at your nostrils, or the rise and fall of your belly.",
                "",
                "Your mind will wander - this is normal and expected.",
                "When you notice you're thinking, simply acknowledge it without judgment.",
                "Gently return your attention to the breath.",
                "",
                "Breathing in, know that you are breathing in.",
                "Breathing out, know that you are breathing out.",
                "",
                "Continue to anchor yourself in the present moment.",
                "Each breath is a new beginning.",
                "There's nowhere to go, nothing to do.",
                "Just this breath, just this moment.",
                "",
                "In the last minute, expand your awareness.",
                "Notice sounds around you, sensations in your body.",
                "Appreciate this time you've given yourself.",
                "",
                "When you're ready, slowly open your eyes.",
                "Carry this mindfulness into your next activity.",
                "You can return to this calm center anytime."
            ]

            benefits = [
                "Increases present-moment awareness",
                "Reduces rumination and worry",
                "Improves emotional regulation",
                "Enhances focus and concentration",
                "Cultivates inner peace"
            ]

        elif style == "loving_kindness":
            script = [
                "Sit comfortably and close your eyes.",
                "Take a few deep breaths to center yourself.",
                "",
                "Begin by directing loving-kindness toward yourself.",
                "Silently repeat these phrases:",
                "",
                "'May I be happy'",
                "'May I be healthy'",
                "'May I be safe'",
                "'May I live with ease'",
                "",
                "Feel the warmth of these wishes for yourself.",
                "You deserve kindness and compassion.",
                "",
                "Now bring to mind someone you love dearly.",
                "Visualize them clearly in your mind's eye.",
                "Extend these wishes to them:",
                "",
                "'May you be happy'",
                "'May you be healthy'",
                "'May you be safe'",
                "'May you live with ease'",
                "",
                "Feel your heart opening with love for them.",
                "",
                "Now think of a neutral person - someone you've seen but don't know well.",
                "Perhaps a cashier, a neighbor, a stranger on the street.",
                "Send them the same loving wishes:",
                "",
                "'May you be happy'",
                "'May you be healthy'",
                "'May you be safe'",
                "'May you live with ease'",
                "",
                "Finally, if you're ready, think of someone with whom you have difficulty.",
                "This is challenging but powerful work.",
                "Send them wishes for wellbeing:",
                "",
                "'May you be happy'",
                "'May you be healthy'",
                "'May you be safe'",
                "'May you live with ease'",
                "",
                "Now expand your circle of compassion to all beings everywhere.",
                "All humans, all animals, all life.",
                "",
                "'May all beings be happy'",
                "'May all beings be healthy'",
                "'May all beings be safe'",
                "'May all beings live with ease'",
                "",
                "Rest in this boundless loving-kindness.",
                "Slowly return your awareness to your breath.",
                "When ready, open your eyes."
            ]

            benefits = [
                "Increases compassion and empathy",
                "Reduces anger and resentment",
                "Improves relationships",
                "Enhances emotional wellbeing",
                "Cultivates forgiveness"
            ]
        else:
            # Default mindfulness
            script = GuidedPracticeLibrary.get_breathing_exercise(duration_minutes).script
            benefits = ["Promotes relaxation and stress relief"]

        return GuidedSession(
            title=f"{style.replace('_', ' ').title()} Meditation",
            session_type="meditation",
            duration_minutes=duration_minutes,
            difficulty="beginner" if style == "mindfulness" else "intermediate",
            script=script,
            benefits=benefits
        )

    @staticmethod
    def get_yoga_flow(duration_minutes: int = 15) -> GuidedSession:
        """Morning Sun Salutation Flow"""
        script = [
            "Stand at the top of your mat in Mountain Pose (Tadasana).",
            "Feet hip-width apart, weight evenly distributed.",
            "Hands at heart center in prayer position.",
            "Take three deep breaths.",
            "",
            "Sun Salutation A - Round 1:",
            "",
            "1. Mountain Pose - Stand tall, grounded",
            "",
            "2. Raised Arms (Urdhva Hastasana)",
            "   Inhale, sweep your arms up overhead",
            "   Gaze upward, lengthen your spine",
            "",
            "3. Standing Forward Fold (Uttanasana)",
            "   Exhale, fold forward from the hips",
            "   Let your head hang heavy",
            "   Hands to floor or blocks",
            "",
            "4. Half Lift (Ardha Uttanasana)",
            "   Inhale, lengthen your spine",
            "   Hands to shins, flat back",
            "",
            "5. Plank Pose",
            "   Exhale, step or jump back to plank",
            "   Shoulders over wrists, body in one line",
            "",
            "6. Four-Limbed Staff (Chaturanga) - MODIFICATION: Knees down",
            "   Exhale, lower halfway down",
            "   Elbows by your ribs",
            "",
            "7. Upward-Facing Dog (Urdhva Mukha Svanasana) or Cobra",
            "   Inhale, press into your hands",
            "   Open your chest, shoulders back",
            "",
            "8. Downward-Facing Dog (Adho Mukha Svanasana)",
            "   Exhale, lift your hips up and back",
            "   Form an inverted V shape",
            "   Hold for 5 breaths",
            "",
            "9. Step or Jump Forward",
            "   Inhale, look forward",
            "   Exhale, step feet to hands",
            "",
            "10. Half Lift",
            "    Inhale, lengthen spine",
            "",
            "11. Forward Fold",
            "    Exhale, fold",
            "",
            "12. Raised Arms",
            "    Inhale, rise up, arms overhead",
            "",
            "13. Mountain Pose",
            "    Exhale, hands to heart",
            "",
            "Rest for a breath, then repeat for 2 more rounds.",
            "",
            "After your final round:",
            "Stand in Mountain Pose",
            "Notice how your body feels - energized, awake, strong",
            "Take a moment of gratitude for your practice",
            "Namaste."
        ]

        return GuidedSession(
            title="Morning Sun Salutation Flow",
            session_type="yoga",
            duration_minutes=duration_minutes,
            difficulty="intermediate",
            script=script,
            benefits=[
                "Energizes the body",
                "Stretches and strengthens muscles",
                "Improves flexibility",
                "Enhances circulation",
                "Prepares mind and body for the day"
            ]
        )

    @staticmethod
    def get_session_recommendations(profile: SpiritualProfile) -> List[GuidedSession]:
        """Get recommended sessions based on spiritual profile"""
        recommendations = []

        # Add breathing if beginner or stressed
        recommendations.append(GuidedPracticeLibrary.get_breathing_exercise(5))

        # Add meditation based on preference
        if MeditationStyle.LOVING_KINDNESS in profile.preferred_styles:
            recommendations.append(
                GuidedPracticeLibrary.get_meditation_session(10, "loving_kindness")
            )
        else:
            recommendations.append(
                GuidedPracticeLibrary.get_meditation_session(10, "mindfulness")
            )

        # Add yoga if practiced
        if 'Yoga' in profile.practices:
            recommendations.append(GuidedPracticeLibrary.get_yoga_flow(15))

        return recommendations


# Singleton access
_spiritual_assessment = SpiritualAssessment()
_practice_library = GuidedPracticeLibrary()


def get_spiritual_assessment() -> SpiritualAssessment:
    """Get Spiritual Assessment instance"""
    return _spiritual_assessment


def get_practice_library() -> GuidedPracticeLibrary:
    """Get Guided Practice Library instance"""
    return _practice_library
