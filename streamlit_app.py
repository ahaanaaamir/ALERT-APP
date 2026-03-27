import streamlit as st
import requests
import os
import smtplib
import time
from email.mime.text import MIMEText

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Research Paper Search System",
    page_icon="📚",
    layout="wide"
)

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("S2_API_KEY")

EMAIL_ADDRESS = "researchalertapp@gmail.com"
APP_PASSWORD = "mxulljzpyjfpwydc"

# =========================
# CSS
# =========================
st.markdown("""
<style>
.main-title {
    font-size: 40px;
    font-weight: bold;
    text-align: center;
    color: #1f4e79;
}
.subtitle {
    text-align: center;
    color: gray;
    margin-bottom: 20px;
}
.result-card {
    background-color: #f5f7fa;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 15px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "offset" not in st.session_state:
    st.session_state.offset = 0

if "saved" not in st.session_state:
    st.session_state.saved = []

if "query" not in st.session_state:
    st.session_state.query = ""

# =========================
# HEADER
# =========================
st.markdown('<div class="main-title">📚 Research Paper Search System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Search • Save • Organize • Share Research Papers</div>', unsafe_allow_html=True)
st.write("---")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("⚙ Search Settings")
LIMIT = st.sidebar.slider("Results per page", 5, 20, 10)

# =========================
# SEARCH FUNCTION
# =========================
def search_papers(query, offset=0):

    if not API_KEY:
        st.error("❌ API key not found. Set S2_API_KEY in environment.")
        return []

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "offset": offset,
        "limit": LIMIT,
        "fields": "title,url,year"
    }

    headers = {
        "x-api-key": API_KEY
    }

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 429:
            st.warning("Rate limit reached. Waiting 2 seconds...")
            time.sleep(2)
            return []

        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return []

# =========================
# EMAIL FUNCTION
# =========================
def send_email(receiver):

    if not receiver:
        st.warning("Enter receiver email.")
        return

    if not st.session_state.saved:
        st.warning("No saved papers.")
        return

    content = "\n\n".join(
        [f"{p['title']} ({p.get('year','N/A')})\n{p['url']}"
         for p in st.session_state.saved]
    )

    msg = MIMEText(content)
    msg["Subject"] = "Saved Research Papers"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_ADDRESS.strip(), APP_PASSWORD.strip())
        server.sendmail(EMAIL_ADDRESS, receiver, msg.as_string())
        server.quit()

        st.success("✅ Email sent successfully!")

    except Exception as e:
        st.error(f"Email Error: {e}")

# =========================
# SEARCH INPUT
# =========================
col1, col2 = st.columns([4,1])

with col1:
    query = st.text_input("🔍 Enter Research Topic", st.session_state.query)

with col2:
    if st.button("Search"):
        st.session_state.query = query
        st.session_state.offset = 0

# =========================
# RESULTS
# =========================
if st.session_state.query:

    papers = search_papers(
        st.session_state.query,
        st.session_state.offset
    )

    st.subheader(f"📄 Results Found: {len(papers)}")

    if papers:
        for i, paper in enumerate(papers):

            st.markdown(f"""
            <div class="result-card">
                <h4><a href="{paper.get('url','#')}" target="_blank">{paper.get('title','No Title')}</a></h4>
                <p><b>Year:</b> {paper.get('year','N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"💾 Save Paper {i}", key=f"save_{i}"):
                if paper not in st.session_state.saved:
                    st.session_state.saved.append(paper)
                    st.success("Saved!")

    else:
        st.info("No papers found.")

    # Pagination
    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button("⬅ Previous"):
            if st.session_state.offset >= LIMIT:
                st.session_state.offset -= LIMIT
                st.rerun()

    with col_next:
        if st.button("Next ➡"):
            st.session_state.offset += LIMIT
            st.rerun()

# =========================
# SAVED SECTION
# =========================
st.write("---")
st.subheader("⭐ Saved Papers")

if st.session_state.saved:
    for p in st.session_state.saved:
        st.markdown(f"- [{p['title']}]({p['url']})")
else:
    st.write("No saved papers yet.")

# =========================
# EMAIL SECTION
# =========================
st.write("---")
st.subheader("📧 Send Saved Papers")

receiver = st.text_input("Receiver Email")

if st.button("Send Saved to Email"):
    send_email(receiver)