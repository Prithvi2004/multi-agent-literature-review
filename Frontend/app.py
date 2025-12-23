import streamlit as st
import streamlit.components.v1 as components
import time
import io
import json
from datetime import datetime

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="ResearchNovel",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'paper_fields_list' not in st.session_state:
    st.session_state['paper_fields_list'] = []
if 'paper_field_content' not in st.session_state:
    st.session_state['paper_field_content'] = ""
if 'paper_field_type' not in st.session_state:
    st.session_state['paper_field_type'] = 'Title'
if 'paper_field_add_warning' not in st.session_state:
    st.session_state['paper_field_add_warning'] = False
if 'paper_field_pending' not in st.session_state:
    st.session_state['paper_field_pending'] = False
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 'input'
if 'analysis_progress' not in st.session_state:
    st.session_state['analysis_progress'] = 0
if 'analysis_complete' not in st.session_state:
    st.session_state['analysis_complete'] = False
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []
if 'research_idea' not in st.session_state:
    st.session_state['research_idea'] = ""
if 'selected_fields' not in st.session_state:
    st.session_state['selected_fields'] = []

# Process any pending paper-field that was submitted in the previous run.
if st.session_state.get('paper_field_pending'):
    pending = st.session_state.pop('paper_field_to_add', None)
    st.session_state['paper_field_pending'] = False
    if pending and pending.get('content'):
        st.session_state['paper_fields_list'].append(pending)
    st.session_state['paper_field_content'] = ''

def handle_add_field():
    content = st.session_state.get('paper_field_content', '').strip()
    field_type = st.session_state.get('paper_field_type', 'Title')
    if content:
        st.session_state['paper_fields_list'].append({'field': field_type, 'content': content})
        # Don't modify the widget's session state directly
        st.session_state['paper_field_add_warning'] = False
    else:
        st.session_state['paper_field_add_warning'] = True

def handle_remove_field(index: int):
    if 0 <= index < len(st.session_state['paper_fields_list']):
        st.session_state['paper_fields_list'].pop(index)

def remove_uploaded_file(index: int):
    if 0 <= index < len(st.session_state['uploaded_files']):
        st.session_state['uploaded_files'].pop(index)

def generate_report_content(format_type: str) -> str:
    """Generate report content based on analysis results"""
    research_idea = st.session_state.get('research_idea', '')
    selected_fields = st.session_state.get('selected_fields', [])
    paper_fields = st.session_state.get('paper_fields_list', [])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if format_type == "PDF":
        # For PDF, we'll return markdown that can be converted
        content = f"""# Research Novelty Assessment Report
Generated on: {timestamp}

## Research Idea
{research_idea}

## Selected Research Fields
{', '.join(selected_fields)}

## Analysis Results
- **Novelty Score**: 87/100
- **Related Papers Found**: 23
- **Key Research Gaps Identified**: 5
- **Analysis Confidence**: 92%

## Key Findings
Your research demonstrates high novelty with significant potential for contribution...

## Recommendations
- Emphasize your hybrid architecture as the primary differentiator
- Include ablation studies to demonstrate symbolic component impact
"""
    elif format_type == "LaTeX":
        content = f"""\\documentclass{{article}}
\\title{{Research Novelty Assessment Report}}
\\author{{ResearchNovel AI}}
\\date{{{timestamp}}}

\\begin{{document}}
\\maketitle

\\section{{Research Idea}}
{research_idea}

\\section{{Selected Fields}}
{', '.join(selected_fields)}

\\section{{Analysis Summary}}
Novelty Score: 87/100\\\\
Related Papers: 23\\\\
Key Gaps: 5\\\\
Confidence: 92\\%

\\end{{document}}
"""
    else:  # Markdown
        content = f"""# Research Novelty Assessment Report

**Generated on:** {timestamp}

## Research Idea
{research_idea}

## Selected Research Fields
{chr(10).join(f"- {field}" for field in selected_fields)}

## Analysis Results
- **Novelty Score**: 87/100 (High novelty)
- **Related Papers Analyzed**: 23
- **Key Research Gaps**: 5
- **Analysis Confidence**: 92%

## Key Findings

### Novel Aspects
- Integration of neuro-symbolic reasoning with multimodal transformers
- Explicit knowledge graph incorporation for explainability
- Novel attention mechanism for symbolic reasoning alignment

### Related Prior Work
1. **Chen et al. (2024)** - *Multimodal Diagnosis with Vision-Language Models*
2. **Gupta & Lee (2023)** - *Neuro-Symbolic AI for Medical Imaging*
3. **Rodriguez et al. (2024)** - *Explainable Medical AI: A Survey*

### Research Gaps Identified
1. No existing work combines multimodal transformers with knowledge graphs
2. Limited research on interpretable attention mechanisms in medical AI
3. Lack of unified frameworks for symbolic-neural hybrid architectures

## Recommendations
- Emphasize your hybrid architecture as the primary differentiator
- Highlight explainability improvements over pure deep learning
- Consider adding ablation studies to demonstrate symbolic component impact
- Include clinical expert evaluation in your validation strategy

---
*Report generated by ResearchNovel AI - Multi-Agent Literature Review System*
"""

    return content

def run_analysis():
    """Run the analysis process"""
    st.session_state['analysis_complete'] = False

    # Store current inputs
    st.session_state['research_idea'] = st.session_state.get('research_idea_input', '')
    st.session_state['selected_fields'] = st.session_state.get('research_fields_select', [])

    # Simulate analysis with optimized timing
    stages = [
        ("Retrieving relevant literature...", 20),
        ("Analyzing paper abstracts...", 40),
        ("Extracting methodologies...", 60),
        ("Computing novelty scores...", 80),
        ("Generating comprehensive report...", 100)
    ]

    progress_bar = st.progress(0)
    status_text = st.empty()

    for stage, progress in stages:
        status_text.markdown(f"**{stage}**")
        progress_bar.progress(progress)
        time.sleep(0.3)  # Reduced sleep time for smoother experience

    status_text.markdown("**Analysis Complete!**")
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()

    st.session_state['analysis_complete'] = True
    # Trigger automatic switch to results and show completion toast
    st.session_state['switch_to_results'] = True
    st.session_state['show_completion_toast'] = True
    st.rerun()
# ----------------------------
# ADVANCED CUSTOM CSS WITH ANIMATIONS
# ----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* === ROOT VARIABLES === */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --primary-light: #818cf8;
        --secondary: #8b5cf6;
        --accent: #ec4899;
        --success: #10b981;
        --warning: #f59e0b;
        --dark-bg: #0a0e27;
        --dark-surface: #141b3d;
        --dark-card: #1e2749;
        --light-bg: #f8fafc;
        --light-surface: #ffffff;
        --text-dark: #1e293b;
        --text-light: #e2e8f0;
        --border-radius-sm: 12px;
        --border-radius: 20px;
        --border-radius-lg: 28px;
        --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        --shadow-lg: 0 20px 60px rgba(0, 0, 0, 0.18);
        --glow: 0 0 30px rgba(99, 102, 241, 0.4);
    }

    /* === KEYFRAME ANIMATIONS === */
    @keyframes gradientFlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    /* === BASE STYLES === */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(-45deg, #0a0e27, #141b3d, #1e2749, #0f1736);
        background-size: 400% 400%;
        animation: gradientFlow 20s ease infinite;
        color: var(--text-light);
    }
    
    /* Animated background particles */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* === GLASSMORPHISM CARDS === */
    .glass-card {
        background: rgba(30, 39, 73, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--shadow);
        transition: var(--transition);
        animation: fadeInUp 0.4s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-color: rgba(99, 102, 241, 0.2);
    }

    /* === JSON PREVIEW CARDS === */
    .json-preview-container {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        margin-top: 0.5rem;
    }

    .json-card {
        background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.25), rgba(15, 23, 42, 0.9));
        border-radius: var(--border-radius-sm);
        border: 1px solid rgba(148, 163, 184, 0.35);
        padding: 1rem 1.2rem 0.9rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.6);
        position: relative;
        overflow: hidden;
    }

    .json-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at top left, rgba(129, 140, 248, 0.3), transparent 55%);
        opacity: 0.35;
        pointer-events: none;
    }

    .json-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.35rem;
        position: relative;
        z-index: 1;
    }

    .json-card-title {
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        color: #e5e7eb;
    }

    .json-card-pill {
        font-size: 0.75rem;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.6);
        color: #9ca3af;
        font-weight: 600;
    }

    .json-card-body {
        position: relative;
        z-index: 1;
        border-radius: 0.6rem;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(30, 64, 175, 0.7);
        box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.85);
    }

    /* === HERO HEADER === */
    .hero-container {
        text-align: center;
        padding: 3rem 0 2rem;
        animation: fadeInUp 0.8s ease-out;
        position: relative;
        z-index: 1;
    }
    
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #e6eef6;
        margin-bottom: 0.6rem;
        letter-spacing: -0.01em;
        text-shadow: 0 6px 18px rgba(2,6,23,0.45);
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #cbd5e1;
        font-weight: 400;
        margin-bottom: 0.8rem;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.5;
        animation: fadeInUp 0.6s ease-out 0.12s backwards;
    }
    
    .hero-badges {
        display: flex;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
        animation: fadeInUp 0.8s ease-out 0.4s backwards;
        margin-top: 1.5rem;
    }
    
    .badge {
        padding: 0.4rem 1rem;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(226,238,246,0.06);
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #cfe7ff;
        transition: var(--transition);
        animation: none;
    }
    
    .badge:hover {
        background: rgba(255,255,255,0.045);
        border-color: rgba(226,238,246,0.12);
        transform: translateY(-2px);
    }

    /* === FORM ELEMENTS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div {
        background: rgba(20, 27, 61, 0.6) !important;
        border: 1.5px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: var(--border-radius-sm) !important;
        color: var(--text-light) !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
        transition: var(--transition) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
        background: rgba(20, 27, 61, 0.9) !important;
    }
    
    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stMultiSelect label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* === BUTTONS === */
    .stButton > button {
        width: 100%;
        height: 3.5rem;
        font-weight: 700;
        font-size: 1.05rem;
        border-radius: var(--border-radius-sm);
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }

    /* === FIELD TAGS === */
    .field-tag {
        display: inline-flex;
        align-items: center;
        padding: 0.6rem 1.2rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.4rem;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.3);
        transition: var(--transition);
        animation: scaleIn 0.3s ease-out;
        cursor: pointer;
    }
    
    .field-tag:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.25));
        border-color: rgba(99, 102, 241, 0.5);
        transform: translateY(-2px);
    }

    /* === PROGRESS STEPS === */
    .progress-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 2rem 0;
        padding: 1.5rem;
        background: rgba(20, 27, 61, 0.4);
        border-radius: var(--border-radius);
        border: 1px solid rgba(99, 102, 241, 0.2);
        animation: fadeInUp 0.6s ease-out;
    }
    
    .progress-step {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .progress-step::after {
        content: '';
        position: absolute;
        top: 20px;
        left: 50%;
        width: 100%;
        height: 3px;
        background: rgba(99, 102, 241, 0.2);
        z-index: -1;
    }
    
    .progress-step:last-child::after {
        display: none;
    }
    
    .progress-icon {
        width: 40px;
        height: 40px;
        background: rgba(99, 102, 241, 0.2);
        border: 2px solid rgba(99, 102, 241, 0.4);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        transition: var(--transition);
    }
    
    .progress-step.active .progress-icon {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-color: transparent;
        color: white;
        animation: pulse 2s infinite;
        box-shadow: var(--glow);
    }
    
    .progress-step.completed .progress-icon {
        background: var(--success);
        border-color: transparent;
        color: white;
    }
    
    .progress-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
    }
    
    .progress-step.active .progress-label {
        color: #c7d2fe;
    }

    /* === METRICS CARDS === */
    .metric-card {
        background: rgba(20, 27, 61, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: var(--border-radius-sm);
        padding: 1.5rem;
        text-align: center;
        transition: var(--transition);
        animation: scaleIn 0.5s ease-out;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 12px 24px rgba(99, 102, 241, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 600;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(20, 27, 61, 0.4);
        padding: 0.5rem;
        border-radius: var(--border-radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--border-radius-sm);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        border: 1px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: rgba(20, 27, 61, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: var(--border-radius-sm) !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        transition: var(--transition) !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: rgba(20, 27, 61, 0.7) !important;
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: rgba(10, 14, 39, 0.95) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        animation: fadeInLeft 0.6s ease-out;
    }

    /* === SLIDER === */
    .stSlider > div > div > div {
        background: rgba(99, 102, 241, 0.3) !important;
    }
    
    .stSlider > div > div > div > div {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.5) !important;
    }

    /* === ANIMATIONS ON SCROLL === */
    .animate-on-scroll {
        animation: fadeInUp 0.8s ease-out;
    }

    /* === LOADING SPINNER === */
    .stSpinner > div {
        border-color: rgba(99, 102, 241, 0.2) !important;
        border-top-color: #6366f1 !important;
    }

    /* === SUCCESS/WARNING MESSAGES === */
    .stSuccess, .stWarning, .stInfo {
        border-radius: var(--border-radius-sm) !important;
        border-left: 4px solid !important;
        backdrop-filter: blur(10px) !important;
        animation: slideDown 0.4s ease-out;
    }

    /* === SAAS STYLE TOAST / POPUP === */
    .saas-toast {
        position: fixed;
        top: 88px;
        right: 28px;
        width: 380px;
        background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
        border: 1px solid rgba(226,238,246,0.06);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: 12px;
        padding: 1rem 1rem;
        box-shadow: 0 12px 40px rgba(2,6,23,0.5);
        color: #e6eef6;
        z-index: 10080 !important;
        animation: fadeInUp 0.45s cubic-bezier(.2,.9,.2,1);
        box-sizing: border-box;
        transform: translateY(0);
        transition: opacity 0.6s ease, transform 0.6s ease;
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
    }

    .saas-toast .toast-icon {
        width: 46px;
        height: 46px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.12));
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        flex: 0 0 46px;
        box-shadow: 0 6px 18px rgba(99,102,241,0.12);
    }

    .saas-toast .toast-body {
        flex: 1 1 auto;
    }

    .saas-toast .toast-title {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.15rem;
        color: #f8fbff;
    }

    .saas-toast .toast-message {
        font-size: 0.9rem;
        color: #cfe7ff;
        line-height: 1.35;
        margin-bottom: 0.5rem;
    }

    .saas-toast .toast-actions {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .saas-toast .btn {
        padding: 0.45rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        border: none;
        cursor: pointer;
    }

    .saas-toast .btn-primary {
        background: linear-gradient(90deg, #4f46e5, #8b5cf6);
        color: white;
        box-shadow: 0 8px 20px rgba(79,70,229,0.18);
    }

    .saas-toast .btn-muted {
        background: rgba(255,255,255,0.02);
        color: #dbeafe;
        border: 1px solid rgba(226,238,246,0.04);
    }

    /* === HIDE STREAMLIT BRANDING === */
    /* Keep the top menu/header visible so Streamlit's Deploy and other
       top controls remain accessible. Only hide the footer. */
    #MainMenu { visibility: visible !important; }
    header { visibility: visible !important; }
    footer { visibility: hidden !important; }

    /* === RESPONSIVE === */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        .hero-subtitle {
            font-size: 1rem;
        }
        .glass-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------
# HERO HEADER WITH ANIMATED GRADIENT
# ----------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">ResearchNovel — Literature Review & Novelty Assessment</div>
    <div class="hero-subtitle">A research-focused tool that assists with literature synthesis, novelty evaluation, and actionable recommendations. Designed for clarity and rigorous academic workflows.</div>
    <div class="hero-badges">
        <span class="badge">Multi‑Agent Analysis</span>
        <span class="badge">RAG‑Enhanced Retrieval</span>
        <span class="badge">Research‑Grade Outputs</span>
        <span class="badge">Real‑time Insights</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# SIDEBAR CONFIGURATION
# ----------------------------
with st.sidebar:
    st.markdown("### Paper-Centric Mode")
    st.markdown("Provide your paper content as the primary input. Research idea and domains are optional refinements.")
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: rgba(99,102,241,0.1); 
    border-radius: 12px; border: 1px solid rgba(99,102,241,0.3);'>
        <div style='font-size: 0.85rem; color: #94a3b8; font-weight: 600;'>
            💡 Powered by
        </div>
        <div style='font-size: 0.9rem; color: #c7d2fe; font-weight: 700; margin-top: 0.25rem;'>
            LLMs • CrewAI • Ollama
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# MAIN CONTENT AREA WITH TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs(["Input & Configure", "Results & Analysis", "Paper Library"])

# If analysis just completed, switch to the Results tab and prepare a toast
if st.session_state.get('switch_to_results', False):
    try:
        tab2.select()
    except Exception:
        pass
    st.session_state['switch_to_results'] = False
    # Keep show flag so the toast can be rendered after switching
    st.session_state['show_completion_toast'] = True

# Render completion toast if requested
if st.session_state.get('show_completion_toast', False):
    # Use a zero-size component that injects the toast into the parent DOM
    components.html(
        """
        <script>
        (function(){
            var doc = window.parent.document;

            // Remove any existing toast
            var existing = doc.getElementById('saasToast');
            if (existing && existing.parentNode) {
                existing.parentNode.removeChild(existing);
            }

            // Create toast container using existing CSS classes
            var toast = doc.createElement('div');
            toast.id = 'saasToast';
            toast.className = 'saas-toast';

            var html = ''
              + '<div class="toast-icon">✓</div>'
              + '<div class="toast-body">'
              +   '<div class="toast-title">Analysis Complete</div>'
              +   '<div class="toast-message">Your novelty assessment is ready. Open the Results & Analysis tab to view the full report and exports.</div>'
              +   '<div class="toast-actions">'
              +     '<button type="button" class="btn btn-primary">Close</button>'
              +   '</div>'
              + '</div>';

            toast.innerHTML = html;
            doc.body.appendChild(toast);

            function dismissSaasToast(){
                if (!toast) return;
                toast.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-8px)';
                setTimeout(function(){
                    if (toast && toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 620);
            }

            // Close button handler
            var btn = toast.querySelector('button');
            if (btn) {
                btn.addEventListener('click', function(ev){
                    ev.preventDefault();
                    ev.stopPropagation();
                    dismissSaasToast();
                });
            }

            // Auto-dismiss after 3 seconds
            setTimeout(dismissSaasToast, 4500);
        })();
        </script>
        """,
        height=0,
        width=0,
    )
    # Clear the flag so the toast doesn't reappear on subsequent reruns
    st.session_state['show_completion_toast'] = False

# TAB 1: INPUT & CONFIGURE
with tab1:
    # Progress Steps Visualization (Paper content is primary)
    has_paper_content = bool(st.session_state.get('paper_fields_list')) or bool(st.session_state.get('uploaded_files'))
    has_research_idea = bool(st.session_state.get('research_idea_input', '').strip())
    has_domains = bool(st.session_state.get('selected_fields'))
    has_analysis_done = bool(st.session_state.get('analysis_complete'))

    step_states = [
        has_paper_content,
        has_research_idea,
        has_domains,
        has_analysis_done,
    ]

    # Determine first incomplete step for "active" styling
    first_incomplete_idx = None
    for idx, done in enumerate(step_states):
        if not done:
            first_incomplete_idx = idx
            break

    step_classes = []
    for idx, done in enumerate(step_states):
        classes = []
        if done:
            classes.append("completed")
        if not done and (first_incomplete_idx == idx):
            classes.append("active")
        step_classes.append(" ".join(classes))

    # Overall numeric completion based on completed steps
    completed_count = sum(1 for s in step_states if s)
    total_steps = len(step_states)
    progress_percent = int((completed_count / total_steps) * 100) if total_steps > 0 else 0



    progress_html = f"""
    <div class="progress-container">
        <div class="progress-step {step_classes[0]}">
            <div class="progress-icon">1</div>
            <div class="progress-label">Paper Content</div>
        </div>
        <div class="progress-step {step_classes[1]}">
            <div class="progress-icon">2</div>
            <div class="progress-label">Research Idea (Optional)</div>
        </div>
        <div class="progress-step {step_classes[2]}">
            <div class="progress-icon">3</div>
            <div class="progress-label">Domains (Optional)</div>
        </div>
        <div class="progress-step {step_classes[3]}">
            <div class="progress-icon">4</div>
            <div class="progress-label">Analysis</div>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

    # Paper Content Section (Primary)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Paper Content")
    st.markdown("*Add specific sections from your paper draft. This is the main input for the analysis.*")

    col1, col2 = st.columns([3, 1])

    with col1:
        paper_field_type = st.selectbox(
            "Select Paper Section",
            options=["Title", "Abstract", "Introduction", "Literature Review", "Methodology",
                     "Results", "Discussion", "Conclusion", "Keywords", "References"],
            key="paper_field_type"
        )

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(st.session_state['paper_fields_list'])}</div>
            <div class="metric-label">Sections Added</div>
        </div>
        """, unsafe_allow_html=True)

    paper_field_content = st.text_area(
        f"Content for: {paper_field_type}",
        value=st.session_state.get('paper_field_content', ''),
        height=150,
        placeholder=f"Paste or type your {paper_field_type.lower()} content here...",
        key="paper_field_content"
    )

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("Add Section", key="add_paper_field_btn"):
            handle_add_field()
            st.rerun()

    if st.session_state.get('paper_field_add_warning'):
        st.warning("⚠️ Please enter content before adding a section.")

    # Display added paper sections
    if st.session_state['paper_fields_list']:
        st.markdown("#### Added Paper Sections")
        for i, item in enumerate(st.session_state['paper_fields_list']):
            with st.expander(f"{item['field']}: {item['content'][:60]}{'...' if len(item['content'])>60 else ''}", expanded=False):
                st.markdown(f"**{item['field']}**")
                st.text(item['content'])
                if st.button("Remove", key=f"remove_field_{i}"):
                    handle_remove_field(i)
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Optional Research Idea Section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Optional Research Idea")
    st.markdown("*Optionally describe your hypothesis, methodology, or problem statement to further focus the analysis*")

    research_idea = st.text_area(
        "Research Idea",
        value=st.session_state.get('research_idea', ''),
        height=180,
        placeholder="Example: I propose a novel hybrid architecture combining multimodal transformers with neuro-symbolic reasoning for interpretable medical image diagnosis. Unlike existing approaches that rely solely on deep learning, my method incorporates symbolic knowledge graphs to provide explainable diagnostic pathways...",
        label_visibility="collapsed",
        key="research_idea_input"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Optional Research Fields Selection
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Optional Research Domains")
    st.markdown("*Optionally select academic fields to steer the literature search and positioning*")

    col1, col2 = st.columns([2, 1])

    with col1:
        fields = [
            "Artificial Intelligence", "Natural Language Processing", "Computer Vision",
            "Machine Learning", "Deep Learning", "Bioinformatics", "Robotics",
            "Human-Computer Interaction", "Theoretical Computer Science", "Data Science",
            "Cognitive Science", "Computational Biology", "Information Retrieval",
            "Knowledge Graphs", "Reinforcement Learning"
        ]
        selected_fields = st.multiselect(
            "Research Fields",
            options=fields,
            default=st.session_state.get('selected_fields', []),
            label_visibility="collapsed",
            key="research_fields_select"
        )

        # Keep selected domains in session state so JSON and progress work
        st.session_state['selected_fields'] = selected_fields

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(selected_fields)}</div>
            <div class="metric-label">Fields Selected</div>
        </div>
        """, unsafe_allow_html=True)

    if selected_fields:
        st.markdown("#### Selected Research Domains")
        tags_html = "".join([f'<span class="field-tag">{field}</span>' for field in selected_fields])
        st.markdown(tags_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Action Button + JSON preview
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    # JSON preview of current input (expand/hide) just above the launch button
    with st.expander("Preview Analysis Input (JSON)", expanded=False):
        paper_data = {
            "paper_sections": st.session_state.get('paper_fields_list', []),
            "uploaded_papers": [
                {
                    "name": f.get('name'),
                    "size_bytes": f.get('size'),
                    "type": f.get('type')
                }
                for f in st.session_state.get('uploaded_files', [])
            ],
        }

        optional_data = {
            "research_idea": st.session_state.get('research_idea_input', '').strip(),
            "selected_domains": st.session_state.get('selected_fields', []),
        }

        paper_json = json.dumps(paper_data, indent=2, ensure_ascii=False)
        optional_json = json.dumps(optional_data, indent=2, ensure_ascii=False)

        st.markdown('<div class="json-preview-container">', unsafe_allow_html=True)

        # Paper data card
        st.markdown(
            f"""
            <div class="json-card">
                <div class="json-card-header">
                    <div class="json-card-title">Paper Data</div>
                    <div class="json-card-pill">Sections: {len(paper_data['paper_sections'])} • Uploads: {len(paper_data['uploaded_papers'])}</div>
                </div>
                <div class="json-card-body">
            """ , unsafe_allow_html=True,
        )
        st.code(paper_json, language="json")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # Optional fields card
        st.markdown(
            f"""
            <div class="json-card">
                <div class="json-card-header">
                    <div class="json-card-title">Optional Fields Data</div>
                    <div class="json-card-pill">Idea: {'Yes' if optional_data['research_idea'] else 'No'} • Domains: {len(optional_data['selected_domains'])}</div>
                </div>
                <div class="json-card-body">
            """ , unsafe_allow_html=True,
        )
        st.code(optional_json, language="json")
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Launch Comprehensive Analysis", key="run_analysis_btn", use_container_width=True):
        has_paper_content_for_run = bool(st.session_state.get('paper_fields_list')) or bool(st.session_state.get('uploaded_files'))
        if not has_paper_content_for_run:
            st.error("Please add paper content (upload papers in the Paper Library tab or add sections above) before running the analysis.")
        else:
            run_analysis()
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: RESULTS & ANALYSIS
with tab2:
    if st.session_state.get('analysis_complete', False):
        st.success("Novelty assessment completed successfully!")

        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">87</div>
                <div class="metric-label">Novelty Score</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">23</div>
                <div class="metric-label">Related Papers</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">5</div>
                <div class="metric-label">Key Gaps</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">92%</div>
                <div class="metric-label">Confidence</div>
            </div>
            """, unsafe_allow_html=True)

        # Main Results Card
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Novelty Assessment Summary")

        research_idea = st.session_state.get('research_idea', '')
        selected_fields = st.session_state.get('selected_fields', [])

        st.markdown(f"""
        #### Overall Assessment
        Your research demonstrates **high novelty** with significant potential for contribution.
        The proposed hybrid architecture addresses a critical gap in interpretable medical AI.

        #### Key Findings

        **Novel Aspects:**
        - Integration of neuro-symbolic reasoning with multimodal transformers
        - Explicit knowledge graph incorporation for explainability
        - Novel attention mechanism for symbolic reasoning alignment

        **Related Prior Work:**
        1. **Chen et al. (2024)** - *"Multimodal Diagnosis with Vision-Language Models"*
           - Focus: Pure deep learning without symbolic reasoning
           - Gap: Limited explainability

        2. **Gupta & Lee (2023)** - *"Neuro-Symbolic AI for Medical Imaging"*
           - Focus: Symbolic reasoning in radiology
           - Gap: Single-modality approach

        3. **Rodriguez et al. (2024)** - *"Explainable Medical AI: A Survey"*
           - Focus: Survey of explanation methods
           - Gap: Lacks concrete hybrid architecture

        **Identified Research Gaps:**
        1. No existing work combines multimodal transformers with knowledge graphs
        2. Limited research on interpretable attention mechanisms in medical AI
        3. Lack of unified frameworks for symbolic-neural hybrid architectures
        4. Insufficient benchmarks for explainable medical diagnosis
        5. Limited real-world clinical validation studies

        **Recommendations:**
        - Emphasize your hybrid architecture as the primary differentiator
        - Highlight the explainability improvements over pure deep learning
        - Consider adding ablation studies to demonstrate symbolic component impact
        - Include clinical expert evaluation in your validation strategy
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        # Download Section
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Export & Share")

        col1, col2, col3 = st.columns(3)

        # Generate report content
        pdf_content = generate_report_content("PDF")
        latex_content = generate_report_content("LaTeX")
        markdown_content = generate_report_content("Markdown")

        with col1:
            st.download_button(
                "Download PDF Report",
                data=pdf_content,
                file_name="novelty_report.md",  # Using .md for now, can be converted to PDF
                mime="text/markdown",
                use_container_width=True,
                key="download_pdf"
            )

        with col2:
            st.download_button(
                "Download LaTeX Source",
                data=latex_content,
                file_name="novelty_report.tex",
                mime="text/plain",
                use_container_width=True,
                key="download_latex"
            )

        with col3:
            st.download_button(
                    "Download Markdown",
                data=markdown_content,
                file_name="novelty_report.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_markdown"
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # Clear Analysis Button
        if st.button("Start New Analysis", key="clear_analysis"):
            st.session_state['analysis_complete'] = False
            st.session_state['research_idea'] = ""
            st.session_state['selected_fields'] = []
            st.session_state['paper_fields_list'] = []
            st.rerun()

    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        ### Analysis Results

        Configure your analysis parameters and launch the analysis in the **Input & Configure** tab
        to see comprehensive results here.

        **What you'll get:**

        - Novelty scoring and assessment
        - Related work identification
        - Research gap analysis
        - Strategic recommendations
        - Citation network visualization
        - Exportable reports in multiple formats

        """)
        st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: PAPER LIBRARY
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Your Paper Collection")
    st.markdown("*Manage and organize your research papers*")

    # Upload section
    uploaded_files = st.file_uploader(
        "Upload Papers (PDF)",
        accept_multiple_files=True,
        type=['pdf'],
        help="Upload PDF files of research papers for analysis",
        key="file_uploader"
    )

    # Add newly uploaded files to session state
    if uploaded_files:
        for file in uploaded_files:
            # Check if file is not already in the list
            if not any(f['name'] == file.name for f in st.session_state['uploaded_files']):
                file_data = {
                    'name': file.name,
                    'size': file.size,
                    'content': file.getvalue(),
                    'type': file.type
                }
                st.session_state['uploaded_files'].append(file_data)

    # Display uploaded files
    if st.session_state['uploaded_files']:
        st.success(f"{len(st.session_state['uploaded_files'])} paper(s) in your library!")

        for i, file_info in enumerate(st.session_state['uploaded_files']):
            with st.expander(f"{file_info['name']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Filename:** {file_info['name']}")
                    st.write(f"**Size:** {file_info['size'] / 1024:.2f} KB")
                    st.write(f"**Type:** {file_info['type']}")

                with col2:
                    # Download button for individual file
                    st.download_button(
                        "Download",
                        data=file_info['content'],
                        file_name=file_info['name'],
                        mime=file_info['type'],
                        key=f"download_file_{i}"
                    )

                with col3:
                    # Remove button
                    if st.button("Remove", key=f"remove_file_{i}"):
                        remove_uploaded_file(i)
                        st.rerun()

        # Clear all files button
        if st.button("Clear All Files", key="clear_all_files"):
            st.session_state['uploaded_files'] = []
            st.rerun()

    else:
        st.info("Upload PDF papers to build your research library")

    # Library Statistics
    if st.session_state['uploaded_files']:
        total_size = sum(f['size'] for f in st.session_state['uploaded_files'])
        st.markdown(f"""
        <div style='margin-top: 1rem; padding: 1rem; background: rgba(99,102,241,0.1); 
        border-radius: 12px; border: 1px solid rgba(99,102,241,0.3);'>
            <div style='font-size: 0.9rem; color: #94a3b8; font-weight: 600;'>
                Library Statistics
            </div>
            <div style='font-size: 0.85rem; color: #c7d2fe; margin-top: 0.5rem;'>
                Total Papers: {len(st.session_state['uploaded_files'])} • 
                Total Size: {total_size / (1024*1024):.2f} MB
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("""
<div style='text-align: center; padding: 3rem 0 2rem; opacity: 0.85;'>
    <div style='font-size: 0.9rem; color: #94a3b8;'>
        ResearchNovel — Multi-Agent Literature Review and Novelty Assessment
    </div>
    <div style='font-size: 0.85rem; color: #8b98a8; margin-top: 0.5rem;'>
        © 2025 ResearchNovel. All rights reserved.
    </div>
</div>
""", unsafe_allow_html=True)
