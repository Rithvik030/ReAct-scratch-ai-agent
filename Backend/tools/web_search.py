from ddgs import DDGS
import requests
from bs4 import BeautifulSoup


def fetch_page_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # remove scripts/styles
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator=" ")
        
        #extractting texts from all paragraph tags in the page
        '''for p in soup.find_all("p"):
            text+=p.get_text()
        
        for li in soup.find_all("li"):
            text+=li.get_text()'''

        # clean text
        text = " ".join(text.split())

        return text[:1000]  # limit size

    except Exception as e:
        return ""


def score_result(r, query):
    score = 0
    url = (r.get("href") or r.get("link") or "").lower()
    title = r.get("title", "").lower()
    body = r.get("body", "").lower()

    text = title + " " + body
    query_words = query.lower().split()

    #  keyword match
    for word in query_words:
        if word in text:
            score += 2


    # penalize junk
    if any(bad in url for bad in ["blog", "news", "transfer", "rumor"]):
        score -= 2


    return score


TRUSTED_SOURCES = {
    "population": ["worldometers.info", "un.org"],
    "time": ["worldtimeserver.com", "24timezones.com","time.is"],
    "sports": [ "whenisthematch.com"
],
    "general": []
}



def detect_category(query):
    q = query.lower()

    scores = {"sports": 0, "time": 0, "population": 0}

    if any(w in q for w in ["match", "game", "fixture"]):
        scores["sports"] += 3

    if "time" in q:
        scores["time"] += 1

    if "population" in q:
        scores["population"] += 3

    if all(v == 0 for v in scores.values()):
        scores["general"] = 1

    return max(scores, key=scores.get)


def web_search(query):
    print("Performing websearch:")

    with DDGS() as ddgs:
        print("Detecting query category")
        category = detect_category(query)
        print(f"Retrieving relevant sites for category:{category}")
        trusted_domains = TRUSTED_SOURCES.get(category, [])

        # build constrained query
        if trusted_domains:
            domain_query = " OR ".join([f"site:{d}" for d in trusted_domains])
            modified_query = f"{query} ({domain_query})"
        else:
            modified_query = query

        print("Search Query Used:", modified_query)

        try:
            results = list(ddgs.text(modified_query, max_results=5))
        except:
            results = []

        if not results:
            print("Fallback to general search...")
            try:
                results = list(ddgs.text(query, max_results=5))
            except:
                results = []

    # 🔥 NOW DO SCORING + FETCH (PUT THIS BACK)
    print("Web result ranking")

    scored_results = []
    print("Ranking the source based on relevance..")
    for r in results:
        score = score_result(r, query)
        scored_results.append((score, r))

    scored_results.sort(reverse=True, key=lambda x: x[0])

    processed_results = []

    for score, r in scored_results[:3]:
        url = r.get("href") or r.get("link")
        if not url:
            continue

        print(f"Fetching: {url} | Score: {score}")

        content = fetch_page_content(url)

        processed_results.append({
            "title": r.get("title", ""),
            "link": url,
            "content": content
        })

    return processed_results