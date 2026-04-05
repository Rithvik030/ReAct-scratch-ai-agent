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

        # clean text
        text = " ".join(text.split())

        return text[:1000]  # limit size

    except Exception as e:
        return ""


def score_result(r, query):
    print("Ranking the web results based on relevance..")
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

    #  domains (soft boost)
    if any(site in url for site in ["espn", "sofascore", "livescore", "premierleague"]):
        score += 3

    # penalize junk
    if any(bad in url for bad in ["blog", "news", "transfer", "rumor"]):
        score -= 2

    # boost structured words
    if any(word in text for word in ["fixture", "schedule", "next match", "date"]):
        score += 3

    # numbers (dates/times)
    if any(char.isdigit() for char in text):
        score += 2

    # penalize blocked sites (optional but useful)
    if "sofascore" in url:
        score -= 3

    return score


def web_search(query):
    print("Performing reranked websearch:")

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))

    # STEP 1: Score results
    scored_results = []
    for r in results:
        s = score_result(r, query)
        url = r.get("href") or r.get("link")
        print(f"Score: {s} | URL: {url}")
        scored_results.append((s, r))

    # STEP 2: Sort by score (highest first)
    scored_results.sort(reverse=True, key=lambda x: x[0])

    #  STEP 3: Fetch top valid results
    visited_urls = set()
    processed_results = []

    for score, r in scored_results:
        url = r.get("href") or r.get("link")

        if not url:
            continue

        # avoid duplicate fetch
        if url in visited_urls:
            continue

        visited_urls.add(url)

        print("Fetching:", url, "| Score:", score)

        content = fetch_page_content(url)

        # 🔹 if fetch fails, fallback to snippet/body
        if not content:
            content = r.get("body", "")

        if content:
            processed_results.append({
                "title": r.get("title", ""),
                "link": url,
                "content": content
            })

        #  stop after 2 good results
        if len(processed_results) == 2:
            break
    
    return processed_results