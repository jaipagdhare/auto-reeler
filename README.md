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


 Useful commands
# Clone & enter repo
git clone [https://github.com/your-username/influenca.git](https://github.com/your-username/influenca.git) && cd influenca

# Install dependencies
pip install tkinterdnd2 ffmpeg-python ffmpeg-progress-yield

# Run it!
python app.py

# Install compiler
pip install pyinstaller

# Package into a single file with embedded assets
pyinstaller --noconsole --onefile --add-data "ffmpeg_bin;ffmpeg_bin" --collect-all tkinterdnd2 app.py
