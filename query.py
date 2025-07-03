import streamlit as st
from openai import OpenAI
import base64
import os
from html import escape  # To escape user/assistant content safely

# Load API key securely
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)

# Encode your local image (ai-tools.webp) to base64
def get_base64_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/webp;base64,{encoded}"

# Get local image background
background_url = get_base64_background("ai-tools.webp")

# ---------- INLINE CSS ----------
st.markdown(f"""
    <style>
    .stApp {{
        background: url('{background_url}') no-repeat center center fixed;
        background-size: cover;
        animation: subtleZoom 30s ease-in-out infinite alternate;
    }}

    @keyframes subtleZoom {{
        0% {{ background-size: 100%; }}
        100% {{ background-size: 110%; }}
    }}

    h1, h3, p {{ color: #ffcc00; text-align: center; }}

    .chat-box {{
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        color: #e0e0e0;
    }}

    .stTextInput > div > div > input {{
        background-color: #333;
        color: white;
        border-radius: 10px;
        padding: 10px;
    }}

    .stFileUploader {{
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.5rem;
        color: white;
    }}

    .stButton > button {{
        background-color: #ff4b4b;
        color: white;
        padding: 4px 10px;
        font-size: 14px;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        width: fit-content;
        margin-top: 5px;
    }}

    .stImage {{
        border: 2px solid white;
        border-radius: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div style="
    background-color: #ffffff;
    padding: 15px 25px;
    border-radius: 12px;
    display: inline-block;
    text-align: center;
">
    <h1 style='color: #000000; margin: 0;'>📸 PictoQuery</h1>
</div>
""", unsafe_allow_html=True)

# ---------- SUB HEADER (Black box aligned right) ----------
st.markdown("""
<div style="
    display: flex;
    justify-content: flex-end;
    margin-top: 10px;
    margin-right: 30px;
">
    <div style="
        background-color: rgba(0, 0, 0, 1);
        padding: 12px 20px;
        border-radius: 10px;
        text-align: right;
    ">
        <p style='color: #FFFFFF; font-weight: 500; font-size: 18px; margin: 0;'>
            Ask questions based on the uploaded image
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- SESSION STATE INIT ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "base64_image" not in st.session_state:
    st.session_state.base64_image = None

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# ---------- LAYOUT ----------
col1, col2 = st.columns([1, 2])

# ---------- LEFT PANEL: IMAGE UPLOAD ----------
with col1:
    uploaded_file = st.file_uploader("📄 Upload your image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file:
        image_bytes = uploaded_file.read()
        st.image(image_bytes, caption="Your Image", use_container_width=True)
        st.session_state.base64_image = base64.b64encode(image_bytes).decode("utf-8")

# ---------- RIGHT PANEL: CHAT HISTORY ----------
with col2:
    st.markdown("""
    <div style="
        background-color: rgba(255, 255, 255, 0.85);
        padding: 12px 20px;
        border-radius: 12px;
        display: inline-block;
        text-align: center;
    ">
        <h3 style='color: #000000; margin: 0;'>
                <span style='color:#000000;'>💬</span> Ask about the image</h3>
    </div>
    """, unsafe_allow_html=True)

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            st.markdown('<div class="chat-box">', unsafe_allow_html=True)
            content = escape(msg["content"])
            if msg["role"] == "user":
                st.markdown(f"**🧑 You:** <span style='color:#fff;'>{content}</span>", unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"**🤖 GPT-4:** <span style='color:#90ee90;'>{content}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)  # Padding for fixed input

# ---------- INPUT FIELD ----------
user_input = st.text_input("Your question", key="user_input_key", label_visibility="collapsed", placeholder="Type your question here...")
send_clicked = st.button("Send", use_container_width=True)

if (user_input and st.session_state.last_input != user_input) or send_clicked:
    if not st.session_state.base64_image:
        st.warning("Please upload an image first.")
    elif user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.last_input = user_input

        try:
            with st.spinner("Analyzing the image..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_input},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{st.session_state.base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")
