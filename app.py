import streamlit as st
import requests
import urllib.parse
import smtplib
from email.message import EmailMessage

# ---------- CONFIG ----------
st.set_page_config(page_title="Research Paper Search", layout="wide")

# ---------- SECRETS ----------
EMAIL = st.secrets["EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

# ---------- SESSION ----------
if "saved_papers" not in st.session_state:
    st.session_state.saved_papers = []

# ---------- FUNCTIONS ----------

def get_semantic_scholar(query):
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search?"
        f"query={urllib.parse.quote(query)}"
        "&limit=10"
        "&fields=title,url,year"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("data", [])
    except:
        return []

def get_openalex(query):
    url = (
        "https://api.openalex.org/works?"
        f"search={urllib.parse.quote(query)}"
        "&per_page=10"
    )
    results = []
    try:
        r = requests.get(url, timeout=10).json()
        for w in r.get("results", []):
            results.append({
                "title": w.get("display_name"),
                "url": w.get("id"),
                "year": w.get("publication_year")
            })
    except:
        pass
    return results

def get_arxiv(query):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=10"
    papers = []
    try:
        r = requests.get(url)
        entries = r.text.split("<entry>")[1:]
        for e in entries:
            title = e.split("<title>")[1].split("</title>")[0]
            link = e.split("<id>")[1].split("</id>")[0]
            papers.append({
                "title": title.strip(),
                "url": link,
                "year": ""
            })
    except:
        pass
    return papers

def send_email():
    if not st.session_state.saved_papers:
        st.warning("No saved papers")
        return

    msg = EmailMessage()
    msg["Subject"] = "Saved Research Papers"
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg.set_content("\n\n".join(st.session_state.saved_papers))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Email error: {e}")

# ---------- UI ----------

st.title("📚 Research Paper Search System")

query = st.text_input("Enter topic")

if st.button("Search Papers"):
    if query:
        with st.spinner("Fetching papers..."):
            papers = []
            papers += get_semantic_scholar(query)
            papers += get_openalex(query)
            papers += get_arxiv(query)

        if not papers:
            st.warning("No papers found")
        else:
            for i, paper in enumerate(papers):
                title = paper.get("title", "No Title")
                url = paper.get("url", "")
                year = paper.get("year", "")

                st.markdown(f"### {i+1}. {title} ({year})")

                if url:
                    st.markdown(f"[Open Paper]({url})")

                if st.button(f"Save Paper {i}", key=f"save_{i}"):
                    st.session_state.saved_papers.append(f"{title}\n{url}")
                    st.success("Saved!")

                st.divider()

# ---------- EMAIL ----------
if st.button("Send Saved Papers to Email"):
    send_email()
