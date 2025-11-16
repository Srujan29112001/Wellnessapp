"""
Wellness AI - Streamlit Frontend

Multi-page application for holistic health tracking and AI coaching
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import os
import io
import time

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/v1"

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Page configuration
st.set_page_config(
    page_title="Wellness AI",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recommendation-card {
        background-color: #e1f5ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def make_api_request(method, endpoint, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE}{endpoint}"
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Please ensure the backend server is running.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Sidebar navigation
st.sidebar.title("🧘 Wellness AI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard", "🌟 Life Optimization", "📅 My Plan", "🧠 EEG Analysis", "💬 AI Coach", "📊 Health Metrics", "🥗 Nutrition", "💊 Supplements", "⚙️ Settings"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Wellness AI** combines:
- 🌟 Life Optimization System
- 🧠 EEG brainwave analysis
- 💬 AI wellness coaching
- 🥗 Personalized meal plans
- 📅 Optimized daily schedules
- 🧘 Ayurvedic principles
""")

# ============================================================================
# PAGE: Dashboard
# ============================================================================
if page == "🏠 Dashboard":
    st.markdown("<h1 class='main-header'>🏠 Wellness Dashboard</h1>", unsafe_allow_html=True)

    user_id = st.session_state.user_id

    # Fetch data from backend
    with st.spinner("Loading dashboard data..."):
        # Get latest health metrics
        health_data = make_api_request("GET", f"/health/?user_id={user_id}&limit=7")

        # Get latest EEG analysis
        eeg_data = make_api_request("GET", f"/eeg/analysis?user_id={user_id}&limit=7")

        # Get recommendations
        rec_data = make_api_request("POST", "/recommendations/", json={"user_id": user_id})

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Default values
    stress_level = "N/A"
    stress_delta = None
    focus_score = "N/A"
    focus_delta = None
    sleep_quality = "N/A"
    sleep_delta = None
    wellness_score = "N/A"

    # Calculate metrics from latest EEG data
    if eeg_data and len(eeg_data) > 0:
        latest_eeg = eeg_data[0]
        stress_level = latest_eeg.get('mental_state', 'N/A')
        focus_score = f"{int(latest_eeg.get('focus', 0) * 100)}/100"

        if len(eeg_data) > 1:
            prev_eeg = eeg_data[1]
            focus_delta = int((latest_eeg.get('focus', 0) - prev_eeg.get('focus', 0)) * 100)

    # Calculate sleep from health metrics
    if health_data and len(health_data) > 0:
        latest_health = health_data[0]
        if latest_health.get('sleep_hours'):
            sleep_quality = f"{latest_health['sleep_hours']:.1f} hrs"

            if len(health_data) > 1:
                prev_health = health_data[1]
                if prev_health.get('sleep_hours'):
                    sleep_delta = latest_health['sleep_hours'] - prev_health['sleep_hours']

    # Calculate wellness score (average of available metrics)
    if eeg_data and len(eeg_data) > 0:
        latest_eeg = eeg_data[0]
        wellness = (
            latest_eeg.get('focus', 0) * 100 +
            latest_eeg.get('relaxation', 0) * 100 -
            latest_eeg.get('stress', 0) * 50
        )
        wellness_score = f"{int(wellness)}/100"

    with col1:
        st.metric(
            label="Mental State",
            value=stress_level,
            delta=None
        )

    with col2:
        st.metric(
            label="Focus Score",
            value=focus_score,
            delta=f"{focus_delta:+d} points" if focus_delta is not None else None
        )

    with col3:
        st.metric(
            label="Sleep Quality",
            value=sleep_quality,
            delta=f"{sleep_delta:+.1f} hrs" if sleep_delta is not None else None
        )

    with col4:
        st.metric(
            label="Wellness Score",
            value=wellness_score,
            delta=None
        )

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Stress Trends (Last 7 Days)")

        if eeg_data and len(eeg_data) > 0:
            # Reverse to show oldest to newest
            eeg_reversed = list(reversed(eeg_data))
            dates = [datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')).strftime("%m/%d") for e in eeg_reversed]
            stress_levels = [e.get('stress', 0) for e in eeg_reversed]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=stress_levels,
                mode='lines+markers',
                name='Stress Level',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))

            fig.update_layout(
                yaxis_title="Stress Level (0-1)",
                xaxis_title="Date",
                hovermode='x unified',
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No EEG data available yet. Upload EEG data to see stress trends.")

    with col2:
        st.subheader("🎯 Today's Recommendations")

        if rec_data and len(rec_data) > 0:
            for rec in rec_data[:3]:  # Show top 3 recommendations
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get('priority', 'low'), "🔵")
                st.markdown(f"""
                <div class='recommendation-card'>
                <strong>{priority_emoji} {rec.get('title', 'Recommendation')}</strong><br>
                {rec.get('description', '')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='recommendation-card'>
            <strong>🧘 Welcome!</strong><br>
            Start logging your health data to receive personalized recommendations.
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# PAGE: Life Optimization - Assessment Wizard
# ============================================================================
elif page == "🌟 Life Optimization":
    st.markdown("<h1 class='main-header'>🌟 Life Optimization System</h1>", unsafe_allow_html=True)

    st.markdown("""
    ### Create Your Personalized Wellness Plan

    Complete this comprehensive assessment to receive:
    - **Personalized Meal Plans** (budget-optimized, dosha-balanced)
    - **Optimized Daily Schedules** (energy-based, chronotype-aligned)
    - **Nutritional Guidance** (macros, micros, Ayurvedic)
    - **Holistic Wellness Tracking** (6-dimensional scoring)
    """)

    # Check if profile exists
    user_id = st.session_state.user_id
    profile_response = make_api_request("GET", f"/life-optimization/profile/{user_id}")

    has_profile = profile_response is not None

    if has_profile:
        st.success("✅ Profile Complete! View your personalized plan in '📅 My Plan'")

        # Show profile summary
        st.markdown("### Your Profile Summary")

        profile = profile_response['profile']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Age", profile['physical']['age'])
            st.metric("Dosha Type", profile['personality']['dosha_type'])

        with col2:
            st.metric("Primary Goal", profile['goals']['primary_goal'].replace('_', ' ').title())
            st.metric("Chronotype", profile['personality']['chronotype'])

        with col3:
            st.metric("Diet Type", profile['dietary_preferences']['diet_type'])
            st.metric("Weekly Budget", f"${profile['dietary_preferences']['budget_per_week']}")

        with col4:
            if 'metabolic_profile' in profile:
                st.metric("Daily Calories", f"{int(profile['metabolic_profile']['target_calories'])}")
                st.metric("TDEE", f"{int(profile['metabolic_profile']['tdee'])}")

        st.markdown("---")

        if st.button("🔄 Update Profile", use_container_width=True):
            st.session_state.editing_profile = True
            st.rerun()

    # Assessment wizard (multi-step form)
    if not has_profile or st.session_state.get('editing_profile', False):
        st.markdown("### Complete Your Wellness Assessment")

        # Initialize session state for wizard
        if 'wizard_step' not in st.session_state:
            st.session_state.wizard_step = 0

        if 'wizard_data' not in st.session_state:
            st.session_state.wizard_data = {}

        step = st.session_state.wizard_step
        total_steps = 9

        # Progress bar
        progress = (step + 1) / total_steps
        st.progress(progress, text=f"Step {step + 1} of {total_steps}")

        # Step 0: Basic Info
        if step == 0:
            st.subheader("📋 Step 1: Basic Information")

            col1, col2 = st.columns(2)

            with col1:
                age = st.number_input("Age", min_value=18, max_value=100, value=30)
                height_cm = st.number_input("Height (cm)", min_value=140, max_value=220, value=170)
                weight_kg = st.number_input("Weight (kg)", min_value=40, max_value=200, value=70)

            with col2:
                gender = st.selectbox("Gender", ["male", "female", "other"])
                activity_level = st.selectbox(
                    "Activity Level",
                    ["sedentary", "light", "moderate", "very_active", "extremely_active"],
                    index=2
                )

            if st.button("Next →", use_container_width=True):
                st.session_state.wizard_data.update({
                    'age': age,
                    'gender': gender,
                    'height_cm': height_cm,
                    'weight_kg': weight_kg,
                    'activity_level': activity_level
                })
                st.session_state.wizard_step += 1
                st.rerun()

        # Step 1: Birth Details (for astrology)
        elif step == 1:
            st.subheader("🌟 Step 2: Birth Details (Optional)")
            st.info("Birth details enable astrological insights and optimal timing guidance")

            col1, col2 = st.columns(2)

            with col1:
                birth_date = st.date_input("Birth Date", value=datetime(1990, 1, 1))
                birth_time = st.time_input("Birth Time (if known)")

            with col2:
                birth_place = st.text_input("Birth Place (City, Country)", value="Mumbai, India")
                latitude = st.number_input("Latitude", value=19.0760, format="%.4f")
                longitude = st.number_input("Longitude", value=72.8777, format="%.4f")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'birth_date': birth_date.isoformat(),
                        'birth_time': birth_time.isoformat(),
                        'birth_place': birth_place,
                        'latitude': latitude,
                        'longitude': longitude
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 2: Personality & Constitution
        elif step == 2:
            st.subheader("🧘 Step 3: Personality & Constitution")

            chronotype = st.selectbox(
                "Chronotype (Sleep Pattern)",
                ["early_bird", "night_owl", "intermediate"],
                help="When do you feel most energetic?"
            )

            st.markdown("**Dosha Type** (Ayurvedic Constitution)")
            st.info("Answer based on your natural tendencies, not current state")

            col1, col2, col3 = st.columns(3)

            with col1:
                vata_pct = st.slider("Vata %", 0, 100, 33, help="Light, creative, anxious when imbalanced")
            with col2:
                pitta_pct = st.slider("Pitta %", 0, 100, 33, help="Intense, driven, irritable when imbalanced")
            with col3:
                kapha_pct = st.slider("Kapha %", 0, 100, 34, help="Stable, calm, lethargic when imbalanced")

            # Auto-balance doshas
            total_dosha = vata_pct + pitta_pct + kapha_pct
            if total_dosha != 100:
                st.warning(f"Dosha percentages should total 100% (currently {total_dosha}%)")

            # Determine primary dosha
            doshas = {'vata': vata_pct, 'pitta': pitta_pct, 'kapha': kapha_pct}
            sorted_doshas = sorted(doshas.items(), key=lambda x: x[1], reverse=True)

            if sorted_doshas[0][1] - sorted_doshas[1][1] > 10:
                dosha_type = sorted_doshas[0][0]
            else:
                dosha_type = f"{sorted_doshas[0][0]}-{sorted_doshas[1][0]}"

            st.success(f"Your Dosha Type: **{dosha_type}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'chronotype': chronotype,
                        'dosha_type': dosha_type,
                        'vata_pct': vata_pct,
                        'pitta_pct': pitta_pct,
                        'kapha_pct': kapha_pct
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 3: Health Profile
        elif step == 3:
            st.subheader("🏥 Step 4: Health Profile")

            conditions = st.multiselect(
                "Health Conditions",
                ["Diabetes", "Hypertension", "Heart Disease", "Asthma", "Arthritis",
                 "Thyroid Issues", "PCOS", "IBS", "Anxiety", "Depression"],
                help="Select all that apply"
            )

            allergies = st.multiselect(
                "Food Allergies",
                ["Peanuts", "Tree Nuts", "Dairy", "Eggs", "Soy", "Gluten", "Shellfish", "Fish"],
                help="Select all that apply"
            )

            deficiencies = st.multiselect(
                "Known Nutrient Deficiencies",
                ["Vitamin D", "Vitamin B12", "Iron", "Calcium", "Magnesium", "Omega-3"],
                help="From recent blood work"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'conditions': conditions,
                        'allergies': [a.lower() for a in allergies],
                        'deficiencies': [d.lower().replace(' ', '_') for d in deficiencies]
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 4: Dietary Preferences
        elif step == 4:
            st.subheader("🥗 Step 5: Dietary Preferences")

            col1, col2 = st.columns(2)

            with col1:
                diet_type = st.selectbox(
                    "Diet Type",
                    ["omnivore", "vegetarian", "vegan", "pescatarian", "paleo", "keto"],
                    index=1
                )

                cuisines = st.multiselect(
                    "Preferred Cuisines",
                    ["indian", "mediterranean", "mexican", "chinese", "thai", "italian",
                     "japanese", "middle_eastern", "american"],
                    default=["indian"]
                )

            with col2:
                budget_per_week = st.number_input("Weekly Food Budget", min_value=20, max_value=500, value=100, step=10)
                budget_currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP"], index=0)

                cooking_skill = st.selectbox(
                    "Cooking Skill",
                    ["beginner", "intermediate", "advanced"],
                    index=1
                )

                cooking_time = st.slider("Time Available per Meal (minutes)", 15, 90, 45, step=5)

            disliked_foods = st.text_input("Disliked Foods (comma-separated)", value="mushrooms")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'diet_type': diet_type,
                        'cuisines': cuisines,
                        'budget_per_week': budget_per_week,
                        'budget_currency': budget_currency,
                        'cooking_skill': cooking_skill,
                        'cooking_time': cooking_time,
                        'disliked_foods': [f.strip() for f in disliked_foods.split(',') if f.strip()]
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 5: Lifestyle
        elif step == 5:
            st.subheader("💼 Step 6: Lifestyle & Work")

            col1, col2 = st.columns(2)

            with col1:
                region = st.text_input("Region/City", value="Mumbai, Maharashtra, India")
                country_code = st.text_input("Country Code", value="IN", max_chars=2)
                occupation = st.text_input("Occupation", value="Software Engineer")

            with col2:
                work_schedule = st.selectbox("Work Schedule", ["office", "remote", "hybrid", "shift_work"])
                work_hours = st.text_input("Typical Work Hours", value="9:00-18:00",
                                          help="Format: HH:MM-HH:MM")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'region': region,
                        'country_code': country_code,
                        'occupation': occupation,
                        'work_schedule': work_schedule,
                        'work_hours': work_hours
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 6: Sleep Preferences
        elif step == 6:
            st.subheader("😴 Step 7: Sleep Preferences")

            col1, col2 = st.columns(2)

            with col1:
                ideal_sleep = st.slider("Ideal Sleep Duration (hours)", 6.0, 10.0, 7.5, step=0.5)
                bedtime = st.time_input("Preferred Bedtime", value=datetime.strptime("22:30", "%H:%M").time())

            with col2:
                wake_time = st.time_input("Preferred Wake Time", value=datetime.strptime("06:00", "%H:%M").time())
                sleep_quality = st.slider("Current Sleep Quality (0-10)", 0, 10, 7)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'ideal_sleep': ideal_sleep,
                        'bedtime': bedtime.isoformat(),
                        'wake_time': wake_time.isoformat(),
                        'sleep_quality': sleep_quality
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 7: Goals & Priorities
        elif step == 7:
            st.subheader("🎯 Step 8: Goals & Priorities")

            primary_goal = st.selectbox(
                "Primary Wellness Goal",
                ["weight_loss", "muscle_gain", "physical_strength", "mental_strength",
                 "spiritual_strength", "stress_reduction", "energy_boost", "overall_health"],
                index=2
            )

            timeline = st.selectbox("Timeline", ["1_month", "3_months", "6_months", "1_year"], index=1)
            urgency = st.selectbox("Urgency", ["gradual", "balanced", "aggressive"], index=1)

            col1, col2 = st.columns(2)

            with col1:
                meditation_min = st.slider("Daily Meditation (minutes)", 0, 60, 20, step=5)
                exercise_min = st.slider("Daily Exercise (minutes)", 0, 120, 45, step=5)

            with col2:
                st.markdown("**Priority Levels (0-10)**")
                priority_nutrition = st.slider("Nutrition", 0, 10, 8)
                priority_exercise = st.slider("Exercise", 0, 10, 7)
                priority_sleep = st.slider("Sleep", 0, 10, 8)
                priority_stress = st.slider("Stress Management", 0, 10, 7)
                priority_spiritual = st.slider("Spiritual Practice", 0, 10, 6)
                priority_budget = st.slider("Budget Adherence", 0, 10, 5)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Next →", use_container_width=True):
                    st.session_state.wizard_data.update({
                        'primary_goal': primary_goal,
                        'timeline': timeline,
                        'urgency': urgency,
                        'meditation_min': meditation_min,
                        'exercise_min': exercise_min,
                        'priority_nutrition': priority_nutrition,
                        'priority_exercise': priority_exercise,
                        'priority_sleep': priority_sleep,
                        'priority_stress': priority_stress,
                        'priority_spiritual': priority_spiritual,
                        'priority_budget': priority_budget
                    })
                    st.session_state.wizard_step += 1
                    st.rerun()

        # Step 8: Custom Preferences
        elif step == 8:
            st.subheader("⚙️ Step 9: Additional Preferences")

            col1, col2 = st.columns(2)

            with col1:
                intermittent_fasting = st.checkbox("Practice Intermittent Fasting")
                fasting_window = None
                if intermittent_fasting:
                    fasting_window = st.selectbox("Fasting Window", ["16:8", "18:6", "20:4"], index=0)

                exercise_prefs = st.multiselect(
                    "Exercise Preferences",
                    ["yoga", "weights", "cardio", "swimming", "cycling", "pilates", "martial_arts"],
                    default=["yoga"]
                )

            with col2:
                spiritual_practices = st.multiselect(
                    "Spiritual Practices",
                    ["meditation", "prayer", "chanting", "journaling", "yoga_nidra"],
                    default=["meditation"]
                )

                supplements = st.multiselect(
                    "Current Supplements",
                    ["vitamin_d", "vitamin_b12", "omega_3", "magnesium", "probiotics",
                     "ashwagandha", "turmeric", "multivitamin"],
                    default=["vitamin_d"]
                )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col2:
                if st.button("Complete Assessment ✅", use_container_width=True, type="primary"):
                    st.session_state.wizard_data.update({
                        'intermittent_fasting': intermittent_fasting,
                        'fasting_window': fasting_window,
                        'exercise_prefs': exercise_prefs,
                        'spiritual_practices': spiritual_practices,
                        'supplements': supplements
                    })

                    # Build complete profile from wizard data
                    wizard_data = st.session_state.wizard_data

                    profile_payload = {
                        "profile": {
                            "user_id": user_id,
                            "birth_details": {
                                "date": wizard_data['birth_date'],
                                "time": wizard_data['birth_time'],
                                "place": wizard_data['birth_place'],
                                "latitude": wizard_data['latitude'],
                                "longitude": wizard_data['longitude'],
                                "timezone": "UTC"
                            },
                            "personality": {
                                "big_five": {
                                    "openness": 0.7,
                                    "conscientiousness": 0.8,
                                    "extraversion": 0.6,
                                    "agreeableness": 0.7,
                                    "neuroticism": 0.4
                                },
                                "chronotype": wizard_data['chronotype'],
                                "dosha_type": wizard_data['dosha_type'],
                                "dosha_percentages": {
                                    "vata": wizard_data['vata_pct'],
                                    "pitta": wizard_data['pitta_pct'],
                                    "kapha": wizard_data['kapha_pct']
                                }
                            },
                            "physical": {
                                "age": wizard_data['age'],
                                "gender": wizard_data['gender'],
                                "height_cm": wizard_data['height_cm'],
                                "weight_kg": wizard_data['weight_kg'],
                                "activity_level": wizard_data['activity_level']
                            },
                            "health": {
                                "conditions": wizard_data.get('conditions', []),
                                "allergies": wizard_data.get('allergies', []),
                                "medications": [],
                                "nutrient_deficiencies": wizard_data.get('deficiencies', []),
                                "digestive_issues": [],
                                "family_history": []
                            },
                            "dietary_preferences": {
                                "diet_type": wizard_data['diet_type'],
                                "cuisine_preferences": wizard_data['cuisines'],
                                "disliked_foods": wizard_data['disliked_foods'],
                                "favorite_foods": [],
                                "budget_per_week": wizard_data['budget_per_week'],
                                "budget_currency": wizard_data['budget_currency'],
                                "cooking_skill": wizard_data['cooking_skill'],
                                "cooking_time_available": wizard_data['cooking_time'],
                                "meal_prep_preference": "daily",
                                "eating_out_frequency": 2
                            },
                            "lifestyle": {
                                "region": wizard_data['region'],
                                "country_code": wizard_data['country_code'],
                                "timezone": "UTC",
                                "occupation": wizard_data['occupation'],
                                "work_schedule_type": wizard_data['work_schedule'],
                                "typical_work_hours": wizard_data['work_hours'],
                                "work_break_preferences": ["lunch"],
                                "commute_time_minutes": 0,
                                "household_size": 1,
                                "has_family_meals": False
                            },
                            "sleep_preferences": {
                                "ideal_sleep_duration": wizard_data['ideal_sleep'],
                                "preferred_bedtime": wizard_data['bedtime'],
                                "preferred_wake_time": wizard_data['wake_time'],
                                "current_sleep_quality": wizard_data['sleep_quality'],
                                "sleep_issues": []
                            },
                            "goals": {
                                "primary_goal": wizard_data['primary_goal'],
                                "secondary_goals": [],
                                "timeline": wizard_data['timeline'],
                                "urgency": wizard_data['urgency'],
                                "target_weight_kg": None,
                                "meditation_minutes_daily": wizard_data['meditation_min'],
                                "exercise_minutes_daily": wizard_data['exercise_min'],
                                "priority_nutrition": wizard_data['priority_nutrition'],
                                "priority_exercise": wizard_data['priority_exercise'],
                                "priority_sleep": wizard_data['priority_sleep'],
                                "priority_stress": wizard_data['priority_stress'],
                                "priority_spiritual": wizard_data['priority_spiritual'],
                                "priority_budget": wizard_data['priority_budget']
                            },
                            "custom_preferences": {
                                "intermittent_fasting": wizard_data['intermittent_fasting'],
                                "fasting_window": wizard_data.get('fasting_window'),
                                "caffeine_preference": "moderate",
                                "alcohol_consumption": "occasional",
                                "supplement_stack": wizard_data['supplements'],
                                "exercise_preferences": wizard_data['exercise_prefs'],
                                "spiritual_practices": wizard_data['spiritual_practices'],
                                "notes": ""
                            }
                        }
                    }

                    # Submit profile to backend
                    with st.spinner("Creating your personalized wellness profile..."):
                        response = make_api_request("POST", "/life-optimization/profile", json=profile_payload)

                        if response and response.get('success'):
                            st.success("✅ Profile created successfully!")
                            st.balloons()

                            # Clear wizard state
                            st.session_state.wizard_step = 0
                            st.session_state.wizard_data = {}
                            st.session_state.editing_profile = False

                            st.info("🎉 Your profile is ready! Go to **📅 My Plan** to see your personalized meal plan and schedule.")

                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to create profile. Please try again.")

# ============================================================================
# PAGE: My Plan - Dashboard
# ============================================================================
elif page == "📅 My Plan":
    st.markdown("<h1 class='main-header'>📅 My Wellness Plan</h1>", unsafe_allow_html=True)

    user_id = st.session_state.user_id

    # Check if profile exists
    profile_response = make_api_request("GET", f"/life-optimization/profile/{user_id}")

    if not profile_response:
        st.warning("⚠️ Please complete your assessment in **🌟 Life Optimization** first")
        st.stop()

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🍽️ Today's Meals", "📅 Today's Schedule", "📊 Wellness Score"])

    with tab1:
        st.subheader("🍽️ Today's Meal Plan")

        # Get or generate meal plan
        meal_plan_response = make_api_request("GET", f"/life-optimization/meal-plan/{user_id}/current")

        if meal_plan_response and meal_plan_response.get('success'):
            meal_plan = meal_plan_response['meal_plan']

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Calories", f"{int(meal_plan['total_calories'])}")
            with col2:
                st.metric("Protein", f"{int(meal_plan['total_protein'])}g")
            with col3:
                st.metric("Cost", f"${meal_plan['total_cost']:.2f}")
            with col4:
                dosha_score = meal_plan.get('dosha_balance_score', 70)
                st.metric("Dosha Balance", f"{int(dosha_score)}/100")

            # Compliance indicators
            col1, col2 = st.columns(2)
            with col1:
                if meal_plan.get('meets_goals'):
                    st.success("✅ Meets nutritional goals")
                else:
                    st.warning("⚠️ Adjust for nutritional compliance")

            with col2:
                if meal_plan.get('meets_budget'):
                    st.success("✅ Within budget")
                else:
                    st.warning("⚠️ Over budget")

            st.markdown("---")

            # Regenerate button
            if st.button("🔄 Regenerate Meal Plan", use_container_width=True):
                with st.spinner("Generating new meal plan..."):
                    regen_response = make_api_request(
                        "POST",
                        f"/life-optimization/meal-plan/{user_id}/regenerate",
                        json={"target_date": date.today().isoformat()}
                    )
                    if regen_response and regen_response.get('success'):
                        st.success("✅ New meal plan generated!")
                        time.sleep(1)
                        st.rerun()

            st.markdown("### Meals")

            # Display each meal
            for i, meal in enumerate(meal_plan['meals']):
                with st.expander(f"{meal['time']} - {meal['meal_type'].upper()}: {meal['name']}", expanded=(i==0)):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**{meal['description']}**")
                        st.markdown(f"*Cooking time: {meal['prep_time_minutes']} minutes*")

                        # Ingredients
                        st.markdown("**Ingredients:**")
                        for ing in meal['ingredients']:
                            reason = ing.get('reason', '')
                            st.markdown(f"- **{ing['name']}**: {ing['quantity']} {ing['unit']} ({reason})")

                        # Cooking instructions
                        if meal.get('cooking_instructions'):
                            st.markdown("**Instructions:**")
                            for idx, instruction in enumerate(meal['cooking_instructions'], 1):
                                st.markdown(f"{idx}. {instruction}")

                        # Timing reason
                        if meal.get('timing_reason'):
                            st.info(f"**Why this timing?** {meal['timing_reason']}")

                    with col2:
                        st.metric("Calories", f"{int(meal['total_nutrients']['calories'])}")
                        st.metric("Protein", f"{int(meal['total_nutrients']['protein_g'])}g")
                        st.metric("Carbs", f"{int(meal['total_nutrients']['carbs_g'])}g")
                        st.metric("Fat", f"{int(meal['total_nutrients']['fat_g'])}g")
                        st.metric("Cost", f"${meal['cost_total']:.2f}")

        else:
            st.info("Generating your first meal plan...")
            if st.button("Generate Meal Plan"):
                with st.spinner("Creating personalized meal plan..."):
                    gen_response = make_api_request(
                        "POST",
                        "/life-optimization/meal-plan/generate",
                        json={
                            "user_id": user_id,
                            "start_date": date.today().isoformat(),
                            "num_days": 1
                        }
                    )
                    if gen_response and gen_response.get('success'):
                        st.success("✅ Meal plan created!")
                        time.sleep(1)
                        st.rerun()

    with tab2:
        st.subheader("📅 Today's Schedule")

        # Get or generate schedule
        schedule_response = make_api_request("GET", f"/life-optimization/schedule/{user_id}/today")

        if schedule_response and schedule_response.get('success'):
            schedule = schedule_response['schedule']

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Sleep", f"{schedule['sleep_hours']}h")
            with col2:
                st.metric("Work", f"{schedule['work_hours']}h")
            with col3:
                st.metric("Exercise", f"{schedule['exercise_minutes']} min")
            with col4:
                st.metric("Free Time", f"{schedule['free_time_minutes']} min")

            st.markdown("---")

            # Energy forecast
            st.markdown("### Energy Forecast")
            forecast = schedule.get('energy_forecast', {})

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Morning", forecast.get('morning', 'moderate').title())
            with col2:
                st.metric("Afternoon", forecast.get('afternoon', 'moderate').title())
            with col3:
                st.metric("Evening", forecast.get('evening', 'moderate').title())

            st.markdown("---")

            # Timeline
            st.markdown("### Daily Timeline")

            # Group activities by time
            for activity in schedule['activities']:
                time_str = activity['time']
                title = activity['title']
                duration = activity['duration_minutes']
                reason = activity.get('reason', '')

                # Color code by activity type
                activity_type = activity.get('activity_type', '')
                if activity_type == 'sleep':
                    color = '#9370DB'
                elif activity_type in ['meditation', 'spiritual_practice']:
                    color = '#FFD700'
                elif activity_type == 'exercise':
                    color = '#FF6347'
                elif activity_type == 'work':
                    color = '#4682B4'
                elif activity_type == 'meal':
                    color = '#32CD32'
                else:
                    color = '#D3D3D3'

                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0; color: white;">
                    <strong>{time_str}</strong> - {title} ({duration} min)<br>
                    <em style="font-size: 0.9em;">{reason}</em>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.info("Generating your optimized schedule...")
            if st.button("Generate Schedule"):
                with st.spinner("Creating personalized schedule..."):
                    gen_response = make_api_request(
                        "POST",
                        "/life-optimization/schedule/generate",
                        json={
                            "user_id": user_id,
                            "target_date": date.today().isoformat(),
                            "include_planetary_hours": False
                        }
                    )
                    if gen_response and gen_response.get('success'):
                        st.success("✅ Schedule created!")
                        time.sleep(1)
                        st.rerun()

    with tab3:
        st.subheader("📊 Holistic Wellness Score")

        st.info("Wellness scoring integrates data from wearables, EEG, voice, and more. Connect your devices in Settings to unlock this feature.")

        # Placeholder for wellness scores
        st.markdown("### Component Scores")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Physical", "75/100")
            st.metric("Mental", "72/100")

        with col2:
            st.metric("Emotional", "78/100")
            st.metric("Spiritual", "68/100")

        with col3:
            st.metric("Nutritional", "80/100")
            st.metric("Overall", "74/100")

        st.markdown("---")

        st.markdown("### Recent Insights")
        st.info("💡 Sleep quality (55/100) is below optimal - consider earlier bedtime")
        st.info("💡 Dosha balance improving - continue current meal plan")
        st.success("✅ Exercise consistency excellent - keep it up!")

# ============================================================================
# PAGE: EEG Analysis
# ============================================================================
elif page == "🧠 EEG Analysis":
    st.markdown("<h1 class='main-header'>🧠 EEG Brainwave Analysis</h1>", unsafe_allow_html=True)

    st.info("""
    Upload your EEG data (CSV format) to analyze your mental state.
    The system will detect stress, focus, relaxation, and drowsiness levels.
    """)

    # File upload
    uploaded_file = st.file_uploader(
        "Upload EEG Data (CSV)",
        type=['csv'],
        help="Expected format: 14 channels x N samples at 256Hz"
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        if uploaded_file is not None:
            st.success("File uploaded successfully!")

            if st.button("🔬 Analyze EEG Data", type="primary"):
                with st.spinner("Analyzing brainwave patterns..."):
                    # Upload file to backend
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/csv')}
                    params = {'user_id': st.session_state.user_id}

                    result = make_api_request("POST", "/eeg/upload", files=files, params=params)

                    if result:
                        st.success("Analysis complete!")

                        # Display results
                        st.subheader("Analysis Results")

                        # Mental state
                        mental_state = result.get('mental_state', 'Unknown')
                        st.markdown(f"### Current Mental State: **{mental_state.title()}**")

                        # Band powers visualization
                        analysis_id = result.get('id')
                        if analysis_id:
                            band_data = make_api_request("GET", f"/eeg/band-powers/{analysis_id}?user_id={st.session_state.user_id}")

                            if band_data:
                                bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
                                powers = [
                                    band_data.get('delta', 0),
                                    band_data.get('theta', 0),
                                    band_data.get('alpha', 0),
                                    band_data.get('beta', 0),
                                    band_data.get('gamma', 0)
                                ]

                                fig = go.Figure(data=[
                                    go.Bar(x=bands, y=powers, marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
                                ])
                                fig.update_layout(
                                    title="Brainwave Band Powers",
                                    yaxis_title="Relative Power",
                                    height=400
                                )
                                st.plotly_chart(fig, use_container_width=True)

                        # Probabilities
                        st.markdown("### Mental State Probabilities")
                        prob_col1, prob_col2, prob_col3, prob_col4 = st.columns(4)

                        with prob_col1:
                            st.metric("Stressed", f"{int(result.get('stress', 0) * 100)}%")
                        with prob_col2:
                            st.metric("Focused", f"{int(result.get('focus', 0) * 100)}%")
                        with prob_col3:
                            st.metric("Relaxed", f"{int(result.get('relaxation', 0) * 100)}%")
                        with prob_col4:
                            st.metric("Drowsy", f"{int(result.get('drowsiness', 0) * 100)}%")

                        # Store result in session state for recommendations
                        if 'latest_eeg_result' not in st.session_state:
                            st.session_state.latest_eeg_result = result

    with col2:
        st.subheader("📋 Recommendations")

        if 'latest_eeg_result' in st.session_state:
            result = st.session_state.latest_eeg_result
            recommendations = result.get('recommendations', [])

            if recommendations:
                st.markdown("**Based on your EEG analysis:**\n")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.markdown("""
                Based on your analysis results:

                **Immediate Actions:**
                - 🧘 Try 5-minute breathing exercise
                - 🚶 Take a short walk
                - 💧 Hydrate

                **Long-term Strategies:**
                - Consider meditation practice
                - Improve sleep hygiene
                - Reduce stress triggers
                """)
        else:
            st.markdown("""
            Upload and analyze EEG data to receive personalized recommendations based on your mental state.
            """)

    # Show recent analyses
    st.markdown("---")
    st.subheader("📊 Recent EEG Analyses")

    with st.spinner("Loading recent analyses..."):
        recent_eeg = make_api_request("GET", f"/eeg/analysis?user_id={st.session_state.user_id}&limit=5")

    if recent_eeg and len(recent_eeg) > 0:
        analyses_df = pd.DataFrame([
            {
                'Date': datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M"),
                'Mental State': a['mental_state'],
                'Stress': f"{int(a['stress'] * 100)}%",
                'Focus': f"{int(a['focus'] * 100)}%",
                'Relaxation': f"{int(a['relaxation'] * 100)}%",
                'Dominant Band': a['dominant_band']
            }
            for a in recent_eeg
        ])
        st.dataframe(analyses_df, use_container_width=True)
    else:
        st.info("No previous analyses found. Upload EEG data to get started!")

# ============================================================================
# PAGE: AI Coach
# ============================================================================
elif page == "💬 AI Coach":
    st.markdown("<h1 class='main-header'>💬 AI Wellness Coach</h1>", unsafe_allow_html=True)

    st.info("Chat with your personal AI wellness coach. The coach has access to your health data, Ayurvedic knowledge, and nutritional science.")

    # Load chat history from backend on first load
    if not st.session_state.chat_history:
        with st.spinner("Loading chat history..."):
            history = make_api_request("GET", f"/coach/chat/history?user_id={st.session_state.user_id}&limit=50")

            if history and len(history) > 0:
                st.session_state.chat_history = [
                    {"role": msg['role'], "content": msg['content']}
                    for msg in history
                ]
            else:
                # Default welcome message
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "Hello! I'm your AI wellness coach. I'm here to help you with stress management, nutrition, sleep, and overall wellbeing. How can I support you today?"}
                ]

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about your health and wellness..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response from backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = make_api_request(
                    "POST",
                    "/coach/chat",
                    json={
                        "message": prompt,
                        "include_context": True
                    },
                    params={"user_id": st.session_state.user_id}
                )

                if response_data:
                    response_message = response_data.get('message', 'Sorry, I encountered an error processing your request.')

                    # Add sources if available
                    sources = response_data.get('sources', [])
                    if sources:
                        response_message += "\n\n**Sources:**\n"
                        for source in sources[:3]:  # Limit to top 3 sources
                            response_message += f"- {source}\n"

                    st.markdown(response_message)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_message})
                else:
                    error_msg = "I'm having trouble connecting right now. Please try again in a moment."
                    st.markdown(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    # Guided sessions section
    st.markdown("---")
    st.subheader("🧘 Start a Guided Session")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌬️ Breathing Exercise", use_container_width=True):
            session_data = make_api_request(
                "POST",
                "/coach/session/start",
                json={"session_type": "breathing", "duration_minutes": 5},
                params={"user_id": st.session_state.user_id}
            )

            if session_data:
                st.success("Breathing session started!")
                instructions = session_data.get('instructions', [])
                for i, instruction in enumerate(instructions, 1):
                    st.markdown(f"{i}. {instruction}")

    with col2:
        if st.button("🧘 Meditation", use_container_width=True):
            session_data = make_api_request(
                "POST",
                "/coach/session/start",
                json={"session_type": "meditation", "duration_minutes": 10},
                params={"user_id": st.session_state.user_id}
            )

            if session_data:
                st.success("Meditation session started!")
                instructions = session_data.get('instructions', [])
                for i, instruction in enumerate(instructions, 1):
                    st.markdown(f"{i}. {instruction}")

    with col3:
        if st.button("🧘‍♀️ Yoga Flow", use_container_width=True):
            session_data = make_api_request(
                "POST",
                "/coach/session/start",
                json={"session_type": "yoga", "duration_minutes": 15},
                params={"user_id": st.session_state.user_id}
            )

            if session_data:
                st.success("Yoga session started!")
                instructions = session_data.get('instructions', [])
                for i, instruction in enumerate(instructions, 1):
                    st.markdown(f"{i}. {instruction}")

# ============================================================================
# PAGE: Health Metrics
# ============================================================================
elif page == "📊 Health Metrics":
    st.markdown("<h1 class='main-header'>📊 Health Metrics Tracking</h1>", unsafe_allow_html=True)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())

    st.markdown("---")

    # Metrics input form
    with st.expander("➕ Log Today's Metrics"):
        with st.form("health_metrics_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                steps = st.number_input("Steps", min_value=0, value=0)
                calories = st.number_input("Calories Burned", min_value=0, value=0)

            with col2:
                sleep_hours = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
                weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0, step=0.1)

            with col3:
                heart_rate = st.number_input("Avg Heart Rate (bpm)", min_value=0, value=0)
                distance = st.number_input("Distance (km)", min_value=0.0, value=0.0, step=0.1)

            submitted = st.form_submit_button("Submit", type="primary")

            if submitted:
                with st.spinner("Saving metrics..."):
                    metric_data = {
                        "date": datetime.now().date().isoformat(),
                        "steps": steps if steps > 0 else None,
                        "calories_burned": calories if calories > 0 else None,
                        "sleep_hours": sleep_hours if sleep_hours > 0 else None,
                        "weight_kg": weight if weight > 0 else None,
                        "heart_rate_avg": heart_rate if heart_rate > 0 else None,
                        "distance_km": distance if distance > 0 else None
                    }

                    result = make_api_request(
                        "POST",
                        "/health/",
                        json=metric_data,
                        params={"user_id": st.session_state.user_id}
                    )

                    if result:
                        st.success("✅ Metrics logged successfully!")
                        st.rerun()

    # Display trends
    st.subheader("📈 Trends")

    # Fetch health metrics
    with st.spinner("Loading health trends..."):
        health_metrics = make_api_request(
            "GET",
            f"/health/?user_id={st.session_state.user_id}&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&limit=100"
        )

    tab1, tab2, tab3, tab4 = st.tabs(["💓 Vitals", "😴 Sleep", "🏃 Activity", "📉 Stress"])

    with tab1:
        # Heart rate trend
        if health_metrics and len(health_metrics) > 0:
            hr_data = pd.DataFrame([
                {
                    'Date': m['date'],
                    'Heart Rate': m.get('heart_rate_avg')
                }
                for m in health_metrics if m.get('heart_rate_avg')
            ])

            if not hr_data.empty:
                hr_data['Date'] = pd.to_datetime(hr_data['Date'])
                hr_data = hr_data.sort_values('Date')

                fig = px.line(hr_data, x='Date', y='Heart Rate', title='Heart Rate Trend')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No heart rate data available. Log your metrics to see trends.")
        else:
            st.info("No health data available. Start logging your metrics!")

    with tab2:
        # Sleep trend
        if health_metrics and len(health_metrics) > 0:
            sleep_data = pd.DataFrame([
                {
                    'Date': m['date'],
                    'Hours': m.get('sleep_hours')
                }
                for m in health_metrics if m.get('sleep_hours')
            ])

            if not sleep_data.empty:
                sleep_data['Date'] = pd.to_datetime(sleep_data['Date'])
                sleep_data = sleep_data.sort_values('Date')

                fig = px.bar(sleep_data, x='Date', y='Hours', title='Sleep Duration')
                fig.add_hline(y=7.0, line_dash="dash", line_color="green", annotation_text="Target: 7 hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sleep data available. Log your sleep to see trends.")
        else:
            st.info("No health data available. Start logging your metrics!")

    with tab3:
        # Activity
        if health_metrics and len(health_metrics) > 0:
            activity_data = pd.DataFrame([
                {
                    'Date': m['date'],
                    'Steps': m.get('steps')
                }
                for m in health_metrics if m.get('steps')
            ])

            if not activity_data.empty:
                activity_data['Date'] = pd.to_datetime(activity_data['Date'])
                activity_data = activity_data.sort_values('Date')

                fig = px.area(activity_data, x='Date', y='Steps', title='Daily Steps')
                fig.add_hline(y=8000, line_dash="dash", line_color="green", annotation_text="Target: 8000 steps")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No activity data available. Log your steps to see trends.")
        else:
            st.info("No health data available. Start logging your metrics!")

    with tab4:
        # Stress levels from EEG
        with st.spinner("Loading stress data..."):
            eeg_analyses = make_api_request("GET", f"/eeg/analysis?user_id={st.session_state.user_id}&limit=30")

        if eeg_analyses and len(eeg_analyses) > 0:
            stress_data = pd.DataFrame([
                {
                    'Date': datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')).date(),
                    'Stress': a.get('stress', 0)
                }
                for a in eeg_analyses
            ])

            stress_data = stress_data.sort_values('Date')

            fig = px.line(stress_data, x='Date', y='Stress', title='Stress Level (from EEG)')
            fig.update_yaxes(range=[0, 1])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No EEG data available. Upload EEG data to track stress levels.")

# ============================================================================
# PAGE: Nutrition
# ============================================================================
elif page == "🥗 Nutrition":
    st.markdown("<h1 class='main-header'>🥗 Nutrition & Diet Tracking</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Log Meal", "📊 Nutrition Summary", "📸 Food Recognition"])

    with tab1:
        st.subheader("Log Your Meal")

        with st.form("meal_log_form"):
            meal_type = st.selectbox("Meal Type", ["breakfast", "lunch", "dinner", "snack"])
            foods = st.text_area("Food Items (one per line)", "")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                calories = st.number_input("Calories", min_value=0, value=0)
            with col2:
                protein = st.number_input("Protein (g)", min_value=0.0, value=0.0)
            with col3:
                carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0)
            with col4:
                fat = st.number_input("Fat (g)", min_value=0.0, value=0.0)

            notes = st.text_input("Notes (optional)")

            if st.form_submit_button("Log Meal", type="primary"):
                with st.spinner("Logging meal..."):
                    food_items = [f.strip() for f in foods.split('\n') if f.strip()]

                    meal_data = {
                        "meal_type": meal_type,
                        "food_items": food_items,
                        "calories": calories if calories > 0 else None,
                        "protein_g": protein if protein > 0 else None,
                        "carbs_g": carbs if carbs > 0 else None,
                        "fat_g": fat if fat > 0 else None,
                        "notes": notes if notes else None
                    }

                    result = make_api_request(
                        "POST",
                        "/meals/",
                        json=meal_data,
                        params={"user_id": st.session_state.user_id}
                    )

                    if result:
                        st.success("✅ Meal logged successfully!")

    with tab2:
        st.subheader("Today's Nutrition Summary")

        with st.spinner("Loading nutrition summary..."):
            today = date.today()
            summary = make_api_request(
                "GET",
                f"/meals/summary/{today.isoformat()}?user_id={st.session_state.user_id}"
            )

        if summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Calories", f"{summary.get('total_calories', 0):,}")
            with col2:
                st.metric("Protein", f"{summary.get('protein_g', 0):.1f}g")
            with col3:
                st.metric("Carbs", f"{summary.get('carbs_g', 0):.1f}g")
            with col4:
                st.metric("Fat", f"{summary.get('fat_g', 0):.1f}g")

            # Macronutrient breakdown
            if summary.get('total_calories', 0) > 0:
                protein_cals = summary.get('protein_g', 0) * 4
                carbs_cals = summary.get('carbs_g', 0) * 4
                fat_cals = summary.get('fat_g', 0) * 9

                fig = go.Figure(data=[go.Pie(
                    labels=['Protein', 'Carbs', 'Fat'],
                    values=[protein_cals, carbs_cals, fat_cals],
                    hole=.3
                )])
                fig.update_layout(title="Macronutrient Distribution")
                st.plotly_chart(fig, use_container_width=True)

            # Show recommendations
            if summary.get('recommendations'):
                st.markdown("**Recommendations:**")
                for rec in summary['recommendations']:
                    st.markdown(f"- {rec}")
        else:
            st.info("No meals logged today. Use the 'Log Meal' tab to get started!")

    with tab3:
        st.subheader("📸 AI Food Recognition")
        st.info("Upload a photo of your meal and our AI will identify the foods and estimate nutrition.")

        uploaded_image = st.file_uploader("Upload meal photo", type=['jpg', 'jpeg', 'png'])

        if uploaded_image:
            st.image(uploaded_image, caption="Your meal", use_column_width=True)

            if st.button("🔍 Analyze Food", type="primary"):
                with st.spinner("Analyzing image..."):
                    files = {'file': (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}

                    result = make_api_request(
                        "POST",
                        "/food/recognize",
                        files=files,
                        params={"user_id": st.session_state.user_id}
                    )

                    if result:
                        st.success("Analysis complete!")

                        # Display detected foods
                        st.markdown("**Detected Foods:**")
                        detected_foods = result.get('detected_foods', [])
                        for food in detected_foods:
                            confidence = food.get('confidence', 0) * 100
                            st.markdown(f"- {food.get('name', 'Unknown')} (confidence: {confidence:.0f}%)")

                        # Display nutritional summary
                        st.markdown("**Estimated Nutrition:**")
                        st.markdown(f"- Calories: ~{result.get('total_calories', 0)} kcal")

                        nutritional_summary = result.get('nutritional_summary', {})
                        if nutritional_summary:
                            st.markdown(f"- Protein: {nutritional_summary.get('protein', 0):.1f}g")
                            st.markdown(f"- Carbs: {nutritional_summary.get('carbs', 0):.1f}g")
                            st.markdown(f"- Fat: {nutritional_summary.get('fat', 0):.1f}g")

                        # Show recommendations
                        if result.get('recommendations'):
                            st.markdown("**Recommendations:**")
                            for rec in result['recommendations']:
                                st.markdown(f"- {rec}")

# ============================================================================
# PAGE: Supplements
# ============================================================================
elif page == "💊 Supplements":
    st.markdown("<h1 class='main-header'>💊 Supplement Tracking</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 My Supplements", "🔍 Search Database", "📸 Scan Label"])

    with tab1:
        st.subheader("Current Supplements")

        with st.spinner("Loading supplements..."):
            supplements = make_api_request("GET", f"/supplements/log?user_id={st.session_state.user_id}&active_only=true")

        if supplements and len(supplements) > 0:
            supp_df = pd.DataFrame([
                {
                    'Supplement': s['supplement_name'],
                    'Dosage': s['dosage'],
                    'Frequency': s['frequency'],
                    'Purpose': s.get('purpose', 'N/A')
                }
                for s in supplements
            ])
            st.dataframe(supp_df, use_container_width=True)
        else:
            st.info("No supplements logged yet. Use the form below to add one!")

        # Add new supplement form
        st.markdown("---")
        st.subheader("➕ Add New Supplement")

        with st.form("add_supplement_form"):
            col1, col2 = st.columns(2)

            with col1:
                supp_name = st.text_input("Supplement Name")
                dosage = st.text_input("Dosage (e.g., 500mg)")
                frequency = st.selectbox("Frequency", ["daily", "twice_daily", "as_needed"])

            with col2:
                start_date = st.date_input("Start Date", value=date.today())
                purpose = st.text_input("Purpose (optional)")
                notes = st.text_area("Notes (optional)")

            if st.form_submit_button("Add Supplement", type="primary"):
                if supp_name and dosage:
                    with st.spinner("Adding supplement..."):
                        supp_data = {
                            "supplement_name": supp_name,
                            "dosage": dosage,
                            "frequency": frequency,
                            "start_date": start_date.isoformat(),
                            "purpose": purpose if purpose else None,
                            "notes": notes if notes else None
                        }

                        result = make_api_request(
                            "POST",
                            "/supplements/log",
                            json=supp_data,
                            params={"user_id": st.session_state.user_id}
                        )

                        if result:
                            st.success("✅ Supplement added successfully!")
                            st.rerun()
                else:
                    st.error("Please provide supplement name and dosage.")

        # Check for interactions
        st.markdown("---")
        if st.button("🔍 Check for Interactions"):
            with st.spinner("Checking interactions..."):
                interactions = make_api_request("GET", f"/supplements/interactions?user_id={st.session_state.user_id}")

                if interactions:
                    if interactions.get('interactions_found', 0) > 0:
                        st.warning(f"Found {interactions['interactions_found']} potential interactions!")
                        for warning in interactions.get('warnings', []):
                            st.warning(warning)
                    else:
                        st.success("No interactions found!")

                    for rec in interactions.get('recommendations', []):
                        st.info(rec)

    with tab2:
        st.subheader("🔍 Supplement Database")

        search = st.text_input("Search supplements...", placeholder="e.g., stress, sleep, energy")

        if search:
            with st.spinner("Searching..."):
                results = make_api_request("GET", f"/supplements/database/search?query={search}&limit=20")

            if results and len(results) > 0:
                for supp in results:
                    with st.expander(f"📌 {supp['name']}"):
                        st.markdown(f"**Category:** {supp['category']}")

                        st.markdown("**Benefits:**")
                        for benefit in supp.get('benefits', []):
                            st.markdown(f"- {benefit}")

                        st.markdown(f"**Dosage:** {supp.get('dosage_range', 'N/A')}")
                        st.markdown(f"**Evidence Level:** {supp.get('evidence_level', 'N/A')}")

                        if supp.get('contraindications'):
                            st.markdown("**Contraindications:**")
                            for contra in supp['contraindications']:
                                st.markdown(f"- ⚠️ {contra}")

                        if supp.get('interactions'):
                            st.markdown("**Interactions:**")
                            for interaction in supp['interactions']:
                                st.markdown(f"- ⚠️ {interaction}")

                        if supp.get('sources'):
                            st.markdown("**Sources:**")
                            for source in supp['sources'][:3]:
                                st.markdown(f"- {source}")
            else:
                st.info("No results found. Try a different search term.")

    with tab3:
        st.subheader("📸 OCR Supplement Label Scanner")
        st.info("Upload a photo of your supplement bottle to extract ingredient information.")

        uploaded_label = st.file_uploader("Upload supplement label", type=['jpg', 'jpeg', 'png'], key='label')

        if uploaded_label:
            st.image(uploaded_label, caption="Supplement label", use_column_width=True)

            if st.button("🔍 Extract Information", type="primary"):
                with st.spinner("Reading label..."):
                    files = {'file': (uploaded_label.name, uploaded_label.getvalue(), uploaded_label.type)}

                    result = make_api_request(
                        "POST",
                        "/food/ocr-supplement",
                        files=files,
                        params={"user_id": st.session_state.user_id}
                    )

                    if result:
                        st.success("Label scanned successfully!")

                        st.markdown("**Extracted Information:**")

                        if result.get('supplement_name'):
                            st.markdown(f"**Supplement:** {result['supplement_name']}")

                        if result.get('dosage'):
                            st.markdown(f"**Dosage:** {result['dosage']}")

                        if result.get('ingredients'):
                            st.markdown("**Ingredients:**")
                            for ingredient in result['ingredients']:
                                st.markdown(f"- {ingredient}")

                        if result.get('suggested_use'):
                            st.markdown(f"**Suggested Use:** {result['suggested_use']}")

                        if result.get('warnings'):
                            st.markdown("**Warnings:**")
                            for warning in result['warnings']:
                                st.warning(warning)

# ============================================================================
# PAGE: Settings
# ============================================================================
elif page == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>⚙️ Settings</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🎯 Goals", "🔔 Preferences"])

    with tab1:
        st.subheader("User Profile")

        # Load current profile
        with st.spinner("Loading profile..."):
            profile = make_api_request("GET", f"/users/me?user_id={st.session_state.user_id}")

        if profile:
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name", value=profile.get('name', ''))
                age = st.number_input("Age", min_value=0, value=profile.get('age', 30))
                gender = st.selectbox("Gender", ["male", "female", "non-binary", "prefer_not_to_say"],
                                     index=["male", "female", "non-binary", "prefer_not_to_say"].index(profile.get('gender', 'non-binary')))

            with col2:
                dosha_options = ["vata", "pitta", "kapha", "vata_pitta", "pitta_kapha", "vata_kapha"]
                current_dosha = profile.get('dosha_type', 'vata_pitta')
                dosha = st.selectbox("Ayurvedic Dosha", dosha_options,
                                   index=dosha_options.index(current_dosha) if current_dosha in dosha_options else 0)
                email = st.text_input("Email", value=profile.get('email', ''))

            if st.button("Take Dosha Assessment"):
                st.info("Complete this questionnaire to determine your Ayurvedic constitution:")

                with st.form("dosha_assessment"):
                    st.markdown("### Dosha Assessment Quiz")

                    physical_build = st.selectbox("Physical Build",
                        ["Thin, light frame", "Medium, muscular", "Large, solid frame"])
                    skin_type = st.selectbox("Skin Type",
                        ["Dry, rough, cool", "Warm, oily, sensitive", "Thick, smooth, cool"])
                    energy_pattern = st.selectbox("Energy Pattern",
                        ["Bursts of energy, variable", "Moderate, sustained", "Steady, consistent"])
                    sleep_pattern = st.selectbox("Sleep Pattern",
                        ["Light, interrupted", "Sound, moderate duration", "Deep, long duration"])
                    stress_response = st.selectbox("Stress Response",
                        ["Anxiety, worry", "Irritability, anger", "Withdrawal, depression"])
                    digestion = st.selectbox("Digestion",
                        ["Variable, gas/bloating", "Strong, tends toward heartburn", "Slow, heavy feeling"])
                    temp_preference = st.selectbox("Temperature Preference",
                        ["Prefer warmth", "Prefer cool", "Adaptable to both"])

                    if st.form_submit_button("Calculate Dosha", type="primary"):
                        with st.spinner("Calculating your dosha..."):
                            assessment_data = {
                                "physical_build": physical_build,
                                "skin_type": skin_type,
                                "energy_pattern": energy_pattern,
                                "sleep_pattern": sleep_pattern,
                                "stress_response": stress_response,
                                "digestion": digestion,
                                "temperature_preference": temp_preference
                            }

                            dosha_result = make_api_request(
                                "POST",
                                "/users/dosha-assessment",
                                json=assessment_data,
                                params={"user_id": st.session_state.user_id}
                            )

                            if dosha_result:
                                st.success(f"Your primary dosha is: **{dosha_result['primary_dosha'].upper()}**")
                                if dosha_result.get('secondary_dosha'):
                                    st.info(f"Secondary dosha: {dosha_result['secondary_dosha'].upper()}")

                                scores = dosha_result.get('scores', {})
                                st.markdown("**Dosha Scores:**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Vata", f"{scores.get('vata', 0)}%")
                                with col2:
                                    st.metric("Pitta", f"{scores.get('pitta', 0)}%")
                                with col3:
                                    st.metric("Kapha", f"{scores.get('kapha', 0)}%")

                                st.markdown("**Characteristics:**")
                                for char in dosha_result.get('characteristics', []):
                                    st.markdown(f"- {char}")

                                st.markdown("**Recommendations:**")
                                for rec in dosha_result.get('recommendations', []):
                                    st.markdown(f"- {rec}")

            if st.button("Save Profile", type="primary"):
                with st.spinner("Updating profile..."):
                    update_data = {
                        "name": name,
                        "age": age,
                        "gender": gender,
                        "dosha_type": dosha
                    }

                    result = make_api_request(
                        "PATCH",
                        "/users/me",
                        json=update_data,
                        params={"user_id": st.session_state.user_id}
                    )

                    # Note: Backend returns 501 Not Implemented, but we show success message
                    st.info("Profile update feature is coming soon!")

    with tab2:
        st.subheader("Health Goals")

        # Load current profile for goals
        if not profile:
            with st.spinner("Loading profile..."):
                profile = make_api_request("GET", f"/users/me?user_id={st.session_state.user_id}")

        current_goals = profile.get('health_goals', []) if profile else []

        goals = st.multiselect(
            "Select your health goals",
            ["Reduce stress", "Improve sleep", "Boost energy", "Lose weight", "Build muscle",
             "Improve focus", "Better nutrition", "Mental clarity"],
            default=current_goals
        )

        medical_conditions = st.text_area("Medical Conditions (for contraindication checking)",
                                          value=', '.join(profile.get('medical_conditions', [])) if profile else '')
        medications = st.text_area("Current Medications",
                                   value=', '.join(profile.get('current_medications', [])) if profile else '')

        if st.button("Save Goals", type="primary"):
            with st.spinner("Updating goals..."):
                update_data = {
                    "health_goals": goals,
                    "medical_conditions": [c.strip() for c in medical_conditions.split(',') if c.strip()],
                    "current_medications": [m.strip() for m in medications.split(',') if m.strip()]
                }

                result = make_api_request(
                    "PATCH",
                    "/users/me",
                    json=update_data,
                    params={"user_id": st.session_state.user_id}
                )

                st.info("Goals update feature is coming soon!")

    with tab3:
        st.subheader("Preferences")

        # Load preferences
        with st.spinner("Loading preferences..."):
            prefs = make_api_request("GET", f"/users/preferences?user_id={st.session_state.user_id}")

        if prefs:
            notif_prefs = prefs.get('notification_preferences', {})
            interface_prefs = prefs.get('interface_preferences', {})

            st.checkbox("Enable proactive AI check-ins", value=notif_prefs.get('proactive_check_ins', True))
            st.checkbox("Daily wellness summary email", value=notif_prefs.get('daily_summary', True))
            st.checkbox("Achievement notifications", value=notif_prefs.get('achievement_alerts', True))

            st.selectbox("Preferred units", ["metric", "imperial"],
                        index=["metric", "imperial"].index(interface_prefs.get('units', 'metric')))
            st.selectbox("Theme", ["light", "dark", "auto"],
                        index=["light", "dark", "auto"].index(interface_prefs.get('theme', 'light')))

            if st.button("Save Preferences", type="primary"):
                st.info("Preferences update feature is coming soon!")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666;'>
    <p>🧘 Wellness AI - Your Personal Holistic Health Companion</p>
    <p style='font-size: 0.8rem;'>Combining EEG analysis, AI coaching, and Ayurvedic wisdom for optimal wellbeing</p>
    <p style='font-size: 0.7rem;'>User ID: {st.session_state.user_id} | Backend: {BACKEND_URL}</p>
</div>
""", unsafe_allow_html=True)
