import requests

def tor_session(port: int = 9150) -> requests.Session:
    """
    Tor Browser معمولاً روی 9150 گوش می‌دهد.
    Tor Service معمولاً 9050 است.
    """
    s = requests.Session()
    proxy = f"socks5h://127.0.0.1:{port}"
    s.proxies = {"http": proxy, "https": proxy}
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ContentDetector/1.0"
    })
    return s

def check_tor(s: requests.Session) -> dict:
    r = s.get("https://check.torproject.org/api/ip", timeout=30)
    r.raise_for_status()
    return r.json()
