# -*- coding: utf-8 -*-
"""
Quality Mastery Index (QMI) Engine
Canonical Mathematical Evaluation Tool for Literary AI Agents (EN/DE/FR -> RU)
Based on the Golden Canon of Russian Literary Translation (Gal, Chukovsky, Lozinsky).
"""

import argparse
import json
import math
import os
import re
import sys

# Language Corridors for Word Count Ratios (Ru_Words / Src_Words)
LANG_CORRIDORS = {
    "EN": {"min_opt": 0.81, "max_opt": 0.92, "warn_low": 0.75, "warn_high": 0.98, "base_u": 1.35},
    "DE": {"min_opt": 0.92, "max_opt": 1.05, "warn_low": 0.85, "warn_high": 1.12, "base_u": 1.15},
    "FR": {"min_opt": 0.73, "max_opt": 0.86, "warn_low": 0.68, "warn_high": 0.92, "base_u": 1.30}
}

BUREAUCRATIC_PATTERNS = [
    r'\bявляется\b', r'\bявлялся\b', r'\bявлялись\b', r'\bявлялась\b',
    r'\bимел\s+место\b', r'\bимела\s+место\b', r'\bимело\s+место\b',
    r'\bданный\b', r'\bданная\b', r'\bданное\b', r'\bданные\b',
    r'\bнекий\b', r'\bнекая\b', r'\bнекое\b',
    r'\bсо\s+стороны\b', r'\bв\s+отношении\b', r'\bв\s+плане\b', r'\bфакт\s+того\b'
]

CALQUE_PATTERNS = [
    r'\bс\s+(?:удивлением|любопытством|интересом|облегчением|осторожностью|тревогой|ужасом)\b'
]

PASSIVE_EXCLUSIONS = {
    'уверен', 'уверена', 'уверены', 'согласен', 'согласна', 'согласны',
    'должен', 'должна', 'должны', 'наивен', 'наивна', 'наивны',
    'пьян', 'пьяна', 'пьяны', 'беременна', 'беременны', 'готов', 'готова', 'готовы'
}

def evaluate_texts(src_text, ru_text, lang="EN", title="Fragment"):
    lang = lang.upper()
    cfg = LANG_CORRIDORS.get(lang, LANG_CORRIDORS["EN"])
    
    clean_ru = re.sub(r'\{\{FN_\d+\}\}', '', ru_text)
    
    src_words = re.findall(r"\b[a-zA-Z\u00C0-\u024F'-]+\b", src_text.lower())
    ru_words = re.findall(r"\b[а-яёА-ЯЁ-]+\b", clean_ru.lower())
    
    n_src = len(src_words)
    n_ru = len(ru_words)
    if n_src == 0 or n_ru == 0:
        return {"title": title, "error": "Empty text source or translation"}
        
    actual_rw = n_ru / n_src
    
    # 1. Lozinsky Volume Invariance (S_vol)
    if cfg["min_opt"] <= actual_rw <= cfg["max_opt"]:
        s_vol = 10.0
    elif actual_rw < cfg["min_opt"]:
        span = cfg["min_opt"] - cfg["warn_low"]
        dist = cfg["min_opt"] - actual_rw
        s_vol = max(3.0, 10.0 - 2.0 * (dist / span))
    else:
        span = cfg["warn_high"] - cfg["max_opt"]
        dist = actual_rw - cfg["max_opt"]
        s_vol = max(3.0, 10.0 - 2.0 * (dist / span))
    s_vol = round(min(10.0, max(0.0, s_vol)), 1)
    
    # 2. Zipf-Heaps Lexical Polyphony (S_lex)
    src_uniq = len(set(src_words))
    ru_uniq = len(set(ru_words))
    u_ratio = ru_uniq / src_uniq if src_uniq else 0
    
    length_correction = 0.04 * math.log(max(1.0, n_src / 1000.0))
    target_u = cfg["base_u"] + length_correction
    
    if u_ratio >= target_u:
        s_lex = 10.0
    else:
        gap = target_u - u_ratio
        s_lex = max(4.0, 10.0 - 20.0 * (gap ** 2))
    s_lex = round(min(10.0, s_lex), 1)
    
    # 3. Nora Gal Verbal Dynamo (S_verb)
    verbs = re.findall(r'\b[а-яё]+(?:л|ла|ло|ли|ть|ти|ет|ют|ит|ат|ят|ешь|ишь|ем|им|ете|ите|ут|лся|лась|лось|лись|вшись|в|я)\b', clean_ru.lower())
    verb_pct = (len(verbs) / n_ru) * 100
    
    if verb_pct >= 24.0:
        s_verb = 10.0
    elif verb_pct >= 22.0:
        s_verb = 9.5 + (verb_pct - 22.0) * 0.25
    elif verb_pct >= 20.0:
        s_verb = 8.5 + (verb_pct - 20.0) * 0.5
    else:
        s_verb = max(3.0, 8.5 - (20.0 - verb_pct) * 0.8)
    s_verb = round(min(10.0, s_verb), 1)
    
    # 4. Stylistic Purity (S_purity)
    bur_count = sum(len(re.findall(p, clean_ru.lower())) for p in BUREAUCRATIC_PATTERNS)
    calque_count = sum(len(re.findall(p, clean_ru.lower())) for p in CALQUE_PATTERNS)
    
    passives = re.findall(r'\b(был|была|было|были)\s+([а-яё]+(?:[ннтт][аоы]?))\b', clean_ru.lower())
    real_passives = [p for p in passives if p[1] not in PASSIVE_EXCLUSIONS]
    n_passives = len(real_passives)
    
    s_purity = 10.0 - (bur_count * 2.0) - (max(0, n_passives - 5) * 0.2) - (max(0, calque_count - 2) * 0.2)
    s_purity = round(min(10.0, max(0.0, s_purity)), 1)
    
    # 5. Composite Score Q_total
    q_total = 0.25 * s_vol + 0.30 * s_lex + 0.25 * s_verb + 0.20 * s_purity
    q_total = round(q_total, 1)
    
    # 6. Academic Status Tier
    if q_total >= 9.6:
        status = "Канонический уровень (Эталон)"
        status_icon = "🌟"
    elif q_total >= 9.0:
        status = "Корректный уровень (Высокий стандарт)"
        status_icon = "✅"
    elif q_total >= 8.0:
        status = "Требует калибровки (Зона недожима)"
        status_icon = "⚠️"
    else:
        status = "Несоответствие канону (Брак)"
        status_icon = "❌"
        
    return {
        "title": title,
        "lang": lang,
        "src_words": n_src,
        "ru_words": n_ru,
        "actual_rw": round(actual_rw, 3),
        "src_uniq": src_uniq,
        "ru_uniq": ru_uniq,
        "u_ratio": round(u_ratio, 2),
        "target_u": round(target_u, 2),
        "verb_pct": round(verb_pct, 1),
        "bureaucratic_count": bur_count,
        "passive_count": n_passives,
        "calque_count": calque_count,
        "score_vol": s_vol,
        "score_lex": s_lex,
        "score_verb": s_verb,
        "score_purity": s_purity,
        "total_score": q_total,
        "status": f"{status_icon} {status}"
    }

def print_table(results):
    print("\n| Раздел / Глава | Полнота (S_vol) | Словарь (S_lex) | Глагол (S_verb) | Чистота (S_pur) | ИТОГ QMI | Статус соответствия |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in results:
        if "error" in r:
            print(f"| **{r['title']}** | ERR | ERR | ERR | ERR | **N/A** | {r['error']} |")
        else:
            print(f"| **{r['title']}** | {r['score_vol']}/10 | {r['score_lex']}/10 | {r['score_verb']}/10 | {r['score_purity']}/10 | **{r['total_score']} / 10** | {r['status']} |")

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="Quality Mastery Index (QMI v1.3.2) Translation Evaluator")
    parser.add_argument("--file", "-f", help="Path to translated JSON file (containing pairs array or list of chapters)")
    parser.add_argument("--orig", "-o", help="Path to original source text file")
    parser.add_argument("--trans", "-t", help="Path to translated Russian text file")
    parser.add_argument("--title", default="Fragment", help="Title of evaluated section")
    parser.add_argument("--lang", "-l", default="EN", type=str.upper, choices=["EN", "DE", "FR"], help="Source language (EN, DE, FR)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    args = parser.parse_args()

    results = []

    if args.orig and args.trans:
        with open(args.orig, "r", encoding="utf-8") as f:
            src_full = f.read()
        with open(args.trans, "r", encoding="utf-8") as f:
            ru_full = f.read()
        results.append(evaluate_texts(src_full, ru_full, lang=args.lang, title=args.title))
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                if "pairs" in item:
                    src_full = " ".join(p.get("en", p.get("orig", "")) for p in item["pairs"])
                    ru_full = " ".join(p.get("ru", "") for p in item["pairs"])
                    title = item.get("title", "Chapter")
                    results.append(evaluate_texts(src_full, ru_full, lang=args.lang, title=title))
        elif isinstance(data, dict) and "pairs" in data:
            src_full = " ".join(p.get("en", p.get("orig", "")) for p in data["pairs"])
            ru_full = " ".join(p.get("ru", "") for p in data["pairs"])
            title = data.get("title", "Text")
            results.append(evaluate_texts(src_full, ru_full, lang=args.lang, title=title))
    else:
        print("QMI Engine v1.3.2 (Calibrated) - Usage:")
        print("  1. Evaluate JSON file:  python qmi_eval.py --file <data.json> [--lang EN/DE/FR]")
        print("  2. Evaluate text files: python qmi_eval.py --orig <orig.txt> --trans <ru.txt> [--lang EN/DE/FR] [--title Title]")
        sys.exit(0)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_table(results)

if __name__ == "__main__":
    main()
