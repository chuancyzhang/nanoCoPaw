from urllib.request import Request, urlopen


def fetch_url(url: str, timeout: int = 20, limit: int = 20000) -> str:
    """Fetch URL content as text with a size limit."""
    req = Request(url, headers={"User-Agent": "nanoCoPaw/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    text = data.decode("utf-8", errors="replace")
    if limit and len(text) > limit:
        return text[:limit]
    return text
