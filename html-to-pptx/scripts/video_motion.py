"""Record explicitly marked HTML slides to MP4 and embed them in PowerPoint.

This is the offline fallback for effects that PresentationML cannot represent,
such as WebGL, shaders, particles, and arbitrary JavaScript. The resulting
movie is embedded in the PPTX and plays in PowerPoint; no browser is launched
during the presentation.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


VIDEO_SPECS_JS = r"""
() => {
  const asNumber = (value, fallback, min, max) => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, Math.round(n))) : fallback;
  };
  return (window.__pptxSlides || []).flatMap((slide, slideIndex) => {
    if (!slide.hasAttribute('data-pptx-video')) return [];
    const trigger = String(slide.dataset.pptxVideoTrigger || 'auto').toLowerCase();
    return [{
      slideIndex,
      duration: asNumber(slide.dataset.pptxVideoDuration || slide.dataset.pptxDuration, 2000, 250, 30000),
      fps: asNumber(slide.dataset.pptxVideoFps, 20, 6, 30),
      trigger: trigger === 'click' ? 'click' : 'auto',
      loop: String(slide.dataset.pptxVideoLoop || '').toLowerCase() === 'true',
    }];
  });
}
"""


RESTART_SLIDE_ANIMATIONS_JS = r"""
(slideIndex) => {
  const slide = (window.__pptxSlides || [])[slideIndex];
  if (!slide) return;
  for (const animation of document.getAnimations({subtree: true})) {
    const target = animation.effect && animation.effect.target;
    if (!(target instanceof Element) || !(target === slide || slide.contains(target))) continue;
    try { animation.cancel(); animation.play(); } catch (_) { /* non-seekable animation */ }
  }
}
"""


PAUSE_SLIDE_ANIMATIONS_JS = r"""
(slideIndex) => {
  const slide = (window.__pptxSlides || [])[slideIndex];
  if (!slide) return 0;
  let count = 0;
  for (const animation of document.getAnimations({subtree: true})) {
    const target = animation.effect && animation.effect.target;
    if (!(target instanceof Element) || !(target === slide || slide.contains(target))) continue;
    try { animation.pause(); count++; } catch (_) { /* animation remains realtime */ }
  }
  return count;
}
"""


SEEK_SLIDE_ANIMATIONS_JS = r"""
(args) => {
  const slide = (window.__pptxSlides || [])[args.slideIndex];
  if (!slide) return;
  for (const animation of document.getAnimations({subtree: true})) {
    const target = animation.effect && animation.effect.target;
    if (!(target instanceof Element) || !(target === slide || slide.contains(target))) continue;
    try { animation.currentTime = args.time; } catch (_) { /* animation remains realtime */ }
  }
}
"""


def ffmpeg_executable() -> str | None:
    """Return an explicit or PATH-discoverable FFmpeg executable."""
    configured = os.environ.get("PPT_FFMPEG_EXECUTABLE", "").strip()
    if configured and Path(configured).is_file():
        return configured
    return shutil.which("ffmpeg")


def _ffmpeg_command(executable: str, frames_dir: Path, fps: int, output: Path) -> list[str]:
    return [
        executable, "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output),
    ]


def _fit_viewport(page) -> None:
    dimensions = page.evaluate("""() => {
      const target = document.querySelector('[data-pptx-target]');
      if (!target) return null;
      const rect = target.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }""")
    if not dimensions or dimensions["width"] <= 0 or dimensions["height"] <= 0:
        raise RuntimeError("video capture: active slide has no usable dimensions")
    page.set_viewport_size({
        "width": max(1, math.ceil(dimensions["width"])),
        "height": max(1, math.ceil(dimensions["height"])),
    })


def _record_frames(page, spec: dict[str, Any], frames_dir: Path) -> None:
    from adapters import ACTIVATE_JS, REASSERT_TARGET_POSITION_JS

    page.evaluate(ACTIVATE_JS, spec["slideIndex"])
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    _fit_viewport(page)
    page.evaluate(REASSERT_TARGET_POSITION_JS)
    page.evaluate(RESTART_SLIDE_ANIMATIONS_JS, spec["slideIndex"])
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    seekable_count = page.evaluate(PAUSE_SLIDE_ANIMATIONS_JS, spec["slideIndex"])

    target = page.locator("[data-pptx-target]").first
    count = max(2, math.ceil(spec["duration"] * spec["fps"] / 1000))
    started = time.monotonic()
    for index in range(count):
        if seekable_count:
            frame_time = round(index * spec["duration"] / (count - 1))
            page.evaluate(SEEK_SLIDE_ANIMATIONS_JS, {"slideIndex": spec["slideIndex"], "time": frame_time})
            page.evaluate("() => new Promise(r => requestAnimationFrame(r))")
        else:
            target_seconds = index / spec["fps"]
            remaining = target_seconds - (time.monotonic() - started)
            if remaining > 0:
                page.wait_for_timeout(math.ceil(remaining * 1000))
        (frames_dir / f"frame_{index:04d}.png").write_bytes(target.screenshot(type="png"))


def record_marked_slide_videos(html_path: Path, out_dir: Path) -> list[dict[str, Any]]:
    """Record each ``data-pptx-video`` slide to a self-contained H.264 MP4."""
    executable = ffmpeg_executable()
    if not executable:
        raise RuntimeError(
            "video motion requires FFmpeg with libx264. Install FFmpeg or set "
            "PPT_FFMPEG_EXECUTABLE to its ffmpeg executable."
        )

    from adapters import DISCOVER_JS
    from measure import open_deck_page

    html_path = Path(html_path).resolve()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with open_deck_page(html_path) as page:
        page.evaluate(DISCOVER_JS)
        specs = page.evaluate(VIDEO_SPECS_JS) or []
        for spec in specs:
            with tempfile.TemporaryDirectory(prefix="h2p_video_frames_") as directory:
                frames_dir = Path(directory)
                _record_frames(page, spec, frames_dir)
                output = out_dir / f"slide-{spec['slideIndex'] + 1:02d}.mp4"
                result = subprocess.run(
                    _ffmpeg_command(executable, frames_dir, spec["fps"], output),
                    capture_output=True, text=True, timeout=120,
                )
            if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
                detail = (result.stderr or result.stdout).strip()[:500]
                raise RuntimeError(f"FFmpeg failed for slide {spec['slideIndex'] + 1}: {detail}")
            results.append({**spec, "path": str(output.resolve())})
    return results


def embed_slide_videos(pptx_path: Path, videos: list[dict[str, Any]]) -> list[int]:
    """Embed MP4 files as full-slide PowerPoint media objects on Windows."""
    if not videos:
        return []
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("embedding video requires Windows PowerPoint and pywin32") from exc

    pptx_path = Path(pptx_path).resolve()
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("PowerPoint.Application")
    embedded = []
    try:
        document = app.Presentations.Open(str(pptx_path), False, False, False)
        try:
            for item in videos:
                index = int(item["slideIndex"]) + 1
                video_path = Path(item["path"])
                if index < 1 or index > document.Slides.Count or not video_path.is_file():
                    continue
                slide = document.Slides.Item(index)
                media = slide.Shapes.AddMediaObject2(
                    str(video_path), False, True, 0, 0,
                    document.PageSetup.SlideWidth, document.PageSetup.SlideHeight,
                )
                settings = media.AnimationSettings.PlaySettings
                settings.PlayOnEntry = item.get("trigger") == "auto"
                settings.LoopUntilStopped = bool(item.get("loop"))
                settings.RewindMovie = True
                embedded.append(index)
            document.Save()
        finally:
            document.Close()
    finally:
        app.Quit()
    return embedded
