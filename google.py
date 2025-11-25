import os, re, requests

API_KEY = "AIzaSyBssftloGfBTl0HaiVGxcsWyJatiUbCyuI"
CX = "b7e22d2d2f22d47e5"
QUERY_BASE = "perro"
q = f"{QUERY_BASE}"

params = {"key": API_KEY, "cx": CX, "q": q, "num": 5, "start": 1}
r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=30)
r.raise_for_status()
items = r.json().get("items", [])

os.makedirs("pdfs", exist_ok=True)
for it in items:
    url = it.get("link", "")
    if not url.lower().endswith(".pdf"):
        continue
    name = re.sub(r'[^\w.-]+', '_', it.get("title", "documento"))[:100] + ".pdf"
    try:
        pdf = requests.get(url, timeout=60)
        pdf.raise_for_status()
        with open(os.path.join("pdfs", name), "wb") as f:
            f.write(pdf.content)
        print("Descargado:", name)
    except Exception as e:
        print("Error con", url, "->", e)



import requests

API_KEY = "AIzaSyBssftloGfBTl0HaiVGxcsWyJatiUbCyuI"
CX = "b7e22d2d2f22d47e5"
q = "filetype:pdf site:scj.gob.cl resolucion"

r = requests.get(
    "https://www.googleapis.com/customsearch/v1",
    params={"key": API_KEY, "cx": CX, "q": q, "num": 10, "start": 1},
    timeout=30
)
r.raise_for_status()
data = r.json()
items = data.get("items", [])
if not items:
    print("Sin resultados. Revisa configuración del PSE y la query.")
else:
    for i, it in enumerate(items, 1):
        print(f"{i}. {it.get('title')}\n   {it.get('link')}")
print("totalResults:", data.get("searchInformation", {}).get("totalResults"))