import streamlit as st
import requests
import urllib.parse
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
# SECRETS
# =========================
EMAIL_ADDRESS = st.secrets["EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

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
# SESSION
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
# SEARCH FUNCTION (MULTI API)
# =========================
def search_papers(query, offset=0):

    results = []
    seen_titles = set()

    # ---------- Semantic Scholar ----------
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "offset": offset,
            "limit": LIMIT,
            "fields": "title,url,year"
        }

        res = requests.get(url, params=params, timeout=10)

        if res.status_code == 429:
            time.sleep(2)
        elif res.status_code == 200:
            data = res.json()
            for p in data.get("data", []):
                title = p.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    results.append(p)

    except:
        pass

    # ---------- OpenAlex ----------
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page=10"
        r = requests.get(url, timeout=10).json()

        for w in r.get("results", []):
            title = w.get("display_name", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                results.append({
                    "title": title,
                    "url": w.get("id"),
                    "year": w.get("publication_year")
                })
    except:
        pass

    # ---------- arXiv ----------
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=10"
        r = requests.get(url)

        entries = r.text.split("<entry>")[1:]

        for e in entries:
            title = e.split("<title>")[1].split("</title>")[0].strip()
            link = e.split("<id>")[1].split("</id>")[0]

            if title and title not in seen_titles:
                seen_titles.add(title)
                results.append({
                    "title": title,
                    "url": link,
                    "year": ""
                })
    except:
        pass

    return results


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
        server.login(EMAIL_ADDRESS, APP_PASSWORD)
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
                <h4><a href="{paper.get('url','#')}" target="_blank">
                {paper.get('title','No Title')}</a></h4>
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
