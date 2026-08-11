# Native Motion

The converter captures supported browser entrance motion before it freezes the
page for static layout measurement. It then emits PresentationML `p:timing`
that PowerPoint recognizes as native animation. The final visual state remains
the editable slide state, so a viewer that does not play animations still sees
the intended layout.

## Automatic Capture

CSS Animations and Web Animations API effects are eligible when they have one
iteration, two or more keyframes, and target a convertible HTML element.

| Browser signal | Native PPT effect |
| --- | --- |
| `opacity: 0` to `opacity: 1` | Fade entrance |
| `translateX` / `translateY` to the final position | Directional wipe entrance |
| `scale(...)` to the final size | Zoom-style entrance |
| `rotate(...)` | Spin emphasis |

The browser duration and delay are preserved in milliseconds. Effects with
infinite/repeating iterations, Canvas/WebGL targets, pseudo-elements, and
multi-stage transforms remain static fallbacks.

## Explicit Motion

Use `data-pptx-motion` when the HTML motion is created by a library the browser
cannot expose through `getAnimations()`, or when a deliberate native effect is
preferred:

```html
<h1 data-pptx-motion="fade">A native PowerPoint entrance</h1>
<div data-pptx-motion="wipe-left" data-pptx-duration="700" data-pptx-delay="120">...</div>
<div data-pptx-motion="zoom">...</div>
<div data-pptx-motion="spin">...</div>
```

Supported values are `fade`, `wipe-left`, `wipe-right`, `wipe-up`,
`wipe-down`, `zoom`, and `spin`. The element must produce one native text box,
shape, or picture in the converted slide. A composite element is safely
skipped when no single native target exists.

## Workflow Gate

Record native motion in `effects-scan.json` as `type: "native-motion"` and
list each slide's chosen behavior. During delivery, inspect the static audit as
usual and, on Windows with PowerPoint installed, run the COM recognition test:

```powershell
D:\GPTworkspace\.venv\Scripts\python.exe -m unittest tests.test_motion -v
```
