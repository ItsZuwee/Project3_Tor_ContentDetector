import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class DetectorConfig:
    model_name: str = "distilgpt2"
    max_chars: int = 2500  # برای کنترل هزینه/زمان
    device: str = "cpu"


class PerplexityDetector:
    def __init__(self, cfg: Optional[DetectorConfig] = None):
        self.cfg = cfg or DetectorConfig()
        self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.cfg.model_name)
        self.model.to(self.cfg.device)
        self.model.eval()

    @torch.no_grad()
    def perplexity(self, text: str) -> float:
        text = (text or "").strip()
        if not text:
            return float("inf")

        # کوتاه‌سازی
        text = text[: self.cfg.max_chars]

        enc = self.tokenizer(text, return_tensors="pt", truncation=True)
        input_ids = enc["input_ids"].to(self.cfg.device)

        # اگر متن خیلی کوتاه بود
        if input_ids.shape[1] < 8:
            return float("inf")

        outputs = self.model(input_ids, labels=input_ids)
        loss = outputs.loss
        ppl = float(torch.exp(loss).cpu().item())
        return ppl

    def score_ai_likeness(self, ppl: float) -> float:
        # نگاشت ساده به بازه 0..1
        # ppl خیلی پایین => امتیاز بالا
        # ppl خیلی بالا => امتیاز پایین
        if not math.isfinite(ppl):
            return 0.0

        # این اعداد قابل تنظیم‌اند (برای گزارش توضیح می‌دی)
        low, high = 20.0, 120.0
        x = (high - ppl) / (high - low)
        if x < 0:
            return 0.0
        if x > 1:
            return 1.0
        return float(x)

    def detect_pages(self, pages: List[Dict]) -> List[Dict]:
        results = []
        for p in pages:
            text = (p.get("text") or "").strip()
            ppl = self.perplexity(text)
            ai_score = self.score_ai_likeness(ppl)

            results.append(
                {
                    "url": p.get("url"),
                    "seed": p.get("seed"),
                    "text_len": p.get("text_len", 0),
                    "perplexity": ppl,
                    "ai_score": ai_score,
                    "label": "AI-like" if ai_score >= 0.6 else "Human-like",
                }
            )
        return results
