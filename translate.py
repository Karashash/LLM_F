import argparse, pathlib
from app.docx_utils import extract_blocks, restore_blocks
from app.llm_client import translate, estimate
from app.validator import validate

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--tgt", required=True, choices=["ru","kk"])
    ap.add_argument("--out")
    args=ap.parse_args()

    blocks, doc = extract_blocks(args.src)
    tokens = sum(len(b['content']) for b in blocks)//4
    print(f"≈ {tokens} tokens, cost ~ ${estimate(tokens):.3f}")

    translated = translate([b['content'] for b in blocks], args.tgt)
    problems = validate([b['content'] for b in blocks], translated)
    if problems:
        print('проблемы:')
        for p in problems: print(' -', p)

    restore_blocks(doc, blocks, translated)
    out_path = args.out or pathlib.Path(args.src).with_stem(f"{pathlib.Path(args.src).stem}_{args.tgt}")
    doc.save(out_path)
    print('Saved to', out_path)

if __name__=='__main__':
    main()
