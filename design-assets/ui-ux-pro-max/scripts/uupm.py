#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/UX Pro Max Search - self-contained BM25 search engine (single file).

A self-contained version of nextlevelbuilder/ui-ux-pro-max-skill's search tool.
No external dependencies (stdlib only). It can:
  1. Search a local CSV database (styles, colors, typography, ux, stacks, ...)
  2. Generate a design system recommendation (--design-system)
  3. Bootstrap its own data from the upstream repo (--fetch-data)

Usage:
    python3 uupm.py "<query>" [--domain <domain>] [-n <max_results>]
    python3 uupm.py "<query>" --stack <stack>
    python3 uupm.py "<query>" --design-system [-p "Name"] [-f markdown|ascii]
    python3 uupm.py --fetch-data              # download CSV data from upstream
"""

import csv
import io
import json
import os
import re
import sys
import argparse
import urllib.request
from pathlib import Path
from math import log
from collections import defaultdict

# ---------------------------------------------------------------------------
# Force UTF-8 output (Windows cp1252 default breaks emoji / box-drawing chars)
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Scripts live in <skill_dir>/scripts/uupm.py. Data lives next to the skill dir:
#   <skill_dir>/data/...   (when copied as part of the skill bundle)
#   <skill_dir>/../data/   (fallback)
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
if not DATA_DIR.exists():
    DATA_DIR = SCRIPT_DIR.parent.parent / "data"

MAX_RESULTS = 3
REASONING_FILE = "ui-reasoning.csv"

# ---------------------------------------------------------------------------
# CSV schema config (mirrors the upstream project)
# ---------------------------------------------------------------------------
CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Category", "Keywords", "Best For", "Type", "AI Prompt Keywords"],
        "output_cols": ["Style Category", "Type", "Keywords", "Primary Colors", "Effects & Animation", "Best For", "Light Mode ✓", "Dark Mode ✓", "Performance", "Accessibility", "Framework Compatibility", "Complexity", "AI Prompt Keywords", "CSS/Technical Keywords", "Implementation Checklist", "Design System Variables"],
    },
    "color": {
        "file": "colors.csv",
        "search_cols": ["Product Type", "Notes"],
        "output_cols": ["Product Type", "Primary", "On Primary", "Secondary", "On Secondary", "Accent", "On Accent", "Background", "Foreground", "Card", "Card Foreground", "Muted", "Muted Foreground", "Border", "Destructive", "On Destructive", "Ring", "Notes"],
    },
    "chart": {
        "file": "charts.csv",
        "search_cols": ["Data Type", "Keywords", "Best Chart Type", "When to Use", "When NOT to Use", "Accessibility Notes"],
        "output_cols": ["Data Type", "Keywords", "Best Chart Type", "Secondary Options", "When to Use", "When NOT to Use", "Data Volume Threshold", "Color Guidance", "Accessibility Grade", "Accessibility Notes", "A11y Fallback", "Library Recommendation", "Interactive Level"],
    },
    "landing": {
        "file": "landing.csv",
        "search_cols": ["Pattern Name", "Keywords", "Conversion Optimization", "Section Order"],
        "output_cols": ["Pattern Name", "Keywords", "Section Order", "Primary CTA Placement", "Color Strategy", "Conversion Optimization"],
    },
    "product": {
        "file": "products.csv",
        "search_cols": ["Product Type", "Keywords", "Primary Style Recommendation", "Key Considerations"],
        "output_cols": ["Product Type", "Keywords", "Primary Style Recommendation", "Secondary Styles", "Landing Page Pattern", "Dashboard Style (if applicable)", "Color Palette Focus"],
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "search_cols": ["Category", "Issue", "Description", "Platform"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"],
    },
    "typography": {
        "file": "typography.csv",
        "search_cols": ["Font Pairing Name", "Category", "Mood/Style Keywords", "Best For", "Heading Font", "Body Font"],
        "output_cols": ["Font Pairing Name", "Category", "Heading Font", "Body Font", "Mood/Style Keywords", "Best For", "Google Fonts URL", "CSS Import", "Tailwind Config", "Notes"],
    },
    "icons": {
        "file": "icons.csv",
        "search_cols": ["Category", "Icon Name", "Keywords", "Best For"],
        "output_cols": ["Category", "Icon Name", "Keywords", "Library", "Import Code", "Usage", "Best For", "Style"],
    },
    "gsap": {
        "file": "motion.csv",
        "search_cols": ["Category", "Intensity Tier", "Keywords", "Trigger"],
        "output_cols": ["Category", "Intensity Tier", "Trigger", "Duration", "Easing", "GSAP Snippet", "Framework Notes", "Do", "Don't", "Performance Notes"],
    },
    "react": {
        "file": "react-performance.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"],
    },
    "web": {
        "file": "app-interface.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": ["Category", "Issue", "Platform", "Description", "Do", "Don't", "Code Example Good", "Code Example Bad", "Severity"],
    },
    "google-fonts": {
        "file": "google-fonts.csv",
        "search_cols": ["Family", "Category", "Stroke", "Classifications", "Keywords", "Subsets", "Designers"],
        "output_cols": ["Family", "Category", "Stroke", "Classifications", "Styles", "Variable Axes", "Subsets", "Designers", "Popularity Rank", "Google Fonts URL"],
    },
}

UNTRUNCATED_COLS = {
    "Code Example Good", "Code Example Bad", "Code Good", "Code Bad",
    "Implementation Checklist", "Design System Variables", "CSS Import",
    "Tailwind Config", "GSAP Snippet",
}

STACK_CONFIG = {
    "react": {"file": "stacks/react.csv"}, "nextjs": {"file": "stacks/nextjs.csv"}, "vue": {"file": "stacks/vue.csv"},
    "svelte": {"file": "stacks/svelte.csv"}, "astro": {"file": "stacks/astro.csv"}, "nuxtjs": {"file": "stacks/nuxtjs.csv"},
    "nuxt-ui": {"file": "stacks/nuxt-ui.csv"}, "angular": {"file": "stacks/angular.csv"}, "laravel": {"file": "stacks/laravel.csv"},
    "swiftui": {"file": "stacks/swiftui.csv"}, "react-native": {"file": "stacks/react-native.csv"},
    "flutter": {"file": "stacks/flutter.csv"}, "jetpack-compose": {"file": "stacks/jetpack-compose.csv"},
    "html-tailwind": {"file": "stacks/html-tailwind.csv"}, "shadcn": {"file": "stacks/shadcn.csv"},
    "threejs": {"file": "stacks/threejs.csv"}, "javafx": {"file": "stacks/javafx.csv"}, "wpf": {"file": "stacks/wpf.csv"},
    "winui": {"file": "stacks/winui.csv"}, "avalonia": {"file": "stacks/avalonia.csv"}, "uno": {"file": "stacks/uno.csv"},
    "uwp": {"file": "stacks/uwp.csv"},
}
AVAILABLE_STACKS = list(STACK_CONFIG.keys())
_STACK_COLS = {
    "search_cols": ["Category", "Guideline", "Description", "Do", "Don't"],
    "output_cols": ["Category", "Guideline", "Description", "Do", "Don't", "Code Good", "Code Bad", "Severity", "Docs URL"],
}

# ---------------------------------------------------------------------------
# Tokenizer / BM25 (ported verbatim from upstream core.py)
# ---------------------------------------------------------------------------
_STOPWORDS = {
    "to", "in", "on", "at", "is", "of", "by", "or", "an", "if", "no", "so",
    "do", "be", "we", "it", "as", "the", "and", "for", "are", "was",
}
_SYNONYMS = {
    "e-commerce": "ecommerce", "dark-mode": "dark", "darkmode": "dark",
    "light-mode": "light", "lightmode": "light", "a11y": "accessibility",
    "nav": "navigation", "sign-up": "signup", "log-in": "login",
    "colour": "color", "colours": "colors", "customisation": "customization",
    "organisation": "organization", "behaviour": "behavior", "ux/ui": "ux ui",
}


def _normalize(text):
    for variant, canonical in _SYNONYMS.items():
        text = text.replace(variant, canonical)
    return text


class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0
        self._term_freqs = []

    def tokenize(self, text):
        text = _normalize(str(text).lower())
        text = re.sub(r"[^\w\s]", " ", text)
        return [w for w in text.split() if len(w) >= 2 and w not in _STOPWORDS]

    def fit(self, documents):
        self.corpus = [self.tokenize(d) for d in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(d) for d in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.N
        self._term_freqs = []
        for doc in self.corpus:
            tf = defaultdict(int)
            for w in doc:
                tf[w] += 1
            self._term_freqs.append(tf)
            for w in tf:
                self.doc_freqs[w] += 1
        for w, f in self.doc_freqs.items():
            self.idf[w] = log((self.N - f + 0.5) / (f + 0.5) + 1)

    def score(self, query):
        query_tokens = self.tokenize(query)
        scores = []
        for idx in range(self.N):
            score = 0
            doc_len = self.doc_lengths[idx]
            tf = self._term_freqs[idx]
            for token in query_tokens:
                if token in self.idf:
                    term_freq = tf.get(token, 0)
                    num = term_freq * (self.k1 + 1)
                    den = term_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                    score += self.idf[token] * num / den
            scores.append((idx, score))
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def vocabulary(self):
        return list(self.idf.keys())


_csv_cache = {}
_bm25_cache = {}


def _load_csv(filepath):
    mtime = filepath.stat().st_mtime
    cached = _csv_cache.get(filepath)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    _csv_cache[filepath] = (mtime, rows)
    return rows


def _get_bm25(filepath, search_cols, data):
    key = (filepath, tuple(search_cols))
    mtime = filepath.stat().st_mtime
    cached = _bm25_cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]
    documents = [" ".join(str(row.get(c, "")) for c in search_cols) for row in data]
    bm25 = BM25()
    bm25.fit(documents)
    _bm25_cache[key] = (mtime, bm25)
    return bm25


def _search_csv(filepath, search_cols, output_cols, query, max_results):
    if not filepath.exists():
        return [], None
    try:
        data = _load_csv(filepath)
    except (csv.Error, OSError, UnicodeDecodeError):
        return [{"_error": f"Failed to read {filepath.name}"}], None
    if not data:
        return [], None
    bm25 = _get_bm25(filepath, search_cols, data)
    ranked = bm25.score(query)
    results = []
    for idx, score in ranked[:max_results]:
        if score > 0:
            row = data[idx]
            results.append({c: row.get(c, "") for c in output_cols if c in row})
    return results, bm25


def _suggest_terms(bm25, query, limit=6):
    if bm25 is None:
        return []
    q_tokens = set(bm25.tokenize(query))
    if not q_tokens:
        return []
    cands = []
    for term in bm25.vocabulary():
        for qt in q_tokens:
            if term.startswith(qt[:3]) or qt.startswith(term[:3]):
                cands.append(term)
                break
    seen, ordered = set(), []
    for t in cands:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered[:limit]


# ---------------------------------------------------------------------------
# Domain auto-detection
# ---------------------------------------------------------------------------
def _load_product_keywords():
    seed = ["saas", "ecommerce", "fintech", "healthcare", "gaming", "portfolio",
            "crypto", "dashboard", "fitness", "marketplace"]
    filepath = DATA_DIR / CSV_CONFIG["product"]["file"]
    if not filepath.exists():
        return seed
    try:
        rows = _load_csv(filepath)
    except Exception:
        return seed
    kws = set(seed)
    for row in rows:
        for kw in re.split(r"[,;]", row.get("Keywords", "")):
            kw = kw.strip().lower()
            if kw and len(kw) >= 3:
                kws.add(kw)
    return sorted(kws, key=len, reverse=True)


_domain_keywords_cache = None


def _domain_keywords():
    global _domain_keywords_cache
    if _domain_keywords_cache is not None:
        return _domain_keywords_cache
    _domain_keywords_cache = {
        "color": ["color", "palette", "hex", "rgb", "token", "semantic", "accent", "muted", "foreground"],
        "chart": ["chart", "graph", "visualization", "trend", "bar", "pie", "scatter", "heatmap", "funnel"],
        "landing": ["landing", "page", "cta", "conversion", "hero", "testimonial", "pricing", "section"],
        "product": _load_product_keywords(),
        "style": ["style", "design", "ui", "minimalism", "glassmorphism", "neumorphism", "brutalism", "dark mode", "flat", "prompt", "css", "checklist", "tailwind"],
        "ux": ["ux", "usability", "accessibility", "wcag", "touch", "scroll", "animation", "keyboard", "navigation", "mobile"],
        "typography": ["font pairing", "heading font", "body font"],
        "google-fonts": ["google font", "font family", "font weight", "font style", "variable font", "font", "typography", "serif", "sans"],
        "icons": ["icon", "icons", "lucide", "heroicons", "symbol", "glyph", "svg icon"],
        "gsap": ["gsap", "scrolltrigger", "stagger", "parallax", "page transition", "scroll reveal", "flip plugin", "splittext"],
        "react": ["react", "next.js", "nextjs", "suspense", "memo", "usecallback", "rerender", "bundle", "dynamic import"],
        "web": ["aria", "focus", "outline", "semantic", "virtualize", "autocomplete", "form", "input type", "preconnect"],
    }
    return _domain_keywords_cache


_domain_tiebreak = ["ux", "product", "style", "color", "typography", "google-fonts",
                    "chart", "landing", "icons", "gsap", "react", "web"]


def detect_domain(query, return_scores=False):
    q = query.lower()
    dk = _domain_keywords()
    scores = {}
    for domain, keywords in dk.items():
        total = 0.0
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", q):
                total += max(1, len(kw.split()))
        scores[domain] = total
    ranked = sorted(scores.items(),
                    key=lambda it: (it[1], -_domain_tiebreak.index(it[0]) if it[0] in _domain_tiebreak else -999),
                    reverse=True)
    best_domain, best_score = ranked[0]
    result = best_domain if best_score > 0 else "style"
    if return_scores:
        runner = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None
        return result, runner
    return result


def search(query, domain=None, max_results=MAX_RESULTS):
    auto = domain is None
    runner = None
    if domain is None:
        domain, runner = detect_domain(query, return_scores=True)
    config = CSV_CONFIG.get(domain, CSV_CONFIG["style"])
    filepath = DATA_DIR / config["file"]
    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}
    results, bm25 = _search_csv(filepath, config["search_cols"], config["output_cols"], query, max_results)
    out = {"domain": domain, "query": query, "file": config["file"], "count": len(results), "results": results}
    if auto:
        out["auto_detected"] = True
        if runner:
            out["runner_up_domain"] = runner
    if not results:
        out["suggestions"] = _suggest_terms(bm25, query)
    return out


def search_stack(query, stack, max_results=MAX_RESULTS):
    if stack not in STACK_CONFIG:
        return {"error": f"Unknown stack: {stack}. Available: {', '.join(AVAILABLE_STACKS)}"}
    filepath = DATA_DIR / STACK_CONFIG[stack]["file"]
    if not filepath.exists():
        return {"error": f"Stack file not found: {filepath}", "stack": stack}
    results, bm25 = _search_csv(filepath, _STACK_COLS["search_cols"], _STACK_COLS["output_cols"], query, max_results)
    out = {"domain": "stack", "stack": stack, "query": query,
           "file": STACK_CONFIG[stack]["file"], "count": len(results), "results": results}
    if not results:
        out["suggestions"] = _suggest_terms(bm25, query)
    return out


# ---------------------------------------------------------------------------
# Design system generator (simplified from upstream design_system.py)
# ---------------------------------------------------------------------------
DIAL_TIERS = {
    "variance": [
        (1, 3, {"label": "Centered / Minimal", "style_keywords": ["Minimalism", "Exaggerated Minimalism", "centered", "symmetric", "grid-based"]}),
        (4, 7, {"label": "Balanced / Modern", "style_keywords": ["modern", "structured", "balanced"]}),
        (8, 10, {"label": "Bold / Asymmetric", "style_keywords": ["Brutalism", "Bento Grids", "asymmetric", "experimental"]}),
    ],
    "motion": [
        (1, 3, {"label": "Subtle", "tier": "Subtle"}),
        (4, 7, {"label": "Standard", "tier": "Standard"}),
        (8, 10, {"label": "Complex", "tier": "Complex"}),
    ],
    "density": [
        (1, 3, {"label": "Spacious", "spacing": {"xs": "4px", "sm": "8px", "md": "24px", "lg": "32px", "xl": "48px", "2xl": "64px", "3xl": "96px"}}),
        (4, 7, {"label": "Standard", "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px", "2xl": "48px", "3xl": "64px"}}),
        (8, 10, {"label": "Dense / Dashboard", "spacing": {"xs": "2px", "sm": "4px", "md": "8px", "lg": "12px", "xl": "16px", "2xl": "24px", "3xl": "32px"}}),
    ],
}

DARK_PRIMARY_MARKERS = ("dark first", "dark primary", "dark only", "dark mode primary", "dark-first")
DARK_QUERY_MARKERS = ("dark", "dark mode", "darkmode", "night", "oled", "midnight")
DARK_ANTI_PATTERN_MARKERS = ("avoid dark", "light mode", "avoid dark-mode")
DARK_BACKGROUND_MAX_LUMINANCE = 0.4


def _relative_luminance(hex_color):
    if not hex_color:
        return None
    v = hex_color.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return None
    try:
        ch = [int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    except ValueError:
        return None
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _palette_is_dark(palette):
    lum = _relative_luminance((palette or {}).get("Background", ""))
    return lum is not None and lum < DARK_BACKGROUND_MAX_LUMINANCE


def _style_is_dark_primary(style):
    if not style:
        return False
    declared = "{} {}".format(style.get("Light Mode ✓", ""), style.get("Dark Mode ✓", "")).lower()
    return any(m in declared for m in DARK_PRIMARY_MARKERS)


def _query_wants_dark(query):
    lowered = (query or "").lower()
    return any(m in lowered for m in DARK_QUERY_MARKERS)


def _resolve_color_mode(query, style):
    if _query_wants_dark(query) or _style_is_dark_primary(style):
        return "dark"
    return "light"


def _select_palette_for_mode(palettes, mode):
    if not palettes:
        return {}
    if mode == "dark":
        for p in palettes:
            if _palette_is_dark(p):
                return p
    return palettes[0]


def _filter_anti_patterns_for_mode(anti_patterns, mode):
    if mode != "dark" or not anti_patterns:
        return anti_patterns
    kept = [c for c in anti_patterns.split("+")
            if not any(m in c.lower() for m in DARK_ANTI_PATTERN_MARKERS)]
    return " + ".join(c.strip() for c in kept if c.strip())


def _resolve_dial(dial_name, value):
    if value is None:
        return None
    value = max(1, min(10, int(value)))
    for lo, hi, info in DIAL_TIERS[dial_name]:
        if lo <= value <= hi:
            return {**info, "value": value}
    return None


def _find_reasoning_rule(reasoning_data, category):
    cat = category.lower()
    for rule in reasoning_data:
        if rule.get("UI_Category", "").lower() == cat:
            return rule
    for rule in reasoning_data:
        c = rule.get("UI_Category", "").lower()
        if c in cat or cat in c:
            return rule
    for rule in reasoning_data:
        c = rule.get("UI_Category", "").lower()
        kws = re.split(r"[/\-\s]+", c)
        if any(kw in cat for kw in kws):
            return rule
    return {}


def _apply_reasoning(reasoning_data, category):
    rule = _find_reasoning_rule(reasoning_data, category)
    if not rule:
        return {
            "pattern": "Hero + Features + CTA",
            "style_priority": ["Minimalism", "Flat Design"],
            "color_mood": "Professional",
            "typography_mood": "Clean",
            "key_effects": "Subtle hover transitions",
            "anti_patterns": "",
            "severity": "MEDIUM",
        }
    try:
        dr = json.loads(rule.get("Decision_Rules", "{}"))
    except json.JSONDecodeError:
        dr = {}
    return {
        "pattern": rule.get("Recommended_Pattern", ""),
        "style_priority": [s.strip() for s in rule.get("Style_Priority", "").split("+")],
        "color_mood": rule.get("Color_Mood", ""),
        "typography_mood": rule.get("Typography_Mood", ""),
        "key_effects": rule.get("Key_Effects", ""),
        "anti_patterns": rule.get("Anti_Patterns", ""),
        "decision_rules": dr,
        "severity": rule.get("Severity", "MEDIUM"),
    }


def _select_best_match(results, priority_keywords):
    if not results:
        return {}
    if not priority_keywords:
        return results[0]
    for pr in priority_keywords:
        pl = pr.lower().strip()
        for r in results:
            sn = r.get("Style Category", "").lower()
            if pl in sn or sn in pl:
                return r
    scored = []
    for r in results:
        rs = str(r).lower()
        score = 0
        for kw in priority_keywords:
            kwl = kw.lower().strip()
            if kwl in r.get("Style Category", "").lower():
                score += 10
            elif kwl in r.get("Keywords", "").lower():
                score += 3
            elif kwl in rs:
                score += 1
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] > 0 else results[0]


def generate_design_system(query, project_name=None, output_format="ascii",
                           variance=None, motion=None, density=None):
    generator = _DesignSystemGenerator()
    return generator.generate(query, project_name, variance=variance, motion=motion, density=density)


class _DesignSystemGenerator:
    SEARCH_CONFIG = {
        "product": {"max_results": 1},
        "style": {"max_results": 3},
        "color": {"max_results": 2},
        "landing": {"max_results": 2},
        "typography": {"max_results": 2},
    }

    def __init__(self):
        self.reasoning_data = self._load_reasoning()

    def _load_reasoning(self):
        fp = DATA_DIR / REASONING_FILE
        if not fp.exists():
            return []
        with open(fp, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _multi_domain_search(self, query, style_priority=None):
        results = {}
        for domain, config in self.SEARCH_CONFIG.items():
            if domain == "style" and style_priority:
                pq = " ".join(style_priority[:2]) if style_priority else query
                results[domain] = search(f"{query} {pq}", domain, config["max_results"])
            else:
                results[domain] = search(query, domain, config["max_results"])
        return results

    def generate(self, query, project_name=None, variance=None, motion=None, density=None):
        variance_info = _resolve_dial("variance", variance)
        motion_info = _resolve_dial("motion", motion)
        density_info = _resolve_dial("density", density)

        product_result = search(query, "product", 1)
        product_results = product_result.get("results", [])
        category = product_results[0].get("Product Type", "General") if product_results else "General"

        reasoning = _apply_reasoning(self.reasoning_data, category)
        style_priority = reasoning.get("style_priority", [])
        effective = style_priority
        if variance_info:
            effective = variance_info["style_keywords"] + style_priority

        search_results = self._multi_domain_search(query, effective)
        search_results["product"] = product_result

        style_results = search_results.get("style", {}).get("results", [])
        color_results = search_results.get("color", {}).get("results", [])
        typography_results = search_results.get("typography", {}).get("results", [])
        landing_results = search_results.get("landing", {}).get("results", [])

        best_style = _select_best_match(style_results, effective)
        color_mode = _resolve_color_mode(query, best_style)
        best_color = _select_palette_for_mode(color_results, color_mode)
        best_typography = typography_results[0] if typography_results else {}
        best_landing = landing_results[0] if landing_results else {}

        motion_snippet = {}
        if motion_info:
            mres = search(f"{query} {motion_info['tier']}", "gsap", 5)
            mm = mres.get("results", [])
            tiered = [m for m in mm if m.get("Intensity Tier") == motion_info["tier"]]
            motion_snippet = tiered[0] if tiered else (mm[0] if mm else {})

        style_effects = best_style.get("Effects & Animation", "")
        combined_effects = style_effects or reasoning.get("key_effects", "")

        return {
            "project_name": project_name or query.upper(),
            "category": category,
            "pattern": {
                "name": best_landing.get("Pattern Name", reasoning.get("pattern", "Hero + Features + CTA")),
                "sections": best_landing.get("Section Order", "Hero > Features > CTA"),
                "cta_placement": best_landing.get("Primary CTA Placement", "Above fold"),
                "color_strategy": best_landing.get("Color Strategy", ""),
                "conversion": best_landing.get("Conversion Optimization", ""),
            },
            "style": {
                "name": best_style.get("Style Category", "Minimalism"),
                "type": best_style.get("Type", "General"),
                "effects": style_effects,
                "keywords": best_style.get("Keywords", ""),
                "best_for": best_style.get("Best For", ""),
                "performance": best_style.get("Performance", ""),
                "accessibility": best_style.get("Accessibility", ""),
                "light_mode": best_style.get("Light Mode ✓", ""),
                "dark_mode": best_style.get("Dark Mode ✓", ""),
            },
            "colors": {
                "primary": best_color.get("Primary", "#2563EB"),
                "on_primary": best_color.get("On Primary", ""),
                "secondary": best_color.get("Secondary", "#3B82F6"),
                "accent": best_color.get("Accent", "#F97316"),
                "background": best_color.get("Background", "#F8FAFC"),
                "foreground": best_color.get("Foreground", "#1E293B"),
                "muted": best_color.get("Muted", ""),
                "border": best_color.get("Border", ""),
                "destructive": best_color.get("Destructive", ""),
                "ring": best_color.get("Ring", ""),
                "notes": best_color.get("Notes", ""),
            },
            "typography": {
                "heading": best_typography.get("Heading Font", "Inter"),
                "body": best_typography.get("Body Font", "Inter"),
                "mood": best_typography.get("Mood/Style Keywords", reasoning.get("typography_mood", "")),
                "best_for": best_typography.get("Best For", ""),
                "google_fonts_url": best_typography.get("Google Fonts URL", ""),
                "css_import": best_typography.get("CSS Import", ""),
            },
            "key_effects": combined_effects,
            "anti_patterns": _filter_anti_patterns_for_mode(reasoning.get("anti_patterns", ""), color_mode),
            "decision_rules": reasoning.get("decision_rules", {}),
            "severity": reasoning.get("severity", "MEDIUM"),
            "dials": {
                "variance": variance_info["value"] if variance_info else None,
                "variance_label": variance_info["label"] if variance_info else None,
                "motion": motion_info["value"] if motion_info else None,
                "motion_label": motion_info["label"] if motion_info else None,
                "density": density_info["value"] if density_info else None,
                "density_label": density_info["label"] if density_info else None,
            },
            "motion_snippet": motion_snippet,
            "spacing_scale": density_info["spacing"] if density_info else None,
        }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------
BOX_WIDTH = 90


def _wrap(text, prefix, width):
    if not text:
        return []
    words = text.split()
    lines = []
    cur = prefix
    for w in words:
        if len(cur) + len(w) + 1 <= width - 2:
            cur += (" " if cur != prefix else "") + w
        else:
            if cur != prefix:
                lines.append(cur)
            cur = prefix + w
    if cur != prefix:
        lines.append(cur)
    return lines


def _hex_to_ansi(hex_color):
    if not hex_color or not hex_color.startswith("#"):
        return ""
    if os.environ.get("COLORTERM", "") not in ("truecolor", "24bit"):
        return ""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return ""
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m██\033[0m "


def _ansi_ljust(s, width):
    visible = len(re.sub(r"\033\[[0-9;]*m", "", s))
    return s + (" " * max(0, width - visible))


def _section_header(name, width):
    label = f"─── {name} "
    fill = "─" * (width - len(label) - 1)
    return f"├{label}{fill}┤"


def format_ascii_box(ds):
    project = ds.get("project_name", "PROJECT")
    pattern, style = ds.get("pattern", {}), ds.get("style", {})
    colors, typography = ds.get("colors", {}), ds.get("typography", {})
    effects, anti = ds.get("key_effects", ""), ds.get("anti_patterns", "")
    dials, motion = ds.get("dials", {}), ds.get("motion_snippet", {})
    w = BOX_WIDTH - 1
    L = []
    L.append("╔" + "═" * w + "╗")
    L.append(_ansi_ljust(f"║  TARGET: {project} - RECOMMENDED DESIGN SYSTEM", BOX_WIDTH) + "║")
    L.append("╚" + "═" * w + "╝")
    L.append("┌" + "─" * w + "┐")
    if any(dials.get(k) is not None for k in ("variance", "motion", "density")):
        L.append(_section_header("DESIGN DIALS", BOX_WIDTH + 1))
        if dials.get("variance") is not None:
            L.append(f"│  Variance: {dials['variance']}/10 — {dials['variance_label']}".ljust(BOX_WIDTH) + "│")
        if dials.get("motion") is not None:
            L.append(f"│  Motion:   {dials['motion']}/10 — {dials['motion_label']}".ljust(BOX_WIDTH) + "│")
        if dials.get("density") is not None:
            L.append(f"│  Density:  {dials['density']}/10 — {dials['density_label']}".ljust(BOX_WIDTH) + "│")
    L.append(_section_header("PATTERN", BOX_WIDTH + 1))
    L.append(f"│  Name: {pattern.get('name', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get("conversion"):
        L.append(f"│     Conversion: {pattern.get('conversion', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get("cta_placement"):
        L.append(f"│     CTA: {pattern.get('cta_placement', '')}".ljust(BOX_WIDTH) + "│")
    sections = [s.strip() for s in pattern.get("sections", "").split(">") if s.strip()]
    L.append("│     Sections:".ljust(BOX_WIDTH) + "│")
    for i, s in enumerate(sections, 1):
        L.append(f"│       {i}. {s}".ljust(BOX_WIDTH) + "│")
    L.append(_section_header("STYLE", BOX_WIDTH + 1))
    L.append(f"│  Name: {style.get('name', '')}".ljust(BOX_WIDTH) + "│")
    if style.get("light_mode") or style.get("dark_mode"):
        L.append(f"│     Mode Support: Light {style.get('light_mode', '')}  Dark {style.get('dark_mode', '')}".ljust(BOX_WIDTH) + "│")
    for line in _wrap(f"Keywords: {style.get('keywords', '')}", "│     ", BOX_WIDTH):
        L.append(line.ljust(BOX_WIDTH) + "│")
    for line in _wrap(f"Best For: {style.get('best_for', '')}", "│     ", BOX_WIDTH):
        L.append(line.ljust(BOX_WIDTH) + "│")
    if style.get("performance") or style.get("accessibility"):
        L.append(f"│     Performance: {style.get('performance', '')} | Accessibility: {style.get('accessibility', '')}".ljust(BOX_WIDTH) + "│")
    L.append(_section_header("COLORS", BOX_WIDTH + 1))
    entries = [("Primary", "primary", "--color-primary"), ("On Primary", "on_primary", "--color-on-primary"),
               ("Secondary", "secondary", "--color-secondary"), ("Accent/CTA", "accent", "--color-accent"),
               ("Background", "background", "--color-background"), ("Foreground", "foreground", "--color-foreground"),
               ("Muted", "muted", "--color-muted"), ("Border", "border", "--color-border"),
               ("Destructive", "destructive", "--color-destructive"), ("Ring", "ring", "--color-ring")]
    for label, key, cssv in entries:
        hv = colors.get(key, "")
        if not hv:
            continue
        swatch = _hex_to_ansi(hv)
        L.append(_ansi_ljust(f"│     {swatch}{label + ':':14s} {hv:10s} ({cssv})", BOX_WIDTH) + "│")
    if colors.get("notes"):
        for line in _wrap(f"Notes: {colors.get('notes', '')}", "│     ", BOX_WIDTH):
            L.append(line.ljust(BOX_WIDTH) + "│")
    L.append(_section_header("TYPOGRAPHY", BOX_WIDTH + 1))
    L.append(f"│  {typography.get('heading', '')} / {typography.get('body', '')}".ljust(BOX_WIDTH) + "│")
    for line in _wrap(f"Mood: {typography.get('mood', '')}", "│     ", BOX_WIDTH):
        L.append(line.ljust(BOX_WIDTH) + "│")
    for line in _wrap(f"Best For: {typography.get('best_for', '')}", "│     ", BOX_WIDTH):
        L.append(line.ljust(BOX_WIDTH) + "│")
    if typography.get("google_fonts_url"):
        L.append(f"│     Google Fonts: {typography.get('google_fonts_url', '')}".ljust(BOX_WIDTH) + "│")
    if effects:
        L.append(_section_header("KEY EFFECTS", BOX_WIDTH + 1))
        for line in _wrap(effects, "│     ", BOX_WIDTH):
            L.append(line.ljust(BOX_WIDTH) + "│")
    if motion:
        L.append(_section_header("MOTION", BOX_WIDTH + 1))
        L.append(f"│  {motion.get('Category', '')} ({motion.get('Intensity Tier', '')})".ljust(BOX_WIDTH) + "│")
        for line in _wrap(f"GSAP: {motion.get('GSAP Snippet', '')}", "│     ", BOX_WIDTH):
            L.append(line.ljust(BOX_WIDTH) + "│")
    if anti:
        L.append(_section_header("AVOID", BOX_WIDTH + 1))
        for line in _wrap(anti, "│     ", BOX_WIDTH):
            L.append(line.ljust(BOX_WIDTH) + "│")
    L.append(_section_header("PRE-DELIVERY CHECKLIST", BOX_WIDTH + 1))
    for item in ["[ ] No emojis as icons (use SVG: Heroicons/Lucide)",
                 "[ ] cursor-pointer on all clickable elements",
                 "[ ] Hover states with smooth transitions (150-300ms)",
                 "[ ] Light mode: text contrast 4.5:1 minimum",
                 "[ ] Focus states visible for keyboard nav",
                 "[ ] prefers-reduced-motion respected",
                 "[ ] Responsive: 375px, 768px, 1024px, 1440px"]:
        L.append(f"│     {item}".ljust(BOX_WIDTH) + "│")
    L.append("└" + "─" * w + "┘")
    return "\n".join(L)


def format_markdown(ds):
    project = ds.get("project_name", "PROJECT")
    pattern, style = ds.get("pattern", {}), ds.get("style", {})
    colors, typography = ds.get("colors", {}), ds.get("typography", {})
    effects, anti = ds.get("key_effects", ""), ds.get("anti_patterns", "")
    dials, motion = ds.get("dials", {}), ds.get("motion_snippet", {})
    L = [f"## Design System: {project}", ""]
    if any(dials.get(k) is not None for k in ("variance", "motion", "density")):
        L.append("### Design Dials")
        for k in ("variance", "motion", "density"):
            if dials.get(k) is not None:
                L.append(f"- **{k.title()}:** {dials[k]}/10 — {dials[k + '_label']}")
        L.append("")
    L += ["### Pattern", f"- **Name:** {pattern.get('name', '')}"]
    if pattern.get("conversion"):
        L.append(f"- **Conversion Focus:** {pattern.get('conversion', '')}")
    if pattern.get("cta_placement"):
        L.append(f"- **CTA Placement:** {pattern.get('cta_placement', '')}")
    L.append(f"- **Sections:** {pattern.get('sections', '')}", "")
    L += ["### Style", f"- **Name:** {style.get('name', '')}"]
    if style.get("keywords"):
        L.append(f"- **Keywords:** {style.get('keywords', '')}")
    if style.get("best_for"):
        L.append(f"- **Best For:** {style.get('best_for', '')}")
    L += ["", "### Colors", "| Role | Hex | CSS Variable |", "|------|-----|--------------|"]
    entries = [("Primary", "primary", "--color-primary"), ("On Primary", "on_primary", "--color-on-primary"),
               ("Secondary", "secondary", "--color-secondary"), ("Accent/CTA", "accent", "--color-accent"),
               ("Background", "background", "--color-background"), ("Foreground", "foreground", "--color-foreground"),
               ("Muted", "muted", "--color-muted"), ("Border", "border", "--color-border"),
               ("Destructive", "destructive", "--color-destructive"), ("Ring", "ring", "--color-ring")]
    for label, key, cssv in entries:
        hv = colors.get(key, "")
        if hv:
            L.append(f"| {label} | `{hv}` | `{cssv}` |")
    if colors.get("notes"):
        L.append(f"\n*Notes: {colors.get('notes', '')}*")
    L += ["", "### Typography", f"- **Heading:** {typography.get('heading', '')}",
          f"- **Body:** {typography.get('body', '')}"]
    if typography.get("mood"):
        L.append(f"- **Mood:** {typography.get('mood', '')}")
    if typography.get("google_fonts_url"):
        L.append(f"- **Google Fonts:** {typography.get('google_fonts_url', '')}")
    if effects:
        L += ["", "### Key Effects", effects]
    if anti:
        L += ["", "### Avoid (Anti-patterns)", f"- {anti.replace(' + ', chr(10) + '- ')}"]
    L += ["", "### Pre-Delivery Checklist",
          "- [ ] No emojis as icons (use SVG: Heroicons/Lucide)",
          "- [ ] cursor-pointer on all clickable elements",
          "- [ ] Hover states with smooth transitions (150-300ms)",
          "- [ ] Light mode: text contrast 4.5:1 minimum",
          "- [ ] Focus states visible for keyboard nav",
          "- [ ] prefers-reduced-motion respected",
          "- [ ] Responsive: 375px, 768px, 1024px, 1440px", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Data bootstrap (download CSV data from upstream repo)
# ---------------------------------------------------------------------------
UPSTREAM_BASE = "https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/.claude/skills/ui-ux-pro-max/data"

# Core data files + stack files
CORE_DATA_FILES = list(CSV_CONFIG.keys()) + [REASONING_FILE]
# note: core files map to actual filenames via CSV_CONFIG[domain]['file']


def _fetch_file(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(raw)
    return len(raw)


def fetch_data(verbose=True):
    """Download the CSV data files from the upstream repo into DATA_DIR."""
    created = []
    failures = []

    # Core domain files (dedupe by actual filename)
    files = {}
    for domain in CSV_CONFIG:
        fname = CSV_CONFIG[domain]["file"]
        files.setdefault(fname, fname)
    files.setdefault(REASONING_FILE, REASONING_FILE)
    # Stack files (fname already includes the stacks/ prefix)
    for stack in STACK_CONFIG:
        fname = STACK_CONFIG[stack]["file"]
        files.setdefault(fname, fname)

    for fname, rel in files.items():
        dest = DATA_DIR / rel
        url = f"{UPSTREAM_BASE}/{rel}"
        try:
            size = _fetch_file(url, dest)
            created.append(str(dest))
            if verbose:
                print(f"  ✓ {rel} ({size} bytes)")
        except Exception as e:
            failures.append((rel, str(e)))
            if verbose:
                print(f"  ✗ {rel}: {e}")

    if verbose:
        print(f"\nFetched {len(created)} files, {len(failures)} failed.")
    if failures:
        print("Failures:", failures)
    return created, failures


# ---------------------------------------------------------------------------
# Output formatting for search results
# ---------------------------------------------------------------------------
TRUNCATE_AT = 300


def format_output(result, full=False):
    if "error" in result:
        return f"Error: {result['error']}"
    out = []
    if result.get("stack"):
        out.append("## UI Pro Max Stack Guidelines")
        out.append(f"**Stack:** {result['stack']} | **Query:** {result['query']}")
    else:
        out.append("## UI Pro Max Search Results")
        dn = result["domain"]
        if result.get("auto_detected"):
            dn += " (auto-detected"
            if result.get("runner_up_domain"):
                dn += f", runner-up: {result['runner_up_domain']}"
            dn += ")"
        out.append(f"**Domain:** {dn} | **Query:** {result['query']}")
    out.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")
    if result["count"] == 0:
        out.append("No matches. The query did not hit the database. Retry with broader/different keywords before falling back to general defaults.")
        if result.get("suggestions"):
            out.append(f"**Closest known terms:** {', '.join(result['suggestions'])}")
        return "\n".join(out)
    for i, row in enumerate(result["results"], 1):
        out.append(f"### Result {i}")
        for k, v in row.items():
            vs = str(v)
            if not full and k not in UNTRUNCATED_COLS and len(vs) > TRUNCATE_AT:
                vs = vs[:TRUNCATE_AT] + "..."
            out.append(f"- **{k}:** {vs}")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="UI Pro Max Search (self-contained)")
    parser.add_argument("query", nargs="?", default=None, help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help="Stack-specific search")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--full", action="store_true", help="Do not truncate long fields")
    parser.add_argument("--design-system", "-ds", action="store_true", help="Generate design system")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format")
    parser.add_argument("--variance", type=int, choices=range(1, 11), help="Design variance dial 1-10")
    parser.add_argument("--motion", type=int, choices=range(1, 11), help="Motion dial 1-10")
    parser.add_argument("--density", type=int, choices=range(1, 11), help="Density dial 1-10")
    parser.add_argument("--fetch-data", action="store_true", help="Download CSV data from upstream")
    parser.add_argument("--data-dir", type=str, default=None, help="Override data directory")

    args = parser.parse_args()

    global DATA_DIR
    if args.data_dir:
        DATA_DIR = Path(args.data_dir)
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.fetch_data:
        fetch_data()
        return

    if not args.query:
        parser.print_help()
        return

    if args.design_system:
        ds = generate_design_system(
            args.query, args.project_name, output_format=args.format,
            variance=args.variance, motion=args.motion, density=args.density,
        )
        if args.json:
            print(json.dumps(ds, indent=2, ensure_ascii=False))
        else:
            print(format_ascii_box(ds) if args.format == "ascii" else format_markdown(ds))
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_output(result, full=args.full))
    else:
        result = search(args.query, args.domain, args.max_results)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_output(result, full=args.full))


if __name__ == "__main__":
    main()
