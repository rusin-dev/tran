import os
import random
import re
import sys

DICT_FILE = os.path.join(os.path.dirname(__file__), "word_translation.csv")
SEPARATOR = ""

CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]+')
CLEAN_RE = re.compile(r'\([^)]*\)|\[[^\]]*\]|<[^>]*>')


def load_dict():
    import csv
    rows = []
    with open(DICT_FILE, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 2 or row[0] == "word":
                continue
            rows.append((row[0].strip().lower(), row[1].strip()))
    return rows


def binary_search(rows, w):
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid][0] < w:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(rows) and rows[lo][0] == w:
        return rows[lo][1]
    return None


def pick_meaning(word, rows, rand=0.5):
    w = word.lower().strip("'\"")
    translation = binary_search(rows, w)
    if translation is None:
        base = w.rstrip("'s")
        if base != w:
            translation = binary_search(rows, base)
    if translation is None and len(w) > 5:
        for suffix, cut in (("ing", 3), ("ed", 2), ("es", 2), ("s", 1)):
            if w.endswith(suffix):
                translation = binary_search(rows, w[:-cut])
                if translation:
                    break
    if not translation:
        return word

    cleaned = CLEAN_RE.sub("", translation)
    candidates = CJK_RE.findall(cleaned)
    if not candidates:
        candidates = CJK_RE.findall(translation)
    if not candidates:
        return word

    uniq = []
    seen = set()
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    weights = [1.0] + [rand] * (len(uniq) - 1)
    return random.choices(uniq, weights=weights, k=1)[0]


def translate(text, rows, rand=0.5):
    tokens = re.findall(r"[a-zA-Z']+|\d+|[.,]|\n+", text)
    out = []
    for tok in tokens:
        if tok == ",":
            out.append("，")
        elif tok == ".":
            out.append("。")
        elif tok.isdigit():
            out.append(tok)
        elif "\n" in tok:
            out.append(tok)
        else:
            out.append(pick_meaning(tok, rows, rand))
    return SEPARATOR.join(out)


def main():
    rows = load_dict()
    if len(sys.argv) > 1:
        print(translate(" ".join(sys.argv[1:]), rows))
        return
    print("奇葩翻译 (English -> 中文, 随机机翻) | 输入 exit 退出")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit"):
            break
        print(translate(text, rows))


if __name__ == "__main__":
    main()
