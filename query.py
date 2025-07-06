import streamlit as st
from openai import OpenAI
import base64
from html import escape

# Load API key securely
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)

# ---------- BACKGROUND ----------
def get_base64_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/webp;base64,{encoded}"

background_url = get_base64_background("ai-tools.webp")

# ---------- CSS ----------
st.markdown(f"""
<style>
.stApp {{
    background: url('{background_url}') no-repeat center center fixed;
    background-size: cover;
    animation: subtleZoom 30s ease-in-out infinite alternate;
    padding: 0 !important;
}}

@keyframes subtleZoom {{
    0% {{ background-size: 100%; }}
    100% {{ background-size: 110%; }}
}}

.chat-scroll {{
    max-height: 60vh;
    overflow-y: auto;
    padding: 1rem;
    background: transparent;
    border-radius: 15px;
}}

.message {{
    background-color: #000000;
    padding: 15px;
    border-radius: 12px;
    margin: 15px 0;
    color: #ffffff;
    font-size: 16px;
    font-family: "Segoe UI", sans-serif;
}}

.bottom-bar {{
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 1rem 2rem;
    background-color: rgba(20, 20, 20, 0.95);
    box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    z-index: 9999;
}}
</style>
""", unsafe_allow_html=True)

# ---------- INIT SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "base64_image" not in st.session_state:
    st.session_state.base64_image = None

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

st.markdown("""
<style>
.header-container {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.main-title {
    background-color: #ffffff;
    padding: 15px 25px;
    border-radius: 12px;
    color: #000000;
    font-size: 32px;
    font-weight: bold;
    font-family: "Segoe UI", sans-serif;
}

.chat-bubble {
    position: relative;
    background: #0078d4;
    color: white;
    padding: 12px 18px;
    border-radius: 15px;
    font-size: 16px;
    font-family: "Segoe UI", sans-serif;
    margin-top: 15px;
    max-width: 300px;
}

.chat-bubble::after {
    content: "";
    position: absolute;
    top: 10px;
    left: -10px;
    width: 0;
    height: 0;
    border: 10px solid transparent;
    border-right-color: #0078d4;
}
</style>

<div class="header-container">
    <div class="main-title">📸 PictoQuery</div>
    <div class="chat-bubble">💬 ASK ABOUT THE UPLOADED IMAGE</div>
</div>
""", unsafe_allow_html=True)


# ---------- CHAT DISPLAY ----------
if st.session_state.messages:
    with st.container():
        st.markdown("<div class='chat-scroll'>", unsafe_allow_html=True)

        for msg in st.session_state.messages:
            role = "💬 You" if msg["role"] == "user" else "🤖 GPT"
            content = escape(msg["content"])
            st.markdown(
                f"""
                <div class='message'>
                    <p><strong>{role}:</strong> {content}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

# ---------- FIXED BOTTOM INPUT BAR ----------
st.markdown('<div class="bottom-bar">', unsafe_allow_html=True)

with st.container():
    uploaded_file = st.file_uploader("📄", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed", key="unique_file_uploader", help="Upload your image")
    
    if uploaded_file:
        image_bytes = uploaded_file.read()
        st.session_state.base64_image = base64.b64encode(image_bytes).decode("utf-8")
        st.image(image_bytes, caption="Uploaded Image", width=300)



    with st.form(key="query_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("", placeholder="Type your question...", label_visibility="collapsed")
        with col2:
            send_clicked = st.form_submit_button("Send")

st.markdown("</div>", unsafe_allow_html=True)

# ---------- PROCESSING INPUT ----------
if (user_input and st.session_state.last_input != user_input) or send_clicked:
    if not st.session_state.base64_image:
        st.warning("⚠️ Please upload an image first.")
    elif user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.last_input = user_input

        try:
            with st.spinner("Analyzing the image..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
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
                    }]
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

