"""
UI/UX Enhancements for Streamlit App

Provides custom styling, components, and helpers
"""
import streamlit as st
import plotly.graph_objects as go


# Enhanced CSS
CUSTOM_CSS = """
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --info-color: #17a2b8;
    }

    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }

    .sub-header {
        font-size: 2rem;
        font-weight: 600;
        color: #667eea;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }

    /* Card components */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .recommendation-card {
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #00acc1;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .success-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
    }

    .warning-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
    }

    .info-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* Progress indicators */
    .progress-container {
        background-color: #e0e0e0;
        border-radius: 1rem;
        padding: 0.5rem;
        margin: 1rem 0;
    }

    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 2rem;
        border-radius: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        transition: width 0.5s ease;
    }

    /* Sidebar enhancements */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }

    /* Table styling */
    .dataframe {
        border-radius: 0.5rem;
        overflow: hidden;
    }

    /* Success/Error messages */
    .stAlert {
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Loading spinner */
    .stSpinner > div {
        border-color: #667eea !important;
    }

    /* Metric value styling */
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
    }

    .metric-label {
        font-size: 1rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Chart containers */
    .chart-container {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }

    /* Form styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 0.5rem;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.5rem 1.5rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f5f7fa;
        border-radius: 0.5rem;
        font-weight: 600;
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .badge-success {
        background-color: #d4edda;
        color: #155724;
    }

    .badge-warning {
        background-color: #fff3cd;
        color: #856404;
    }

    .badge-danger {
        background-color: #f8d7da;
        color: #721c24;
    }

    .badge-info {
        background-color: #d1ecf1;
        color: #0c5460;
    }
</style>
"""


def apply_custom_css():
    """Apply custom CSS to the app"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_metric_card(label: str, value, delta=None, delta_color="normal"):
    """
    Render enhanced metric card

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: Color for delta (normal, inverse, off)
    """
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_progress_bar(value: float, max_value: float = 100, label: str = ""):
    """
    Render custom progress bar

    Args:
        value: Current value
        max_value: Maximum value
        label: Optional label
    """
    percentage = min((value / max_value) * 100, 100)

    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {percentage}%">
            {label} {percentage:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, badge_type: str = "info"):
    """
    Render badge

    Args:
        text: Badge text
        badge_type: Type (success, warning, danger, info)
    """
    st.markdown(f"""
    <span class="badge badge-{badge_type}">{text}</span>
    """, unsafe_allow_html=True)


def render_info_box(title: str, content: str, box_type: str = "info"):
    """
    Render styled info box

    Args:
        title: Box title
        content: Box content
        box_type: Type (info, success, warning, recommendation)
    """
    st.markdown(f"""
    <div class="{box_type}-card">
        <h3 style="margin-top: 0;">{title}</h3>
        <p style="margin-bottom: 0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def create_gauge_chart(value: float, title: str, max_value: float = 100):
    """
    Create gauge chart for metrics

    Args:
        value: Current value
        title: Chart title
        max_value: Maximum value for gauge
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24}},
        delta={'reference': max_value * 0.7},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_value * 0.33], 'color': '#ffebee'},
                {'range': [max_value * 0.33, max_value * 0.67], 'color': '#fff3e0'},
                {'range': [max_value * 0.67, max_value], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={'color': "darkblue", 'family': "Arial"}
    )

    return fig


def show_loading_animation(text: str = "Loading..."):
    """Show loading animation with custom text"""
    with st.spinner(text):
        import time
        time.sleep(0.5)


def render_stats_grid(stats: dict):
    """
    Render statistics in a grid layout

    Args:
        stats: Dictionary of {label: value} pairs
    """
    cols = st.columns(len(stats))

    for col, (label, value) in zip(cols, stats.items()):
        with col:
            render_metric_card(label, value)


def render_timeline(events: list):
    """
    Render timeline of events

    Args:
        events: List of dicts with {time, title, description}
    """
    for event in events:
        st.markdown(f"""
        <div style="position: relative; padding-left: 2rem; margin: 1rem 0;">
            <div style="position: absolute; left: 0; top: 0; width: 0.5rem; height: 100%; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);"></div>
            <div style="background: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                <div style="font-weight: bold; color: #667eea;">{event.get('time', '')}</div>
                <div style="font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0;">{event.get('title', '')}</div>
                <div style="color: #666;">{event.get('description', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_comparison_card(left_label: str, left_value, right_label: str, right_value):
    """Render comparison card showing two metrics side by side"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <div class="metric-label">{left_label}</div>
            <div class="metric-value">{left_value}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="success-card" style="text-align: center;">
            <div class="metric-label">{right_label}</div>
            <div class="metric-value">{right_value}</div>
        </div>
        """, unsafe_allow_html=True)
