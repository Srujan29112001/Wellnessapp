"""
Full Natal Chart Calculator.

Generates complete astrological birth chart with:
- All planets, houses, and aspects
- Vedic (Sidereal) and Western (Tropical) systems
- Health insights from planetary positions
- Wellness recommendations based on chart
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math
import json
from pathlib import Path


@dataclass
class PlanetPosition:
    """Planet position in chart."""
    name: str
    sign: str
    degree: float
    house: int
    retrograde: bool = False
    dignity: str = ""  # domicile, exaltation, detriment, fall, or neutral


@dataclass
class HouseInfo:
    """House information."""
    number: int
    sign: str
    degree: float
    ruling_planet: str
    significance: str


@dataclass
class Aspect:
    """Aspect between two planets."""
    planet1: str
    planet2: str
    type: str  # conjunction, opposition, trine, square, sextile
    angle: float
    orb: float
    applying: bool  # True if aspect is applying, False if separating


@dataclass
class NatalChart:
    """Complete natal chart."""
    # Birth details
    birth_date: datetime
    birth_place: str
    latitude: float
    longitude: float
    timezone_offset: float

    # Chart type
    chart_system: str = "tropical"  # or "sidereal"

    # Chart elements
    planets: List[PlanetPosition] = field(default_factory=list)
    houses: List[HouseInfo] = field(default_factory=list)
    aspects: List[Aspect] = field(default_factory=list)

    # Derived information
    ascendant: Optional[PlanetPosition] = None
    midheaven: Optional[PlanetPosition] = None
    sun_sign: str = ""
    moon_sign: str = ""
    rising_sign: str = ""

    # Health-specific insights
    health_indicators: Dict = field(default_factory=dict)
    wellness_recommendations: List[str] = field(default_factory=list)
    vulnerable_body_parts: List[str] = field(default_factory=list)
    dietary_guidance: List[str] = field(default_factory=list)


class NatalChartService:
    """Service for calculating natal charts."""

    # Zodiac signs
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    # Planet names
    PLANETS = [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
    ]

    # House significations
    HOUSE_MEANINGS = {
        1: "Self, appearance, vitality, overall health",
        2: "Resources, voice, throat, neck, food intake",
        3: "Communication, shoulders, arms, nervous system",
        4: "Home, chest, breasts, emotional health",
        5: "Creativity, stomach, heart, children",
        6: "Health, daily routine, digestive system, illness",
        7: "Partnerships, kidneys, lower back",
        8: "Transformation, reproductive organs, chronic issues",
        9: "Philosophy, hips, thighs, liver",
        10: "Career, knees, bones, structure",
        11: "Community, ankles, circulatory system",
        12: "Spirituality, feet, immune system, hidden illnesses"
    }

    # Planet-body part rulership
    PLANET_BODY_PARTS = {
        "Sun": ["Heart", "Spine", "Vitality", "Eyes (right)"],
        "Moon": ["Stomach", "Breasts", "Fluids", "Eyes (left)", "Emotions"],
        "Mercury": ["Nervous system", "Lungs", "Hands", "Communication"],
        "Venus": ["Kidneys", "Throat", "Skin", "Reproductive organs"],
        "Mars": ["Blood", "Muscles", "Head", "Energy", "Immune response"],
        "Jupiter": ["Liver", "Hips", "Thighs", "Growth", "Fat metabolism"],
        "Saturn": ["Bones", "Teeth", "Skin", "Joints", "Chronic conditions"],
        "Uranus": ["Nervous system", "Ankles", "Sudden changes"],
        "Neptune": ["Pineal gland", "Feet", "Immune system", "Psychic sensitivity"],
        "Pluto": ["Reproductive organs", "Elimination", "Regeneration"]
    }

    # Health insights by sign
    SIGN_HEALTH = {
        "Aries": {
            "strengths": ["High energy", "Quick recovery"],
            "vulnerabilities": ["Headaches", "Inflammation", "Accidents"],
            "recommendations": ["Manage stress", "Cooling foods", "Protect head"]
        },
        "Taurus": {
            "strengths": ["Strong constitution", "Endurance"],
            "vulnerabilities": ["Throat issues", "Weight gain", "Thyroid"],
            "recommendations": ["Regular exercise", "Throat care", "Metabolism support"]
        },
        "Gemini": {
            "strengths": ["Mental agility", "Adaptability"],
            "vulnerabilities": ["Anxiety", "Respiratory issues", "Nervous tension"],
            "recommendations": ["Grounding practices", "Deep breathing", "Routine"]
        },
        "Cancer": {
            "strengths": ["Strong intuition", "Nurturing"],
            "vulnerabilities": ["Digestive issues", "Emotional eating", "Water retention"],
            "recommendations": ["Emotional processing", "Digestive enzymes", "Comfort without food"]
        },
        "Leo": {
            "strengths": ["Vitality", "Strong heart"],
            "vulnerabilities": ["Heart issues", "Back pain", "Burnout"],
            "recommendations": ["Heart-healthy diet", "Spinal care", "Rest periods"]
        },
        "Virgo": {
            "strengths": ["Health consciousness", "Attention to detail"],
            "vulnerabilities": ["Digestive sensitivity", "Anxiety", "Perfectionism stress"],
            "recommendations": ["Probiotics", "Relaxation", "Self-compassion"]
        },
        "Libra": {
            "strengths": ["Balance seeking", "Social wellness"],
            "vulnerabilities": ["Kidney issues", "Lower back pain", "Indecision stress"],
            "recommendations": ["Hydration", "Back exercises", "Clear boundaries"]
        },
        "Scorpio": {
            "strengths": ["Regenerative capacity", "Deep healing"],
            "vulnerabilities": ["Reproductive issues", "Intense emotions", "Obsessive tendencies"],
            "recommendations": ["Emotional release", "Reproductive health", "Detoxification"]
        },
        "Sagittarius": {
            "strengths": ["Optimism", "Resilience"],
            "vulnerabilities": ["Hip/thigh issues", "Liver stress", "Overindulgence"],
            "recommendations": ["Moderation", "Liver support", "Hip flexibility"]
        },
        "Capricorn": {
            "strengths": ["Discipline", "Longevity"],
            "vulnerabilities": ["Bone/joint issues", "Depression", "Rigidity"],
            "recommendations": ["Calcium/Vitamin D", "Flexibility", "Joy cultivation"]
        },
        "Aquarius": {
            "strengths": ["Innovation", "Unique health approaches"],
            "vulnerabilities": ["Circulation issues", "Ankle problems", "Nervous system"],
            "recommendations": ["Movement", "Grounding", "Circulation support"]
        },
        "Pisces": {
            "strengths": ["Sensitivity", "Intuitive healing"],
            "vulnerabilities": ["Feet problems", "Immune weakness", "Escapism"],
            "recommendations": ["Foot care", "Immune support", "Healthy boundaries"]
        }
    }

    def __init__(self, use_swiss_ephemeris: bool = False):
        """
        Initialize natal chart service.

        Args:
            use_swiss_ephemeris: Use Swiss Ephemeris for precise calculations
                                (requires pyswisseph library)
        """
        self.use_swiss_ephemeris = use_swiss_ephemeris

        if use_swiss_ephemeris:
            try:
                import swisseph as swe
                self.swe = swe
                print("✅ Using Swiss Ephemeris for precise calculations")
            except ImportError:
                print("⚠️  Swiss Ephemeris not available, using simplified calculations")
                self.use_swiss_ephemeris = False
                self.swe = None
        else:
            self.swe = None

    def calculate_natal_chart(
        self,
        birth_date: datetime,
        latitude: float,
        longitude: float,
        birth_place: str = "",
        chart_system: str = "tropical"
    ) -> NatalChart:
        """
        Calculate complete natal chart.

        Args:
            birth_date: Birth date and time (timezone-aware)
            latitude: Birth latitude
            longitude: Birth longitude
            birth_place: Birth place name
            chart_system: "tropical" (Western) or "sidereal" (Vedic)

        Returns:
            Complete natal chart
        """
        chart = NatalChart(
            birth_date=birth_date,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            timezone_offset=birth_date.utcoffset().total_seconds() / 3600 if birth_date.utcoffset() else 0,
            chart_system=chart_system
        )

        if self.use_swiss_ephemeris and self.swe:
            self._calculate_with_swiss_ephemeris(chart)
        else:
            self._calculate_simplified(chart)

        # Generate health insights
        self._generate_health_insights(chart)

        return chart

    def _calculate_with_swiss_ephemeris(self, chart: NatalChart):
        """Calculate chart using Swiss Ephemeris (most accurate)."""
        import swisseph as swe

        # Convert datetime to Julian Day
        jd = swe.julday(
            chart.birth_date.year,
            chart.birth_date.month,
            chart.birth_date.day,
            chart.birth_date.hour + chart.birth_date.minute / 60.0
        )

        # Calculate houses (Placidus system)
        houses, ascmc = swe.houses(
            jd,
            chart.latitude,
            chart.longitude,
            b'P'  # Placidus
        )

        # Ascendant and MC
        asc_degree = ascmc[0]
        mc_degree = ascmc[1]

        asc_sign_index = int(asc_degree / 30)
        chart.rising_sign = self.SIGNS[asc_sign_index]
        chart.ascendant = PlanetPosition(
            name="Ascendant",
            sign=chart.rising_sign,
            degree=asc_degree % 30,
            house=1
        )

        mc_sign_index = int(mc_degree / 30)
        chart.midheaven = PlanetPosition(
            name="Midheaven",
            sign=self.SIGNS[mc_sign_index],
            degree=mc_degree % 30,
            house=10
        )

        # Calculate planets
        planet_ids = [
            swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
            swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO
        ]

        for i, planet_id in enumerate(planet_ids):
            planet_data = swe.calc_ut(jd, planet_id)
            longitude = planet_data[0][0]

            # Adjust for sidereal if needed
            if chart.chart_system == "sidereal":
                ayanamsa = swe.get_ayanamsa_ut(jd)
                longitude -= ayanamsa

            sign_index = int(longitude / 30) % 12
            sign = self.SIGNS[sign_index]
            degree = longitude % 30

            # Determine house
            house = self._determine_house(longitude, houses)

            # Check if retrograde
            retrograde = planet_data[0][3] < 0

            planet = PlanetPosition(
                name=self.PLANETS[i],
                sign=sign,
                degree=degree,
                house=house,
                retrograde=retrograde
            )

            chart.planets.append(planet)

            # Store sun and moon signs
            if planet.name == "Sun":
                chart.sun_sign = sign
            elif planet.name == "Moon":
                chart.moon_sign = sign

        # Calculate houses
        for i, house_cusp in enumerate(houses):
            if i < 12:
                sign_index = int(house_cusp / 30) % 12
                house_info = HouseInfo(
                    number=i + 1,
                    sign=self.SIGNS[sign_index],
                    degree=house_cusp % 30,
                    ruling_planet=self._get_ruling_planet(self.SIGNS[sign_index]),
                    significance=self.HOUSE_MEANINGS.get(i + 1, "")
                )
                chart.houses.append(house_info)

        # Calculate aspects
        chart.aspects = self._calculate_aspects(chart.planets)

    def _calculate_simplified(self, chart: NatalChart):
        """Simplified calculation without Swiss Ephemeris."""
        # This is a simplified version for demo purposes
        # In production, you should use Swiss Ephemeris or similar library

        # For now, use sun sign based on birth month
        month = chart.birth_date.month
        day = chart.birth_date.day

        # Approximate sun sign
        sun_sign_index = self._get_sun_sign_index(month, day)
        chart.sun_sign = self.SIGNS[sun_sign_index]

        # Create basic sun position
        sun = PlanetPosition(
            name="Sun",
            sign=chart.sun_sign,
            degree=15.0,  # Approximate mid-sign
            house=1  # Simplified
        )
        chart.planets.append(sun)

        # Approximate moon and other planets
        # This is very simplified - real calculation needs ephemeris data
        print("⚠️  Using simplified calculations. Install pyswisseph for accurate charts.")
        print("   pip install pyswisseph")

    def _get_sun_sign_index(self, month: int, day: int) -> int:
        """Get sun sign index from birth date (simplified)."""
        sun_sign_dates = [
            (3, 21), (4, 20), (5, 21), (6, 21),
            (7, 23), (8, 23), (9, 23), (10, 23),
            (11, 22), (12, 22), (1, 20), (2, 19)
        ]

        for i, (start_month, start_day) in enumerate(sun_sign_dates):
            next_i = (i + 1) % 12
            end_month, end_day = sun_sign_dates[next_i]

            if start_month <= month <= (end_month if end_month >= start_month else 12):
                if month == start_month and day < start_day:
                    return (i - 1) % 12
                return i

        return 0

    def _determine_house(self, planet_longitude: float, house_cusps: List[float]) -> int:
        """Determine which house a planet is in."""
        for i in range(12):
            house_start = house_cusps[i]
            house_end = house_cusps[(i + 1) % 12]

            # Handle wrap-around at 360°
            if house_end < house_start:
                if planet_longitude >= house_start or planet_longitude < house_end:
                    return i + 1
            else:
                if house_start <= planet_longitude < house_end:
                    return i + 1

        return 1  # Default to 1st house

    def _get_ruling_planet(self, sign: str) -> str:
        """Get ruling planet of zodiac sign."""
        rulers = {
            "Aries": "Mars",
            "Taurus": "Venus",
            "Gemini": "Mercury",
            "Cancer": "Moon",
            "Leo": "Sun",
            "Virgo": "Mercury",
            "Libra": "Venus",
            "Scorpio": "Pluto",
            "Sagittarius": "Jupiter",
            "Capricorn": "Saturn",
            "Aquarius": "Uranus",
            "Pisces": "Neptune"
        }
        return rulers.get(sign, "Unknown")

    def _calculate_aspects(self, planets: List[PlanetPosition]) -> List[Aspect]:
        """Calculate aspects between planets."""
        aspects = []

        # Aspect definitions (angle, orb)
        aspect_types = {
            "conjunction": (0, 8),
            "opposition": (180, 8),
            "trine": (120, 8),
            "square": (90, 8),
            "sextile": (60, 6),
        }

        for i, planet1 in enumerate(planets):
            for planet2 in planets[i+1:]:
                # Calculate angular distance
                angle = abs(
                    (planet1.degree + planet1.sign.index(planet1.sign) * 30) -
                    (planet2.degree + planet2.sign.index(planet2.sign) * 30)
                )

                # Normalize to 0-180
                if angle > 180:
                    angle = 360 - angle

                # Check each aspect type
                for aspect_name, (target_angle, orb) in aspect_types.items():
                    if abs(angle - target_angle) <= orb:
                        aspect = Aspect(
                            planet1=planet1.name,
                            planet2=planet2.name,
                            type=aspect_name,
                            angle=angle,
                            orb=abs(angle - target_angle),
                            applying=True  # Simplified
                        )
                        aspects.append(aspect)
                        break

        return aspects

    def _generate_health_insights(self, chart: NatalChart):
        """Generate health insights from natal chart."""
        health_indicators = {
            "vitality_level": "moderate",
            "constitution": "balanced",
            "vulnerable_systems": [],
            "strengths": [],
            "recommended_focus": []
        }

        # Analyze Sun (vitality)
        sun = next((p for p in chart.planets if p.name == "Sun"), None)
        if sun:
            sun_health = self.SIGN_HEALTH.get(sun.sign, {})
            health_indicators["strengths"].extend(sun_health.get("strengths", []))
            health_indicators["vulnerable_systems"].extend(sun_health.get("vulnerabilities", []))
            chart.wellness_recommendations.extend(sun_health.get("recommendations", []))
            chart.vulnerable_body_parts.extend(self.PLANET_BODY_PARTS.get("Sun", []))

        # Analyze Moon (emotional/fluid health)
        moon = next((p for p in chart.planets if p.name == "Moon"), None)
        if moon:
            moon_health = self.SIGN_HEALTH.get(moon.sign, {})
            health_indicators["vulnerable_systems"].extend(moon_health.get("vulnerabilities", []))
            chart.vulnerable_body_parts.extend(self.PLANET_BODY_PARTS.get("Moon", []))

        # Analyze 6th house (health and disease)
        sixth_house = next((h for h in chart.houses if h.number == 6), None)
        if sixth_house:
            house_health = self.SIGN_HEALTH.get(sixth_house.sign, {})
            chart.wellness_recommendations.append(
                f"6th house focus: {', '.join(house_health.get('recommendations', []))}"
            )

        # Analyze planets in 6th house
        sixth_house_planets = [p for p in chart.planets if p.house == 6]
        for planet in sixth_house_planets:
            chart.vulnerable_body_parts.extend(
                self.PLANET_BODY_PARTS.get(planet.name, [])
            )

        chart.health_indicators = health_indicators

        # Dietary guidance based on sun sign
        if sun:
            chart.dietary_guidance = self._get_dietary_guidance(sun.sign)

    def _get_dietary_guidance(self, sun_sign: str) -> List[str]:
        """Get dietary guidance based on sun sign."""
        dietary_guides = {
            "Aries": ["Cooling foods", "Reduce red meat", "Avoid excessive spice"],
            "Taurus": ["Light meals", "Avoid excess sweets", "Stimulating spices"],
            "Gemini": ["Warm, grounding foods", "Regular meal times", "Avoid cold/raw excess"],
            "Cancer": ["Easy-to-digest", "Probiotic-rich", "Warm liquids"],
            "Leo": ["Heart-healthy fats", "Cooling foods", "Moderate portions"],
            "Virgo": ["Simple, pure ingredients", "Probiotics", "Avoid processed"],
            "Libra": ["Balanced meals", "Kidney-supporting foods", "Adequate hydration"],
            "Scorpio": ["Detoxifying foods", "Avoid excess stimulants", "Cleansing herbs"],
            "Sagittarius": ["Moderation", "Liver-supporting", "Avoid overindulgence"],
            "Capricorn": ["Calcium-rich", "Warming foods", "Regular meals"],
            "Aquarius": ["Circulation-boosting", "Varied diet", "Adequate protein"],
            "Pisces": ["Immune-supporting", "Avoid excess sugar", "Grounding foods"]
        }
        return dietary_guides.get(sun_sign, ["Balanced, whole foods"])

    def export_chart_summary(self, chart: NatalChart) -> Dict:
        """Export chart as dictionary for API/frontend."""
        return {
            "birth_info": {
                "date": chart.birth_date.isoformat(),
                "place": chart.birth_place,
                "latitude": chart.latitude,
                "longitude": chart.longitude,
                "system": chart.chart_system
            },
            "core_placements": {
                "sun_sign": chart.sun_sign,
                "moon_sign": chart.moon_sign,
                "rising_sign": chart.rising_sign
            },
            "planets": [
                {
                    "name": p.name,
                    "sign": p.sign,
                    "degree": round(p.degree, 2),
                    "house": p.house,
                    "retrograde": p.retrograde
                }
                for p in chart.planets
            ],
            "houses": [
                {
                    "number": h.number,
                    "sign": h.sign,
                    "ruling_planet": h.ruling_planet,
                    "significance": h.significance
                }
                for h in chart.houses
            ],
            "aspects": [
                {
                    "planet1": a.planet1,
                    "planet2": a.planet2,
                    "type": a.type,
                    "angle": round(a.angle, 2)
                }
                for a in chart.aspects
            ],
            "health_insights": {
                "vulnerable_body_parts": chart.vulnerable_body_parts,
                "wellness_recommendations": chart.wellness_recommendations,
                "dietary_guidance": chart.dietary_guidance,
                "health_indicators": chart.health_indicators
            }
        }


# Singleton
_natal_chart_service = None

def get_natal_chart_service() -> NatalChartService:
    """Get singleton natal chart service."""
    global _natal_chart_service
    if _natal_chart_service is None:
        _natal_chart_service = NatalChartService(use_swiss_ephemeris=True)
    return _natal_chart_service


# Example usage
if __name__ == "__main__":
    from datetime import datetime, timezone, timedelta

    service = NatalChartService(use_swiss_ephemeris=True)

    # Example birth data
    birth_datetime = datetime(1990, 7, 25, 14, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))  # IST
    latitude = 19.0760  # Mumbai
    longitude = 72.8777

    print("=== Calculating Natal Chart ===\n")
    chart = service.calculate_natal_chart(
        birth_date=birth_datetime,
        latitude=latitude,
        longitude=longitude,
        birth_place="Mumbai, India",
        chart_system="tropical"
    )

    print(f"Birth: {chart.birth_date}")
    print(f"Place: {chart.birth_place}")
    print(f"\nSun Sign: {chart.sun_sign}")
    print(f"Moon Sign: {chart.moon_sign}")
    print(f"Rising Sign: {chart.rising_sign}")

    print(f"\nPlanetary Positions:")
    for planet in chart.planets[:5]:  # First 5 planets
        retro = " (R)" if planet.retrograde else ""
        print(f"  {planet.name}: {planet.sign} {planet.degree:.2f}° (House {planet.house}){retro}")

    print(f"\nHealth Insights:")
    print(f"  Vulnerable Areas: {', '.join(chart.vulnerable_body_parts[:5])}")
    print(f"  Recommendations:")
    for rec in chart.wellness_recommendations[:3]:
        print(f"    - {rec}")

    print(f"\n  Dietary Guidance:")
    for guide in chart.dietary_guidance:
        print(f"    - {guide}")

    # Export summary
    summary = service.export_chart_summary(chart)
    print(f"\nChart calculated successfully!")
    print(f"Total planets: {len(summary['planets'])}")
    print(f"Total aspects: {len(summary['aspects'])}")
