---
name: ui-ux-pro-max
description: "UI/UX design intelligence for web and mobile. Searchable design database (84+ styles, 190+ color palettes, 74 font pairings, 190+ product types, 98 UX guidelines, 25 chart types, 22 stacks). Use when designing, building, or reviewing UI: pages, components, color schemes, typography, layout, accessibility, animation, or data visualization. Includes an embedded Python search engine (BM25) that can bootstrap its own data from the upstream repo."
---

# UI/UX Pro Max - Design Intelligence (Self-Contained Engine)

A searchable UI/UX design database with an **embedded Python search engine**. The engine (BM25) is inlined as source below; when you need to query the database, materialize it to a persistent path, bootstrap the CSV data from the upstream repo (once), then search.

## What this skill provides

- **84+ design styles** (minimalism, glassmorphism, neumorphism, brutalism, bento, dark mode, ...) with color/effect/accessibility metadata and implementation checklists
- **190+ color palettes** organized by product type, with semantic CSS variable tokens and WCAG notes
- **74 font pairings** with Google Fonts URLs and CSS imports
- **190+ product-type rules** (SaaS, e-commerce, fintech, healthcare, gaming, ...) with recommended patterns and anti-patterns
- **98 UX guidelines** with Do / Don't / severity (accessibility, touch, performance, layout, typography, animation, forms, navigation, charts)
- **25 chart types**, icon sets, GSAP motion presets
- **22 tech stacks** (React, Next.js, Vue, Svelte, Astro, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, Jetpack Compose, Angular, Laravel, JavaFX, WPF, WinUI, Avalonia, Uno, UWP, Three.js, HTML/CSS)

## When to use

Use when the task involves **UI structure, visual design decisions, interaction patterns, or UX quality control**: designing new pages, creating/refactoring UI components, choosing color/typography/spacing/layout systems, reviewing UI for UX/accessibility/consistency, implementing navigation/animation/responsive behavior, or improving perceived quality.

Skip for pure backend logic, API/database design, non-visual performance work, infrastructure/DevOps, or non-visual scripts.

## How to use the embedded engine

### 1. 脚本位置（合集内）

本 skill 的搜索引擎代码位于合集内部：

```
ppt-skills-collection/design-assets/ui-ux-pro-max/scripts/uupm.py
```

> 脚本路径与合集根目录的相对关系：从合集根 `ppt-skills-collection/` 出发，`design-assets/ui-ux-pro-max/scripts/uupm.py`。合集复制到 skills 目录后，路径为 `skills/ppt-skills-collection/design-assets/ui-ux-pro-max/scripts/uupm.py`。

数据目录 `<skill_dir>/data/` 存放 CSV 数据文件。脚本默认读取 `<skill_dir>/data/`，失败时回退到 `<skill_dir>/../data/`。

### 2. Bootstrap the data（首次，需网络）

```bash
python <skill_dir>/scripts/uupm.py --fetch-data --data-dir <skill_dir>/data
```

This downloads all 35 CSV data files (styles, colors, typography, ux, stacks, ...) from the upstream repo into `<skill_dir>/data/`. Run it again later to refresh.

> ⚠️ **首次使用前**：若 `<skill_dir>/data/` 不存在或为空，必须先运行上面的 `--fetch-data` 命令初始化数据。搜索引擎在数据目录为空时返回明确的 "File not found" 错误，而非空结果——此时不要误判为"没有匹配"，先初始化再搜索。

### 3. Search

```bash
python <skill_dir>/scripts/uupm.py "<query>" --data-dir <skill_dir>/data
python <skill_dir>/scripts/uupm.py "<query>" --domain color --data-dir <skill_dir>/data
python <skill_dir>/scripts/uupm.py "<query>" --design-system -p "Project" --data-dir <skill_dir>/data
python <skill_dir>/scripts/uupm.py "<query>" --stack react --data-dir <skill_dir>/data
```

### Command reference

| Command | Purpose |
|---------|---------|
| `uupm.py "<query>"` | Search with auto domain detection |
| `uupm.py "<query>" --domain <style/color/typography/ux/chart/landing/product/icons/gsap/react/web/google-fonts>` | Search a specific domain |
| `uupm.py "<query>" --stack <react/nextjs/vue/...>` | Stack-specific guidelines |
| `uupm.py "<query>" --design-system -p "Name"` | Full design system recommendation |
| `uupm.py --fetch-data` | Download/refresh the CSV data |
| `-n <N>` | Max results (default 3) |
| `--json` | Machine-readable JSON output |

### Design dials (with --design-system)

- `--variance 1-10` — Centered/minimal (low) → Bold/asymmetric (high)
- `--motion 1-10` — Subtle → complex (attaches a GSAP snippet)
- `--density 1-10` — Spacious → dense/dashboard spacing scale

## Embedded script behavior notes

- The engine only uses the Python standard library (no pip installs).
- If the data dir is empty, searches return an explicit "File not found" error — run `--fetch-data` first.
- 0-result searches are real misses, not empty matches. Retry with broader keywords; if still empty, say explicitly that no database match was found and fall back to general defaults.
- Output is UTF-8 (box-drawing and emoji safe).

## Priority rule categories (quick reference)

| Priority | Category | Impact | Key Checks | Anti-Patterns |
|----------|----------|--------|------------|----------------|
| 1 | Accessibility | CRITICAL | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels | Removing focus rings, Icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | Min 44x44px, 8px+ spacing, Loading feedback | Hover-only reliance, Instant state changes |
| 3 | Performance | HIGH | WebP/AVIF, Lazy loading, CLS < 0.1 | Layout thrashing, Layout shift |
| 4 | Style Selection | HIGH | Match product type, Consistency, SVG icons | Mixing flat & skeuomorphic, Emoji icons |
| 5 | Layout & Responsive | HIGH | Mobile-first, Breakpoints, No horizontal scroll | Fixed px widths, Disabled zoom |
| 6 | Typography & Color | MEDIUM | Base 16px, Line-height 1.5, Semantic tokens | <12px body, Gray-on-gray, Raw hex |
| 7 | Animation | MEDIUM | 150-300ms, Motion means meaning | Decorative-only, No reduced-motion |
| 8 | Forms & Feedback | MEDIUM | Visible labels, Error near field | Placeholder-only labels, Errors at top only |
| 9 | Navigation | HIGH | Predictable back, Bottom nav <=5, Deep links | Overloaded nav, Broken back |
| 10 | Charts & Data | LOW | Legends, Tooltips, Accessible colors | Color-only meaning |

## Source & License

- **Original project**: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT License)
- **Adaptation**: consolidated the upstream Python scripts (core.py + search.py + design_system.py) into a single self-contained `uupm.py` with a `--fetch-data` bootstrap, for environments that cannot install multi-file skills (Claude Desktop). All search logic and CSV schemas preserved.
- **Script location**: `scripts/uupm.py`（已从 SKILL.md 中抽出为独立文件）
- **License**: MIT.