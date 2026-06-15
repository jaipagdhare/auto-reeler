import ffmpeg

def auto_format_clip(input_file, output_file, start_time, duration, zoom_width=2400):
    """
    Converts a gameplay clip (any aspect ratio) into a 9:16 vertical video (1080x1920)
    with a blurred background fill and a zoomed, centered foreground.

    Args:
        input_file:  Path to the source clip.
        output_file: Path for the rendered output.
        start_time:  Trim start as "HH:MM:SS" or seconds.
        duration:    Length of the clip in seconds.
        zoom_width:  How wide to scale the foreground — higher = more zoom. Default 2400.
    """
    input_stream = ffmpeg.input(input_file, ss=start_time, t=duration)
    video_branches = input_stream.video.split()
    bg_branch = video_branches[0]
    fg_branch = video_branches[1]

    # ── BACKGROUND ────────────────────────────────────────────────────────────
    # BUG FIX: The original scaled width to 1080 first (giving only 675px height
    # for a 1680×1050 input), then tried to crop 1920px tall — which fails silently
    # or stretches. Correct approach: scale HEIGHT to 1920 so the frame always
    # covers the full canvas, then crop the excess width from the center.
    background = (
        bg_branch
        .filter('scale', -2, 1920)          # scale to fill height, keep aspect ratio
        .filter('crop', 1080, 1920)          # crop excess width from center
        .filter('boxblur', lr=20, lp=2)     # blur the background
    )

    # ── FOREGROUND (ZOOMED) ───────────────────────────────────────────────────
    # Scale up to zoom_width wide, then crop center 1080px.
    # For 1680×1050 @ zoom_width=2400 → 2400×1500, cropped to 1080×1500.
    foreground = (
        fg_branch
        .filter('scale', zoom_width, -2)            # zoom in, keep aspect ratio
        .filter('crop', 1080, 'in_h', '(in_w-1080)/2', 0)  # crop center column 
    )

    # ── COMPOSITE ─────────────────────────────────────────────────────────────
    # Overlay foreground centered vertically on the blurred background.
    combined_video = ffmpeg.overlay(background, foreground, x=0, y='(H-h)/2')

    # 1-second fade to black at the end
    fade_start = duration - 1
    final_video = combined_video.filter('fade', type='out', start_time=fade_start, duration=1)

    audio = input_stream.audio

    # ── EXPORT ────────────────────────────────────────────────────────────────
    (
        ffmpeg.output(
            final_video, audio, output_file,
            vcodec='libx264',
            acodec='aac',
            pix_fmt='yuv420p',
            r=60,
            **{'b:v': '8M'}   # good bitrate for 1080p upload (Instagram/YouTube Shorts)
        )
        .overwrite_output()
        .run()
    )
    print(f"Done! Saved to: {output_file}")


# ── RUN ───────────────────────────────────────────────────────────────────────
auto_format_clip(
    input_file="/run/media/jaip/Windows/Record/Counter-strike  Global Offensive/grant road.mp4",
    output_file="/run/media/jaip/Windows/Record/INSTA/grand road final.mp4",
    start_time="00:01:26",
    duration=40,
    zoom_width=1700   # tweak this to adjust how zoomed-in the foreground looks
)