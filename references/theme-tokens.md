# 主题 Token 值手册

> **完整可落地**。36 套主题（html-ppt）+ 4 套中国场景（codex-ppt）+ 1 套 MBB 咨询 = **41 套**，每套都有完整的 CSS `:root` token 值。
> 数据来源：html-ppt-skill `assets/themes/*.css`（MIT）+ codex-ppt-skill 风格定义（MIT）+ mbb-decks 视觉系统。
>
> ⚠️ **反俗套字体注意**：部分上游主题的 `--font-display` 可能通过 `var(--font-sans)` 回退到 Inter/Roboto。执行层在写入 HTML 时应检查：如果选定主题的 `--font-display` 含 Inter/Roboto，替换为 `'Noto Sans SC','Microsoft YaHei',sans-serif`；或从 `design-system.md` 主题目录中选有性格的替代字体。本文件保留上游原始 token 不做修改（数据溯源），修补在执行层做。

执行层 axi-front-design 只需：
1. 从数据护照读「主题方案」字段（如 `swiss-grid`）
2. 在本文件找到对应主题，把它全部 `:root` 变量写入 HTML `<style>` 块
3. **检查 `--font-display` 并修补**（见上段反俗套注意）
4. 所有组件颜色/圆角/阴影/字体从 CSS 变量读取，禁止硬编码

---

## Light & calm（浅色冷静）

### minimal-white — 极简白 · clean restraint

```css
:root {
  --bg: #ffffff; --bg-soft: #fafafa; --surface: #ffffff; --surface-2: #f5f5f6;
  --border: rgba(17,18,22,.08); --border-strong: rgba(17,18,22,.16);
  --text-1: #0c0d10; --text-2: #55596a; --text-3: #9ca1b0;
  --accent: #111216; --accent-2: #3b3f4a; --accent-3: #6b6f7a;
  --good: #1aaf6c; --warn: #c98500; --bad: #c13a3a;
  --grad: linear-gradient(135deg, #111216, #3b3f4a);
  --grad-soft: linear-gradient(135deg, #f5f5f6, #ffffff);
  --radius: 14px; --radius-sm: 8px; --radius-lg: 22px;
  --shadow: 0 1px 2px rgba(17,18,22,.04), 0 8px 24px rgba(17,18,22,.06);
  --shadow-lg: 0 20px 60px rgba(17,18,22,.1);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Inter', 'Noto Sans SC', sans-serif;
  --letter-tight: -.035em;
}
```

### editorial-serif — 杂志衬线 · high editorial

```css
:root {
  --bg: #faf7f2; --bg-soft: #f3efe6; --surface: #ffffff; --surface-2: #f7f2e8;
  --border: rgba(40,28,18,.12); --border-strong: rgba(40,28,18,.24);
  --text-1: #1b1410; --text-2: #5c4a3e; --text-3: #8a7868;
  --accent: #8a2a1c; --accent-2: #c97a4a; --accent-3: #1b1410;
  --good: #3f7d4f; --warn: #b07a1f; --bad: #8a2a1c;
  --grad: linear-gradient(135deg, #8a2a1c, #c97a4a);
  --grad-soft: linear-gradient(135deg, #faf7f2, #f3efe6);
  --radius: 4px; --radius-sm: 2px; --radius-lg: 8px;
  --shadow: 0 2px 12px rgba(40,28,18,.06);
  --shadow-lg: 0 20px 50px rgba(40,28,18,.14);
  --font-sans: 'Playfair Display', 'Noto Serif SC', serif;
  --font-display: 'Playfair Display', 'Noto Serif SC', serif;
  --font-serif: 'Playfair Display', 'Noto Serif SC', serif;
  --letter-tight: -.02em;
}
```

### soft-pastel — 马卡龙 · soft pastel

```css
:root {
  --bg: #fdf7fb; --bg-soft: #fbeef3; --surface: #ffffff; --surface-2: #fdf0f5;
  --border: rgba(120,70,110,.12); --border-strong: rgba(120,70,110,.22);
  --text-1: #3a1f33; --text-2: #6b4d62; --text-3: #a28a99;
  --accent: #f49bb8; --accent-2: #b5d5f0; --accent-3: #f7d08a;
  --good: #9dd9a3; --warn: #f7d08a; --bad: #ef9a9a;
  --grad: linear-gradient(135deg, #f49bb8, #b5d5f0 55%, #c4a0e8);
  --grad-soft: linear-gradient(135deg, #fbeef3, #eaf4fc);
  --radius: 24px; --radius-sm: 16px; --radius-lg: 32px;
  --shadow: 0 8px 28px rgba(244,155,184,.18);
  --shadow-lg: 0 24px 70px rgba(181,213,240,.3);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### xiaohongshu-white — 小红书白底高级感

```css
:root {
  --bg: #fffdfb; --bg-soft: #fff6f1; --surface: #ffffff; --surface-2: #fff1ea;
  --border: rgba(60,30,20,.1); --border-strong: rgba(60,30,20,.22);
  --text-1: #1a1210; --text-2: #4f3a32; --text-3: #a08d85;
  --accent: #ff2742; --accent-2: #ff7a90; --accent-3: #ffb38a;
  --good: #3ba55c; --warn: #f5a524; --bad: #ff2742;
  --grad: linear-gradient(135deg, #ff2742, #ff7a90 55%, #ffb38a);
  --grad-soft: linear-gradient(135deg, #fff6f1, #ffeae0);
  --radius: 20px; --radius-sm: 14px; --radius-lg: 28px;
  --shadow: 0 12px 30px rgba(255,39,66,.08);
  --shadow-lg: 0 24px 60px rgba(255,39,66,.14);
  --font-sans: 'Noto Sans SC', 'Inter', sans-serif;
  --font-display: 'Noto Serif SC', 'Playfair Display', serif;
  --letter-tight: -.02em;
}
```

### solarized-light — 低眩光 · 适合工作坊/教学

```css
:root {
  --bg: #fdf6e3; --bg-soft: #eee8d5; --surface: #ffffff; --surface-2: #f5efd7;
  --border: rgba(88,110,117,.2); --border-strong: rgba(88,110,117,.4);
  --text-1: #073642; --text-2: #586e75; --text-3: #93a1a1;
  --accent: #268bd2; --accent-2: #2aa198; --accent-3: #d33682;
  --good: #859900; --warn: #b58900; --bad: #dc322f;
  --grad: linear-gradient(135deg, #268bd2, #2aa198 50%, #859900);
  --grad-soft: linear-gradient(135deg, #fdf6e3, #eee8d5);
  --radius: 10px; --radius-sm: 6px; --radius-lg: 16px;
  --shadow: 0 6px 20px rgba(88,110,117,.14);
  --shadow-lg: 0 18px 50px rgba(88,110,117,.24);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### catppuccin-latte — Catppuccin 浅 · 技术分享

```css
:root {
  --bg: #eff1f5; --bg-soft: #e6e9ef; --surface: #ffffff; --surface-2: #eef0f4;
  --border: rgba(76,79,105,.14); --border-strong: rgba(76,79,105,.28);
  --text-1: #4c4f69; --text-2: #6c6f85; --text-3: #9ca0b0;
  --accent: #8839ef; --accent-2: #1e66f5; --accent-3: #ea76cb;
  --good: #40a02b; --warn: #df8e1d; --bad: #d20f39;
  --grad: linear-gradient(135deg, #8839ef, #1e66f5 50%, #04a5e5);
  --grad-soft: linear-gradient(135deg, #eff1f5, #e6e9ef);
  --radius: 14px; --radius-sm: 10px; --radius-lg: 22px;
  --shadow: 0 8px 24px rgba(76,79,105,.1);
  --shadow-lg: 0 20px 56px rgba(76,79,105,.16);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

---

## Bold & statement（大胆宣言）

### sharp-mono — 黑白高对比 · sharp mono

```css
:root {
  --bg: #ffffff; --bg-soft: #ffffff; --surface: #ffffff; --surface-2: #000000;
  --border: #000000; --border-strong: #000000;
  --text-1: #000000; --text-2: #1a1a1a; --text-3: #4a4a4a;
  --accent: #000000; --accent-2: #000000; --accent-3: #ff2200;
  --good: #008800; --warn: #ff9900; --bad: #ff0000;
  --grad: linear-gradient(135deg, #000, #222);
  --grad-soft: linear-gradient(135deg, #fff, #eee);
  --radius: 0; --radius-sm: 0; --radius-lg: 0;
  --shadow: 4px 4px 0 #000; --shadow-lg: 8px 8px 0 #000;
  --font-sans: 'Archivo Black', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Archivo Black', sans-serif;
  --letter-tight: -.04em;
}
```

### neo-brutalism — 厚描边+硬阴影+明黄

```css
:root {
  --bg: #fffef0; --bg-soft: #fffbd0; --surface: #ffffff; --surface-2: #fff38a;
  --border: #000000; --border-strong: #000000;
  --text-1: #000000; --text-2: #222222; --text-3: #555555;
  --accent: #ffd400; --accent-2: #ff5ca8; --accent-3: #3a7cff;
  --good: #00b36b; --warn: #ff9900; --bad: #ff3a30;
  --grad: linear-gradient(135deg, #ffd400, #ff5ca8);
  --grad-soft: linear-gradient(135deg, #fffbd0, #fff);
  --radius: 6px; --radius-sm: 4px; --radius-lg: 10px;
  --shadow: 6px 6px 0 #000; --shadow-lg: 10px 10px 0 #000;
  --font-sans: 'Space Grotesk', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Archivo Black', 'Space Grotesk', sans-serif;
  --letter-tight: -.03em;
}
```

### bauhaus — 几何+红黄蓝原色

```css
:root {
  --bg: #f4efe3; --bg-soft: #e8e2d1; --surface: #ffffff; --surface-2: #f4efe3;
  --border: #111111; --border-strong: #111111;
  --text-1: #111111; --text-2: #333333; --text-3: #666666;
  --accent: #e03c27; --accent-2: #f4c430; --accent-3: #1d4eaf;
  --good: #1b8c3c; --warn: #f4c430; --bad: #e03c27;
  --grad: linear-gradient(135deg, #e03c27 0 33%, #f4c430 33% 66%, #1d4eaf 66% 100%);
  --grad-soft: linear-gradient(135deg, #f4efe3, #e8e2d1);
  --radius: 0; --radius-sm: 0; --radius-lg: 0;
  --shadow: 4px 4px 0 #111; --shadow-lg: 8px 8px 0 #111;
  --font-sans: 'Space Grotesk', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Archivo Black', sans-serif;
  --letter-tight: -.03em;
}
```

### swiss-grid — 瑞士网格 · Helvetica 感

```css
:root {
  --bg: #ffffff; --bg-soft: #f4f4f4; --surface: #ffffff; --surface-2: #f4f4f4;
  --border: #111111; --border-strong: #111111;
  --text-1: #111111; --text-2: #444444; --text-3: #888888;
  --accent: #d6001c; --accent-2: #111111; --accent-3: #888888;
  --good: #0f8a2f; --warn: #d38a00; --bad: #d6001c;
  --grad: linear-gradient(135deg, #d6001c, #111);
  --grad-soft: linear-gradient(135deg, #f4f4f4, #fff);
  --radius: 0; --radius-sm: 0; --radius-lg: 0;
  --shadow: none; --shadow-lg: none;
  --font-sans: 'Inter', 'Helvetica Neue', Helvetica, 'Noto Sans SC', sans-serif;
  --font-display: 'Inter', 'Helvetica Neue', Helvetica, sans-serif;
  --letter-tight: -.04em;
}
```

### memphis-pop — 孟菲斯波普

```css
:root {
  --bg: #fef6e8; --bg-soft: #fdebc7; --surface: #ffffff; --surface-2: #fff1d1;
  --border: #111111; --border-strong: #111111;
  --text-1: #111111; --text-2: #333333; --text-3: #666666;
  --accent: #ff3d8b; --accent-2: #37c2d7; --accent-3: #ffcc00;
  --good: #6ac04c; --warn: #ffcc00; --bad: #ff3d8b;
  --grad: linear-gradient(135deg, #ff3d8b, #ffcc00 50%, #37c2d7);
  --grad-soft: linear-gradient(135deg, #fdebc7, #fff1d1);
  --radius: 10px; --radius-sm: 6px; --radius-lg: 18px;
  --shadow: 5px 5px 0 #111; --shadow-lg: 9px 9px 0 #111;
  --font-sans: 'Space Grotesk', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Archivo Black', sans-serif;
}
```

---

## Cool & dark（深色冷静）

### catppuccin-mocha — Catppuccin 深

```css
:root {
  --bg: #1e1e2e; --bg-soft: #181825; --surface: #313244; --surface-2: #45475a;
  --border: rgba(205,214,244,.12); --border-strong: rgba(205,214,244,.24);
  --text-1: #cdd6f4; --text-2: #a6adc8; --text-3: #7f849c;
  --accent: #cba6f7; --accent-2: #89b4fa; --accent-3: #f5c2e7;
  --good: #a6e3a1; --warn: #f9e2af; --bad: #f38ba8;
  --grad: linear-gradient(135deg, #cba6f7, #89b4fa 50%, #94e2d5);
  --grad-soft: linear-gradient(135deg, #313244, #45475a);
  --radius: 14px; --radius-sm: 10px; --radius-lg: 22px;
  --shadow: 0 10px 30px rgba(0,0,0,.35);
  --shadow-lg: 0 24px 60px rgba(0,0,0,.5);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### dracula — Dracula 紫红

```css
:root {
  --bg: #282a36; --bg-soft: #21222c; --surface: #343746; --surface-2: #44475a;
  --border: rgba(248,248,242,.12); --border-strong: rgba(248,248,242,.24);
  --text-1: #f8f8f2; --text-2: #bdbde0; --text-3: #6272a4;
  --accent: #bd93f9; --accent-2: #ff79c6; --accent-3: #8be9fd;
  --good: #50fa7b; --warn: #f1fa8c; --bad: #ff5555;
  --grad: linear-gradient(135deg, #bd93f9, #ff79c6 55%, #8be9fd);
  --grad-soft: linear-gradient(135deg, #343746, #44475a);
  --radius: 12px; --radius-sm: 8px; --radius-lg: 18px;
  --shadow: 0 10px 30px rgba(0,0,0,.4);
  --shadow-lg: 0 22px 60px rgba(0,0,0,.55);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### tokyo-night — 蓝夜

```css
:root {
  --bg: #1a1b26; --bg-soft: #16161e; --surface: #24283b; --surface-2: #2f334d;
  --border: rgba(192,202,245,.12); --border-strong: rgba(192,202,245,.24);
  --text-1: #c0caf5; --text-2: #a9b1d6; --text-3: #565f89;
  --accent: #7aa2f7; --accent-2: #bb9af7; --accent-3: #7dcfff;
  --good: #9ece6a; --warn: #e0af68; --bad: #f7768e;
  --grad: linear-gradient(135deg, #7aa2f7, #bb9af7 55%, #f7768e);
  --grad-soft: linear-gradient(135deg, #24283b, #2f334d);
  --radius: 12px; --radius-sm: 8px; --radius-lg: 20px;
  --shadow: 0 10px 30px rgba(0,0,0,.45);
  --shadow-lg: 0 24px 62px rgba(0,0,0,.6);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### nord — 北欧清冷蓝白

```css
:root {
  --bg: #2e3440; --bg-soft: #272b35; --surface: #3b4252; --surface-2: #434c5e;
  --border: rgba(236,239,244,.12); --border-strong: rgba(236,239,244,.24);
  --text-1: #eceff4; --text-2: #d8dee9; --text-3: #7b8394;
  --accent: #88c0d0; --accent-2: #81a1c1; --accent-3: #b48ead;
  --good: #a3be8c; --warn: #ebcb8b; --bad: #bf616a;
  --grad: linear-gradient(135deg, #88c0d0, #81a1c1 50%, #b48ead);
  --grad-soft: linear-gradient(135deg, #3b4252, #434c5e);
  --radius: 12px; --radius-sm: 8px; --radius-lg: 20px;
  --shadow: 0 10px 30px rgba(0,0,0,.35);
  --shadow-lg: 0 22px 60px rgba(0,0,0,.5);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### gruvbox-dark — 温暖复古深

```css
:root {
  --bg: #282828; --bg-soft: #1d2021; --surface: #3c3836; --surface-2: #504945;
  --border: rgba(235,219,178,.14); --border-strong: rgba(235,219,178,.28);
  --text-1: #ebdbb2; --text-2: #d5c4a1; --text-3: #928374;
  --accent: #fabd2f; --accent-2: #fe8019; --accent-3: #b8bb26;
  --good: #b8bb26; --warn: #fabd2f; --bad: #fb4934;
  --grad: linear-gradient(135deg, #fe8019, #fabd2f 55%, #b8bb26);
  --grad-soft: linear-gradient(135deg, #3c3836, #504945);
  --radius: 6px; --radius-sm: 4px; --radius-lg: 12px;
  --shadow: 0 10px 30px rgba(0,0,0,.5);
  --shadow-lg: 0 24px 60px rgba(0,0,0,.65);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### rose-pine — 玫瑰松柔和暗

```css
:root {
  --bg: #191724; --bg-soft: #1f1d2e; --surface: #26233a; --surface-2: #2a2740;
  --border: rgba(224,222,244,.12); --border-strong: rgba(224,222,244,.24);
  --text-1: #e0def4; --text-2: #c4b8d8; --text-3: #6e6a86;
  --accent: #ebbcba; --accent-2: #c4a7e7; --accent-3: #9ccfd8;
  --good: #31748f; --warn: #f6c177; --bad: #eb6f92;
  --grad: linear-gradient(135deg, #ebbcba, #c4a7e7 55%, #9ccfd8);
  --grad-soft: linear-gradient(135deg, #26233a, #2a2740);
  --radius: 14px; --radius-sm: 10px; --radius-lg: 22px;
  --shadow: 0 10px 30px rgba(0,0,0,.4);
  --shadow-lg: 0 22px 58px rgba(0,0,0,.55);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### arctic-cool — 冷色调 蓝/青/石板灰

```css
:root {
  --bg: #f2f6fb; --bg-soft: #e7eef7; --surface: #ffffff; --surface-2: #edf3fa;
  --border: rgba(40,70,110,.12); --border-strong: rgba(40,70,110,.24);
  --text-1: #0e1f33; --text-2: #3a5778; --text-3: #6b819b;
  --accent: #1e6fb0; --accent-2: #17b1b1; --accent-3: #6f8aa6;
  --good: #1aaf84; --warn: #d19030; --bad: #c5485a;
  --grad: linear-gradient(135deg, #1e6fb0, #17b1b1 60%, #5fb9d6);
  --grad-soft: linear-gradient(135deg, #e7eef7, #dff3f3);
  --radius: 14px; --radius-sm: 10px; --radius-lg: 22px;
  --shadow: 0 10px 28px rgba(40,70,110,.12);
  --shadow-lg: 0 24px 60px rgba(40,70,110,.18);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

---

## Warm & vibrant（暖色活力）

### sunset-warm — 暖色调 橘/珊瑚/琥珀

```css
:root {
  --bg: #fff7ef; --bg-soft: #ffeedc; --surface: #ffffff; --surface-2: #fff2e0;
  --border: rgba(120,60,20,.12); --border-strong: rgba(120,60,20,.22);
  --text-1: #2a160a; --text-2: #6b4630; --text-3: #a28572;
  --accent: #e36a2d; --accent-2: #f2a341; --accent-3: #d94860;
  --good: #5ea35a; --warn: #f2a341; --bad: #d94860;
  --grad: linear-gradient(135deg, #d94860, #e36a2d 50%, #f2a341);
  --grad-soft: linear-gradient(135deg, #ffeedc, #ffe0d0);
  --radius: 18px; --radius-sm: 12px; --radius-lg: 28px;
  --shadow: 0 12px 32px rgba(227,106,45,.16);
  --shadow-lg: 0 24px 64px rgba(227,106,45,.22);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

---

## Effect-heavy（特效）

### glassmorphism — 毛玻璃+光斑

```css
:root {
  --bg: #0b1024; --bg-soft: #0e1530; --surface: rgba(255,255,255,.06); --surface-2: rgba(255,255,255,.1);
  --border: rgba(255,255,255,.14); --border-strong: rgba(255,255,255,.28);
  --text-1: #f2f4ff; --text-2: #c3c8e6; --text-3: #8287a8;
  --accent: #7dd3fc; --accent-2: #c084fc; --accent-3: #f0abfc;
  --good: #86efac; --warn: #fde68a; --bad: #fca5a5;
  --grad: linear-gradient(135deg, #7dd3fc, #c084fc 55%, #f0abfc);
  --grad-soft: linear-gradient(135deg, rgba(125,211,252,.18), rgba(192,132,252,.18));
  --radius: 22px; --radius-sm: 14px; --radius-lg: 30px;
  --shadow: 0 20px 60px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.12);
  --shadow-lg: 0 30px 80px rgba(0,0,0,.5);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### aurora — 极光渐变

```css
:root {
  --bg: #06091c; --bg-soft: #0a1130; --surface: rgba(255,255,255,.05); --surface-2: rgba(255,255,255,.08);
  --border: rgba(180,220,255,.14); --border-strong: rgba(180,220,255,.28);
  --text-1: #e8f0ff; --text-2: #b4c4e4; --text-3: #6a7a9e;
  --accent: #5ef2c6; --accent-2: #7aa2ff; --accent-3: #c984ff;
  --good: #5ef2c6; --warn: #ffd27a; --bad: #ff8ab0;
  --grad: linear-gradient(135deg, #5ef2c6, #7aa2ff 50%, #c984ff);
  --grad-soft: linear-gradient(135deg, rgba(94,242,198,.2), rgba(201,132,255,.2));
  --radius: 20px; --radius-sm: 14px; --radius-lg: 28px;
  --shadow: 0 20px 60px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.08);
  --shadow-lg: 0 30px 80px rgba(0,0,0,.55);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### rainbow-gradient — 彩虹流动渐变（白底）

```css
:root {
  --bg: #ffffff; --bg-soft: #f8f8fb; --surface: #ffffff; --surface-2: #f4f4f8;
  --border: rgba(20,20,40,.08); --border-strong: rgba(20,20,40,.2);
  --text-1: #0c0d10; --text-2: #4d5162; --text-3: #9096a8;
  --accent: #ff4d8b; --accent-2: #7a5cff; --accent-3: #36b6ff;
  --good: #1aaf6c; --warn: #f5a524; --bad: #e0445a;
  --grad: linear-gradient(90deg, #ff0080, #ff4d00, #ff9900, #ffe600, #00c853, #0091ea, #6200ea, #ff0080);
  --grad-soft: linear-gradient(135deg, #fff, #f8f8fb);
  --radius: 16px; --radius-sm: 10px; --radius-lg: 24px;
  --shadow: 0 12px 32px rgba(124,92,255,.1);
  --shadow-lg: 0 24px 60px rgba(124,92,255,.18);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### blueprint — 蓝图工程网格底纹

```css
:root {
  --bg: #0b3a6f; --bg-soft: #0a3260; --surface: rgba(255,255,255,.06); --surface-2: rgba(255,255,255,.1);
  --border: rgba(190,220,255,.3); --border-strong: rgba(190,220,255,.55);
  --text-1: #e8f3ff; --text-2: #b8d4f0; --text-3: #7da8cf;
  --accent: #ffffff; --accent-2: #aee1ff; --accent-3: #ffd27a;
  --good: #8ef0a6; --warn: #ffd27a; --bad: #ff8a96;
  --grad: linear-gradient(135deg, #ffffff, #aee1ff);
  --grad-soft: linear-gradient(135deg, #0a3260, #0b3a6f);
  --radius: 2px; --radius-sm: 2px; --radius-lg: 4px;
  --shadow: none; --shadow-lg: 0 16px 40px rgba(0,0,0,.3);
  --font-sans: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  --font-display: 'JetBrains Mono', monospace;
}
```

### terminal-green — 绿屏终端+发光字

```css
:root {
  --bg: #030a04; --bg-soft: #041308; --surface: #0a1b10; --surface-2: #0d2614;
  --border: rgba(0,255,120,.22); --border-strong: rgba(0,255,120,.42);
  --text-1: #8cff9a; --text-2: #4bd17a; --text-3: #2f8a4d;
  --accent: #00ff88; --accent-2: #67ffd0; --accent-3: #b6ff6b;
  --good: #00ff88; --warn: #ffe066; --bad: #ff6464;
  --grad: linear-gradient(135deg, #00ff88, #67ffd0);
  --grad-soft: linear-gradient(135deg, #0a1b10, #0d2614);
  --radius: 4px; --radius-sm: 2px; --radius-lg: 8px;
  --shadow: 0 0 30px rgba(0,255,136,.15);
  --shadow-lg: 0 0 60px rgba(0,255,136,.28);
  --font-sans: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  --font-display: 'JetBrains Mono', monospace;
  --letter-tight: -.01em;
}
```

---

## v2 补充

### corporate-clean — 白+海军蓝 · 企业商务

```css
:root {
  --bg: #ffffff; --bg-soft: #f5f7fa; --surface: #ffffff; --surface-2: #f0f3f7;
  --border: rgba(10,37,64,.12); --border-strong: rgba(10,37,64,.28);
  --text-1: #0a2540; --text-2: #425466; --text-3: #8898aa;
  --accent: #0a2540; --accent-2: #1d4ed8; --accent-3: #64748b;
  --good: #0e9f6e; --warn: #d97706; --bad: #dc2626;
  --grad: linear-gradient(135deg, #0a2540, #1d4ed8);
  --grad-soft: linear-gradient(135deg, #f0f4fb, #e4ecf7);
  --radius: 6px; --radius-sm: 4px; --radius-lg: 10px;
  --shadow: 0 1px 3px rgba(10,37,64,.08), 0 4px 12px rgba(10,37,64,.05);
  --shadow-lg: 0 4px 12px rgba(10,37,64,.1), 0 16px 40px rgba(10,37,64,.08);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### pitch-deck-vc — YC 风 · 融资路演

```css
:root {
  --bg: #ffffff; --bg-soft: #fafbfc; --surface: #ffffff; --surface-2: #f5f7fa;
  --border: rgba(20,30,50,.1); --border-strong: rgba(20,30,50,.22);
  --text-1: #0b0d12; --text-2: #4a5270; --text-3: #8b93a8;
  --accent: #0070f3; --accent-2: #7928ca; --accent-3: #ff4ecb;
  --good: #0cce6b; --warn: #f5a524; --bad: #ee0000;
  --grad: linear-gradient(135deg, #0070f3, #7928ca);
  --grad-soft: linear-gradient(135deg, #e8f0ff, #f3e8ff);
  --radius: 14px; --radius-sm: 8px; --radius-lg: 22px;
  --shadow: 0 2px 8px rgba(20,30,50,.06), 0 12px 32px rgba(20,30,50,.06);
  --shadow-lg: 0 8px 24px rgba(20,30,50,.1), 0 30px 80px rgba(20,30,50,.1);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Inter', 'Noto Sans SC', sans-serif;
}
```

### academic-paper — 学术白皮书

```css
:root {
  --bg: #fdfcf8; --bg-soft: #f7f5ed; --surface: #ffffff; --surface-2: #f5f3ea;
  --border: rgba(20,20,20,.14); --border-strong: rgba(20,20,20,.35);
  --text-1: #0a0a0a; --text-2: #333333; --text-3: #707070;
  --accent: #1a3a7a; --accent-2: #0a0a0a; --accent-3: #8a1a1a;
  --good: #1a5a2a; --warn: #8a6a1a; --bad: #8a1a1a;
  --grad: linear-gradient(135deg, #1a3a7a, #0a0a0a);
  --grad-soft: linear-gradient(135deg, #e8edf8, #f5f3ea);
  --radius: 0px; --radius-sm: 0px; --radius-lg: 0px;
  --shadow: none;
  --shadow-lg: 0 1px 2px rgba(0,0,0,.1);
  --font-sans: 'Latin Modern Roman', 'Playfair Display', 'Noto Serif SC', Georgia, serif;
  --font-serif: 'Latin Modern Roman', 'Playfair Display', 'Noto Serif SC', Georgia, serif;
  --font-display: 'Latin Modern Roman', 'Playfair Display', 'Noto Serif SC', Georgia, serif;
}
```

### japanese-minimal — 和风极简 · 朱红

```css
:root {
  --bg: #fafaf5; --bg-soft: #f2f0e6; --surface: #ffffff; --surface-2: #f5f3ea;
  --border: rgba(40,30,20,.1); --border-strong: rgba(40,30,20,.3);
  --text-1: #1a1a18; --text-2: #5c564c; --text-3: #9c958a;
  --accent: #d93a2a; --accent-2: #1a1a18; --accent-3: #c9a961;
  --good: #4a6b3e; --warn: #c9a961; --bad: #d93a2a;
  --grad: linear-gradient(135deg, #d93a2a, #1a1a18);
  --grad-soft: linear-gradient(135deg, #faeae6, #f5f3ea);
  --radius: 0px; --radius-sm: 0px; --radius-lg: 2px;
  --shadow: none;
  --shadow-lg: 0 1px 0 rgba(40,30,20,.12);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-serif: 'Noto Serif SC', 'Playfair Display', serif;
  --font-display: 'Noto Serif SC', 'Playfair Display', serif;
}
```

### engineering-whiteprint — 坐标纸网格+等宽

```css
:root {
  --bg: #ffffff; --bg-soft: #f8fafc; --surface: #ffffff; --surface-2: #f4f7fb;
  --border: rgba(10,30,70,.22); --border-strong: #0a1e46;
  --text-1: #0a1e46; --text-2: #3a4a6a; --text-3: #8090a8;
  --accent: #0a1e46; --accent-2: #1e5ac4; --accent-3: #c42a10;
  --good: #1a6a3a; --warn: #c47a10; --bad: #c42a10;
  --grad: linear-gradient(135deg, #0a1e46, #1e5ac4);
  --grad-soft: linear-gradient(135deg, #eaf0fb, #f4f7fb);
  --radius: 0px; --radius-sm: 0px; --radius-lg: 0px;
  --shadow: none;
  --shadow-lg: 0 0 0 1px var(--border-strong);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-mono: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  --font-display: 'JetBrains Mono', 'Inter', monospace;
}
```

### magazine-bold — 奶油+超大 Playfair+橙 spot

```css
:root {
  --bg: #f5efe2; --bg-soft: #ebe4d2; --surface: #fbf6e8; --surface-2: #ede5d0;
  --border: rgba(10,10,10,.16); --border-strong: #0a0a0a;
  --text-1: #0a0a0a; --text-2: #2a2a2a; --text-3: #6a6458;
  --accent: #ea5a1a; --accent-2: #0a0a0a; --accent-3: #c42a10;
  --good: #2a6a2a; --warn: #ea5a1a; --bad: #c42a10;
  --grad: linear-gradient(135deg, #ea5a1a, #c42a10);
  --grad-soft: linear-gradient(135deg, #fbe4d0, #f5d6c0);
  --radius: 0px; --radius-sm: 0px; --radius-lg: 2px;
  --shadow: none;
  --shadow-lg: 6px 6px 0 var(--accent);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-serif: 'Playfair Display', 'Noto Serif SC', Georgia, serif;
  --font-display: 'Playfair Display', 'Noto Serif SC', Georgia, serif;
}
```

### news-broadcast — 白+红竖条+Oswald 大写

```css
:root {
  --bg: #ffffff; --bg-soft: #f4f4f4; --surface: #ffffff; --surface-2: #ececec;
  --border: rgba(0,0,0,.14); --border-strong: #0a0a0a;
  --text-1: #0a0a0a; --text-2: #3a3a3a; --text-3: #7a7a7a;
  --accent: #e11d2d; --accent-2: #0a0a0a; --accent-3: #ffd100;
  --good: #0e7c3a; --warn: #ffd100; --bad: #e11d2d;
  --grad: linear-gradient(90deg, #e11d2d 0%, #e11d2d 100%);
  --grad-soft: linear-gradient(135deg, #fde5e7, #f4f4f4);
  --radius: 0px; --radius-sm: 0px; --radius-lg: 2px;
  --shadow: none;
  --shadow-lg: 0 4px 0 var(--accent);
  --font-sans: 'Oswald', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Oswald', 'Inter', 'Noto Sans SC', sans-serif;
}
```

### midcentury — 奶油+芥末/青/焦橙+锐利几何

```css
:root {
  --bg: #f3ead8; --bg-soft: #ebdfc4; --surface: #f9f2e0; --surface-2: #e8dcbe;
  --border: rgba(60,40,20,.18); --border-strong: rgba(60,40,20,.4);
  --text-1: #201810; --text-2: #5a4830; --text-3: #9a8868;
  --accent: #d4902a; --accent-2: #2a7a7f; --accent-3: #c7502a;
  --good: #5a7a3a; --warn: #d4902a; --bad: #c7502a;
  --grad: linear-gradient(135deg, #d4902a, #c7502a 55%, #2a7a7f);
  --grad-soft: linear-gradient(135deg, #f4e0b6, #eac7a8);
  --radius: 2px; --radius-sm: 0px; --radius-lg: 4px;
  --shadow: 4px 4px 0 rgba(40,25,10,.12);
  --shadow-lg: 6px 6px 0 rgba(40,25,10,.2), 0 10px 24px rgba(40,25,10,.14);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Playfair Display', 'Noto Serif SC', serif;
}
```

### retro-tv — 暖奶油+CRT 扫描线+琥珀橙

```css
:root {
  --bg: #f5ecd7; --bg-soft: #efe4c6; --surface: #fbf5e2; --surface-2: #efe3c2;
  --border: rgba(120,70,20,.22); --border-strong: rgba(120,70,20,.45);
  --text-1: #2a1a08; --text-2: #6b4a22; --text-3: #a68656;
  --accent: #e67e14; --accent-2: #c73a1f; --accent-3: #f2b544;
  --good: #3e8940; --warn: #e67e14; --bad: #c73a1f;
  --grad: linear-gradient(135deg, #c73a1f, #e67e14 55%, #f2b544);
  --grad-soft: linear-gradient(135deg, #fde6c4, #fbd9a0);
  --radius: 10px; --radius-sm: 6px; --radius-lg: 16px;
  --shadow: 0 6px 0 rgba(80,40,0,.12), 0 12px 28px rgba(80,40,0,.15);
  --shadow-lg: 0 10px 0 rgba(80,40,0,.15), 0 24px 50px rgba(80,40,0,.2);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Playfair Display', 'Noto Serif SC', serif;
}
```

### cyberpunk-neon — 黑+霓虹粉青黄+发光+mono

```css
:root {
  --bg: #000000; --bg-soft: #0a0a12; --surface: #0f0f1a; --surface-2: #14141f;
  --border: rgba(255,0,170,.25); --border-strong: rgba(0,240,255,.55);
  --text-1: #f5f7ff; --text-2: #b4b8d4; --text-3: #6b6e8a;
  --accent: #ff2bd6; --accent-2: #00f0ff; --accent-3: #f9f871;
  --good: #39ff14; --warn: #f9f871; --bad: #ff2bd6;
  --grad: linear-gradient(135deg, #ff2bd6, #7a00ff 50%, #00f0ff);
  --grad-soft: linear-gradient(135deg, rgba(255,43,214,.18), rgba(0,240,255,.18));
  --radius: 6px; --radius-sm: 3px; --radius-lg: 10px;
  --shadow: 0 0 0 1px rgba(255,43,214,.35), 0 0 24px rgba(255,43,214,.35), 0 0 48px rgba(0,240,255,.18);
  --shadow-lg: 0 0 0 1px rgba(0,240,255,.5), 0 0 40px rgba(0,240,255,.45), 0 0 80px rgba(255,43,214,.3);
  --font-sans: 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}
```

### vaporwave — 深紫+粉红青蓝渐变

```css
:root {
  --bg: #1a0938; --bg-soft: #261050; --surface: rgba(255,255,255,.06); --surface-2: rgba(255,255,255,.1);
  --border: rgba(255,110,199,.28); --border-strong: rgba(0,245,255,.5);
  --text-1: #fdf0ff; --text-2: #d4a8e8; --text-3: #8a6ba8;
  --accent: #ff6ec7; --accent-2: #00f5ff; --accent-3: #ffd166;
  --grad: linear-gradient(135deg, #ff6ec7 0%, #c94fff 35%, #00f5ff 100%);
  --grad-soft: linear-gradient(135deg, rgba(255,110,199,.25), rgba(0,245,255,.25));
  --radius: 18px; --radius-sm: 10px; --radius-lg: 28px;
  --shadow: 0 20px 60px rgba(255,110,199,.2), 0 0 1px rgba(0,245,255,.6);
  --shadow-lg: 0 30px 80px rgba(255,110,199,.3), 0 0 2px rgba(0,245,255,.8);
  --font-sans: 'Space Grotesk', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Space Grotesk', 'Inter', sans-serif;
}
```

### y2k-chrome — 银铬渐变+彩虹 accent+大圆角

```css
:root {
  --bg: #dfe4ec; --bg-soft: #eef1f6; --surface: rgba(255,255,255,.72); --surface-2: rgba(255,255,255,.5);
  --border: rgba(120,135,170,.32); --border-strong: rgba(80,100,140,.55);
  --text-1: #1a1f2e; --text-2: #4a536a; --text-3: #8590a6;
  --accent: #8a5cff; --accent-2: #3ccfd8; --accent-3: #ff84c4;
  --grad: linear-gradient(135deg, #b8c4d8 0%, #f5f7fb 30%, #8a9ab8 55%, #e8ecf4 80%, #6b7a95 100%);
  --grad-soft: linear-gradient(135deg, #c9e4ff, #f5d6ff 50%, #d6fffa);
  --radius: 26px; --radius-sm: 16px; --radius-lg: 36px;
  --shadow: 0 12px 30px rgba(70,90,130,.22), inset 0 1px 0 rgba(255,255,255,.9), inset 0 -1px 0 rgba(80,100,140,.2);
  --shadow-lg: 0 24px 60px rgba(70,90,130,.35), inset 0 2px 0 rgba(255,255,255,.95);
  --font-sans: 'Space Grotesk', 'Inter', 'Noto Sans SC', sans-serif;
  --font-display: 'Space Grotesk', 'Inter', sans-serif;
}
```

---

## 中国场景 4 套（codex-ppt，MIT）

> 来自 ningzimu/codex-ppt-skill（MIT License）。以下是根据其风格定义（色彩体系、字体、视觉规则）转译的完整 `:root` CSS token——格式与 html-ppt 36 套一致，axi-front-design 直接复制使用。
> ⚠️ 反俗套字体注意：这 4 套的 `--font-sans` / `--font-display` 使用 Source Han Sans / Noto Sans SC，不含 Inter/Roboto——符合合集反俗套规则。

### party-gov-red — 党政机关汇报 · 庄严权威

```css
:root {
  --bg: #fff9f2; --bg-soft: #fff3e6; --surface: #ffffff; --surface-2: #fdf5ec;
  --border: rgba(196,30,58,.12); --border-strong: rgba(196,30,58,.24);
  --text-1: #1a0a0a; --text-2: #4a3830; --text-3: #8c7b70;
  --accent: #c41e3a; --accent-2: #d6a84b; --accent-3: #8b1a2b;
  --good: #2e7d32; --warn: #d6a84b; --bad: #c41e3a;
  --grad: none;
  --grad-soft: none;
  --radius: 2px; --radius-sm: 1px; --radius-lg: 4px;
  --shadow: none;
  --shadow-lg: none;
  --font-sans: 'Noto Sans SC', 'Microsoft YaHei', 'Source Han Sans SC', sans-serif;
  --font-display: 'Noto Serif SC', 'SimHei', 'Source Han Serif SC', serif;
  --font-serif: 'Noto Serif SC', 'Source Han Serif SC', serif;
  --letter-tight: -.02em;
}
```

### academic-defense — 科研答辩/基金申请 · 正式学术

```css
:root {
  --bg: #ffffff; --bg-soft: #f5f8fc; --surface: #ffffff; --surface-2: #eef2f8;
  --border: rgba(0,63,143,.10); --border-strong: rgba(0,63,143,.20);
  --text-1: #0a1628; --text-2: #3a4a5c; --text-3: #6b7d91;
  --accent: #003f8f; --accent-2: #0b5cad; --accent-3: #b5121b;
  --good: #1b8c3e; --warn: #d97706; --bad: #b5121b;
  --grad: none;
  --grad-soft: none;
  --radius: 2px; --radius-sm: 1px; --radius-lg: 4px;
  --shadow: 0 2px 8px rgba(0,63,143,.06);
  --shadow-lg: 0 8px 24px rgba(0,63,143,.12);
  --font-sans: 'Source Han Sans SC', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-display: 'Source Han Serif SC', 'Noto Serif SC', 'SimHei', serif;
  --font-serif: 'Source Han Serif SC', 'Noto Serif SC', serif;
  --letter-tight: -.02em;
}
```

### courseware-blue — 教学课件/技术培训 · 清晰可信

```css
:root {
  --bg: #ffffff; --bg-soft: #eaf3fb; --surface: #ffffff; --surface-2: #eaf3fb;
  --border: rgba(11,46,109,.08); --border-strong: rgba(11,46,109,.18);
  --text-1: #0a1628; --text-2: #2e405b; --text-3: #5c7292;
  --accent: #0b2e6d; --accent-2: #1769aa; --accent-3: #245c8a;
  --good: #1a9e4f; --warn: #de8800; --bad: #d1383a;
  --grad: none;
  --grad-soft: linear-gradient(135deg, #eaf3fb, #ffffff);
  --radius: 6px; --radius-sm: 4px; --radius-lg: 10px;
  --shadow: 0 2px 12px rgba(11,46,109,.08);
  --shadow-lg: 0 12px 36px rgba(11,46,109,.16);
  --font-sans: 'Noto Sans SC', 'Microsoft YaHei', 'Source Han Sans SC', sans-serif;
  --font-display: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-serif: 'Noto Serif SC', serif;
  --letter-tight: -.025em;
}
```

### handdrawn-explainer — 手绘技术解释 · 亲和轻压

```css
:root {
  --bg: #fcfbf7; --bg-soft: #f5f2ea; --surface: #fcfbf7; --surface-2: #f0ede4;
  --border: rgba(47,52,55,.10); --border-strong: rgba(47,52,55,.18);
  --text-1: #2f3437; --text-2: #5c6063; --text-3: #8f9294;
  --accent: #bfd7f1; --accent-2: #c9dfc3; --accent-3: #f2c9c9;
  --good: #7daf7c; --warn: #e8c766; --bad: #d98b8b;
  --grad: none;
  --grad-soft: none;
  --radius: 3px; --radius-sm: 2px; --radius-lg: 6px;
  --shadow: none;
  --shadow-lg: none;
  --font-sans: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-display: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-serif: 'Noto Serif SC', serif;
  --letter-tight: -.01em;
}
```

---

## MBB 咨询 1 套（mbb-decks 视觉系统，MIT）

> `mbb-consulting` 是把 mbb-decks 硬编码颜色（`#051C2C` 海军蓝、`#2251FF` 电光蓝、`#FFFFFF` 白底、Georgia 标题、Calibri 正文）转译为 design-system token，供执行层在咨询场景直接使用。

### mbb-consulting — MBB 咨询 · 董事会/高管汇报

```css
:root {
  --bg: #ffffff; --bg-soft: #f7f8fa; --surface: #ffffff; --surface-2: #f0f1f3;
  --border: #e5e7eb; --border-strong: rgba(5,28,44,.24);
  --text-1: #051c2c; --text-2: #1a1a1a; --text-3: #949ba8;
  --accent: #2251ff; --accent-2: #051c2c; --accent-3: #64748b;
  --good: #0e9f6e; --warn: #d97706; --bad: #dc2626;
  --grad: none;
  --grad-soft: none;
  --radius: 0px; --radius-sm: 0px; --radius-lg: 0px;
  --shadow: none;
  --shadow-lg: none;
  --font-sans: 'Calibri', 'Noto Sans SC', sans-serif;
  --font-display: 'Georgia', 'Noto Serif SC', serif;
  --font-serif: 'Georgia', 'Noto Serif SC', serif;
}
```

---

## 设计语言 → 主题映射表

> 使 claude-design 产出的 10 种设计语言方向能与 design-system 41 套主题落地。

| 设计语言 | 推荐主题（首选） | 备选主题 |
|---------|----------------|---------|
| 瑞士编辑式 | `swiss-grid` | `corporate-clean` / `minimal-white` |
| 包豪斯几何 | `bauhaus` | `neo-brutalism` / `memphis-pop` |
| Kenya Hara 留白 | `japanese-minimal` | `minimal-white` / `editorial-serif` |
| Dieter Rams 工业 | `engineering-whiteprint` | `minimal-white` / `corporate-clean` |
| 杂志编辑式 | `magazine-bold` | `editorial-serif` / `news-broadcast` |
| Zine / risograph | `neo-brutalism` | `memphis-pop` / `midcentury` |
| Field.io / 动效诗学 | `aurora` | `glassmorphism` / `cyberpunk-neon` |
| 粗野主义 web | `sharp-mono` | `terminal-green` / `swiss-grid` |
| Sagmeister 实验 | `vaporwave` | `cyberpunk-neon` / `y2k-chrome` |
| Y2K 未来复古 | `y2k-chrome` | `vaporwave` / `rainbow-gradient` |
| MBB 咨询 | `mbb-consulting` | `corporate-clean` |

---

来源：
- 36 套 html-ppt 主题 token 值来自 [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) `assets/themes/*.css`（MIT License）
- 4 套中国场景来自 [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) 风格定义（MIT License）
- MBB 咨询主题基于 [floflo11/mbb-decks](https://github.com/floflo11/mbb-decks) 视觉系统转译（MIT License）
