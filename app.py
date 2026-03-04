import streamlit as st
import requests
import io
import json
from PIL import Image
from urllib.parse import urlparse

st.set_page_config(page_title="ReverseLens", layout="centered", initial_sidebar_state="expanded")

API = "http://localhost:8000"

if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None


# ============ SIDEBAR - AUTH ============

with st.sidebar:
    st.title("⚙️ Settings")

    if st.session_state.token:
        st.success(f"👤 {st.session_state.username}")
        if st.button("Chiqish"):
            st.session_state.token = None
            st.session_state.username = None
            st.rerun()
        st.divider()
        st.markdown("**Auth bilan:** history saqlanadi + limit 20/min")
    else:
        auth_tab = st.radio("", ["Kirish", "Ro'yxatdan o'tish"], horizontal=True)

        uname = st.text_input("Username", key="auth_user")
        pwd = st.text_input("Password", type="password", key="auth_pwd")

        if st.button("✅ Tasdiqlash"):
            if uname and pwd:
                endpoint = "/login" if auth_tab == "Kirish" else "/register"
                try:
                    r = requests.post(f"{API}{endpoint}", json={"username": uname, "password": pwd}, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.token = data["token"]
                        st.session_state.username = data["username"]
                        st.rerun()
                    else:
                        st.error(r.json().get("error", "Xatolik"))
                except requests.ConnectionError:
                    st.error("Server ishlamayapti")
            else:
                st.warning("Maydonlarni to'ldiring")

        st.divider()
        st.markdown("**Auth'siz:** limit 10/min, history yo'q")


# ============ MAIN ============

st.title("🔍 ReverseLens")
st.markdown("Reverse image search + AI description")


def is_ok_url(url):
    try:
        p = urlparse(url)
        return p.scheme in ['http', 'https']
    except:
        return False


def call_analyze(img_bytes, source="upload"):
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
    headers = {}
    endpoint = f"{API}/analyze"

    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
        endpoint = f"{API}/analyze/auth"

    try:
        with st.spinner(f"🤖 Agent ishlayapti... ({source})"):
            r = requests.post(endpoint, files=files, headers=headers, timeout=120)

        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            st.error("⏱️ So'rovlar limiti. Biroz kuting.")
        elif r.status_code == 401:
            st.error("🔑 Token eskirgan. Qayta kiring.")
            st.session_state.token = None
        else:
            st.error(f"Server: {r.status_code}")
        return None

    except requests.Timeout:
        st.error("⏱️ Timeout")
        return None
    except requests.ConnectionError:
        st.error("❌ Server ishlamayapti (localhost:8000)")
        return None


def show_result(result):
    st.success("✅ Tayyor!")
    st.markdown(f"### {result['answer']}")

    if result.get("cached"):
        st.info("💾 Cache'dan (tezkor)")

    if result.get("sources"):
        with st.expander("📎 Manbalar", expanded=False):
            for s in result["sources"]:
                if s["url"]:
                    st.markdown(f"- [{s['title'][:70]}]({s['url']})")
                else:
                    st.markdown(f"- {s['title']}")

    if result.get("steps"):
        with st.expander("🧠 Agent qadamlari", expanded=False):
            for i, step in enumerate(result["steps"]):
                icon = "✅" if step.get("status") == "done" else "❌"
                line = f"{icon} **{step['action']}**"
                if step.get("engine"):
                    line += f" ({step['engine']})"
                if step.get("count") is not None:
                    line += f" → {step['count']} ta natija"
                if step.get("quality"):
                    line += f" → {step['quality']}"
                st.markdown(line)


# ============ TABS ============

tab1, tab2, tab3 = st.tabs(["📤 Upload", "🔗 URL", "📜 History"])

with tab1:
    uploaded = st.file_uploader("Rasm tanlang", type=["jpg", "jpeg", "png", "gif", "webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_container_width=True)
        if st.button("🔍 Analyze", key="btn_up"):
            result = call_analyze(uploaded.getvalue(), "upload")
            if result:
                show_result(result)

with tab2:
    url_input = st.text_input("Rasm URL", placeholder="https://example.com/image.jpg")
    if url_input:
        if is_ok_url(url_input):
            try:
                with st.spinner("📥 Yuklanmoqda..."):
                    r = requests.get(url_input, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    img_bytes = r.content
                    img = Image.open(io.BytesIO(img_bytes))
                st.image(img, use_container_width=True)
                if st.button("🔍 Analyze", key="btn_url"):
                    result = call_analyze(img_bytes, "url")
                    if result:
                        show_result(result)
            except:
                st.error("Rasmni yuklab bo'lmadi")
        else:
            st.warning("URL noto'g'ri")

with tab3:
    if not st.session_state.token:
        st.info("📝 Tarixni ko'rish uchun tizimga kiring (sidebar)")
    else:
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            r = requests.get(f"{API}/history", headers=headers, timeout=5)
            if r.status_code == 200:
                items = r.json().get("history", [])
                if not items:
                    st.info("Hali tarix yo'q")
                for item in items:
                    with st.expander(f"🕐 {item['created_at']} — {item['answer'][:50]}..."):
                        st.markdown(f"**Javob:** {item['answer']}")
                        if item.get("sources"):
                            st.markdown("**Manbalar:**")
                            for s in item["sources"]:
                                if s.get("url"):
                                    st.markdown(f"- [{s['title'][:50]}]({s['url']})")
                        if item.get("agent_steps"):
                            st.markdown("**Agent qadamlari:**")
                            for step in item["agent_steps"]:
                                st.text(f"  {step.get('action', '?')} → {step.get('status', '?')}")
            else:
                st.error("Tarixni olishda xatolik")
        except:
            st.error("Server bilan bog'lanib bo'lmadi")

st.divider()
st.markdown("**Stack:** TinEye + Yandex + Bing → Ollama llama3.1 (agentic loop) | **Auth:** JWT | **Free**")
