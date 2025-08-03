import os, math, re, json
from typing import List
from openai import OpenAI
from tqdm import tqdm
from .prompts import SYSTEM_PROMPT

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
client = OpenAI()

PH_RE = re.compile(r"(\d[\d .,:/]*|https?://\S+|www\.\S+)")

def _mask(txt: str):
    placeholders = PH_RE.findall(txt)
    masked = PH_RE.sub("{NUM}", txt)
    return masked, placeholders

def _unmask(txt: str, placeholders):
    for ph in placeholders:
        txt = txt.replace("{NUM}", ph, 1)
    return txt

def estimate(tokens: int) -> float:
    return tokens / 1000 * 0.0125

def _split_batches(texts: List[str], max_batch_tok: int):
    batches, buf, cur = [], [], 0
    for t in texts:
        tok = max(1, math.ceil(len(t) / 4))
        if cur + tok > max_batch_tok and buf:
            batches.append(buf)
            buf, cur = [], 0
        buf.append(t)
        cur += tok
    if buf:
        batches.append(buf)
    return batches

def translate(texts: List[str], target: str, max_batch_tok: int = 2000) -> List[str]:
    out: List[str] = []
    for buf in tqdm(_split_batches(texts, max_batch_tok), desc="GPT"):
        masked, placeholders = zip(*[_mask(t) for t in buf])

        user_msg = (
            f"Target language: {target}. "
            "Translate each element of the JSON array below. "
            "Return ONLY a valid JSON array of the translated strings in the same order.\n\n"
            + json.dumps(list(masked), ensure_ascii=False)
        )

        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                { "role": "system", "content": SYSTEM_PROMPT },
                { "role": "user", "content": user_msg }
            ],
        )

        reply = resp.choices[0].message.content.strip()
        clean = reply.strip()

        if clean.startswith("```"):
            clean = clean.split("```")[1]

        start = clean.find("[")
        end = clean.find("]", start)
        if start == -1 or end == -1:
            raise ValueError("ошибка:\n" + clean[:200])

        json_str = clean[start: end + 1]

        try:
            parts = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"ошибка:\n{json_str}") from e

        if len(parts) != len(buf):
            raise ValueError(
                f"{len(parts)} blocks, expected {len(buf)}."
            )

        for txt, ph_list in zip(parts, placeholders):
            out.append(_unmask(txt, ph_list))

    return out
