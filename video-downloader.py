#   - Video Downloader mit yt-dlp.exe + aria2 + Tkinter
#   - Copyright 2026 by Lars Kuehn
#   - Version 1.0.5 (20.02.2026)
#   - Licensed under the MIT License
#   - https://github.com/1Bln21/VideoDownloader
#   - nutzt yt-dlp.exe aus .\bin\ (kein Python-Modul nötig)
#   - kein Konsolenfenster
#   - Progressbar: indeterminate während Download (absichtlich)

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import os
import sys
import shutil
import subprocess


APP_NAME = "Video Downloader"
APP_VERSION = "1.0.5"
APP_COPYRIGHT = "Copyright 2026 by Lars Kuehn"


# ----------------- Pfade / Tools -----------------

def get_base_dir() -> str:
    """Ordner der laufenden EXE (PyInstaller) oder des .py Scripts."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_tool(name: str) -> str | None:
    """
    Tools liegen in .\bin\ (nicht neben der EXE).
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


def popen_hidden_kwargs() -> dict:
    """Windows: keine extra Konsolenfenster für yt-dlp/aria2/ffmpeg."""
    if os.name != "nt":
        return {}
    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return {"creationflags": CREATE_NO_WINDOW, "startupinfo": si}


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

    ytdlp_exe = find_tool("yt-dlp")
    if not ytdlp_exe:
        messagebox.showerror(
            "Fehler",
            "yt-dlp.exe wurde nicht gefunden.\n\n"
            "Bitte yt-dlp.exe in .\\bin\\ legen oder yt-dlp in den PATH aufnehmen."
        )
        return

    aria2_path = find_tool("aria2c")
    if not aria2_path:
        messagebox.showerror(
            "Fehler",
            "aria2c.exe wurde nicht gefunden.\n\n"
            "Bitte aria2c.exe in .\\bin\\ legen oder in den PATH aufnehmen."
        )
        return

    ffmpeg_path = find_tool("ffmpeg")
    if not ffmpeg_path:
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
    status_var.set("Analysiere …")
    item_var.set("")
    root.update_idletasks()

    # Format (dein bisheriger Selector)
    format_selector = "bv*+ba/best/b[ext=mp4]/best"

    # aria2 Settings
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
    aria2_args_str = " ".join(aria2_args)

    outtmpl = os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s")

    def run_worker():
        try:
            # Progressbar: indeterminate während Download
            def start_ui():
                status_var.set("Starte Download …")
                progress_bar.configure(mode="indeterminate")
                progress_bar.start(10)

            root.after(0, start_ui)

            cmd = [
                ytdlp_exe,
                url,
                "-f", format_selector,
                "-o", outtmpl,
                "--merge-output-format", "mp4",
                "--windows-filenames",
                "--restrict-filenames",
                "--trim-filenames", "150",
                "--no-part",
                "--no-continue",
                "--force-overwrites",
                "--ignore-errors",
                "--retries", "10",
                "--fragment-retries", "10",
                "--cookies-from-browser", "firefox",
                "--external-downloader", aria2_path,
                "--external-downloader-args", f"aria2c:{aria2_args_str}",
                "--no-warnings",
            ]

            if ffmpeg_path:
                cmd += ["--ffmpeg-location", os.path.dirname(ffmpeg_path)]

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                **popen_hidden_kwargs()
            )

            output = (proc.stdout or "").strip()

            def done_ui():
                progress_bar.stop()
                progress_bar.configure(mode="determinate")
                if proc.returncode == 0:
                    progress_var.set(100)
                    status_var.set("Fertig.")
                else:
                    progress_var.set(0)
                    status_var.set("Fehler.")
                    # kurze Fehlermeldung, aber ohne Terminal
                    msg = output[-1500:] if output else f"Exit Code: {proc.returncode}"
                    messagebox.showerror("Fehler beim Download", msg)

            root.after(0, done_ui)

        except Exception as ex:
            err_text = str(ex)

            def err_ui():
                progress_bar.stop()
                progress_bar.configure(mode="determinate")
                status_var.set("Fehler.")
                messagebox.showerror("Fehler beim Download", err_text)

            root.after(0, err_ui)

    threading.Thread(target=run_worker, daemon=True).start()


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
