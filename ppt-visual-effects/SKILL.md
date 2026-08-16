---
name: "ppt-visual-effects"
description: "PPT 执行层视觉增强引擎。在做幻灯片时，对每一页主动判断是否需要嵌入ECharts图表、Shadertoy着色器、Three.js 3D、Spline交互或Matter.js物理动画，并直接生成代码。触发：ppt-workflow执行层展开页面时自动介入。"
---

# PPT Visual Effects — 主动视觉增强引擎

你是 `ppt-workflow` 执行层的视觉增强模块。**本 skill 由 ppt-workflow 在执行层 Step 6 显式加载一次**，随后对每一页已展开的 HTML 逐个应用扫描——每检查一页，判断该页是否需要嵌入视觉增强库，并直接生成对应代码。

## 触发时机

由 `ppt-workflow` 第 3 层（执行层）Step 6 加载一次后逐页扫描注入。加载后对 deck 中每一页 `.slide` 依次执行以下扫描，不是只扫描一页。

## 主动扫描规则（逐页判断）

对每张幻灯片，按以下决策树判断：

```
页面内容 → 需要用什么增强？

封面/过渡页/CTA 页（深色背景）
  └── 自动注入 Shadertoy 背景着色器
      ⚠️ 例外：如果深色封面页主内容区文字占比 > 80%（纯大标题+副标题，无图无品牌底色装饰），跳过着色器——大号文字+留白本身已是足够的视觉语言
      搜索关键词：ocean waves / aurora / gradient flow / particle field
      生成：<script type="x-shader/x-fragment"> + 适配品牌色的着色器代码

数据展示页（有数字、对比、趋势、占比）
  └── 自动注入 ECharts 图表
      选择规则：单个大数字 → 环形图+中心KPI | 趋势 → 主题河流图
               分类占比 → 南丁格尔玫瑰图 | 多维评分 → 雷达图
      生成：echarts.init() + setOption() 完整配置

需要"元气/活力/能量"视觉表达
  └── 手写 Canvas 粒子系统（~60行，不引入外部库）
      粒子行为：从中心向四周扩散 / 绕轨道旋转 / 随鼠标微动

需要 3D 场景（产品展示、空间感概念、海洋/地形隐喻）
  └── 优先判断：做得到吗？
      ├── 简单抽象 3D（几何体旋转、波浪曲面）→ 用 Three.js（importmap）
      ├── 需要快速出效果的交互式 3D → 用 Spline（<spline-viewer> 组件）
      └── 太复杂或没明确需求 → 不加，保持洁净

需要物理碰撞感（"碰撞""堆积""传递""活力弹跳"概念）
  └── 注入 Matter.js
      场景模式：Ball Pool（活力）/ Newton's Cradle（传递）/ Stack（积累）
      生成：Matter.Engine.create() → 渲染循环
```

## 工作流

```
Step 1: 扫描页面内容
  - 读每页的文本和标题
  - 识别：数据数字？深色背景？物理隐喻？3D 需求？

Step 2: 匹配 → 生成代码
  - 匹配到一种增强 → 直接写对应的 <script> 或 <canvas> 代码块
  - 代码必须嵌入到该页的 .slide 容器内
  - 不能只写"建议用 ECharts"——必须生成可运行的完整代码

Step 3: 遵守约束
  - 用 CDN 引入，不用 npm install
  - 颜色必须使用设计系统 CSS 变量：`var(--accent)` / `var(--accent-2)` / `var(--accent-3)` / `var(--bg)` / `var(--text-1)` 等。**严禁硬编码 hex 或使用 --navy/--coral 等不存在的变量名**。着色器颜色从当前主题 :root 变量读取：JS 中用 `getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()` 解析 hex → RGB
  - Canvas/WebGL 元素设 pointer-events: none（不挡翻页）
  - 幻灯片隐藏时暂停动画（监听 .slide:not(.active)）

Step 4: 自检
  - 代码能在浏览器直接运行？
  - 没有破坏原有幻灯片布局？
  - 颜色和设计系统一致？
```

## 各库嵌入模板

### Shadertoy 背景着色器（封面/过渡页/CTA）

```html
<script src="https://cdn.jsdelivr.net/npm/shader-web-background@0.4.2/dist/shader-web-background.min.js"></script>
<script type="x-shader/x-fragment" id="slide-N-bg">
precision highp float;
uniform vec3 iResolution;
uniform float iTime;
uniform vec3 uColor1;  // 品牌主色
uniform vec3 uColor2;  // 品牌强调色

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    // ... 着色器逻辑 ...
}

void main() { mainImage(gl_FragColor, gl_FragCoord.xy); }
</script>
<script>
shaderWebBackground.shade({
    shaders: { image: { id: 'slide-N-bg' } },
    uniforms: {
        uColor1: [0.039, 0.165, 0.369],
        uColor2: [1.0, 0.325, 0.286]
    }
});
</script>
```

### ECharts 数据图表（数据页）

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<div id="chart-slide-N" style="width:600px;height:400px;position:relative;z-index:1"></div>
<script>
(function() {
  const dom = document.getElementById('chart-slide-N');
  if (!dom) return;
  const chart = echarts.init(dom);
  chart.setOption({
    // 配色用品牌 token
    color: ['#0A2A5E', '#FF5349', '#7A8A9E', '#E2E8F0'],
    // ... 完整配置 ...
  });
  // 幻灯片切换时 resize
  const observer = new MutationObserver(() => {
    if (dom.closest('.slide.active')) chart.resize();
  });
})();
</script>
```

### Canvas 粒子系统（活力/氛围页）

```html
<canvas id="particles-slide-N" style="position:absolute;inset:0;pointer-events:none;z-index:0"></canvas>
<script>
(function() {
  const canvas = document.getElementById('particles-slide-N');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 1280; canvas.height = 720;

  const particles = Array.from({length: 60}, () => ({
    x: Math.random() * 1280, y: Math.random() * 720,
    vx: (Math.random() - 0.5) * 1.2, vy: (Math.random() - 0.5) * 1.2,
    r: Math.random() * 3 + 1,
    alpha: Math.random() * 0.4 + 0.1
  }));

  function draw() {
    const slide = canvas.closest('.slide');
    if (!slide || !slide.classList.contains('active')) {
      requestAnimationFrame(draw); return;
    }
    ctx.clearRect(0, 0, 1280, 720);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > 1280) p.vx *= -1;
      if (p.y < 0 || p.y > 720) p.vy *= -1;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(10,42,94,${p.alpha})`; ctx.fill();
    });
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
```

### Three.js 3D 场景（概念页）

```html
<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.170/build/three.module.js" } }
</script>
<script type="module">
import * as THREE from 'three';
const canvas = document.getElementById('three-slide-N');
if (!canvas) throw new Error('No canvas');

const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setSize(1280, 720);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1280/720, 0.1, 100);
camera.position.z = 5;

// 场景构建（~150行）

function animate() {
  const slide = canvas.closest('.slide');
  if (slide && slide.classList.contains('active')) {
    renderer.render(scene, camera);
  }
  requestAnimationFrame(animate);
}
animate();
</script>
```

### Spline 3D 交互模型

```html
<script type="module" src="https://unpkg.com/@splinetool/viewer@1.9/build/spline-viewer.js"></script>
<spline-viewer
  url="https://prod.spline.design/SCENE-ID/scene.splinecode"
  style="position:absolute;inset:0;z-index:0;pointer-events:none">
</spline-viewer>
```

**注意**: Spline 场景需要提前在 spline.design 创建并导出。如果用户没有现成的 `.splinecode` URL，改用 Three.js 手写场景。

### Matter.js 物理动画（互动/概念页）

```html
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.20.0/build/matter.min.js"></script>
<script>
(function() {
  const { Engine, Render, World, Bodies, Body, Events } = Matter;
  const container = document.getElementById('matter-slide-N');
  if (!container) return;

  const engine = Engine.create();
  const render = Render.create({
    element: container,
    engine: engine,
    options: { width: 800, height: 500, wireframes: false,
               background: 'transparent' }
  });

  // 场景构建

  Render.run(render);
  const runner = setInterval(() => Engine.update(engine, 1000/60), 16);

  // 幻灯片隐藏时暂停
  const observer = new MutationObserver(() => {
    const active = container.closest('.slide')?.classList.contains('active');
    if (active) { /* resume */ } else { /* pause */ }
  });
})();
</script>
```

## 约束规则

| 规则 | 说明 |
|------|------|
| CDN 引入 | 所有库通过 jsdelivr/unpkg CDN 引入，不需要 npm install |
| 颜色系统 | 使用设计系统 CSS 变量（`var(--accent)` / `var(--accent-2)` / `var(--accent-3)` / `var(--bg)` / `var(--text-1/2/3)`），不硬编码 hex |
| 指针穿透 | Canvas/WebGL 默认 `pointer-events: none`，不拦截翻页事件 |
| 惰性渲染 | `.slide:not(.active)` 时暂停动画循环，节省 CPU |
| 代码量控制 | 单个嵌入 ≤ 200 行，超过说明需求太复杂，降级为装饰背景 |
| 优先判断必要性 | 不是每页都需要增强。纯文字排版页不加，破坏留白美学 |
| 明确不触发 | 白底纯文字页（主内容区文字占比 > 80% 且无图/数据/图表）、已经有复杂排版的对比页、附录/引用页 |

## 与 ppt-workflow 的关系

```
ppt-workflow 第 3 层执行时:
  axi-front-design 展开第 N 页
    → ppt-visual-effects 扫描第 N 页
      → 匹配到需要增强？是 → 生成代码嵌入
                         否 → 跳过
    → 第 N+1 页
```

## 与 mbb-decks 图表选择的职责划分

当同一页同时有 ghost deck 的"图表建议"和 ppt-visual-effects 的自动扫描时：
- **ghost deck 图表建议优先**：如果 mbb-decks 标注了图表类型（waterfall / bar / scatter 等），按标注实现 ECharts 配置
- **无标注时用本 skill 的决策树**：扫描页面内容公式化选图
- **冲突时以 ghost deck 为准**，本 skill 只做实现不重新选型

## 来源

- ECharts: https://echarts.apache.org/ Apache 2.0
- Three.js: https://threejs.org/ MIT
- shader-web-background: https://github.com/xemantic/shader-web-background MIT
- Matter.js: https://brm.io/matter-js/ MIT
- Spline: https://spline.design/ Free/Paid
