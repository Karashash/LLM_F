import re
PH_RE = re.compile(r"\{NUM\}")

def validate(src_blocks, translated):
    issues = []
    for i, (src, trg) in enumerate(zip(src_blocks, translated)):
        if PH_RE.findall(src) != PH_RE.findall(trg):
            issues.append(f"Блок {i}: потеряны или перепутаны {{NUM}}.")
    return issues
