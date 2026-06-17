import os
import sys
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import ffmpeg
from ffmpeg_progress_yield import FfmpegProgress

# ── RESOLVE BUNDLED FFMPEG PATHS ─────────────────────────────────────────────
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

FFMPEG_BIN  = resource_path("ffmpeg_bin")
FFMPEG_EXE  = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
FFPROBE_EXE = os.path.join(FFMPEG_BIN, "ffprobe.exe")

# Also update PATH so any indirect subprocess calls work
os.environ["PATH"] = FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")

# Config lives in user home so the bundled exe can write to it
if hasattr(sys, '_MEIPASS'):
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".auto_reeler_config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".app_config.json")

# ── CORE VIDEO & AUDIO MIXING LOGIC ──────────────────────────────────────────
def auto_format_clip(input_file, output_file, start_time, duration, zoom_width=2400, end_sound=None, progress_callback=None):
    try:
        duration_s = float(duration)
        
        input_stream = ffmpeg.input(input_file, ss=start_time, t=duration_s)
        video_branches = input_stream.video.split()
        bg_branch = video_branches[0]
        fg_branch = video_branches[1]

        background = (
            bg_branch
            .filter('scale', -2, 1920)
            .filter('crop', 1080, 1920)
            .filter('boxblur', lr=20, lp=2)
        )

        foreground = (
            fg_branch
            .filter('scale', zoom_width, -2)
            .filter('crop', 1080, 'in_h', '(in_w-1080)/2', 0)
        )

        combined_video = ffmpeg.overlay(background, foreground, x=0, y='(H-h)/2')
        fade_start = duration_s - 1
        if fade_start < 0:
            fade_start = 0
            
        final_video = combined_video.filter('fade', type='out', start_time=fade_start, duration=1)
        main_audio = input_stream.audio
        
        if end_sound and os.path.exists(end_sound):
            try:
                sound_probe = ffmpeg.probe(end_sound, cmd=FFPROBE_EXE)
                sound_duration = float(sound_probe['format']['duration'])
            except Exception:
                sound_duration = 1.0
            
            delay_start_ms = int(max(0, (duration_s - sound_duration)) * 1000)
            sfx_stream = ffmpeg.input(end_sound).audio.filter('adelay', f"{delay_start_ms}|{delay_start_ms}")
            final_audio = ffmpeg.filter([main_audio, sfx_stream], 'amix', inputs=2, duration='first')
        else:
            final_audio = main_audio

        cmd = (
            ffmpeg.output(
                final_video, final_audio, output_file,
                vcodec='libx264', acodec='aac', pix_fmt='yuv420p', r=60, **{'b:v': '8M'}
            )
            .overwrite_output()
            .compile()
        )

        # Use the bundled ffmpeg executable explicitly
        cmd[0] = FFMPEG_EXE

        with FfmpegProgress(cmd) as ff:
            for progress in ff.run_command_with_progress():
                if progress_callback:
                    progress_callback(progress)

        return True
    except Exception as e:
        print("\n=== FFmpeg Render Failure Details ===")
        print(e)
        print("=====================================\n")
        return False

# ── HELPER UTILITIES ─────────────────────────────────────────────────────────
def clean_dropped_path(raw_path):
    path = raw_path.strip()
    if path.startswith('{') and path.endswith('}'):
        path = path[1:-1]
    if path.startswith('file:///'):
        path = path[8:]
    elif path.startswith('file://'):
        path = path[7:]
    return os.path.normpath(path)

def time_to_seconds(t_str):
    if not t_str.strip():
        return None
    try:
        parts = list(map(int, t_str.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except ValueError:
        return None

def get_video_duration(input_file):
    try:
        probe = ffmpeg.probe(input_file, cmd=FFPROBE_EXE)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream and 'duration' in video_stream:
            return float(video_stream['duration'])
        elif 'format' in probe and 'duration' in probe['format']:
            return float(probe['format']['duration'])
    except Exception as e:
        print(f"Probe Error: {e}")
    return None

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_input_file": "",
        "last_output_dir": "",
        "last_sound_file": "",
        "start_time": "00:00:00",
        "end_time": "",
        "zoom_width": "1700"
    }

def save_config(input_file, output_dir, sound_file, start, end, zoom):
    config_data = {
        "last_input_file": input_file,
        "last_output_dir": output_dir,
        "last_sound_file": sound_file,
        "start_time": start,
        "end_time": end,
        "zoom_width": zoom
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Failed to save config: {e}")

# ── PRETTIER MODERN GUI APPLICATION ──────────────────────────────────────────
class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vertical Video Engine Pro")
        self.root.geometry("620x700")
        self.root.configure(bg="#11111b")
        
        self.config = load_config()
        self.selected_file_path = ""
        self.selected_sound_path = self.config.get("last_sound_file", "")
        self.last_output_dir = self.config.get("last_output_dir", "")

        self.setup_styles()
        self.build_ui()
        self.apply_saved_session()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background="#11111b", foreground="#cdd6f4")
        self.style.configure("TLabel", background="#11111b", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("TEntry", fieldbackground="#1e1e2e", foreground="#cdd6f4", borderwidth=1, font=("Segoe UI", 10))
        self.style.configure("Action.TButton", background="#b4befe", foreground="#11111b", font=("Segoe UI", 11, "bold"), borderwidth=0)
        self.style.map("Action.TButton", background=[("active", "#a6adc8"), ("disabled", "#313244")])
        self.style.configure("Horizontal.TProgressbar", troughcolor="#1e1e2e", background="#a6e3a1", thickness=18)

    def build_ui(self):
        header_frame = tk.Frame(self.root, bg="#11111b")
        header_frame.pack(pady=(25, 15))
        tk.Label(header_frame, text="VERTICAL VIDEO ENGINE", bg="#11111b", fg="#cdd6f4", font=("Segoe UI", 18, "bold")).pack()
        tk.Label(header_frame, text="CS:GO Clip → 9:16 Reels Pipeline", bg="#11111b", fg="#6c7086", font=("Segoe UI", 10)).pack()

        # Drop Zone 1: Master Video
        self.video_drop = tk.Label(
            self.root, 
            text="📥 DRAG & DROP GAMEPLAY VIDEO HERE\n(or click to browse filesystem)", 
            bg="#1e1e2e", fg="#bac2de", font=("Segoe UI Semibold", 10),
            bd=1, relief="solid", height=4, cursor="hand2"
        )
        self.video_drop.pack(pady=(10, 2), padx=35, fill="x")
        self.video_drop.drop_target_register(DND_FILES)
        self.video_drop.dnd_bind('<<Drop>>', self.handle_video_drop)
        self.video_drop.bind("<Button-1>", self.browse_video)

        self.lbl_file_path = tk.Label(self.root, text="No source video loaded", fg="#f38ba8", bg="#11111b", font=("Segoe UI", 9, "italic"), wraplength=500)
        self.lbl_file_path.pack(pady=(0, 15))

        # Drop Zone 2: Audio File
        self.audio_drop = tk.Label(
            self.root, 
            text="🎵 DRAG & DROP ENDING SFX AUDIO HERE\n(or click to browse for .m4a / .mp3)", 
            bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI Semibold", 9),
            bd=1, relief="solid", height=3, cursor="hand2"
        )
        self.audio_drop.pack(pady=(5, 2), padx=35, fill="x")
        self.audio_drop.drop_target_register(DND_FILES)
        self.audio_drop.dnd_bind('<<Drop>>', self.handle_audio_drop)
        self.audio_drop.bind("<Button-1>", self.browse_audio)

        self.lbl_sound_path = tk.Label(self.root, text="No dynamic end-sound active (will skip mix)", fg="#7f849c", bg="#11111b", font=("Segoe UI", 9, "italic"), wraplength=500)
        self.lbl_sound_path.pack(pady=(0, 20))

        # Configurations Grid Form
        form_wrapper = tk.Frame(self.root, bg="#1e1e2e", padx=25, pady=20, bd=1, relief="solid")
        form_wrapper.pack(padx=35, fill="x")

        ttk.Label(form_wrapper, text="Clip Start Position:", font=("Segoe UI", 10, "bold"), background="#1e1e2e").grid(row=0, column=0, sticky="w", pady=8)
        self.ent_start = ttk.Entry(form_wrapper, width=22, justify="center")
        self.ent_start.grid(row=0, column=1, sticky="e", pady=8)

        ttk.Label(form_wrapper, text="Clip End Position:", font=("Segoe UI", 10, "bold"), background="#1e1e2e").grid(row=1, column=0, sticky="w", pady=8)
        self.ent_end = ttk.Entry(form_wrapper, width=22, justify="center")
        self.ent_end.grid(row=1, column=1, sticky="e", pady=8)

        ttk.Label(form_wrapper, text="Foreground Zoom Width:", font=("Segoe UI", 10, "bold"), background="#1e1e2e").grid(row=2, column=0, sticky="w", pady=8)
        self.ent_zoom = ttk.Entry(form_wrapper, width=22, justify="center")
        self.ent_zoom.grid(row=2, column=1, sticky="e", pady=8)
        
        form_wrapper.grid_columnconfigure(1, weight=1)

        # Engine Progress Area
        self.progress_val = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, style="Horizontal.TProgressbar", variable=self.progress_val, max=100)
        self.progress_bar.pack(pady=(25, 2), padx=35, fill="x")

        self.lbl_status = tk.Label(self.root, text="System Idle", bg="#11111b", fg="#6c7086", font=("Segoe UI Semibold", 10))
        self.lbl_status.pack(pady=5)

        self.btn_run = ttk.Button(self.root, text="🚀 GOOOO SKRRRRRRRRRRR", style="Action.TButton", command=self.start_processing)
        self.btn_run.pack(pady=(10, 20), padx=35, fill="x", ipady=8)

    def apply_saved_session(self):
        self.ent_start.insert(0, self.config.get("start_time", "00:00:00"))
        self.ent_end.insert(0, self.config.get("end_time", ""))
        self.ent_zoom.insert(0, self.config.get("zoom_width", "1700"))
        
        saved_file = self.config.get("last_input_file", "")
        if saved_file and os.path.exists(saved_file):
            self.update_video_display(saved_file)
            
        if self.selected_sound_path and os.path.exists(self.selected_sound_path):
            self.update_audio_display(self.selected_sound_path)

    def handle_video_drop(self, event):
        self.update_video_display(clean_dropped_path(event.data))

    def handle_audio_drop(self, event):
        self.update_audio_display(clean_dropped_path(event.data))

    def browse_video(self, event=None):
        initial_dir = os.path.dirname(self.selected_file_path) if self.selected_file_path else None
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi")])
        if file_path:
            self.update_video_display(file_path)

    def browse_audio(self, event=None):
        initial_dir = os.path.dirname(self.selected_sound_path) if self.selected_sound_path else None
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Audio Files", "*.m4a *.mp3 *.wav *.ogg *.aac")])
        if file_path:
            self.update_audio_display(file_path)

    def update_video_display(self, path):
        self.selected_file_path = path
        self.lbl_file_path.config(text=f"Ready: {os.path.basename(path)}", fg="#a6e3a1")
        self.lbl_status.config(text="System Ready", fg="#a6adc8")
        self.progress_val.set(0)

    def update_audio_display(self, path):
        self.selected_sound_path = path
        self.lbl_sound_path.config(text=f"Active Outro Mix: {os.path.basename(path)}", fg="#f9e2af")

    def update_progress_ui(self, value):
        self.progress_val.set(value)
        self.lbl_status.config(text=f"Compiling Video Pipelines... {int(value)}%", fg="#f9e2af")

    def start_processing(self):
        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            messagebox.showerror("Error", "Please make sure to supply a valid gameplay source video file first.")
            return

        t_start = self.ent_start.get().strip()
        t_end = self.ent_end.get().strip()
        
        start_secs = time_to_seconds(t_start)
        if start_secs is None:
            messagebox.showerror("Error", "Invalid Format in clip start timestamp parameters.")
            return

        if not t_end:
            self.lbl_status.config(text="Querying source metadata...", fg="#f9e2af")
            self.root.update_idletasks()
            end_secs = get_video_duration(self.selected_file_path)
            if end_secs is None:
                messagebox.showerror("Error", "Could not parse internal video format parameters automatically.")
                return
        else:
            end_secs = time_to_seconds(t_end)
            if end_secs is None:
                messagebox.showerror("Error", "Invalid Format in clip termination metrics.")
                return

        duration = end_secs - start_secs
        if duration <= 0:
            messagebox.showerror("Error", "Ending constraints must follow structural entry start points.")
            return

        try:
            zoom_w = int(self.ent_zoom.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Foreground canvas zoom metrics must resolve as integers.")
            return

        initial_dir = self.last_output_dir if self.last_output_dir and os.path.exists(self.last_output_dir) else None
        output_file = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".mp4",
            filetypes=[("MP4 Video File", "*.mp4")],
            initialfile="vertical_" + os.path.basename(self.selected_file_path)
        )
        
        if not output_file:
            return

        self.last_output_dir = os.path.dirname(output_file)
        save_config(self.selected_file_path, self.last_output_dir, self.selected_sound_path, t_start, t_end, str(zoom_w))

        self.btn_run.config(state="disabled")
        self.progress_val.set(0)
        
        threading.Thread(
            target=self.processing_worker, 
            args=(self.selected_file_path, output_file, t_start, duration, zoom_w, self.selected_sound_path),
            daemon=True
        ).start()

    def processing_worker(self, infile, outfile, start, duration, zoom, sound_path):
        def callback(percentage):
            self.root.after(0, lambda: self.update_progress_ui(percentage))

        success = auto_format_clip(infile, outfile, start, duration, zoom, end_sound=sound_path, progress_callback=callback)
        self.root.after(0, lambda: self.processing_finished(success, outfile))

    def processing_finished(self, success, outfile):
        self.btn_run.config(state="normal")
        if success:
            self.progress_val.set(100)
            self.lbl_status.config(text="Transformation Successful!", fg="#a6e3a1")
            messagebox.showinfo("Success", f"Render Pipeline completed successfully!\nFile exported to:\n{outfile}")
        else:
            self.progress_val.set(0)
            self.lbl_status.config(text="Render Engine Aborted", fg="#f38ba8")
            messagebox.showerror("Error", "An unexpected exception halted the conversion encoder. Check shell output logs.")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
