# 🎬 REELS GO SKRRRRRRRRRRRRRRRRRRr

> Wide-screen gameplay ➡️ Premium 9:16 vertical clips. One-click magic. ✨

---

## 🔥 Key Highlights

* 🤖 **Auto-FFmpeg:** Missing the backend? It automatically downloads & installs FFmpeg on first launch.
* 🎵 **Outro SFX:** Drag-and-drop an audio file (like `quack.m4a`) to inject it seamlessly at the very end.
* 🎯 **Smart Split-Canvas:** Scales, blurs the background, and sharpens the zoomed foreground automatically.
* 💾 **Infinite Memory:** Saves your timestamps, custom zoom values, and folder locations.

---

## 🎨 Interface Preview

```text
 🎬 Shorts & Reels Studio
 ┌─────────────────────────────────────────┐
 │ 📥 DRAG & DROP GAMEPLAY VIDEO HERE      │
 ├─────────────────────────────────────────┤
 │ 🎵 DRAG & DROP ENDING SFX HERE          │
 ├─────────────────────────────────────────┤
 │  Clip Start: [ 00:01:26 ]               │
 │  Clip End:   [          ] (Auto-End)    │
 │  Zoom Width: [   1700   ]               │
 ├─────────────────────────────────────────┤
 │ ⚡ Compiling Video... 42% [████░░░░░░] │
 └─────────────────────────────────────────┘


## 🪟 Standalone Windows EXE (no prerequisites needed)

- Go to **Actions → Build Windows EXE** and download the `auto-reeler-windows-exe` artifact.
- Extract and run `app.exe` on Windows (no Python/FFmpeg install required).

## Useful commands (local development)

```bash
# Clone & enter repo
git clone https://github.com/your-username/auto-reeler.git && cd auto-reeler

# Install dependencies
pip install tkinterdnd2 ffmpeg-python ffmpeg-progress-yield

# Run app
python app.py

# Build executable (after placing ffmpeg.exe + ffprobe.exe in ./ffmpeg_bin)
pip install pyinstaller
pyinstaller --clean --noconfirm app.spec
```
