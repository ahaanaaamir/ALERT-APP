import streamlit as st
import requests
import urllib.parse
import smtplib
from email.mime.text import MIMEText

# ================= CONFIG =================
st.set_page_config(page_title="Research Search Engine", layout="wide")

EMAIL = st.secrets["EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

# ================= SESSION =================
if "saved" not in st.session_state:
    st.session_state.saved = []

# ================= FETCH FUNCTIONS =================

def semantic_scholar(query):
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": 10,
            "fields": "title,url,year"
        }
        res = requests.get(url, params=params).json()
        return res.get("data", [])
    except:
        return []

def openalex(query):
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page=10"
        data = requests.get(url).json()
        return [{
            "title": w.get("display_name"),
            "url": w.get("id"),
            "year": w.get("publication_year")
        } for w in data.get("results", [])]
    except:
        return []

def arxiv(query):
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=10"
        r = requests.get(url).text
        entries = r.split("<entry>")[1:]
        results = []
        for e in entries:
            title = e.split("<title>")[1].split("</title>")[0]
            link = e.split("<id>")[1].split("</id>")[0]
            results.append({"title": title.strip(), "url": link, "year": ""})
        return results
    except:
        return []

def crossref(query):
    try:
        url = f"https://api.crossref.org/works?query={query}&rows=10"
        data = requests.get(url).json()
        return [{
            "title": item["title"][0] if item.get("title") else "No Title",
            "url": item.get("URL"),
            "year": item.get("issued", {}).get("date-parts", [[None]])[0][0]
        } for item in data["message"]["items"]]
    except:
        return []

# ================= MERGE =================

def search_all(query):
    results = []
    seen = set()

    for source in [semantic_scholar, openalex, arxiv, crossref]:
        data = source(query)
        for p in data:
            title = p.get("title", "")
            if title and title not in seen:
                seen.add(title)
                results.append(p)

    return results

# ================= EMAIL =================

def send_email(receiver):
    if not receiver or not st.session_state.saved:
        st.warning("Enter email and save papers first.")
        return

    content = "\n\n".join(
        [f"{p['title']} ({p.get('year','')})\n{p['url']}" for p in st.session_state.saved]
    )

    msg = MIMEText(content)
    msg["Subject"] = "Saved Research Papers"
    msg["From"] = EMAIL
    msg["To"] = receiver

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, receiver, msg.as_string())
        server.quit()
        st.success("Email sent!")
    except Exception as e:
        st.error(str(e))

# ================= UI =================

st.title("📚 Multi-Platform Research Search Engine")

query = st.text_input("Enter topic")

if st.button("Search"):
    if query:
        with st.spinner("Searching across platforms..."):
            results = search_all(query)

        st.write(f"### Results Found: {len(results)}")

        for i, p in enumerate(results):
            st.markdown(f"**{i+1}. {p['title']} ({p.get('year','')})**")
            st.markdown(f"[Open Paper]({p['url']})")

            if st.button(f"Save {i}", key=i):
                st.session_state.saved.append(p)

            st.markdown("---")

# ================= SAVED =================

st.subheader("Saved Papers")

for p in st.session_state.saved:
    st.markdown(f"- [{p['title']}]({p['url']})")

# ================= EMAIL =================

receiver = st.text_input("Enter email")

if st.button("Send Saved to Email"):
    send_email(receiver)
