"""
Authentication UI Components for Streamlit

Provides login, register, and session management
"""
import streamlit as st
import requests
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AUTH_API = f"{BACKEND_URL}/api/v1/auth"


def init_session_state():
    """Initialize authentication-related session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'access_token' not in st.session_state:
        st.session_state.access_token = None

    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None

    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None


def login(email: str, password: str) -> bool:
    """
    Login user with email and password

    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        response = requests.post(
            f"{AUTH_API}/login",
            json={"email": email, "password": password},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Store tokens
            st.session_state.access_token = data['access_token']
            st.session_state.refresh_token = data['refresh_token']
            st.session_state.authenticated = True

            # Get user info
            user_info = get_user_info(data['access_token'])
            if user_info:
                st.session_state.user_data = user_info
                st.session_state.user_id = user_info['user_id']

            return True
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False


def register(email: str, password: str, name: str, age: int = None) -> bool:
    """
    Register new user

    Returns:
        bool: True if registration successful, False otherwise
    """
    try:
        payload = {
            "email": email,
            "password": password,
            "name": name
        }
        if age:
            payload["age"] = age

        response = requests.post(
            f"{AUTH_API}/register",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Store tokens
            st.session_state.access_token = data['access_token']
            st.session_state.refresh_token = data['refresh_token']
            st.session_state.authenticated = True

            # Get user info
            user_info = get_user_info(data['access_token'])
            if user_info:
                st.session_state.user_data = user_info
                st.session_state.user_id = user_info['user_id']

            return True
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"Registration failed: {error_detail}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False


def get_user_info(access_token: str) -> dict:
    """Get current user information"""
    try:
        response = requests.get(
            f"{AUTH_API}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None

    except requests.exceptions.RequestException:
        return None


def logout():
    """Logout current user"""
    try:
        if st.session_state.get('access_token'):
            requests.post(
                f"{AUTH_API}/logout",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                timeout=5
            )
    except:
        pass

    # Clear session state
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_data = None
    st.session_state.user_id = None


def render_login_page():
    """Render login/register page"""
    st.markdown("<h1 class='main-header'>🧘 Wellness AI</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <p style='font-size: 1.2rem; color: #666;'>
            Your personalized holistic health companion
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs for login and register
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Login to Your Account")

            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            with col2:
                demo_btn = st.form_submit_button("Demo", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    with st.spinner("Logging in..."):
                        if login(email, password):
                            st.success("Login successful! 🎉")
                            time.sleep(1)
                            st.rerun()

            if demo_btn:
                with st.spinner("Logging in as demo user..."):
                    if login("demo@wellnessai.com", "demo123"):
                        st.success("Logged in as demo user! 🎉")
                        time.sleep(1)
                        st.rerun()

    with tab2:
        with st.form("register_form"):
            st.subheader("Create New Account")

            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your.email@example.com", key="reg_email")
            password = st.text_input("Password", type="password", placeholder="Min. 8 characters", key="reg_password")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            age = st.number_input("Age (optional)", min_value=1, max_value=120, value=None, step=1)

            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

            if submitted:
                if not name or not email or not password:
                    st.error("Please fill in all required fields")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Creating account..."):
                        if register(email, password, name, age):
                            st.success("Account created successfully! 🎉")
                            time.sleep(1)
                            st.rerun()

    # Demo credentials info
    with st.expander("ℹ️ Demo Account"):
        st.info("""
        **Demo Credentials:**
        - Email: `demo@wellnessai.com`
        - Password: `demo123`

        Use the demo account to explore all features without registration.
        """)

    # Feature highlights
    st.markdown("---")
    st.markdown("### ✨ Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🧠 EEG Analysis**
        - Brainwave monitoring
        - Mental state detection
        - Stress & focus tracking
        """)

    with col2:
        st.markdown("""
        **🥗 Meal Planning**
        - Personalized nutrition
        - Budget optimization
        - Ayurvedic balance
        """)

    with col3:
        st.markdown("""
        **📅 Life Optimization**
        - Daily schedules
        - Energy forecasting
        - Holistic wellness
        """)


def require_auth():
    """
    Decorator-like function to require authentication
    Call this at the start of protected pages
    """
    init_session_state()

    if not st.session_state.authenticated:
        render_login_page()
        st.stop()

    # Verify token is still valid
    if st.session_state.access_token:
        try:
            response = requests.post(
                f"{AUTH_API}/verify-token",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                timeout=5
            )
            if response.status_code != 200:
                # Token expired or invalid
                st.warning("Your session has expired. Please log in again.")
                logout()
                st.rerun()
        except:
            pass  # Network error, allow through


def render_user_info():
    """Render user info in sidebar"""
    if st.session_state.authenticated and st.session_state.user_data:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{st.session_state.user_data.get('name', 'User')}**")
        st.sidebar.markdown(f"📧 {st.session_state.user_data.get('email', '')}")

        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()


def get_auth_headers() -> dict:
    """Get authorization headers for API requests"""
    if st.session_state.get('access_token'):
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


import time
