import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from tqdm import tqdm

from tor_client import TorClient, TorConfig


def normalize_url(u: str) -> Optional[str]:
    u = (u or "").strip()
    if not u:
        return None
    # اگر scheme نداره، ردش می‌کنیم تا خرابکاری نشه
    if not u.startswith(("http://", "https://")):
        return None
    return u


def read_seed_urls(seed_path: Path) -> List[str]:
    urls = []
    for line in seed_path.read_text(encoding="utf-8").splitlines():
        u = normalize_url(line)
        if u:
            urls.append(u)
    # یکتا
    return list(dict.fromkeys(urls))


def extract_text_and_links(html: str, base_url: str) -> Tuple[str, List[str]]:
    soup = BeautifulSoup(html, "lxml")

    # حذف اسکریپت/استایل
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # متن
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    # لینک‌ها
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        abs_u = urljoin(base_url, href)
        abs_u = normalize_url(abs_u)
        if abs_u:
            links.append(abs_u)

    return text, links


def same_host(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def crawl(
    seed_urls: List[str],
    out_pages_path: Path,
    max_pages: int = 20,
    max_depth: int = 1,
    same_domain_only: bool = True,
    tor_port: int = 9150,
) -> List[Dict]:
    client = TorClient(TorConfig(socks_port=tor_port))

    queue: List[Tuple[str, int, str]] = []  # (url, depth, seed_host_url)
    visited = set()

    for s in seed_urls:
        queue.append((s, 0, s))

    pages: List[Dict] = []

    pbar = tqdm(total=max_pages, desc="Crawling", ncols=80)
    while queue and len(pages) < max_pages:
        url, depth, seed_ref = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = client.get(url)
            ct = (resp.headers.get("content-type") or "").lower()
            if resp.status_code != 200 or "text/html" not in ct:
                continue

            html = resp.text
            text, links = extract_text_and_links(html, url)

            pages.append(
                {
                    "url": url,
                    "seed": seed_ref,
                    "status": resp.status_code,
                    "content_type": ct,
                    "text": text,
                    "text_len": len(text),
                }
            )
            pbar.update(1)

            # توسعه صف
            if depth < max_depth:
                for lk in links:
                    if lk in visited:
                        continue
                    if same_domain_only and not same_host(lk, seed_ref):
                        continue
                    queue.append((lk, depth + 1, seed_ref))

        except Exception:
            # برای تمرین: خطاها رو فعلا بی‌سر و صدا رد می‌کنیم
            continue

    pbar.close()

    out_pages_path.parent.mkdir(parents=True, exist_ok=True)
    out_pages_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    return pages
