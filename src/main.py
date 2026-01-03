import json
from pathlib import Path

from crawler import crawl, read_seed_urls
from detector import PerplexityDetector, DetectorConfig


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out"


def main():
    seed_path = DATA / "seed_urls.txt"
    pages_path = OUT / "pages.json"
    detections_path = OUT / "detections.json"

    if not seed_path.exists():
        raise FileNotFoundError(f"Missing seed file: {seed_path}")

    seed_urls = read_seed_urls(seed_path)
    if not seed_urls:
        raise RuntimeError("seed_urls.txt is empty or invalid. Put http(s) URLs, one per line.")

    # 1) Crawl
    pages = crawl(
        seed_urls=seed_urls,
        out_pages_path=pages_path,
        max_pages=20,
        max_depth=1,
        same_domain_only=True,
        tor_port=9150,  # اگر Tor service داری: 9050
    )

    # 2) Detect
    detector = PerplexityDetector(DetectorConfig(model_name="distilgpt2", device="cpu"))
    detections = detector.detect_pages(pages)

    OUT.mkdir(parents=True, exist_ok=True)
    detections_path.write_text(json.dumps(detections, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done. pages saved to: {pages_path}")
    print(f"Done. detections saved to: {detections_path}")

    # خلاصه سریع
    top = sorted(detections, key=lambda x: x["ai_score"], reverse=True)[:5]
    print("\nTop AI-like (by ai_score):")
    for r in top:
        print(f"- {r['ai_score']:.2f} | ppl={r['perplexity']:.1f} | {r['url']}")


if __name__ == "__main__":
    main()
