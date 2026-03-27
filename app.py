import tkinter as tk
import requests
import webbrowser
import urllib.parse
import smtplib
from email.message import EmailMessage
import threading

PAGE = 0
STEP = 10
papers = []
saved_papers = []

EMAIL = "[researchalertapp@gmail.com](mailto:researchalertapp@gmail.com)"
APP_PASSWORD = "qkahcamlhmonjesm"

# ---------- EMAIL ----------

def send_email():
if not saved_papers:
result_box.insert(tk.END, "\nNo saved papers.\n")
return

```
msg = EmailMessage()
msg["Subject"] = "Saved Research Papers"
msg["From"] = EMAIL
msg["To"] = EMAIL
msg.set_content("\n\n".join(saved_papers))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

    result_box.insert(tk.END, "\nSaved papers sent to email.\n")

except Exception as e:
    result_box.insert(tk.END, f"\nEmail error: {e}\n")
```

# ---------- OPEN PAPER ----------

def open_paper(index):
url = papers[index].get("url")
if url:
webbrowser.open(url)

# ---------- SAVE PAPER ----------

def save_paper(index):
p = papers[index]
title = p.get("title", "")
url = p.get("url", "")

```
saved_papers.append(f"{title}\n{url}")

result_box.insert(tk.END, "\nPaper saved.\n")
```

# ---------- OPENALEX ----------

def get_openalex(query):

```
page_num = (PAGE // STEP) + 1

url = (
    "https://api.openalex.org/works?"
    f"search={urllib.parse.quote(query)}"
    f"&page={page_num}"
    f"&per_page={STEP}"
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
```

# ---------- ARXIV ----------

def get_arxiv(query):

```
url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=10"

papers = []

try:

    r = requests.get(url)

    if r.status_code == 200:

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
```

# ---------- FETCH RESULTS ----------

def fetch_results():

```
global papers

query = entry.get().strip()

if not query:
    return

result_box.delete("1.0", tk.END)
result_box.insert(tk.END, "Loading papers...\n")

url = (
    "https://api.semanticscholar.org/graph/v1/paper/search?"
    f"query={urllib.parse.quote(query)}"
    f"&offset={PAGE}&limit={STEP}"
    "&fields=title,url,year"
)

headers = {"User-Agent": "ResearchApp"}

try:

    response = requests.get(url, headers=headers, timeout=15)
    data = response.json()

    papers = data.get("data", [])

    papers += get_openalex(query)
    papers += get_arxiv(query)

    result_box.delete("1.0", tk.END)

    if not papers:
        result_box.insert(tk.END, "No papers found.\n")
        return

    for i, paper in enumerate(papers):

        title = paper.get("title", "No Title")
        year = paper.get("year", "")

        start = result_box.index(tk.END)

        result_box.insert(
            tk.END,
            f"{i+1}. {title} ({year})\n"
        )

        end = result_box.index(tk.END)

        tag = f"paper{i}"

        result_box.tag_add(tag, start, end)
        result_box.tag_config(tag, foreground="blue", underline=1)

        result_box.tag_bind(tag, "<Enter>",
                            lambda e: result_box.config(cursor="hand2"))

        result_box.tag_bind(tag, "<Leave>",
                            lambda e: result_box.config(cursor="arrow"))

        result_box.tag_bind(tag, "<Button-1>",
                            lambda e, idx=i: open_paper(idx))

        s_start = result_box.index(tk.END)

        result_box.insert(tk.END, "[Save Paper]\n\n")

        s_end = result_box.index(tk.END)

        save_tag = f"save{i}"

        result_box.tag_add(save_tag, s_start, s_end)
        result_box.tag_config(save_tag, foreground="green")

        result_box.tag_bind(save_tag, "<Enter>",
                            lambda e: result_box.config(cursor="hand2"))

        result_box.tag_bind(save_tag, "<Leave>",
                            lambda e: result_box.config(cursor="arrow"))

        result_box.tag_bind(save_tag, "<Button-1>",
                            lambda e, idx=i: save_paper(idx))

except Exception as e:

    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, f"Search error:\n{e}")
```

def search():

```
global PAGE

PAGE = 0

threading.Thread(target=fetch_results).start()
```

def next_page():

```
global PAGE

PAGE += STEP

threading.Thread(target=fetch_results).start()
```

def prev_page():

```
global PAGE

if PAGE >= STEP:
    PAGE -= STEP

threading.Thread(target=fetch_results).start()
```

def refresh():

```
threading.Thread(target=fetch_results).start()
```

# ---------- UI ----------

root = tk.Tk()

root.title("Research Paper Search System")

root.geometry("950x650")

tk.Label(root, text="Enter topic:").pack()

entry = tk.Entry(root, width=90)

entry.pack()

entry.bind("<Return>", lambda e: search())

tk.Button(root, text="Search Papers", command=search).pack(pady=5)

result_box = tk.Text(root, wrap="word")

result_box.pack(expand=True, fill="both")

nav_frame = tk.Frame(root)

nav_frame.pack()

tk.Button(nav_frame, text="Previous", command=prev_page).pack(side="left", padx=5)

tk.Button(nav_frame, text="Next", command=next_page).pack(side="left", padx=5)

tk.Button(nav_frame, text="Refresh", command=refresh).pack(side="left", padx=5)

tk.Button(root, text="Send Saved to Email",
command=send_email).pack(pady=5)

root.mainloop()
