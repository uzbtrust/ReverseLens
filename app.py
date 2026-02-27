import streamlit as st
import requests
import io
from PIL import Image
from urllib.parse import urlparse

st.set_page_config(page_title="ReverseLens", layout="centered", initial_sidebar_state="collapsed")

st.title("🔍 ReverseLens")
st.markdown("Upload or paste image URL — get instant AI description using reverse search + Ollama")

API_URL = "http://localhost:8000/analyze"

def is_valid_image_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    except:
        return False

def analyze_image(img_bytes, source="upload"):
    try:
        files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
        with st.spinner(f"🔄 Analyzing... ({source})"):
            r = requests.post(API_URL, files=files, timeout=120)

        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Server error: {r.status_code}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout — search took too long. Try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Make sure FastAPI is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

tab1, tab2 = st.tabs(["📤 Upload", "🔗 URL"])

with tab1:
    st.subheader("Upload Image")
    uploaded = st.file_uploader("Choose image", type=["jpg", "jpeg", "png", "gif", "webp"])

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_container_width=True)

        if st.button("🔍 Analyze", key="btn_upload"):
            img_bytes = uploaded.getvalue()
            result = analyze_image(img_bytes, "upload")

            if result:
                st.success("✅ Done!")
                st.markdown(f"**Description:** {result['answer']}")

                if result['sources']:
                    st.markdown("**Sources:**")
                    for src in result['sources']:
                        if src['url']:
                            st.markdown(f"- [{src['title'][:60]}...]({src['url']})")
                        else:
                            st.markdown(f"- {src['title']}")

                if result.get('cached'):
                    st.info("💾 From cache (instant)")

with tab2:
    st.subheader("Image URL")
    url_input = st.text_input("Paste image URL", placeholder="https://example.com/image.jpg")

    if url_input:
        if is_valid_image_url(url_input):
            try:
                with st.spinner("📥 Loading image..."):
                    r = requests.get(url_input, timeout=10)
                    img_bytes = r.content
                    img = Image.open(io.BytesIO(img_bytes))

                st.image(img, use_container_width=True)

                if st.button("🔍 Analyze", key="btn_url"):
                    result = analyze_image(img_bytes, "url")

                    if result:
                        st.success("✅ Done!")
                        st.markdown(f"**Description:** {result['answer']}")

                        if result['sources']:
                            st.markdown("**Sources:**")
                            for src in result['sources']:
                                if src['url']:
                                    st.markdown(f"- [{src['title'][:60]}...]({src['url']})")
                                else:
                                    st.markdown(f"- {src['title']}")

                        if result.get('cached'):
                            st.info("💾 From cache (instant)")
            except Exception as e:
                st.error(f"Failed to load image: {str(e)}")
        else:
            st.warning("⚠️ Enter valid image URL (.jpg, .png, etc)")

st.divider()
st.markdown("**Tech:** TinEye reverse search + Ollama llama3.1 | **Free:** No API keys needed")
