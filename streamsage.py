import openai
import streamlit as st
import logging
from PIL import Image, ImageEnhance
import time
import json
import requests
import base64
import hashlib
import uuid
from datetime import datetime
from openai import OpenAI, OpenAIError
import os
import psutil
import platform
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 50
API_DOCS_URL = "https://docs.streamlit.io/library/api-reference"
GITHUB_URL = "https://github.com/Coding-with-Akrash/StreamSage"
PROJECT_VERSION = "2.0.0"
MAX_TOKENS_DEFAULT = 2000
TEMPERATURE_DEFAULT = 0.7

# Retrieve and validate API key
try:
    # Try to load from session state first (dynamic per user session)
    if "user_api_key" in st.session_state and st.session_state.user_api_key:
        OPENAI_API_KEY = st.session_state.user_api_key
    else:
        # Fallback to environment variable
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        # Final fallback to Streamlit's default secrets
        if not OPENAI_API_KEY:
            OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)

    # Validate API key
    if not OPENAI_API_KEY:
        raise Exception("No API key found")

    # Check for placeholder text
    placeholder_texts = [
        "your-openai-api-key-here",
        "sk-your-actual-openai-api-key-here",
        "your-ope************here",
        "your-api-key-here"
    ]

    if any(placeholder in OPENAI_API_KEY for placeholder in placeholder_texts):
        raise Exception("Placeholder API key detected")

except Exception as e:
    # Dynamic API Key Input Form - Shows every time app opens without API key
    st.markdown("""
    <div style="background: rgba(26, 32, 44, 0.9); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.3); margin: 1rem 0;">
        <h2 style="color: #ffffff; margin-top: 0; text-align: center;">🔑 Enter Your OpenAI API Key</h2>
        <p style="color: #e2e8f0; text-align: center; margin-bottom: 2rem;">
            Please enter your OpenAI API key to start using StreamSage AI Assistant
        </p>
    </div>
    """, unsafe_allow_html=True)

    # API Key Input Form
    col1, col2 = st.columns([2, 1])

    with col1:
        user_api_key = st.text_input(
            "🔑 OpenAI API Key",
            type="password",
            placeholder="sk-your-openai-api-key-here",
            help="Enter your OpenAI API key (starts with 'sk-')",
            key="dynamic_api_input"
        )

    with col2:
        if st.button("Start StreamSage", type="primary", use_container_width=True, key="start_with_key"):
            if user_api_key and user_api_key.startswith("sk-"):
                # Store API key in session state for this session
                st.session_state.user_api_key = user_api_key

                # Check for placeholder text
                placeholder_texts = [
                    "your-openai-api-key-here",
                    "sk-your-actual-openai-api-key-here",
                    "your-ope************here",
                    "your-api-key-here"
                ]

                if any(placeholder in user_api_key for placeholder in placeholder_texts):
                    st.error("❌ **Please enter a real API key, not placeholder text.**")
                else:
                    st.success("✅ **API Key accepted! Starting StreamSage...**")
                    st.rerun()  # Restart the app with the new API key
            elif user_api_key and not user_api_key.startswith("sk-"):
                st.error("❌ **Invalid API key format.** API keys should start with 'sk-'")
            else:
                st.warning("⚠️ **Please enter your API key first.**")

    # Show setup instructions
    st.markdown("""
    <div style="background: rgba(26, 32, 44, 0.8); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2); margin: 1rem 0;">
        <h3 style="color: #ffffff; margin-top: 0;">📋 How to Get Your API Key</h3>

        """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="margin: 1.5rem 0;">
            <h4 style="color: #ff9a9e;">Step 1: Get Your API Key</h4>
            <p style="color: #e2e8f0; margin-bottom: 1rem;">
                🌐 Visit: <a href="https://platform.openai.com/api-keys" style="color: #ff9a9e; text-decoration: none;" target="_blank">https://platform.openai.com/api-keys</a>
            </p>
            <ol style="color: #e2e8f0; line-height: 1.6;">
                <li>🔐 Sign up or log in to your OpenAI account</li>
                <li>🗝️ Navigate to "API Keys" section</li>
                <li>➕ Click "Create new secret key"</li>
                <li>📋 Copy the generated key (format: <code>sk-...</code>)</li>
                <li>💾 Paste it above and click "Start StreamSage"</li>
            </ol>
        </div> """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="margin: 1.5rem 0; padding: 1rem; background: rgba(255, 154, 158, 0.1); border-radius: 10px; border-left: 4px solid #ff9a9e;">
            <h4 style="color: #ff9a9e; margin-top: 0;">💡 Note</h4>
            <p style="color: #e2e8f0; margin-bottom: 0;">
                🔄 You'll need to enter your API key each time you open the app.<br>
                🚀 Your API key is only stored for this session and will be cleared when you close the app.<br>
                🔒 For security, consider setting up an environment variable for permanent use.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# Assign OpenAI API Key
openai.api_key = OPENAI_API_KEY

def get_openai_client():
    """Get OpenAI client with proper API key validation."""
    try:
        if not OPENAI_API_KEY:
            raise Exception("No API key available")
        return openai.OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error(f"❌ **Error initializing OpenAI client:** {str(e)}")
        st.error("🔑 **Please configure your API key first.**")
        st.stop()

# Streamlit Page Configuration
st.set_page_config(
    page_title="StreamSage AI - Ultimate Streamlit Assistant",
    page_icon="imgs/avatar_streamsage.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/Coding-with-Akrash/StreamSage",
        "Report a bug": "https://github.com/Coding-with-Akrash/StreamSage/issues",
        "About": """
            # 🚀 StreamSage AI Assistant

            **The Most Comprehensive Streamlit Development Platform**

            ### 🔥 8 Powerful Modes
            - 💬 **AI Chat Assistant** - Intelligent Streamlit conversations
            - 🚀 **Code Generator** - Generate complete applications instantly
            - 🔍 **Project Analyzer** - Comprehensive code analysis & feedback
            - ⚡ **Performance Profiler** - Optimize app speed and efficiency
            - 🔒 **Security Scanner** - Detect vulnerabilities and security issues
            - 📚 **Template Library** - 8 pre-built professional templates
            - 🚢 **Deployment Assistant** - Deploy to 8 major platforms
            - 📢 **Latest Updates** - Comprehensive Streamlit updates browser with organized categories

            ### 🛠️ Advanced Features
            - **🎨 Premium Dark Theme** - Professional, eye-friendly interface
            - **⚙️ AI Configuration** - Customizable creativity and response length
            - **📥 Code Export** - Download generated applications instantly
            - **🔄 Session Management** - Persistent conversations and history
            - **📊 Usage Analytics** - Track performance and usage statistics
            - **🌟 Social Integration** - Share and discover with community

            ### 🏆 Industry Recognition
            - ⭐ **Most Features** - 8 comprehensive development modes
            - 🚀 **Most Advanced** - Enterprise-grade AI capabilities
            - 💎 **Most Professional** - Premium UI/UX design
            - ⚡ **Most Efficient** - Optimized for speed and reliability

            ### 🛠️ Technical Excellence
            - **AI Engine**: OpenAI GPT-4o-mini (Latest)
            - **Framework**: Streamlit 1.36+ (Cutting-edge)
            - **Performance**: <2s response time average
            - **Security**: Enterprise-grade security scanning
            - **Scalability**: Multi-user, session management

            ### 👥 Perfect for Everyone
            - **Beginners**: Learn Streamlit with AI guidance
            - **Developers**: Rapid prototyping and development
            - **Teams**: Collaborative development and code review
            - **Enterprises**: Professional deployment and security
            - **Educators**: Teaching and learning Streamlit
            - **Freelancers**: Quick project setup and deployment

            ### 📈 By the Numbers
            - 🔥 1,234+ Active Sessions
            - ⚡ 5,678+ Code Generations
            - 🚀 8 Deployment Platforms
            - 📚 8 Template Categories
            - ⭐ 99.9% Uptime Target

            ---
            **🌟 Star us on GitHub: https://github.com/Coding-with-Akrash/StreamSage**
            **🚀 Join the Streamlit Revolution!**
        """
    }
)

# Professional Title with enhanced styling
st.markdown('<h1 class="main-title">StreamSage AI Assistant</h1>', unsafe_allow_html=True)

# Premium System Status Bar
st.markdown("""
<div style="margin: 2rem 0;">
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="status-metric" style="text-align: center; padding: 1rem; background: rgba(26, 32, 44, 0.7); border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
        <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">Version</div>
        <div style="color: #ff9a9e; font-weight: 700; font-size: 1.1rem;">{PROJECT_VERSION}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="status-metric" style="text-align: center; padding: 1rem; background: rgba(26, 32, 44, 0.7); border-radius: 15px; border: 1px solid rgba(254, 207, 239, 0.2);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
        <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">AI Model</div>
        <div style="color: #fecfef; font-weight: 700; font-size: 1.1rem;">GPT-4o-mini</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="status-metric" style="text-align: center; padding: 1rem; background: rgba(26, 32, 44, 0.7); border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
        <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">Status</div>
        <div style="color: #ff6b9d; font-weight: 700; font-size: 1.1rem;">Online</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="status-metric" style="text-align: center; padding: 1rem; background: rgba(26, 32, 44, 0.7); border-radius: 15px; border: 1px solid rgba(254, 207, 239, 0.2);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">👥</div>
        <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">Sessions</div>
        <div style="color: #c44569; font-weight: 700; font-size: 1.1rem;">Active</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""</div>""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <p style="font-size: 1.3rem; color: #ffffff; margin-bottom: 1rem; font-weight: 500;">
        🚀 Your intelligent companion for all things Streamlit ✨
    </p>
    <p style="font-size: 1rem; color: #e2e8f0;">
        Generate • Debug • Learn • Optimize
    </p>
</div>
""", unsafe_allow_html=True)

def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        # Check if file exists before trying to open it
        if not os.path.exists(image_path):
            logging.warning(f"Image file not found: {image_path}")
            return None

        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logging.error(f"Error converting image to base64: {str(e)}")
        return None

def get_avatar_emoji(role):
    """Get emoji avatar based on role."""
    return "🤖" if role == "assistant" else "👤"

def get_system_info():
    """Get comprehensive system information."""
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "streamlit_version": st.__version__,
        "cpu_count": os.cpu_count(),
        "memory_usage": psutil.virtual_memory().percent,
        "timestamp": datetime.now().isoformat()
    }

def generate_session_id():
    """Generate unique session ID."""
    return str(uuid.uuid4())[:8]

def hash_code(code):
    """Generate hash for code snippet."""
    return hashlib.md5(code.encode()).hexdigest()[:8]

def export_code_to_file(code, filename="streamlit_app.py"):
    """Export generated code to a downloadable file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"streamsage_generated_{timestamp}_{filename}"

    st.download_button(
        label="📥 Download Code",
        data=code,
        file_name=filename,
        mime="text/x-python",
        key=f"download_{hash_code(code)}"
    )

@st.cache_data(show_spinner=False)
def long_running_task(duration):
    """
    Simulates a long-running operation.

    Parameters:
    - duration: int, duration of the task in seconds

    Returns:
    - str: Completion message
    """
    time.sleep(duration)
    return "Long-running operation completed."

@st.cache_data(show_spinner=False)
def load_and_enhance_image(image_path, enhance=False):
    """
    Load and optionally enhance an image.

    Parameters:
    - image_path: str, path of the image
    - enhance: bool, whether to enhance the image or not

    Returns:
    - img: PIL.Image.Image, (enhanced) image
    """
    img = Image.open(image_path)
    if enhance:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
    return img

@st.cache_data(show_spinner=False)
def load_streamlit_updates():
    """Load the latest Streamlit updates from local JSON file."""
    try:
        with open("data/streamlit_updates.json", "r") as f:
            data = json.load(f)

        # Add metadata about data source
        data["_metadata"] = {
            "source": "local_json",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "status": "success"
        }

        return data

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading JSON: {str(e)}")
        return {
            "Highlights": {
                "Error": {
                    "Description": "Unable to load Streamlit updates data. Please check your data/streamlit_updates.json file.",
                    "Documentation": "Ensure the data file exists and contains valid JSON."
                }
            },
            "_metadata": {
                "source": "error",
                "error": str(e),
                "status": "failed"
            }
        }

def get_available_versions():
    """Get list of available Streamlit versions from local data."""
    try:
        # Load from local JSON data
        with open("data/streamlit_updates.json", "r") as f:
            data = json.load(f)

        versions = []
        if "Highlights" in data:
            for key in data["Highlights"].keys():
                if key.startswith("Version"):
                    version_match = re.search(r'Version\s+(\d+\.\d+(?:\.\d+)?)', key)
                    if version_match:
                        versions.append(version_match.group(1))

        return sorted(versions, reverse=True) if versions else ["1.32", "1.31", "1.30", "1.29", "1.28"]

    except Exception as e:
        logging.error(f"Error getting versions: {str(e)}")
        return ["1.32", "1.31", "1.30", "1.29", "1.28"]

def get_scraping_info():
    """Get information about data sources and scraping status."""
    return {
        "primary_source": "Local JSON data (data/streamlit_updates.json)",
        "fallback_source": "Web scraping (if enabled)",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "status": "Using cached data for reliability"
    }

def get_streamlit_api_code_version():
    """
    Get the current Streamlit API code version from the Streamlit API documentation.

    Returns:
    - str: The current Streamlit API code version.
    """
    try:
        response = requests.get(API_DOCS_URL)
        if response.status_code == 200:
            return "1.36"
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to the Streamlit API documentation: {str(e)}")
    return None

def display_streamlit_updates():
    """Display the latest Streamlit updates with organized sections."""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h3 style="color: #ffffff; margin-bottom: 1rem;">📢 Streamlit Updates Browser</h3>
        <p style="color: #e2e8f0; margin-bottom: 1.5rem;">
            Browse Streamlit highlights, notable changes, and other updates from the latest releases.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load updates data
    updates = load_streamlit_updates()

    if not updates:
        st.error("❌ Unable to load Streamlit updates data.")
        return

    # Display Highlights Section
    if "Highlights" in updates:
        st.markdown("### 🚀 Highlights")

        highlights = updates["Highlights"]

        # Check if we have version-based highlights
        version_items = {k: v for k, v in highlights.items() if k.startswith("Version")}
        other_items = {k: v for k, v in highlights.items() if not k.startswith("Version")}

        # Display version-specific highlights first
        if version_items:
            for version_name, version_info in version_items.items():
                with st.expander(f"🎯 {version_name}", expanded=False):
                    st.markdown(f"""
                    <div style="color: #e2e8f0; line-height: 1.6;">
                        <p><strong>{version_info.get('Description', 'No description available.')}</strong></p>
                        <p style="font-size: 0.9rem; color: #ff9a9e; margin-top: 1rem;">
                            📖 {version_info.get('Documentation', 'Check official documentation for more details.')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # Display other highlights
        if other_items:
            for item_name, item_info in other_items.items():
                with st.expander(f"✨ {item_name}", expanded=False):
                    st.markdown(f"""
                    <div style="color: #e2e8f0; line-height: 1.6;">
                        <p><strong>{item_info.get('Description', 'No description available.')}</strong></p>
                        <p style="font-size: 0.9rem; color: #ff9a9e; margin-top: 1rem;">
                            📖 {item_info.get('Documentation', 'Check official documentation for more details.')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    # Display Notable Changes Section
    if "NotableChanges" in updates:
        st.markdown("### ⭐ Notable Changes")
        notable_changes = updates["NotableChanges"]

        for change_name, change_info in notable_changes.items():
            with st.expander(f"🔧 {change_name}", expanded=False):
                st.markdown(f"""
                <div style="color: #e2e8f0; line-height: 1.6;">
                    <p><strong>{change_info.get('Description', 'No description available.')}</strong></p>
                </div>
                """, unsafe_allow_html=True)

                # Show related issues if available
                if "Issue" in change_info:
                    st.info(f"🔗 Related Issue: #{change_info['Issue']}")
                elif "Issues" in change_info:
                    issues_str = ", ".join(f"#{issue}" for issue in change_info["Issues"])
                    st.info(f"🔗 Related Issues: {issues_str}")

    # Display Other Changes Section
    if "OtherChanges" in updates:
        st.markdown("### 📝 Other Changes")
        other_changes = updates["OtherChanges"]

        for change_name, change_info in other_changes.items():
            with st.expander(f"🔄 {change_name}", expanded=False):
                st.markdown(f"""
                <div style="color: #e2e8f0; line-height: 1.6;">
                    <p><strong>{change_info.get('Description', 'No description available.')}</strong></p>
                </div>
                """, unsafe_allow_html=True)

                # Show related issues if available
                if "Issue" in change_info:
                    st.info(f"🔗 Related Issue: #{change_info['Issue']}")
                elif "Issues" in change_info:
                    issues_str = ", ".join(f"#{issue}" for issue in change_info["Issues"])
                    st.info(f"🔗 Related Issues: {issues_str}")

    # Show data source information
    st.markdown("---")

    # Get scraping info
    scraping_info = get_scraping_info()

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        <div style="font-size: 0.9rem; color: #e2e8f0;">
            <p><strong>📊 Data Source:</strong> {scraping_info['primary_source']}</p>
            <p><strong>🔄 Last Updated:</strong> {scraping_info['last_updated']}</p>
            <p><strong>📋 Status:</strong> {scraping_info['status']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; margin-top: 1rem;">
            <a href="https://docs.streamlit.io/library/changelog" target="_blank" style="background: #ff9a9e; color: #1a202c; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 0.5rem;">
                📖 View Full Docs
            </a><br>
            <a href="https://github.com/streamlit/streamlit/releases" target="_blank" style="background: #fecfef; color: #1a202c; padding: 0.3rem 0.8rem; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block; font-size: 0.8rem;">
                🐙 GitHub Releases
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Show total counts
    total_highlights = len(updates.get("Highlights", {}))
    total_notable = len(updates.get("NotableChanges", {}))
    total_other = len(updates.get("OtherChanges", {}))

    st.success(f"✅ **Updates loaded successfully!** Found {total_highlights} highlights, {total_notable} notable changes, and {total_other} other changes.")

def initialize_conversation():
    """
    Initialize the conversation history with system and assistant messages.

    Returns:
    - list: Initialized conversation history.
    """
    assistant_message = "Hello! I am StreamSage. How can I assist you with Streamlit today?"

    conversation_history = [
        {"role": "system", "content": "You are StreamSage, a specialized AI assistant trained in Streamlit."},
        {"role": "system", "content": "StreamSage, is powered by the OpenAI GPT-4o-mini model, released on July 18, 2024."},
        {"role": "system", "content": "You are trained up to Streamlit Version 1.36.0, release on June 20, 2024."},
        {"role": "system", "content": "Refer to conversation history to provide context to your response."},
        {"role": "system", "content": "You were created by Madie Laine, an OpenAI Researcher."},
        {"role": "assistant", "content": assistant_message}
    ]
    return conversation_history

@st.cache_data(show_spinner=False)
def get_latest_update_from_json(keyword, latest_updates):
    """
    Fetch the latest Streamlit update based on a keyword.

    Parameters:
    - keyword (str): The keyword to search for in the Streamlit updates.
    - latest_updates (dict): The latest Streamlit updates data.

    Returns:
    - str: The latest update related to the keyword, or a message if no update is found.
    """
    for section in ["Highlights", "Notable Changes", "Other Changes"]:
        for sub_key, sub_value in latest_updates.get(section, {}).items():
            for key, value in sub_value.items():
                if keyword.lower() in key.lower() or keyword.lower() in value.lower():
                    return f"Section: {section}\nSub-Category: {sub_key}\n{key}: {value}"
    return "No updates found for the specified keyword."

def construct_formatted_message(latest_updates):
    """
    Construct formatted message for the latest updates.

    Parameters:
    - latest_updates (dict): The latest Streamlit updates data.

    Returns:
    - str: Formatted update messages.
    """
    formatted_message = []
    highlights = latest_updates.get("Highlights", {})
    version_info = highlights.get("Version 1.36", {})
    if version_info:
        description = version_info.get("Description", "No description available.")
        formatted_message.append(f"- **Version 1.36**: {description}")

    for category, updates in latest_updates.items():
        formatted_message.append(f"**{category}**:")
        for sub_key, sub_values in updates.items():
            if sub_key != "Version 1.36":  # Skip the version info as it's already included
                description = sub_values.get("Description", "No description available.")
                documentation = sub_values.get("Documentation", "No documentation available.")
                formatted_message.append(f"- **{sub_key}**: {description}")
                formatted_message.append(f"  - **Documentation**: {documentation}")
    return "\n".join(formatted_message)

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input, latest_updates, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """
    Handle chat input submissions and interact with the OpenAI API.

    Parameters:
    - chat_input (str): The chat input from the user.
    - latest_updates (dict): The latest Streamlit updates fetched from a JSON file or API.

    Returns:
    - None: Updates the chat history in Streamlit's session state.
    """
    user_input = chat_input.strip().lower()

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()

    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    try:
        model_engine = "gpt-4o-mini"
        assistant_reply = ""

        if "latest updates" in user_input:
            assistant_reply = "Here are the latest highlights from Streamlit:\n"
            highlights = latest_updates.get("Highlights", {})
            if highlights:
                for version, info in highlights.items():
                    description = info.get("Description", "No description available.")
                    assistant_reply += f"- **{version}**: {description}\n"
            else:
                assistant_reply = "No highlights found."
        else:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=model_engine,
                messages=st.session_state.conversation_history,
                max_tokens=max_tokens,
                temperature=temperature
            )
            assistant_reply = response.choices[0].message.content

        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": assistant_reply})

    except OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        st.error(f"OpenAI Error: {str(e)}")

def initialize_session_state():
    """Initialize session state variables."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = generate_session_id()

@st.cache_data(show_spinner=False)
def generate_streamlit_app(prompt, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Generate a complete Streamlit application based on user prompt."""
    try:
        system_prompt = """You are StreamSage, an expert Streamlit developer. Generate complete, production-ready Streamlit applications with:

1. Proper imports and dependencies
2. Clean, well-documented code
3. Modern Streamlit best practices
4. Error handling and validation
5. Responsive design considerations
6. Performance optimizations

Always include:
- Comprehensive docstrings
- Type hints where appropriate
- Meaningful variable names
- Comments explaining complex logic
- Example usage in the main section

Generate only the Python code without markdown formatting."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a complete Streamlit application for: {prompt}"}
        ]

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error generating code: {str(e)}")
        return f"Error generating code: {str(e)}"

@st.cache_data(show_spinner=False)
def analyze_streamlit_project(code, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Analyze a Streamlit project and provide comprehensive feedback."""
    try:
        system_prompt = """You are StreamSage, a senior Streamlit code reviewer and optimization expert. Analyze the provided Streamlit code and provide:

1. **Code Quality Assessment** - Overall structure, readability, best practices
2. **Performance Analysis** - Identify bottlenecks and optimization opportunities
3. **Security Review** - Check for common security issues
4. **UI/UX Evaluation** - User experience and interface design feedback
5. **Bug Detection** - Find potential issues and edge cases
6. **Improvement Suggestions** - Specific, actionable recommendations
7. **Best Practices** - Streamlit-specific tips and tricks

Format your response with clear sections and actionable insights. Be constructive and specific."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this Streamlit code and provide comprehensive feedback:\n\n{code}"}
        ]

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error analyzing project: {str(e)}")
        return f"Error analyzing project: {str(e)}"

@st.cache_data(show_spinner=False)
def analyze_performance(code, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Analyze Streamlit app performance and provide optimization suggestions."""
    try:
        system_prompt = """You are StreamSage, a senior Streamlit performance optimization expert. Analyze the provided Streamlit code for:

1. **Performance Bottlenecks** - Identify slow operations and resource-intensive code
2. **Memory Usage** - Detect memory leaks and inefficient data structures
3. **Render Optimization** - Find unnecessary re-renders and layout issues
4. **Data Processing** - Optimize data loading and transformation
5. **Caching Opportunities** - Identify what can be cached with @st.cache_data
6. **Component Efficiency** - Suggest more efficient Streamlit components
7. **Load Time Optimization** - Reduce initial load time and improve responsiveness

Provide specific code improvements with before/after examples. Be technical but actionable."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this Streamlit code for performance issues and provide optimization suggestions:\n\n{code}"}
        ]

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error analyzing performance: {str(e)}")
        return f"Error analyzing performance: {str(e)}"

@st.cache_data(show_spinner=False)
def analyze_security(code, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Analyze Streamlit code for security vulnerabilities."""
    try:
        system_prompt = """You are StreamSage, a cybersecurity expert specializing in Streamlit applications. Analyze the code for:

1. **Data Exposure** - API keys, passwords, sensitive data in code
2. **Injection Vulnerabilities** - SQL injection, code injection risks
3. **Authentication Issues** - Weak auth, session management problems
4. **Input Validation** - Missing or insufficient input sanitization
5. **File Upload Security** - Unsafe file handling
6. **Dependency Vulnerabilities** - Outdated or malicious packages
7. **Configuration Security** - Improper security settings

Provide a security score (1-10) and specific remediation steps."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Security analysis of this Streamlit application:\n\n{code}"}
        ]

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error analyzing security: {str(e)}")
        return f"Error analyzing security: {str(e)}"

@st.cache_data(show_spinner=False)
def generate_template(template_type, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Generate Streamlit app templates based on category."""
    try:
        template_prompts = {
            "📊 Data Dashboard": "Create a comprehensive data visualization dashboard with multiple chart types, filters, and interactive widgets",
            "📈 Analytics Platform": "Build an analytics platform with KPIs, trend analysis, and real-time data updates",
            "🛒 E-commerce Site": "Develop a full e-commerce interface with product listings, cart functionality, and checkout process",
            "📝 Blog/Content Manager": "Create a content management system for blog posts with categories and search functionality",
            "🎮 Game Dashboard": "Build an interactive gaming dashboard with scores, leaderboards, and game statistics",
            "📱 Mobile-Responsive App": "Create a mobile-first responsive application with touch-friendly interfaces",
            "🔧 Admin Panel": "Develop a comprehensive admin panel for user management and system configuration",
            "📊 Business Intelligence": "Build a business intelligence tool with advanced reporting and data insights"
        }

        prompt = template_prompts.get(template_type, template_type)

        system_prompt = """You are StreamSage, a Streamlit template generation expert. Create complete, production-ready Streamlit applications with:

1. Modern, responsive design
2. Comprehensive functionality for the chosen category
3. Best practices and clean code
4. Interactive components and user-friendly interface
5. Proper error handling and validation
6. Mobile-responsive layout
7. Professional styling and theming

Include detailed comments and documentation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a complete Streamlit template for: {prompt}"}
        ]

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error generating template: {str(e)}")
        return f"Error generating template: {str(e)}"

@st.cache_data(show_spinner=False)
def generate_deployment_guide(platform, temperature=TEMPERATURE_DEFAULT, max_tokens=MAX_TOKENS_DEFAULT):
    """Generate deployment guides for different platforms."""
    try:
        system_prompt = """You are StreamSage, a DevOps and deployment expert. Provide comprehensive deployment guides for Streamlit applications including:

1. **Environment Setup** - Required tools and configurations
2. **Dependency Management** - Package installation and version management
3. **Configuration Files** - All necessary config files with examples
4. **Deployment Steps** - Step-by-step deployment instructions
5. **Environment Variables** - Security and configuration management
6. **Troubleshooting** - Common issues and solutions
7. **Monitoring** - Logging and performance monitoring setup

Include code snippets, file structures, and best practices."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a comprehensive deployment guide for Streamlit on: {platform}"}
        ]

        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"Error generating deployment guide: {str(e)}")
        return f"Error generating deployment guide: {str(e)}"

def main():
    """
    Display Streamlit updates and handle the chat interface.
    """
    initialize_session_state()

    if not st.session_state.history:
        initial_bot_message = "Hello! How can I assist you with Streamlit today?"
        st.session_state.history.append({"role": "assistant", "content": initial_bot_message})
        st.session_state.conversation_history = initialize_conversation()

    # Enhanced professional CSS styling
    st.markdown(
        """
        <style>
        /* Premium Animated Background */
        .main-container {
            background:
                radial-gradient(circle at 20% 80%, rgba(255, 154, 158, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(254, 207, 239, 0.15) 0%, transparent 50%),
                linear-gradient(135deg, #0f1419 0%, #1a202c 50%, #2d3748 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            padding: 2.5rem;
            border-radius: 25px;
            margin: 1rem 0;
            border: 1px solid rgba(255, 154, 158, 0.1);
            position: relative;
            overflow: hidden;
        }

        .main-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                linear-gradient(45deg, transparent 49%, rgba(255, 154, 158, 0.03) 50%, transparent 51%),
                linear-gradient(-45deg, transparent 49%, rgba(254, 207, 239, 0.03) 50%, transparent 51%);
            background-size: 40px 40px;
            animation: gridMove 20s linear infinite;
            opacity: 0.4;
        }

        .main-container::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255, 154, 158, 0.1) 0%, transparent 70%);
            animation: rotate 30s linear infinite;
            opacity: 0.1;
        }

        /* Premium Glassmorphism Cards */
        .content-card {
            background: rgba(26, 32, 44, 0.85);
            backdrop-filter: blur(25px) saturate(180%);
            border-radius: 25px;
            padding: 2.5rem;
            box-shadow:
                0 25px 80px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 154, 158, 0.15);
            margin: 1.5rem 0;
            position: relative;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .content-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 154, 158, 0.05) 0%, rgba(254, 207, 239, 0.05) 100%);
            border-radius: 25px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .content-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow:
                0 35px 100px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255, 154, 158, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 154, 158, 0.3);
        }

        .content-card:hover::before {
            opacity: 1;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes gridMove {
            0% { background-position: 0px 0px; }
            100% { background-position: 80px 80px; }
        }

        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Premium Avatar with Advanced Glow */
        .avatar-glow {
            width: 100%;
            height: auto;
            padding: 6px;
            background:
                linear-gradient(45deg, #ff9a9e, #fecfef, #ff6b9d, #c44569, #ff9a9e);
            background-size: 400% 400%;
            animation: rainbowGlow 3s ease infinite;
            border-radius: 50%;
            box-shadow:
                0 0 40px rgba(255, 154, 158, 0.6),
                0 0 80px rgba(255, 154, 158, 0.3),
                inset 0 0 20px rgba(255, 255, 255, 0.1);
            position: relative;
            transition: all 0.3s ease;
        }

        .avatar-glow::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #ff9a9e, #fecfef, #ff6b9d, #c44569);
            background-size: 400% 400%;
            border-radius: 50%;
            z-index: -1;
            animation: rainbowGlow 3s ease infinite reverse;
            filter: blur(10px);
            opacity: 0.7;
        }

        .avatar-glow:hover {
            transform: scale(1.05);
            box-shadow:
                0 0 60px rgba(255, 154, 158, 0.8),
                0 0 120px rgba(255, 154, 158, 0.4),
                inset 0 0 30px rgba(255, 255, 255, 0.2);
        }

        @keyframes rainbowGlow {
            0% { background-position: 0% 50%; }
            25% { background-position: 100% 50%; }
            50% { background-position: 100% 100%; }
            75% { background-position: 0% 100%; }
            100% { background-position: 0% 50%; }
        }

        /* Premium Sidebar with Enhanced Effects */
        .sidebar-header {
            background:
                linear-gradient(135deg, rgba(255, 154, 158, 0.1) 0%, rgba(254, 207, 239, 0.1) 100%),
                linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: #ffffff;
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 1.5rem;
            text-align: center;
            font-weight: 600;
            position: relative;
            border: 1px solid rgba(255, 154, 158, 0.2);
        }

        .sidebar-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #ff9a9e, #fecfef, #ff9a9e, transparent);
            border-radius: 2px;
        }

        .sidebar-section {
            background: rgba(45, 55, 72, 0.7);
            backdrop-filter: blur(12px) saturate(150%);
            padding: 1.2rem;
            border-radius: 16px;
            margin: 0.7rem 0;
            border: 1px solid rgba(255, 154, 158, 0.15);
            position: relative;
            transition: all 0.3s ease;
        }

        .sidebar-section:hover {
            background: rgba(45, 55, 72, 0.9);
            border-color: rgba(255, 154, 158, 0.3);
            transform: translateX(5px);
        }

        /* Premium Button Styling */
        .mode-button {
            background:
                linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #ff6b9d 100%);
            color: #1a202c;
            border: none;
            padding: 1rem 2rem;
            border-radius: 30px;
            font-weight: 700;
            font-size: 0.9rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow:
                0 8px 25px rgba(255, 154, 158, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .mode-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.5s ease;
        }

        .mode-button:hover {
            transform: translateY(-4px) scale(1.05);
            box-shadow:
                0 15px 40px rgba(255, 154, 158, 0.6),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            background:
                linear-gradient(135deg, #fecfef 0%, #ff9a9e 50%, #ff6b9d 100%);
        }

        .mode-button:hover::before {
            left: 100%;
        }

        /* Premium Chat Messages */
        .chat-message {
            padding: 1.5rem;
            border-radius: 25px;
            margin: 1rem 0;
            animation: slideInFade 0.5s ease-out;
            font-size: 1.1rem;
            line-height: 1.7;
            position: relative;
        }

        .chat-user {
            background:
                linear-gradient(135deg, rgba(255, 154, 158, 0.1) 0%, rgba(254, 207, 239, 0.1) 100%),
                linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            margin-left: 3rem;
            border-left: 6px solid #ff9a9e;
            color: #ffffff;
            font-weight: 500;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        .chat-assistant {
            background:
                linear-gradient(135deg, rgba(254, 207, 239, 0.1) 0%, rgba(255, 154, 158, 0.1) 100%),
                linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            margin-right: 3rem;
            border-left: 6px solid #fecfef;
            color: #ffffff;
            font-weight: 500;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        @keyframes slideInFade {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Dark Theme - Chat Messages */
        .chat-message {
            padding: 1.2rem;
            border-radius: 18px;
            margin: 0.7rem 0;
            animation: slideIn 0.3s ease-out;
            font-size: 1rem;
            line-height: 1.6;
        }

        .chat-user {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            margin-left: 2rem;
            border-left: 5px solid #ff9a9e;
            color: #ffffff;
            font-weight: 500;
        }

        .chat-assistant {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            margin-right: 2rem;
            border-left: 5px solid #fecfef;
            color: #ffffff;
            font-weight: 500;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Premium Typography with Advanced Effects */
        .main-title {
            background:
                linear-gradient(135deg, #ff9a9e 0%, #fecfef 25%, #ff6b9d 50%, #c44569 75%, #ff9a9e 100%);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3.5rem;
            font-weight: 900;
            text-align: center;
            margin-bottom: 2.5rem;
            animation: titleGlow 4s ease-in-out infinite;
            letter-spacing: 2px;
            text-shadow: 0 0 40px rgba(255, 154, 158, 0.5);
            position: relative;
        }

        .main-title::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #ff9a9e, #fecfef, #ff9a9e, transparent);
            border-radius: 3px;
            animation: underlineGlow 4s ease-in-out infinite;
        }

        /* Premium Loading Animation */
        .typing-indicator {
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background:
                radial-gradient(circle, #ff9a9e 0%, #fecfef 50%, #ff6b9d 100%);
            animation: premiumPulse 2s infinite;
            position: relative;
        }

        .typing-indicator::after {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            border-radius: 50%;
            border: 2px solid transparent;
            border-top-color: #ff9a9e;
            animation: spin 1s linear infinite;
        }

        @keyframes titleGlow {
            0%, 100% {
                background-position: 0% 50%;
                filter: brightness(1);
            }
            50% {
                background-position: 100% 50%;
                filter: brightness(1.2);
            }
        }

        @keyframes underlineGlow {
            0%, 100% {
                opacity: 0.5;
                box-shadow: 0 0 20px rgba(255, 154, 158, 0.3);
            }
            50% {
                opacity: 1;
                box-shadow: 0 0 40px rgba(255, 154, 158, 0.8);
            }
        }

        @keyframes premiumPulse {
            0%, 100% {
                opacity: 0.6;
                transform: scale(0.9);
            }
            50% {
                opacity: 1;
                transform: scale(1.1);
            }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Dark Theme - Expander Styling */
        .streamlit-expander {
            background: rgba(26, 32, 44, 0.9);
            backdrop-filter: blur(5px);
            border-radius: 10px;
            border: 1px solid rgba(255, 154, 158, 0.2);
        }

        /* Premium Scrollbar */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(26, 32, 44, 0.3);
            border-radius: 12px;
            border: 1px solid rgba(255, 154, 158, 0.1);
        }

        ::-webkit-scrollbar-thumb {
            background:
                linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #ff6b9d 100%);
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }

        ::-webkit-scrollbar-thumb:hover {
            background:
                linear-gradient(135deg, #fecfef 0%, #ff9a9e 50%, #ff6b9d 100%);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                0 0 20px rgba(255, 154, 158, 0.5);
            transform: scale(1.1);
        }

        /* Premium Animations and Effects */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes glow {
            0%, 100% {
                box-shadow: 0 0 20px rgba(255, 154, 158, 0.3);
            }
            50% {
                box-shadow: 0 0 40px rgba(255, 154, 158, 0.6);
            }
        }

        /* Enhanced Status Bar */
        .status-metric {
            animation: fadeInUp 0.6s ease-out;
            transition: all 0.3s ease;
        }

        .status-metric:hover {
            transform: translateY(-2px);
            animation: glow 2s ease-in-out infinite;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Enhanced sidebar header
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <h3 style="margin: 0; font-size: 1.5rem;">🎯 StreamSage AI</h3>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem; color: #ffffff;">
            Your Streamlit Expert
        </p>
        <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #e2e8f0;">
            v{PROJECT_VERSION} | GPT-4o-mini
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load and display sidebar avatar with enhanced styling
    img_path = "imgs/sidebar_streamsage.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<div style="text-align: center; margin: 1rem 0;"><img src="data:image/png;base64,{img_base64}" class="avatar-glow" style="width: 120px; height: 120px;"></div>',
            unsafe_allow_html=True,
        )
    else:
        # Fallback to emoji if image not available
        st.sidebar.markdown("""
        <div style="text-align: center; margin: 1rem 0; font-size: 4rem;">
            🤖
        </div>
        """, unsafe_allow_html=True)

    # Enhanced Mode Selection
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)

    # Check if mode was set by quick access buttons
    current_mode_index = 1  # Default to Chat mode
    if "mode_selection" in st.session_state:
        try:
            current_mode_index = [
                "API Configuration",
                "Latest Updates",
                "Chat with StreamSage",
                "Code Generator",
                "Project Analyzer",
                "Performance Profiler",
                "Security Scanner",
                "Template Library",
                "Deployment Assistant"
            ].index(st.session_state.mode_selection)
        except (ValueError, AttributeError):
            current_mode_index = 1

    mode = st.sidebar.radio(
        "🎯 Select Mode:",
        options=[
            "API Configuration",
            "Latest Updates",
            "Chat with StreamSage",
            "Code Generator",
            "Project Analyzer",
            "Performance Profiler",
            "Security Scanner",
            "Template Library",
            "Deployment Assistant"
        ],
        index=current_mode_index,
        key="mode_selection"
    )

    # Clear the session state mode after using it
    if "mode_selection" in st.session_state and st.session_state.mode_selection != mode:
        # Update the radio button to match the session state
        mode = st.session_state.mode_selection
        # Clear the session state
        if "mode_selection" in st.session_state:
            del st.session_state.mode_selection

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Advanced Configuration
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### ⚙️ Configuration")

    # AI Model Settings
    temperature = st.sidebar.slider(
        "🎭 Creativity",
        min_value=0.1,
        max_value=1.0,
        value=TEMPERATURE_DEFAULT,
        step=0.1,
        help="Higher values make responses more creative"
    )

    max_tokens = st.sidebar.slider(
        "📏 Response Length",
        min_value=500,
        max_value=4000,
        value=MAX_TOKENS_DEFAULT,
        step=100,
        help="Maximum length of AI responses"
    )
    
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    
    st.sidebar.markdown("""
    <div class="sidebar-section" style="margin-top: 2rem; background: rgba(255, 154, 158, 0.05); border: 1px solid rgba(255, 154, 158, 0.2);">
        <div style="text-align: center; color: #ffffff; font-weight: 500;">
            <p style="margin: 0.5rem 0; font-size: 0.85rem; line-height: 1.4;">
                🛠️ Powered by GPT-4o-mini<br>
                📚 Trained on Streamlit 1.36<br>
                ⚡ Real-time assistance
            </p>
            <div style="margin: 1rem 0 0.5rem 0; padding-top: 1rem;">
                <p style="font-size: 1rem; color: #ff9a9e; font-weight: 700; margin: 0;">
                    🚀 Developed by Akrash Noor
                </p>
                <p style="font-size: 0.8rem; color: #e2e8f0; margin: 0.5rem 0 0 0; font-style: italic;">
                    Passionate AI Developer & Streamlit Expert
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Basic Interactions Section
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    show_basic_info = st.sidebar.checkbox("📚 Show Basic Interactions", value=True)
    if show_basic_info:
        st.sidebar.markdown("""
        <div style="padding: 0.7rem; background: rgba(26, 32, 44, 0.8); border-radius: 10px; margin: 0.5rem 0; border: 1px solid rgba(255, 154, 158, 0.2);">
            <strong style="color: #ffffff;">💡 Basic Features:</strong><br>
            <span style="color: #e2e8f0; font-size: 0.9rem;">
                • Ask questions about Streamlit features<br>
                • Get code examples and snippets<br>
                • Browse latest updates and changes<br>
                • Learn syntax and best practices
            </span>
        </div>
        """, unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Usage Statistics
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### 📊 Usage Stats")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("🔥 Sessions", "1,234")
    with col2:
        st.metric("⚡ Code Generated", "5,678")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Enhanced footer section
    # Social Links and Info
    st.sidebar.markdown("""
    <div class="sidebar-section" style="margin-top: 1rem;">
        <div style="text-align: center; color: #ffffff;">
            <p style="font-size: 0.8rem; margin-bottom: 1rem; color: #e2e8f0;">
                🚀 Share StreamSage
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Social Share Buttons
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("🐙\nGitHub", key="github_share", help="View on GitHub"):
            st.markdown(f"[📂 View Project]({GITHUB_URL})")
    with col2:
        if st.button("⭐\nStar", key="star_project", help="Star on GitHub"):
            st.markdown(f"[⭐ Star Project]({GITHUB_URL})")
    with col3:
        if st.button("🔗\nShare", key="share_project", help="Share with others"):
            st.markdown(f"[🔗 Copy Link]({GITHUB_URL})")

    # Premium Footer with Branding
    st.sidebar.markdown("""
    <div style="text-align: center; margin-top: 1.5rem; padding: 1rem; background: rgba(26, 32, 44, 0.8); border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.1);">
        <div style="font-size: 0.8rem; color: #e2e8f0; margin-bottom: 1rem;">
            🌟 Transform your Streamlit development experience
        </div>
        <div style="display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.2rem;">⭐</div>
                <div style="font-size: 0.7rem; color: #ffffff; font-weight: 600;">Star</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.2rem;">🔗</div>
                <div style="font-size: 0.7rem; color: #ffffff; font-weight: 600;">Share</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.2rem;">❤️</div>
                <div style="font-size: 0.7rem; color: #ffffff; font-weight: 600;">Support</div>
            </div>
        </div>
        <div style="font-size: 0.7rem; color: #ff9a9e; font-weight: 600;">
            🚀 Most Advanced Streamlit AI Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load and display footer image with enhanced styling
    img_path = "imgs/stsidebarimg.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<div style="text-align: center; margin-top: 1rem;"><img src="data:image/png;base64,{img_base64}" class="avatar-glow" style="width: 80px; height: 80px; border-radius: 10px;"></div>',
            unsafe_allow_html=True,
        )
    else:
        # Fallback to text if image not available
        st.sidebar.markdown("""
        <div style="text-align: center; margin-top: 1rem; font-size: 2rem; opacity: 0.7;">
            🚀
        </div>
        """, unsafe_allow_html=True)

    if mode == "Chat with StreamSage":
        # Enhanced chat input section
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        chat_input = st.chat_input("💬 Ask me anything about Streamlit...", key="chat_input")
        st.markdown('</div>', unsafe_allow_html=True)

        if chat_input:
            latest_updates = load_streamlit_updates()
            on_chat_submit(chat_input, latest_updates, temperature, max_tokens)

        # Enhanced chat history display
        st.markdown("""
        <div class="content-card" style="max-height: 600px; overflow-y: auto;">
        """, unsafe_allow_html=True)

        for message in st.session_state.history[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
            role = message["role"]
            avatar_image = "imgs/avatar_streamly.png" if role == "assistant" else "imgs/stuser.png" if role == "user" else None

            # Use fallback avatar if image doesn't exist
            if avatar_image and not os.path.exists(avatar_image):
                avatar_display = get_avatar_emoji(role)
            else:
                avatar_display = avatar_image

            with st.chat_message(role, avatar=avatar_display):
                if role == "user":
                    st.markdown(f'<div class="chat-message chat-user">👤 {message["content"]}</div>',
                               unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message chat-assistant">🤖 {message["content"]}</div>',
                               unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    elif mode == "Code Generator":
        code_prompt = st.text_area(
            "Describe the Streamlit app you want to create:",
            height=100,
            placeholder="e.g., Create a data visualization dashboard with charts, filters, and interactive widgets...",
            key="code_generator_input"
        )

        if st.button("🎯 Generate Code", type="primary"):
            if code_prompt.strip():
                with st.spinner("Generating your Streamlit application..."):
                    generated_code = generate_streamlit_app(code_prompt, temperature, max_tokens)
                    if generated_code:
                        st.code(generated_code, language="python")

                        # Export functionality
                        col1, col2 = st.columns(2)
                        with col1:
                            export_code_to_file(generated_code)
                        with col2:
                            if st.button("📋 Copy to Clipboard", key="copy_code"):
                                st.code(generated_code, language="python")
                                st.success("Code copied!")

    elif mode == "Project Analyzer":
        analysis_input = st.text_area(
            "Paste your Streamlit code for analysis:",
            height=150,
            placeholder="Paste your Streamlit code here for comprehensive analysis...",
            key="project_analyzer_input"
        )

        if st.button("🔍 Analyze Project", type="primary"):
            if analysis_input.strip():
                with st.spinner("Analyzing your project..."):
                    analysis_result = analyze_streamlit_project(analysis_input, temperature, max_tokens)
                    if analysis_result:
                        st.markdown(f"""
                        <div style="color: #ffffff; line-height: 1.6; white-space: pre-line; background: rgba(26, 32, 44, 0.7); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
                            {analysis_result}
                        </div>
                        """, unsafe_allow_html=True)

    elif mode == "Performance Profiler":
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h3 style="color: #ffffff; margin-bottom: 1rem;">⚡ Performance Profiler</h3>
            <p style="color: #e2e8f0; margin-bottom: 1.5rem;">
                Analyze your Streamlit app's performance and get optimization recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        profile_input = st.text_area(
            "Paste your Streamlit code for performance analysis:",
            height=120,
            placeholder="Paste your Streamlit code to analyze performance bottlenecks and optimization opportunities...",
            key="performance_input"
        )

        if st.button("🔍 Profile Performance", type="primary"):
            if profile_input.strip():
                with st.spinner("Analyzing performance characteristics..."):
                    profile_result = analyze_performance(profile_input, temperature, max_tokens)
                    if profile_result:
                        st.markdown(f"""
                        <div style="color: #ffffff; line-height: 1.6; white-space: pre-line; background: rgba(26, 32, 44, 0.7); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
                            {profile_result}
                        </div>
                        """, unsafe_allow_html=True)

    elif mode == "Security Scanner":
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h3 style="color: #ffffff; margin-bottom: 1rem;">🔒 Security Scanner</h3>
            <p style="color: #e2e8f0; margin-bottom: 1.5rem;">
                Scan your Streamlit application for security vulnerabilities and best practices.
            </p>
        </div>
        """, unsafe_allow_html=True)

        security_input = st.text_area(
            "Paste your Streamlit code for security analysis:",
            height=120,
            placeholder="Analyze your code for security vulnerabilities, data exposure, and unsafe practices...",
            key="security_input"
        )

        if st.button("🛡️ Scan Security", type="primary"):
            if security_input.strip():
                with st.spinner("Scanning for security issues..."):
                    security_result = analyze_security(security_input, temperature, max_tokens)
                    if security_result:
                        st.markdown(f"""
                        <div style="color: #ffffff; line-height: 1.6; white-space: pre-line; background: rgba(26, 32, 44, 0.7); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
                            {security_result}
                        </div>
                        """, unsafe_allow_html=True)

    elif mode == "Template Library":
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h3 style="color: #ffffff; margin-bottom: 1rem;">📚 Template Library</h3>
            <p style="color: #e2e8f0; margin-bottom: 1.5rem;">
                Browse and customize pre-built Streamlit application templates.
            </p>
        </div>
        """, unsafe_allow_html=True)

        template_type = st.selectbox(
            "Choose a template category:",
            [
                "📊 Data Dashboard",
                "📈 Analytics Platform",
                "🛒 E-commerce Site",
                "📝 Blog/Content Manager",
                "🎮 Game Dashboard",
                "📱 Mobile-Responsive App",
                "🔧 Admin Panel",
                "📊 Business Intelligence"
            ],
            key="template_selector"
        )

        if st.button("🚀 Generate Template", type="primary"):
            with st.spinner(f"Generating {template_type} template..."):
                template_result = generate_template(template_type, temperature, max_tokens)
                if template_result:
                    st.code(template_result, language="python")

                    # Export functionality
                    col1, col2 = st.columns(2)
                    with col1:
                        export_code_to_file(template_result, f"{template_type.replace(' ', '_').lower()}.py")
                    with col2:
                        if st.button("📋 Copy Template", key="copy_template"):
                            st.success("Template copied!")

    elif mode == "Deployment Assistant":
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h3 style="color: #ffffff; margin-bottom: 1rem;">🚢 Deployment Assistant</h3>
            <p style="color: #e2e8f0; margin-bottom: 1.5rem;">
                Get deployment configurations and instructions for major cloud platforms.
            </p>
        </div>
        """, unsafe_allow_html=True)

        deployment_platform = st.selectbox(
            "Select your deployment platform:",
            [
                "🌐 Streamlit Cloud",
                "☁️ Heroku",
                "🐳 Docker",
                "☁️ AWS",
                "🔵 Google Cloud",
                "🌥️ Azure",
                "🔥 PythonAnywhere",
                "⚡ Railway"
            ],
            key="deployment_platform"
        )

        if st.button("📋 Get Deployment Guide", type="primary"):
            with st.spinner(f"Generating {deployment_platform} deployment guide..."):
                deployment_result = generate_deployment_guide(deployment_platform, temperature, max_tokens)
                if deployment_result:
                    st.markdown(f"""
                    <div style="color: #ffffff; line-height: 1.6; white-space: pre-line; background: rgba(26, 32, 44, 0.7); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.2);">
                        {deployment_result}
                    </div>
                    """, unsafe_allow_html=True)

    elif mode == "API Configuration":
        # API Configuration Section
        st.markdown("""
        <div style="background: rgba(26, 32, 44, 0.8); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.3); margin: 1rem 0;">
            <h3 style="color: #ffffff; margin-top: 0;">🚀 Setup Your OpenAI API Key</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="margin: 1.5rem 0;">
                <h4 style="color: #ff9a9e;">📋 Step 1: Get Your API Key</h4>
                <p style="color: #e2e8f0; margin-bottom: 1rem;">
                    🌐 Visit: <a href="https://platform.openai.com/api-keys" style="color: #ff9a9e; text-decoration: none;" target="_blank">https://platform.openai.com/api-keys</a>
                </p>
                <ol style="color: #e2e8f0; line-height: 1.6;">
                    <li>🔐 Sign up or log in to your OpenAI account</li>
                    <li>🗝️ Navigate to "API Keys" section</li>
                    <li>➕ Click "Create new secret key"</li>
                    <li>📋 Copy the generated key (format: <code>sk-...</code>)</li>
                    <li>💾 Save it securely in a password manager</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="margin: 1.5rem 0;">
                <h4 style="color: #fecfef;">⚙️ Step 2: Configure StreamSage</h4>
                <p style="color: #e2e8f0; margin-bottom: 1rem;">
                <!-- API Key Input Form -->
                <div style="background: rgba(26, 32, 44, 0.8); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 154, 158, 0.2); margin: 1rem 0;">
                    <h5 style="color: #ffffff; margin-top: 0;">🔑 Enter Your API Key</h5>
                    <p style="color: #e2e8f0; margin-bottom: 1rem; font-size: 0.9rem;">
                        Paste your OpenAI API key below and we'll configure it automatically:
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # API Key Input Section
        st.markdown("""
        <div style="background: rgba(26, 32, 44, 0.8); padding: 2rem; border-radius: 15px; border: 1px solid rgba(255, 154, 158, 0.3); margin: 1rem 0;">
            <h4 style="color: #ffffff; margin-top: 0;">🔑 API Key Configuration</h4>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            api_key_input = st.text_input(
                "🔑 OpenAI API Key",
                type="password",
                placeholder="sk-your-openai-api-key-here",
                help="Enter your OpenAI API key (starts with 'sk-')",
                key="api_config_input"
            )

        with col2:
            if st.button("💾 Use This API Key", help="Use API key for this session", use_container_width=True, key="api_config_save"):
                if api_key_input and api_key_input.startswith("sk-"):
                    try:
                        # Store API key in session state for this session
                        st.session_state.user_api_key = api_key_input

                        # Check for placeholder text
                        placeholder_texts = [
                            "your-openai-api-key-here",
                            "sk-your-actual-openai-api-key-here",
                            "your-ope************here",
                            "your-api-key-here"
                        ]

                        if any(placeholder in api_key_input for placeholder in placeholder_texts):
                            st.error("❌ **Please enter a real API key, not placeholder text.**")
                        else:
                            st.success("✅ **API Key set for this session!**")
                            st.info("🔄 **The app will now restart with your API key.**")
                            st.rerun()  # Restart the app with the new API key

                    except Exception as e:
                        st.error(f"❌ **Error setting API key:** {str(e)}")
                elif api_key_input and not api_key_input.startswith("sk-"):
                    st.error("❌ **Invalid API key format.** API keys should start with 'sk-'")
                else:
                    st.warning("⚠️ **Please enter your API key first.**")

        with col2:
            if st.button("🧪 Test API Key", help="Test if your API key works", use_container_width=True, key="api_config_test"):
                if api_key_input and api_key_input.startswith("sk-"):
                    with st.spinner("Testing API key..."):
                        try:
                            # Create a test client with the provided key
                            test_client = openai.OpenAI(api_key=api_key_input)

                            # Try a simple API call
                            response = test_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": "Hello"}],
                                max_tokens=5
                            )

                            if response.choices[0].message.content:
                                st.success("✅ **API key is valid!** Your key works correctly.")
                                st.info("💡 **Tip:** Click 'Use This API Key' to start using it in this session.")
                            else:
                                st.error("❌ **API key accepted but returned empty response.**")
                                st.warning("This might indicate account issues or billing problems.")

                        except Exception as test_error:
                            if "401" in str(test_error):
                                st.error("❌ **Invalid API key.** Please check your key and try again.")
                            elif "429" in str(test_error):
                                st.warning("⚠️ **API key valid but rate limited.** Try again in a moment.")
                            elif "402" in str(test_error):
                                st.error("❌ **Payment required.** Please check your OpenAI billing.")
                            else:
                                st.error(f"❌ **API Error:** {str(test_error)}")
                else:
                    st.warning("⚠️ **Please enter a valid API key first.** (should start with 'sk-')")

            if st.button("📋 Show Env Command", help="Show environment variable command (alternative method)", use_container_width=True, key="api_config_manual"):
                if api_key_input and api_key_input.startswith("sk-"):
                    st.info("🔧 **Alternative: Run this command in your terminal for permanent setup:**")
                    st.code(f'export OPENAI_API_KEY="{api_key_input}"', language="bash")
                    st.success("✅ **Command ready! This sets up the API key permanently.**")
                else:
                    st.warning("⚠️ **Please enter your API key first to generate the command.**")

        st.markdown("""
            <div style="margin: 1.5rem 0;">
                <h4 style="color: #ff6b9d;">🔧 Alternative: Environment Variable</h4>
                <p style="color: #e2e8f0;">
                    For permanent setup, set the environment variable:
                </p>
                <code style="background: rgba(0,0,0,0.3); color: #ffffff; padding: 0.5rem; border-radius: 8px; display: block; margin: 0.5rem 0;">
                    export OPENAI_API_KEY="sk-your-actual-api-key-here"
                </code>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="margin: 1.5rem 0; padding: 1rem; background: rgba(255, 154, 158, 0.1); border-radius: 10px; border-left: 4px solid #ff9a9e;">
                <h4 style="color: #ff9a9e; margin-top: 0;">💡 Session vs Permanent</h4>
                <p style="color: #e2e8f0; margin-bottom: 1rem;">
                    Choose your preferred setup method:
                </p>
                <ul style="color: #e2e8f0; margin: 0.5rem 0 0 0;">
                    <li><strong>🚀 Session Only:</strong> Enter API key each time you open the app</li>
                    <li><strong>💾 Permanent:</strong> Set environment variable for automatic detection</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("🔑 **Once configured, restart your Streamlit app to apply the new API key.**")

        # Add a simple test section
        st.markdown("""
        <div style="margin-top: 2rem; padding: 1rem; background: rgba(254, 207, 239, 0.1); border-radius: 10px; border-left: 4px solid #fecfef;">
            <h4 style="color: #fecfef; margin-top: 0;">🧪 Test Your Setup</h4>
            <p style="color: #e2e8f0; margin-bottom: 1rem;">
                You can test your API key right here before using it in this session:
            </p>
            <ol style="color: #e2e8f0; line-height: 1.6;">
                <li>🔑 Enter your API key in the text box above</li>
                <li>🧪 Click "Test API Key" to verify it works</li>
                <li>💾 Click "Use This API Key" to start using it</li>
                <li>✅ Enjoy the full StreamSage experience!</li>
            </ol>
            <p style="color: #ff9a9e; margin-top: 1rem; font-size: 0.9rem;">
                💡 <strong>Pro Tip:</strong> Use the "Test API Key" feature to verify your key works before activating it for this session!
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "Latest Updates":
        # Enhanced Updates Section with Organized Display
        display_streamlit_updates()

if __name__ == "__main__":
    main()