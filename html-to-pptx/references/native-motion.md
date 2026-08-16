# Native Motion

The converter captures supported browser motion before it freezes the page for
static layout measurement. It then emits PresentationML `p:timing` that
PowerPoint recognizes as native animation. The final visual state remains the
editable slide state, so a viewer that does not play animations still sees the
intended layout.

## Automatic Capture

CSS Animations and Web Animations API effects are eligible when they have one
iteration, two or more keyframes, and target a convertible HTML element.

| Browser signal | Native PPT effect |
| --- | --- |
| `opacity: 0` to `opacity: 1` | Fade entrance |
| `translateX` / `translateY` to the final position | Relative `p:animMotion` path |
| `scale(...)` to the final size | `p:animScale` |
| `rotate(...)` | `p:animRot` |

The browser duration and delay are preserved in milliseconds. Effects with
infinite/repeating iterations, Canvas/WebGL targets, pseudo-elements, and 3D
transforms remain static fallbacks. A multi-property 2D transform is split
into parallel native behaviors automatically. For exact multi-stage
choreography, use the plan contract below.

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

## Composable Motion Plans

`data-pptx-motion-plan` accepts a JSON array. Each entry becomes one native
timeline effect, so several entries can target the same object. `click` starts
the next main-sequence item, `with` runs it alongside the preceding item, and
`after` starts it when the preceding item completes. Different objects can use
different delays for staggered choreography.

```html
<div data-pptx-motion-plan='[
  {"effect":"fade", "duration":300, "trigger":"click"},
  {"effect":"motion", "path":"M 0 0 L 0.18 -0.08 E", "duration":650, "trigger":"with"},
  {"effect":"scale", "from":[80,80], "to":[115,115], "duration":650, "trigger":"with"},
  {"effect":"rotate", "by":360, "duration":650, "trigger":"with"},
  {"effect":"fade", "duration":250, "trigger":"after"}
]'>Hero</div>
```

Plan effects are `fade`, `wipe-left`, `wipe-right`, `wipe-up`, `wipe-down`,
`zoom`, `spin`, `motion`, `scale`, and `rotate`.

- `motion.path` is a PowerPoint relative path. To animate from an offset into
  the static final position, use `M <x> <y> L 0 0 E`.
- `scale.from` and `scale.to` are percentages: `[80, 80]` means 80% and
  `[100, 100]` means the unchanged final size.
- `rotate.by` is in degrees. Use `rotate.from`/`rotate.to` when the animation
  should end at the static final rotation.
- `duration` and `delay` are milliseconds. The element must map to one native
  shape, text box, or picture; otherwise the plan is reported as skipped.

The generated nodes are `p:animMotion`, `p:animScale`, `p:animRot`, and
`p:animEffect` inside a PowerPoint `p:timing` tree. The implementation is an
independent PresentationML writer; external SVG/SMIL converters are useful
references but are not copied because their licenses may not be compatible.

## Semantic Groups and Text Builds

Apply a motion marker to the smallest **semantic group**, not an arbitrary
child. A card is normally one group: its background shape, illustration, and
copy enter together on one click. Marking only the text or only the image
makes the narrative look disconnected. When an image is deliberate static
context, keep it outside the marked group and animate the sequence elements
that the presenter is explaining.

- Each independently explained item gets its own click group; its generated
  background and text effects run together (`with previous`).
- A non-empty text box uses PowerPoint's ordinary `p:spTgt` target and a
  `p:bldP` **without** `animBg`. `animBg="1"` is only for a background shape.
  Setting it on text animates the transparent text-box surface rather than the
  glyphs, which can leave the audience seeing no text animation.
- Do not hand-write `p:bg` targets or force `txEl` targets. They can look
  present in the Animation Pane yet fail in desktop Slide Show mode.
- Pages that act as a stable reading or scanning endpoint should explicitly
  record `visualEffect.status: "skipped"`; animation is not a default.

## Embedded Video Motion

For WebGL, Canvas, shaders, particles, video compositing, or arbitrary
JavaScript that cannot be represented as native PresentationML, mark the whole
slide with `data-pptx-video` and convert with `--embed-video-motion`:

```html
<section class="slide" data-pptx-slide data-pptx-video
  data-pptx-video-duration="2400"
  data-pptx-video-fps="24"
  data-pptx-video-trigger="auto">
  <!-- Three.js, Canvas, shader, or other non-native motion -->
</section>
```

The converter records the declared slide, encodes an H.264 MP4, and asks
PowerPoint to embed it as a full-slide media object. Playback happens entirely
inside PowerPoint and does not open a browser or require network access.
`data-pptx-video-trigger="click"` leaves playback under the presenter's click;
`auto` starts it on slide entry. `data-pptx-video-loop="true"` enables looping.

This mode requires FFmpeg with `libx264`, Windows PowerPoint, and `pywin32`.
Set `PPT_FFMPEG_EXECUTABLE` when FFmpeg is not on `PATH`. The visual result is
preserved, but the embedded motion is a video rather than editable or
interactive PowerPoint objects.

## Workflow Gate

Record native motion in `effects-scan.json` as `type: "native-motion"` and
list each slide's chosen behavior. Conversion produces `motion-audit.json`;
it checks click groups, synchronized effects, invalid `p:bg` targets, and text
builds that incorrectly use `animBg`. On Windows it also asks PowerPoint COM to
recognize the main sequence. During delivery, attach that file in
`delivery.motionAudit`, hash it against the final PPTX, cover every animated
slide, and record a real Slide Show observation with evidence. COM recognition,
static HTML/PPT comparison, and the Animation Pane are supplementary checks;
none is a substitute for observed playback.

Run the focused regression suite when changing native motion:

```powershell
D:\GPTworkspace\.venv\Scripts\python.exe -m unittest tests.test_motion -v
```
