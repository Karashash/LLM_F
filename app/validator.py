# app/validator.py
import difflib, re

PH_RE = re.compile(r"\{NUM\}")

def validate(src_blocks, tgt_blocks):
    issues = []
    for i, (s, t) in enumerate(zip(src_blocks, tgt_blocks)):
        if PH_RE.findall(s) != PH_RE.findall(t):
            issues.append(f"Блок {i}: placeholders mismatch")
        if not t.strip():
            issues.append(f"Блок {i}: пустой перевод")
    return issues

def html_diff(a: str, b: str) -> str:
    return difflib.HtmlDiff().make_table(
        a.splitlines(), b.splitlines(),
        fromdesc="Original", todesc="Translated",
        context=True, numlines=1,
    )
