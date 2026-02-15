#   - Video Downloader mit yt-dlp + aria2 + Tkinter
#   - Copyright 2026 by Lars Kuehn
#   - Version 0.5.1 (15.02.2026)
#   - Licensed under the MIT License
#   - https://github.com/deinusername/VideoDownloader  (später eintragen)
#   - Einfache GUI für YouTube-Video/Playlist-Downloads
#   - Unterstützt Einzelvideos und Playlists
#   - Zeigt Fortschritt, Geschwindigkeit, ETA an
#   - Nutzt aria2 für schnellere Downloads (Segmentierung)
#   - Robust gegenüber Fehlern, mit Retries
#   - Windows/OneDrive-freundliche Dateinamen und Einstellungen

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import yt_dlp
import os
import shutil


APP_NAME = "Video Downloader"
APP_VERSION = "0.5.1"
APP_COPYRIGHT = "Copyright 2026 by Lars Kuehn"


def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path_var.set(folder)


def human_bytes(n: float | int | None) -> str:
    if not n:
        return "0 B"
    n = float(n)
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    return f"{n:.1f} {units[i]}"


def human_speed(n: float | int | None) -> str:
    if not n:
        return "0 B/s"
    return f"{human_bytes(n)}/s"


def human_eta(seconds: int | float | None) -> str:
    if seconds is None:
        return "?"
    try:
        seconds = int(seconds)
    except Exception:
        return "?"
    if seconds < 0:
        return "?"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def show_about():
    about_text = (
        f"{APP_NAME} v{APP_VERSION}\n"
        f"{APP_COPYRIGHT}\n\n"
        "Danke an die genutzten Drittanbieter-Projekte:\n"
        "- yt-dlp (yt-dlp Contributors)\n"
        "- FFmpeg (FFmpeg Developers)\n"
        "- aria2 (Tatsuhiro Tsujikawa & Contributors)\n"
        "- Python / Tkinter (Python Software Foundation & Community)\n\n"
        "Hinweis: Dieses Programm ist nicht offiziell mit den oben genannten\n"
        "Projekten verbunden."
    )
    messagebox.showinfo("About", about_text)


def close_app():
    # sauber beenden (auch wenn ein Download-Thread noch läuft)
    # Thread ist daemon=True, also killt Python beim Exit alles.
    root.quit()
    root.destroy()


def download_video():
    url = url_var.get().strip()
    download_path = download_path_var.get().strip()

    if not url:
        messagebox.showerror("Fehler", "Bitte eine URL eingeben.")
        return
    if not download_path:
        messagebox.showerror("Fehler", "Bitte einen Download-Ordner wählen.")
        return

    # aria2 check (freundlicher Fail statt mystischem Explodieren)
    aria2_path = shutil.which("aria2c")
    if not aria2_path:
        messagebox.showerror(
            "Fehler",
            "aria2c wurde nicht gefunden.\n\n"
            "Bitte aria2 installieren und sicherstellen, dass aria2c.exe im PATH ist\n"
            "oder im selben Ordner wie das Programm liegt."
        )
        return

    # UI reset
    progress_var.set(0)
    progress_bar.configure(mode="determinate", maximum=100)
    status_var.set("Initialisiere …")
    item_var.set("")
    root.update_idletasks()

    # Robust + Windows/OneDrive-freundlich
    format_selector = "bv*+ba/best/b[ext=mp4]/best"

    # Shared auth/extractor settings (wie bei deiner EXE)
    common_opts = {
        "cookiesfrombrowser": ("firefox",),
        "remote_components": ["ejs:github"],
        "quiet": True,
        "no_warnings": True,
    }

    # Ermittelt Playlist-Gesamtzahl (Y) + initiale Anzeige
    playlist_total = {"n": None}  # mutable closure container

    def ui_set_status(text: str):
        status_var.set(text)

    def ui_set_item(text: str):
        item_var.set(text)

    def ui_set_progress(pct: float):
        if pct < 0:
            pct = 0
        if pct > 100:
            pct = 100
        progress_var.set(pct)

    def progress_hook(d: dict):
        """
        Läuft im Worker-Thread. UI-Updates nur via root.after.
        d enthält u.a. status, downloaded_bytes, total_bytes, eta, speed, info_dict...
        """
        try:
            st = d.get("status")

            info = d.get("info_dict") or {}
            title = info.get("title") or ""
            p_index = info.get("playlist_index")  # 1-based
            p_total = playlist_total["n"]

            if p_index and p_total:
                header = f"{p_index} von {p_total}"
            elif p_index:
                header = f"Item {p_index}"
            else:
                header = ""

            if title:
                item_text = f"{header}  –  {title}" if header else title
            else:
                item_text = header

            if st == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                eta = d.get("eta")
                speed = d.get("speed")

                if total:
                    pct = (downloaded / total) * 100.0
                else:
                    pct = 0.0

                status_text = (
                    f"{pct:5.1f}%  |  {human_bytes(downloaded)} / {human_bytes(total)}"
                    f"  |  {human_speed(speed)}  |  ETA {human_eta(eta)}"
                )
                root.after(0, ui_set_item, item_text)
                root.after(0, ui_set_progress, pct)
                root.after(0, ui_set_status, status_text)

            elif st == "finished":
                root.after(0, ui_set_item, item_text)
                root.after(0, ui_set_status, "Download fertig – verarbeite (Merge/FFmpeg) …")
                root.after(0, lambda: progress_bar.configure(mode="indeterminate"))
                root.after(0, lambda: progress_bar.start(10))

            elif st == "error":
                root.after(0, ui_set_item, item_text)
                root.after(0, ui_set_status, "Fehler beim Download")

        except Exception:
            pass

    # --- aria2 "mehr Bums" Settings ---
    # Achtung: YouTube/CDNs können bei zu aggressiven Settings mit 429/403 reagieren.
    aria2_args = [
        "-x", "16",                 # max connections per server
        "-s", "16",                 # number of connections per download
        "-k", "2M",                 # segment size
        "--max-tries=10",
        "--retry-wait=1",
        "--timeout=10",
        "--file-allocation=none",
        "--console-log-level=warn",
    ]

    ydl_opts = {
        # Titel kürzen + ID anhängen (eindeutig) + Windows-sicher
        "outtmpl": os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s"),

        **common_opts,

        # Format & Merge
        "format": format_selector,
        "merge_output_format": "mp4",

        # Windows/OneDrive-Problemkiller
        "windowsfilenames": True,
        "restrictfilenames": True,
        "trim_file_name": 150,
        "nopart": True,
        "continuedl": False,
        "overwrites": True,
        "ignoreerrors": True,

        # Stabilität
        "retries": 10,
        "fragment_retries": 10,

        # aria2 als externer Downloader
        "external_downloader": "aria2c",
        "external_downloader_args": {"default": aria2_args},

        # Fortschritt
        "progress_hooks": [progress_hook],
    }

    def run_yt_dlp():
        try:
            # 1) Playlistgröße ermitteln (damit "X von Y" geht)
            root.after(0, ui_set_status, "Analysiere Link …")
            with yt_dlp.YoutubeDL({
                **common_opts,
                "extract_flat": True,
                "skip_download": True,
            }) as ydl_probe:
                info = ydl_probe.extract_info(url, download=False)

            if isinstance(info, dict) and info.get("_type") == "playlist":
                entries = info.get("entries") or []
                try:
                    entries_list = [e for e in entries if e]
                except TypeError:
                    entries_list = []
                playlist_total["n"] = len(entries_list) if entries_list else None

                pl_title = info.get("title") or "Playlist"
                root.after(
                    0,
                    ui_set_item,
                    f"Playlist: {pl_title} ({playlist_total['n'] or '?'} Videos)"
                )
            else:
                playlist_total["n"] = None

            # 2) Download starten
            root.after(0, ui_set_status, "Starte Download …")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 3) Fertig
            def done_ui():
                progress_bar.stop()
                progress_bar.configure(mode="determinate")
                progress_var.set(100)
                status_var.set("Fertig.")
                messagebox.showinfo("Fertig", "Download abgeschlossen!")

            root.after(0, done_ui)

        except Exception as ex:
            err_text = str(ex)

            def err_ui():
                progress_bar.stop()
                progress_bar.configure(mode="determinate")
                status_var.set("Fehler.")
                messagebox.showerror("Fehler beim Download", err_text)

            root.after(0, err_ui)

    threading.Thread(target=run_yt_dlp, daemon=True).start()


# --- GUI ---
root = tk.Tk()
root.title(f"{APP_NAME} v{APP_VERSION} – {APP_COPYRIGHT}")

# ---- Menüs ----
menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Close", command=close_app)
menubar.add_cascade(label="File", menu=file_menu)

help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menubar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menubar)

# --- Vars ---
url_var = tk.StringVar()
download_path_var = tk.StringVar()
status_var = tk.StringVar(value="Bereit.")
item_var = tk.StringVar(value="")
progress_var = tk.DoubleVar(value=0)

padx = 10

tk.Label(root, text="YouTube / Video URL (auch Playlist):").pack(pady=(10, 0))
tk.Entry(root, textvariable=url_var, width=80).pack(padx=padx, pady=5)

tk.Label(root, text="Download-Ordner:").pack(pady=(10, 0))
tk.Entry(root, textvariable=download_path_var, width=80).pack(padx=padx, pady=5)
tk.Button(root, text="Ordner wählen", command=select_folder).pack(pady=5)

# Statusbereich
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=padx, pady=(10, 6))
tk.Label(root, textvariable=item_var, anchor="w", justify="left").pack(fill="x", padx=padx)
tk.Label(root, textvariable=status_var, anchor="w", justify="left").pack(fill="x", padx=padx, pady=(2, 6))

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=padx, pady=(0, 10))

tk.Button(root, text="Download starten", command=download_video).pack(pady=(0, 15))

# Fenster-X auch sauber behandeln
root.protocol("WM_DELETE_WINDOW", close_app)

root.mainloop()
