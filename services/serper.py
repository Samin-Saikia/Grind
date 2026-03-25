import requests
from config import config


def search(query, num=5):
    if not config.SERPER_API_KEY:
        return ""
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=8,
        )
        data = response.json()
        results = []
        for item in data.get("organic", [])[:num]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append(f"- {title}: {snippet} ({link})")
        return "\n".join(results)
    except Exception as e:
        return f"Search unavailable: {e}"


def research_for_tasks(domains, profile_summary):
    if not domains:
        return ""
    queries = []
    for domain in domains[:2]:
        queries.append(f"latest {domain} techniques tools 2024")
        queries.append(f"{domain} learning path intermediate to advanced")
    combined = []
    for q in queries[:3]:
        result = search(q, num=3)
        if result:
            combined.append(f"Query: {q}\n{result}")
    return "\n\n".join(combined)


def research_topic(topic, level="intermediate"):
    results = []
    queries = [
        f"{topic} explained {level}",
        f"{topic} best resources 2024",
        f"{topic} common mistakes misconceptions",
    ]
    for q in queries:
        r = search(q, num=3)
        if r:
            results.append(f"Query: {q}\n{r}")
    return "\n\n".join(results)
