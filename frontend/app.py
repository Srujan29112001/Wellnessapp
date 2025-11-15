"""
Wellness AI - Streamlit Frontend

Multi-page application for holistic health tracking and AI coaching
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/v1"

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

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Stress Level",
            value="Medium",
            delta="-10% vs yesterday",
            delta_color="inverse"
        )

    with col2:
        st.metric(
            label="Focus Score",
            value="72/100",
            delta="+5 points"
        )

    with col3:
        st.metric(
            label="Sleep Quality",
            value="7.2 hrs",
            delta="+0.5 hrs"
        )

    with col4:
        st.metric(
            label="Wellness Score",
            value="85/100",
            delta="+3 points"
        )

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Stress Trends (Last 7 Days)")

        # Sample data
        dates = pd.date_range(end=datetime.now(), periods=7).strftime("%m/%d")
        stress_levels = [0.6, 0.7, 0.5, 0.8, 0.6, 0.5, 0.4]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(dates),
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

    with col2:
        st.subheader("🎯 Today's Recommendations")

        st.markdown("""
        <div class='recommendation-card'>
        <strong>🧘 Breathing Exercise</strong><br>
        Try 5 minutes of box breathing to reduce afternoon stress spike.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='recommendation-card'>
        <strong>💊 Magnesium</strong><br>
        Consider taking magnesium in the evening for better sleep.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='recommendation-card'>
        <strong>🥗 Nutrition</strong><br>
        Add more leafy greens to boost magnesium intake naturally.
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
                    # Simulate analysis (in production, call backend API)
                    import time
                    time.sleep(2)

                    # Display results
                    st.subheader("Analysis Results")

                    # Mental state
                    st.markdown("### Current Mental State: **Stressed**")

                    # Band powers visualization
                    bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
                    powers = [0.15, 0.20, 0.25, 0.35, 0.05]

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
                        st.metric("Stressed", "65%", delta=None)
                    with prob_col2:
                        st.metric("Focused", "20%", delta=None)
                    with prob_col3:
                        st.metric("Relaxed", "10%", delta=None)
                    with prob_col4:
                        st.metric("Drowsy", "5%", delta=None)

    with col2:
        st.subheader("📋 Recommendations")

        st.markdown("""
        Based on your EEG analysis:

        **Immediate Actions:**
        - 🧘 Try 5-minute breathing exercise
        - 🚶 Take a short walk
        - 💧 Hydrate

        **Long-term Strategies:**
        - Consider Ashwagandha supplement
        - Establish regular meditation practice
        - Improve sleep hygiene

        **Dominant Band:** Beta (indicates mental activity/stress)
        """)

# ============================================================================
# PAGE: AI Coach
# ============================================================================
elif page == "💬 AI Coach":
    st.markdown("<h1 class='main-header'>💬 AI Wellness Coach</h1>", unsafe_allow_html=True)

    st.info("Chat with your personal AI wellness coach. The coach has access to your health data, Ayurvedic knowledge, and nutritional science.")

    # Chat history
    if 'chat_history' not in st.session_state:
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

        # Generate response (demo)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                import time
                time.sleep(1)

                # Demo response
                response = f"""I understand you're asking about: "{prompt}"

Based on your recent health data:
- Your stress levels have been elevated (EEG shows high beta activity)
- Sleep quality: 7.2 hours (good, but could be improved)
- Your Vata-Pitta dosha suggests you benefit from grounding practices

**My recommendations:**

1. **Immediate:** Try a 5-minute box breathing exercise (4-4-4-4 pattern)
2. **Supplement:** Consider Ashwagandha (300mg) with dinner to reduce cortisol
3. **Diet:** Add magnesium-rich foods (nuts, seeds, leafy greens)
4. **Lifestyle:** Establish a calming evening routine 1 hour before bed

Would you like me to guide you through a breathing exercise now, or would you prefer more information about any of these recommendations?

*[Sources: Your EEG data from yesterday, Ayurvedic dosha assessment, PubMed research on stress management]*
"""

                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

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
                steps = st.number_input("Steps", min_value=0, value=8000)
                calories = st.number_input("Calories Burned", min_value=0, value=2000)

            with col2:
                sleep_hours = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, value=7.5, step=0.5)
                weight = st.number_input("Weight (kg)", min_value=0.0, value=70.0, step=0.1)

            with col3:
                heart_rate = st.number_input("Avg Heart Rate (bpm)", min_value=0, value=70)
                mood = st.select_slider("Mood", options=["Very Low", "Low", "Medium", "Good", "Excellent"])

            submitted = st.form_submit_button("Submit", type="primary")

            if submitted:
                st.success("✅ Metrics logged successfully!")

    # Display trends
    st.subheader("📈 Trends")

    tab1, tab2, tab3, tab4 = st.tabs(["💓 Vitals", "😴 Sleep", "🏃 Activity", "📉 Stress"])

    with tab1:
        # Heart rate trend
        dates = pd.date_range(end=datetime.now(), periods=14)
        hr_data = pd.DataFrame({
            'Date': dates,
            'Heart Rate': [72, 70, 75, 71, 69, 73, 74, 70, 68, 72, 71, 70, 69, 71]
        })

        fig = px.line(hr_data, x='Date', y='Heart Rate', title='Heart Rate Trend')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Sleep trend
        sleep_data = pd.DataFrame({
            'Date': dates,
            'Hours': [7.5, 6.5, 7.0, 8.0, 7.2, 6.8, 7.5, 7.0, 6.5, 7.8, 7.2, 7.0, 7.5, 7.2]
        })

        fig = px.bar(sleep_data, x='Date', y='Hours', title='Sleep Duration')
        fig.add_hline(y=7.0, line_dash="dash", line_color="green", annotation_text="Target: 7 hours")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Activity
        activity_data = pd.DataFrame({
            'Date': dates,
            'Steps': [8500, 7200, 9100, 10200, 8800, 7500, 6500, 9000, 8200, 9500, 8700, 9200, 8500, 8900]
        })

        fig = px.area(activity_data, x='Date', y='Steps', title='Daily Steps')
        fig.add_hline(y=8000, line_dash="dash", line_color="green", annotation_text="Target: 8000 steps")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        # Stress levels from EEG
        stress_data = pd.DataFrame({
            'Date': dates,
            'Stress': [0.6, 0.7, 0.5, 0.4, 0.6, 0.8, 0.7, 0.5, 0.6, 0.5, 0.4, 0.5, 0.6, 0.4]
        })

        fig = px.line(stress_data, x='Date', y='Stress', title='Stress Level (from EEG)')
        fig.update_yaxes(range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: Nutrition
# ============================================================================
elif page == "🥗 Nutrition":
    st.markdown("<h1 class='main-header'>🥗 Nutrition & Diet Tracking</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Log Meal", "📊 Nutrition Summary", "📸 Food Recognition"])

    with tab1:
        st.subheader("Log Your Meal")

        with st.form("meal_log_form"):
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            foods = st.text_area("Food Items (one per line)", "Grilled chicken\nMixed salad\nQuinoa")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                calories = st.number_input("Calories", min_value=0, value=500)
            with col2:
                protein = st.number_input("Protein (g)", min_value=0.0, value=35.0)
            with col3:
                carbs = st.number_input("Carbs (g)", min_value=0.0, value=40.0)
            with col4:
                fat = st.number_input("Fat (g)", min_value=0.0, value=15.0)

            if st.form_submit_button("Log Meal", type="primary"):
                st.success("✅ Meal logged successfully!")

    with tab2:
        st.subheader("Today's Nutrition Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Calories", "1,850", delta="150 under target")
        with col2:
            st.metric("Protein", "95g", delta="+10g vs target")
        with col3:
            st.metric("Carbs", "180g", delta="On target")
        with col4:
            st.metric("Fat", "65g", delta="-5g vs target")

        # Macronutrient breakdown
        fig = go.Figure(data=[go.Pie(
            labels=['Protein', 'Carbs', 'Fat'],
            values=[95*4, 180*4, 65*9],
            hole=.3
        )])
        fig.update_layout(title="Macronutrient Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📸 AI Food Recognition")
        st.info("Upload a photo of your meal and our AI will identify the foods and estimate nutrition.")

        uploaded_image = st.file_uploader("Upload meal photo", type=['jpg', 'jpeg', 'png'])

        if uploaded_image:
            st.image(uploaded_image, caption="Your meal", use_column_width=True)

            if st.button("🔍 Analyze Food"):
                with st.spinner("Analyzing image..."):
                    import time
                    time.sleep(2)

                    st.success("Analysis complete!")
                    st.markdown("""
                    **Detected Foods:**
                    - Mixed salad (confidence: 92%)
                    - Grilled chicken (confidence: 87%)
                    - Quinoa (confidence: 78%)

                    **Estimated Nutrition:**
                    - Calories: ~450 kcal
                    - Protein: 40g
                    - Carbs: 35g
                    - Fat: 12g
                    """)

# ============================================================================
# PAGE: Supplements
# ============================================================================
elif page == "💊 Supplements":
    st.markdown("<h1 class='main-header'>💊 Supplement Tracking</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 My Supplements", "🔍 Search Database", "📸 Scan Label"])

    with tab1:
        st.subheader("Current Supplements")

        # Sample data
        supplements = pd.DataFrame({
            'Supplement': ['Ashwagandha', 'Magnesium Glycinate', 'Omega-3'],
            'Dosage': ['500mg', '400mg', '1000mg EPA/DHA'],
            'Frequency': ['Daily (evening)', 'Daily (evening)', 'Daily (with meals)'],
            'Purpose': ['Stress reduction', 'Sleep support', 'Inflammation, brain health']
        })

        st.dataframe(supplements, use_container_width=True)

        if st.button("➕ Add New Supplement"):
            st.info("Add supplement form would appear here")

    with tab2:
        st.subheader("🔍 Supplement Database")

        search = st.text_input("Search supplements...", placeholder="e.g., stress, sleep, energy")

        if search:
            st.markdown("""
            ### Ashwagandha
            **Category:** Adaptogenic Herb (Ayurvedic)

            **Benefits:**
            - Reduces stress and anxiety
            - Lowers cortisol levels
            - Improves sleep quality
            - Supports cognitive function

            **Dosage:** 300-600mg daily

            **Evidence Level:** Strong (Multiple RCTs)

            **Contraindications:**
            - Pregnancy/breastfeeding
            - Autoimmune conditions
            - Thyroid medication (may interact)

            [View Full Details]
            """)

    with tab3:
        st.subheader("📸 OCR Supplement Label Scanner")
        st.info("Upload a photo of your supplement bottle to extract ingredient information.")

        uploaded_label = st.file_uploader("Upload supplement label", type=['jpg', 'jpeg', 'png'], key='label')

        if uploaded_label:
            st.image(uploaded_label, caption="Supplement label", use_column_width=True)

            if st.button("🔍 Extract Information"):
                with st.spinner("Reading label..."):
                    import time
                    time.sleep(2)

                    st.success("Label scanned successfully!")
                    st.markdown("""
                    **Extracted Information:**

                    **Supplement:** Ashwagandha Extract

                    **Dosage:** 500mg per capsule

                    **Ingredients:**
                    - Ashwagandha root extract (standardized to 5% withanolides)
                    - Cellulose capsule

                    **Suggested Use:** 1 capsule daily with meals

                    **Warnings:** Consult doctor if pregnant or nursing

                    [Check for Interactions with Your Current Stack]
                    """)

# ============================================================================
# PAGE: Settings
# ============================================================================
elif page == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>⚙️ Settings</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🎯 Goals", "🔔 Preferences"])

    with tab1:
        st.subheader("User Profile")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name", value="Demo User")
            age = st.number_input("Age", min_value=0, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Prefer not to say"])

        with col2:
            dosha = st.selectbox("Ayurvedic Dosha", ["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Not sure"])
            email = st.text_input("Email", value="demo@wellnessai.com")

        if st.button("Take Dosha Assessment"):
            st.info("Dosha assessment quiz would appear here")

        if st.button("Save Profile", type="primary"):
            st.success("✅ Profile updated!")

    with tab2:
        st.subheader("Health Goals")

        goals = st.multiselect(
            "Select your health goals",
            ["Reduce stress", "Improve sleep", "Boost energy", "Lose weight", "Build muscle",
             "Improve focus", "Better nutrition", "Mental clarity"],
            default=["Reduce stress", "Improve sleep"]
        )

        medical_conditions = st.text_area("Medical Conditions (for contraindication checking)")
        medications = st.text_area("Current Medications")

        if st.button("Save Goals", type="primary"):
            st.success("✅ Goals updated!")

    with tab3:
        st.subheader("Preferences")

        st.checkbox("Enable proactive AI check-ins", value=True)
        st.checkbox("Daily wellness summary email", value=True)
        st.checkbox("Achievement notifications", value=True)

        st.selectbox("Preferred units", ["Metric", "Imperial"])
        st.selectbox("Theme", ["Light", "Dark", "Auto"])

        if st.button("Save Preferences", type="primary"):
            st.success("✅ Preferences updated!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🧘 Wellness AI - Your Personal Holistic Health Companion</p>
    <p style='font-size: 0.8rem;'>Combining EEG analysis, AI coaching, and Ayurvedic wisdom for optimal wellbeing</p>
</div>
""", unsafe_allow_html=True)
