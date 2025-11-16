"""
Guided Wellness Sessions
Breathing exercises, meditation, yoga, and relaxation techniques
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionType(str, Enum):
    """Types of guided sessions"""
    BREATHING = "breathing"
    MEDITATION = "meditation"
    YOGA = "yoga"
    SLEEP = "sleep"
    STRESS_RELIEF = "stress_relief"
    FOCUS = "focus"
    ENERGY = "energy"


class GuidedSessionGenerator:
    """
    Generate guided wellness session scripts and instructions
    """

    def __init__(self):
        """Initialize session generator"""
        self.sessions = self._load_session_templates()

    def _load_session_templates(self) -> Dict:
        """Load predefined session templates"""
        return {
            SessionType.BREATHING: {
                "box_breathing": {
                    "name": "Box Breathing (4-4-4-4)",
                    "duration_minutes": 5,
                    "description": "Military-grade stress relief technique",
                    "benefits": [
                        "Reduces stress and anxiety",
                        "Improves focus and concentration",
                        "Lowers heart rate and blood pressure"
                    ],
                    "instructions": [
                        "Find a comfortable seated position",
                        "Close your eyes and relax your shoulders",
                        "Breathe in slowly through your nose for 4 counts",
                        "Hold your breath for 4 counts",
                        "Exhale slowly through your mouth for 4 counts",
                        "Hold empty for 4 counts",
                        "Repeat this cycle for 5 minutes"
                    ],
                    "script": """
Welcome to Box Breathing. This technique is used by Navy SEALs to stay calm under pressure.

Find a comfortable seated position. [PAUSE 3]

Close your eyes, and let your shoulders relax. [PAUSE 3]

We'll breathe together in a pattern of four counts each.

Breathe in through your nose... 1, 2, 3, 4. [PAUSE 4]

Hold... 1, 2, 3, 4. [PAUSE 4]

Exhale through your mouth... 1, 2, 3, 4. [PAUSE 4]

Hold empty... 1, 2, 3, 4. [PAUSE 4]

Again, breathe in... 1, 2, 3, 4. [PAUSE 4]

Hold... 1, 2, 3, 4. [PAUSE 4]

Exhale... 1, 2, 3, 4. [PAUSE 4]

Hold... 1, 2, 3, 4. [PAUSE 4]

Continue this pattern on your own for the next few minutes. [PAUSE 240]

Slowly open your eyes. Notice how you feel. Well done.
"""
                },
                "478_breathing": {
                    "name": "4-7-8 Breathing (Relaxing Breath)",
                    "duration_minutes": 3,
                    "description": "Dr. Andrew Weil's technique for falling asleep faster",
                    "benefits": [
                        "Induces deep relaxation",
                        "Helps with sleep onset",
                        "Reduces anxiety"
                    ],
                    "instructions": [
                        "Sit or lie down comfortably",
                        "Place tongue tip behind upper front teeth",
                        "Breathe in through nose for 4 counts",
                        "Hold breath for 7 counts",
                        "Exhale through mouth for 8 counts (whoosh sound)",
                        "Repeat 4 times"
                    ],
                    "script": """
Welcome to the 4-7-8 Breathing technique, designed by Dr. Andrew Weil.

Get comfortable, either sitting or lying down. [PAUSE 3]

Place the tip of your tongue behind your upper front teeth, and keep it there throughout. [PAUSE 3]

Exhale completely through your mouth, making a whoosh sound. [PAUSE 4]

Close your mouth. Breathe in quietly through your nose for 4 counts... 1, 2, 3, 4. [PAUSE 4]

Hold your breath for 7 counts... 1, 2, 3, 4, 5, 6, 7. [PAUSE 7]

Exhale completely through your mouth for 8 counts... 1, 2, 3, 4, 5, 6, 7, 8. [PAUSE 8]

That's one breath. Let's do it again. [PAUSE 2]

Breathe in through your nose... 1, 2, 3, 4. [PAUSE 4]

Hold... 1, 2, 3, 4, 5, 6, 7. [PAUSE 7]

Exhale through your mouth... 1, 2, 3, 4, 5, 6, 7, 8. [PAUSE 8]

Two more rounds on your own. [PAUSE 40]

Excellent. Notice the calm you've created.
"""
                },
                "energizing_breath": {
                    "name": "Energizing Breath (Kapalabhati)",
                    "duration_minutes": 5,
                    "description": "Yogic breathing to boost energy and mental clarity",
                    "benefits": [
                        "Increases energy and alertness",
                        "Clears mental fog",
                        "Stimulates digestion"
                    ],
                    "instructions": [
                        "Sit upright with straight spine",
                        "Take a deep breath in",
                        "Forcefully exhale through nose while contracting abs",
                        "Let inhalation happen passively",
                        "Repeat rapidly 20-30 times",
                        "Rest and observe"
                    ]
                }
            },

            SessionType.MEDITATION: {
                "body_scan": {
                    "name": "Body Scan Meditation",
                    "duration_minutes": 15,
                    "description": "Progressive relaxation for stress release",
                    "benefits": [
                        "Releases physical tension",
                        "Increases body awareness",
                        "Promotes deep relaxation"
                    ],
                    "script": """
Welcome to Body Scan Meditation.

Lie down on your back in a comfortable position. [PAUSE 5]

Close your eyes. Take three deep breaths. [PAUSE 15]

Bring your attention to your feet. Notice any sensations... warmth, coolness, tingling. [PAUSE 10]

As you breathe out, release any tension in your feet. [PAUSE 5]

Move your awareness to your calves... notice the contact with the surface beneath you. [PAUSE 10]

Breathe out any tightness. [PAUSE 5]

Shift to your thighs... heavy, relaxed. [PAUSE 10]

Your hips and pelvis... let them soften. [PAUSE 10]

Your abdomen... rising and falling with each breath. [PAUSE 10]

Your chest... heart beating steadily. [PAUSE 10]

Your shoulders... let them drop away from your ears. [PAUSE 10]

Your arms... hands... fingers... completely relaxed. [PAUSE 10]

Your neck... jaw... allow your face to soften. [PAUSE 10]

Your entire body, from toes to head, at ease. [PAUSE 20]

Take three more deep breaths. [PAUSE 15]

Slowly open your eyes. Move gently.
"""
                },
                "loving_kindness": {
                    "name": "Loving-Kindness Meditation (Metta)",
                    "duration_minutes": 10,
                    "description": "Cultivate compassion for self and others",
                    "benefits": [
                        "Increases positive emotions",
                        "Reduces self-criticism",
                        "Enhances empathy"
                    ],
                    "script": """
Welcome to Loving-Kindness Meditation.

Sit comfortably. Close your eyes. [PAUSE 5]

Begin by bringing yourself to mind. Picture yourself clearly. [PAUSE 5]

Silently repeat these phrases:

May I be happy. [PAUSE 3]
May I be healthy. [PAUSE 3]
May I be safe. [PAUSE 3]
May I live with ease. [PAUSE 5]

Feel the warmth of these wishes for yourself. [PAUSE 10]

Now bring to mind someone you love. See their face. [PAUSE 5]

May you be happy. [PAUSE 3]
May you be healthy. [PAUSE 3]
May you be safe. [PAUSE 3]
May you live with ease. [PAUSE 5]

Extend these wishes further, to a neutral person... someone you barely know. [PAUSE 5]

May you be happy. May you be healthy. May you be safe. May you live with ease. [PAUSE 10]

Finally, extend loving-kindness to all beings everywhere. [PAUSE 5]

May all beings be happy. [PAUSE 3]
May all beings be healthy. [PAUSE 3]
May all beings be safe. [PAUSE 3]
May all beings live with ease. [PAUSE 10]

Rest in this feeling of universal goodwill. [PAUSE 15]

Gently open your eyes.
"""
                },
                "mindfulness": {
                    "name": "Mindfulness of Breath",
                    "duration_minutes": 10,
                    "description": "Foundation mindfulness practice",
                    "benefits": [
                        "Improves concentration",
                        "Reduces mind wandering",
                        "Builds awareness"
                    ]
                }
            },

            SessionType.SLEEP: {
                "sleep_story": {
                    "name": "Sleep Story: Forest Walk",
                    "duration_minutes": 20,
                    "description": "Guided visualization for sleep",
                    "script": """
Close your eyes. Let your body sink into the bed. [PAUSE 5]

Imagine you're walking on a soft forest path. [PAUSE 5]

The air is cool and fresh. You hear birds singing in the distance. [PAUSE 5]

Sunlight filters through the leaves above, creating dancing shadows. [PAUSE 5]

With each step, you feel more relaxed. [PAUSE 5]

You come to a small stream. The water flows gently over smooth stones. [PAUSE 10]

You sit by the stream, listening to its soothing sound. [PAUSE 10]

Your breathing slows. Your mind quiets. [PAUSE 10]

You are completely at peace. [PAUSE 20]

Let yourself drift into sleep...
"""
                }
            },

            SessionType.STRESS_RELIEF: {
                "5_senses": {
                    "name": "5-4-3-2-1 Grounding Exercise",
                    "duration_minutes": 5,
                    "description": "Sensory grounding for anxiety",
                    "instructions": [
                        "Acknowledge 5 things you can see",
                        "Acknowledge 4 things you can touch",
                        "Acknowledge 3 things you can hear",
                        "Acknowledge 2 things you can smell",
                        "Acknowledge 1 thing you can taste"
                    ]
                }
            },

            SessionType.FOCUS: {
                "pomodoro_prep": {
                    "name": "Pomodoro Preparation",
                    "duration_minutes": 2,
                    "description": "Mental preparation for focused work",
                    "script": """
You're about to begin a focused work session.

Take a deep breath. [PAUSE 3]

Set a clear intention for what you'll accomplish. [PAUSE 5]

Eliminate distractions. [PAUSE 3]

Your mind is sharp. Your focus is clear. [PAUSE 3]

Begin.
"""
                }
            }
        }

    def get_session(
        self,
        session_type: SessionType,
        variant: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict:
        """
        Get a guided session

        Args:
            session_type: Type of session
            variant: Specific variant (e.g., "box_breathing")
            duration_minutes: Customize duration

        Returns:
            Session details with script and instructions
        """
        sessions = self.sessions.get(session_type, {})

        if not sessions:
            logger.warning(f"No sessions found for type: {session_type}")
            return {}

        # Get specific variant or first available
        if variant and variant in sessions:
            session = sessions[variant]
        else:
            # Get first session of this type
            session = list(sessions.values())[0]

        # Customize duration if specified
        if duration_minutes:
            session = session.copy()
            session["duration_minutes"] = duration_minutes

        return session

    def get_available_sessions(self, session_type: Optional[SessionType] = None) -> List[Dict]:
        """Get list of available sessions"""
        if session_type:
            sessions = self.sessions.get(session_type, {})
            return [
                {
                    "type": session_type,
                    "variant": variant,
                    "name": info["name"],
                    "duration": info["duration_minutes"],
                    "description": info.get("description", "")
                }
                for variant, info in sessions.items()
            ]
        else:
            # All sessions
            all_sessions = []
            for stype, sessions in self.sessions.items():
                for variant, info in sessions.items():
                    all_sessions.append({
                        "type": stype,
                        "variant": variant,
                        "name": info["name"],
                        "duration": info["duration_minutes"],
                        "description": info.get("description", "")
                    })
            return all_sessions

    def create_custom_session(
        self,
        session_type: SessionType,
        user_goal: str,
        duration_minutes: int
    ) -> Dict:
        """
        Create a custom session based on user goal

        Args:
            session_type: Type of session
            user_goal: User's specific goal
            duration_minutes: Desired duration

        Returns:
            Custom session
        """
        # This could use LLM to generate custom scripts
        # For now, return a base session with customization
        base_session = self.get_session(session_type)

        custom_session = base_session.copy()
        custom_session["custom"] = True
        custom_session["user_goal"] = user_goal
        custom_session["duration_minutes"] = duration_minutes

        return custom_session

    def log_session_completion(
        self,
        user_id: str,
        session_type: SessionType,
        variant: str,
        completed: bool,
        feedback: Optional[str] = None
    ) -> Dict:
        """Log session completion for tracking"""
        log_entry = {
            "user_id": user_id,
            "session_type": session_type,
            "variant": variant,
            "completed": completed,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        }

        # In production, save to database
        logger.info(f"Session completed: {session_type}/{variant} by {user_id}")

        return log_entry


# Singleton
_session_generator: Optional[GuidedSessionGenerator] = None


def get_session_generator() -> GuidedSessionGenerator:
    """Get or create session generator singleton"""
    global _session_generator
    if _session_generator is None:
        _session_generator = GuidedSessionGenerator()
    return _session_generator
