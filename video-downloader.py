#   - Video Downloader mit yt-dlp + aria2 + Tkinter
#   - Copyright 2026 by Lars Kuehn
#   - Version 1.0.4 (20.02.2026)
#   - Licensed under the MIT License
#   - hhttps://github.com/1Bln21/VideoDownloader
#   - Einfache GUI für YouTube-Video/Playlist-Downloads
#   - Unterstützt Einzelvideos und Playlists
#   - Zeigt Fortschritt, Geschwindigkeit, ETA an - momentan broken wegen yt-dlp/aria2 API-Änderungen, wird aber gefixt
#   - Nutzt aria2 für schnellere Downloads (Segmentierung)
#   - Robust gegenüber Fehlern, mit Retries
#   - Windows/OneDrive-freundliche Dateinamen und Einstellungen
#   - Etliche Bug Fixes und Verbesserungen gegenüber früheren Versionen

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import os
import sys
import shutil
import subprocess
import yt_dlp


APP_NAME = "Video Downloader"
APP_VERSION = "1.0.4"
APP_COPYRIGHT = "Copyright 2026 by Lars Kuehn"


# ----------------- Pfade / Tools -----------------

def get_base_dir() -> str:
    """Ordner der laufenden EXE (PyInstaller) oder des .py Scripts."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_tool(name: str) -> str | None:
    """
    FIX für DLL/Ordinal-Probleme nach PyInstaller:
    Tools liegen in .\bin\ (nicht neben der EXE), damit Windows keine falschen DLLs greift.
    Sucht in: <base>\bin\<tool>.exe, dann <base>\<tool>.exe, dann PATH.
    """
    base_dir = get_base_dir()

    candidates = [
        os.path.join(base_dir, "bin", f"{name}.exe"),
        os.path.join(base_dir, "bin", name),
        os.path.join(base_dir, f"{name}.exe"),
        os.path.join(base_dir, name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    return shutil.which(name)


# ----------------- GUI Helfer -----------------

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path_var.set(folder)


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
    root.quit()
    root.destroy()


# ----------------- Safe Clipboard / Context Menu -----------------

def safe_paste(entry: tk.Entry):
    """Einfügen ohne Crash bei leerer Zwischenablage."""
    try:
        text = entry.clipboard_get()
    except tk.TclError:
        return

    if not text:
        return

    try:
        if entry.selection_present():
            entry.delete("sel.first", "sel.last")
    except tk.TclError:
        pass

    entry.insert(tk.INSERT, text)


def add_context_menu_to_entry(entry: tk.Entry):
    menu = tk.Menu(entry, tearoff=0)

    def do_cut():
        entry.event_generate("<<Cut>>")

    def do_copy():
        entry.event_generate("<<Copy>>")

    def do_paste():
        safe_paste(entry)

    def do_select_all():
        entry.selection_range(0, tk.END)
        entry.icursor(tk.END)

    menu.add_command(label="Ausschneiden", command=do_cut)
    menu.add_command(label="Kopieren", command=do_copy)
    menu.add_command(label="Einfügen", command=do_paste)
    menu.add_separator()
    menu.add_command(label="Alles markieren", command=do_select_all)

    def popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    entry.bind("<Button-3>", popup)          # Windows/Linux
    entry.bind("<Control-Button-1>", popup)  # macOS


# FIX: "break" muss wirklich zurückgegeben werden (sonst doppelt eingefügt)
def add_shift_insert_paste(entry: tk.Entry):
    def _handler(_e):
        safe_paste(entry)
        return "break"
    entry.bind("<Shift-Insert>", _handler)


def add_ctrl_v_safe_paste(entry: tk.Entry):
    def _handler(_e):
        safe_paste(entry)
        return "break"
    entry.bind("<Control-v>", _handler)
    entry.bind("<Control-V>", _handler)


# ----------------- Windows: Child-Prozesse ohne Konsolenfenster -----------------

class HiddenProcessPatcher:
    """
    Patcht subprocess.Popen temporär, damit aria2c/ffmpeg/ffprobe unter Windows
    OHNE extra Konsolenfenster gestartet werden.
    """
    def __init__(self, hide_for_exe_names: set[str]):
        self.hide_for = {n.lower() for n in hide_for_exe_names}
        self._orig_popen = None

    def __enter__(self):
        if os.name != "nt":
            return self

        self._orig_popen = subprocess.Popen
        CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        def _needs_hide(args) -> bool:
            try:
                if isinstance(args, (list, tuple)) and args:
                    exe = str(args[0]).lower()
                else:
                    exe = str(args).strip().strip('"').split(" ")[0].lower()
                exe_base = os.path.basename(exe)
                return exe_base in self.hide_for
            except Exception:
                return False

        def patched_popen(*p_args, **p_kwargs):
            args = p_args[0] if p_args else p_kwargs.get("args")
            if _needs_hide(args):
                if "creationflags" not in p_kwargs:
                    p_kwargs["creationflags"] = CREATE_NO_WINDOW
                if "startupinfo" not in p_kwargs:
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = 0  # SW_HIDE
                    p_kwargs["startupinfo"] = si
            return self._orig_popen(*p_args, **p_kwargs)

        subprocess.Popen = patched_popen
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._orig_popen is not None:
            subprocess.Popen = self._orig_popen
        return False


# ----------------- Human helpers -----------------

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


# ----------------- Download -----------------

def download_video():
    url = url_var.get().strip()
    download_path = download_path_var.get().strip()

    if not url:
        messagebox.showerror("Fehler", "Bitte eine URL eingeben.")
        return
    if not download_path:
        messagebox.showerror("Fehler", "Bitte einen Download-Ordner wählen.")
        return

    aria2_path = find_tool("aria2c")
    if not aria2_path:
        messagebox.showerror(
            "Fehler",
            "aria2c wurde nicht gefunden.\n\n"
            "Bitte aria2 installieren und sicherstellen, dass aria2c.exe im PATH ist\n"
            "oder im Unterordner .\\bin\\ liegt."
        )
        return

    # optional: ffmpeg check (yt-dlp kann auch ohne, aber merge dann nicht)
    ffmpeg_path = find_tool("ffmpeg")
    if not ffmpeg_path:
        # nicht hart abbrechen, aber sinnvoller Hinweis
        messagebox.showwarning(
            "Hinweis",
            "ffmpeg.exe wurde nicht gefunden.\n"
            "Downloads können funktionieren, aber Merging/MP4-Ausgabe kann scheitern.\n\n"
            "Lege ffmpeg.exe in .\\bin\\ oder in den PATH."
        )

    # UI reset
    progress_var.set(0)
    progress_bar.configure(mode="determinate", maximum=100)
    progress_bar.stop()
    status_var.set("Initialisiere …")
    item_var.set("")
    root.update_idletasks()

    format_selector = "bv*+ba/best/b[ext=mp4]/best"

    common_opts = {
        "cookiesfrombrowser": ("firefox",),
        "remote_components": ["ejs:github"],
        "quiet": True,
        "no_warnings": True,
    }

    playlist_total = {"n": None}

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
        try:
            st = d.get("status")
            info = d.get("info_dict") or {}

            title = info.get("title") or ""
            p_index = info.get("playlist_index")
            p_total = playlist_total["n"]

            if p_index and p_total:
                header = f"{p_index} von {p_total}"
            elif p_index:
                header = f"Item {p_index}"
            else:
                header = ""

            item_text = f"{header}  –  {title}" if (header and title) else (title or header)

            if st == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                eta = d.get("eta")
                speed = d.get("speed")

                if total:
                    pct = (downloaded / total) * 100.0
                    root.after(0, lambda: progress_bar.configure(mode="determinate"))
                    root.after(0, lambda: progress_bar.stop())
                    root.after(0, ui_set_progress, pct)

                    status_text = (
                        f"{pct:5.1f}%  |  {human_bytes(downloaded)} / {human_bytes(total)}"
                        f"  |  {human_speed(speed)}  |  ETA {human_eta(eta)}"
                    )
                else:
                    # aria2 kann totals oft nicht liefern -> ehrlich sein:
                    root.after(0, lambda: progress_bar.configure(mode="indeterminate"))
                    root.after(0, lambda: progress_bar.start(10))
                    status_text = (
                        f"Läuft…  |  {human_speed(speed)}  |  ETA {human_eta(eta)}"
                    )

                root.after(0, ui_set_item, item_text)
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

    aria2_args = [
        "-x", "16",
        "-s", "16",
        "-k", "2M",
        "--max-tries=10",
        "--retry-wait=1",
        "--timeout=10",
        "--file-allocation=none",
        "--console-log-level=warn",
    ]

    ydl_opts = {
        "outtmpl": os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s"),
        **common_opts,

        "format": format_selector,
        "merge_output_format": "mp4",

        "windowsfilenames": True,
        "restrictfilenames": True,
        "trim_file_name": 150,
        "nopart": True,
        "continuedl": False,
        "overwrites": True,
        "ignoreerrors": True,

        "retries": 10,
        "fragment_retries": 10,

        # Tools-Pfade (bin-fähig)
        "ffmpeg_location": os.path.dirname(ffmpeg_path) if ffmpeg_path else None,

        "external_downloader": aria2_path,
        "external_downloader_args": {"default": aria2_args},

        "progress_hooks": [progress_hook],
    }

    # yt-dlp mag keine None in manchen Feldern -> raus damit
    if ydl_opts.get("ffmpeg_location") is None:
        ydl_opts.pop("ffmpeg_location", None)

    def run_yt_dlp():
        try:
            root.after(0, ui_set_status, "Analysiere Link …")

            with HiddenProcessPatcher({"aria2c.exe", "aria2c", "ffmpeg.exe", "ffmpeg", "ffprobe.exe", "ffprobe"}):
                # Probe Playlistgröße
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
                    root.after(0, ui_set_item, f"Playlist: {pl_title} ({playlist_total['n'] or '?'} Videos)")
                else:
                    playlist_total["n"] = None

                # Download
                root.after(0, ui_set_status, "Starte Download …")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            def done_ui():
                progress_bar.stop()
                progress_bar.configure(mode="determinate")
                progress_var.set(100)
                status_var.set("Fertig.")

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


# ----------------- GUI -----------------

root = tk.Tk()
root.title(f"{APP_NAME} v{APP_VERSION} – {APP_COPYRIGHT}")

menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Close", command=close_app)
menubar.add_cascade(label="File", menu=file_menu)

help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menubar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menubar)

url_var = tk.StringVar()
download_path_var = tk.StringVar()
status_var = tk.StringVar(value="Bereit.")
item_var = tk.StringVar(value="")
progress_var = tk.DoubleVar(value=0)

padx = 10

tk.Label(root, text="YouTube / Video URL (auch Playlist):").pack(pady=(10, 0))
url_entry = tk.Entry(root, textvariable=url_var, width=80)
url_entry.pack(padx=padx, pady=5)

tk.Label(root, text="Download-Ordner:").pack(pady=(10, 0))
path_entry = tk.Entry(root, textvariable=download_path_var, width=80)
path_entry.pack(padx=padx, pady=5)

tk.Button(root, text="Ordner wählen", command=select_folder).pack(pady=5)

add_context_menu_to_entry(url_entry)
add_context_menu_to_entry(path_entry)
add_shift_insert_paste(url_entry)
add_shift_insert_paste(path_entry)
add_ctrl_v_safe_paste(url_entry)
add_ctrl_v_safe_paste(path_entry)

ttk.Separator(root, orient="horizontal").pack(fill="x", padx=padx, pady=(10, 6))
tk.Label(root, textvariable=item_var, anchor="w", justify="left").pack(fill="x", padx=padx)
tk.Label(root, textvariable=status_var, anchor="w", justify="left").pack(fill="x", padx=padx, pady=(2, 6))

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=padx, pady=(0, 10))

tk.Button(root, text="Download starten", command=download_video).pack(pady=(0, 15))

root.protocol("WM_DELETE_WINDOW", close_app)

root.mainloop()
