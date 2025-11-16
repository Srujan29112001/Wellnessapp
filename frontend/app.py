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
    ["🏠 Dashboard", "🧠 EEG Analysis", "💬 AI Coach", "📊 Health Metrics", "🥗 Nutrition", "💊 Supplements", "⚙️ Settings"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Wellness AI** combines:
- EEG brainwave analysis
- AI wellness coaching
- Personalized recommendations
- Ayurvedic principles
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
