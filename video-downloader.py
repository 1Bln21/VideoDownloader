#   - Video Downloader mit yt-dlp (Python-Modul) + Tkinter
#   - Copyright 2026 by Lars Kuehn
#   - Version 1.1.3-win (12.04.2026)
#   - Licensed under the MIT License
#   - https://github.com/1Bln21/VideoDownloader
#   - Zielplattform: Windows 11
#   - Voraussetzungen:
#       pip install yt-dlp
#       ffmpeg: https://ffmpeg.org/download.html
#         oder: winget install --id=Gyan.FFmpeg -e
#   - Tkinter ist in der Standardinstallation von Python für Windows enthalten.

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import os
import shutil

import re
import yt_dlp


APP_NAME      = "Video Downloader"
APP_VERSION   = "1.1.3-win"
APP_COPYRIGHT = "Copyright 2026 by Lars Kuehn"


# ═══════════════════════════════════════════════════════════
#  Übersetzungen / Translations
# ═══════════════════════════════════════════════════════════

STRINGS: dict[str, dict[str, str]] = {
    "de": {
        # Menüleiste
        "menu_file":               "Datei",
        "menu_close":              "Schließen",
        "menu_browser":            "Browser / Cookies",
        "menu_cookie_select":      "Cookie-Datei wählen…",
        "menu_cookie_help":        "Cookie-Datei-Anleitung",
        "menu_no_browser":         "Kein Browser (keine Cookies)",
        "menu_settings":           "Einstellungen",
        "menu_language":           "Sprache",
        "menu_lang_de":            "Deutsch",
        "menu_lang_en":            "English",
        "menu_format":             "Videoformat",
        "menu_help":               "Hilfe",
        "menu_about":              "Über",
        # Labels
        "lbl_url":                 "YouTube / Video URL (auch Playlist):",
        "lbl_folder":              "Download-Ordner:",
        # Buttons
        "btn_folder":              "Ordner wählen",
        "btn_smb":                 "Netzwerk / UNC",
        "btn_download":            "Download starten",
        "btn_cancel":              "Download abbrechen",
        "btn_queue_mode_off":      "☰ Warteschlange",
        "btn_queue_mode_on":       "✕ Einzelner Link",
        "btn_queue_add":           "+ Hinzufügen",
        "btn_queue_remove":        "Entfernen",
        "btn_queue_clear":         "Liste leeren",
        "btn_queue_download":      "Alle herunterladen",
        "lbl_queue":               "Warteschlange ({0} URLs):",
        "status_queue_n":          "Queue {0} von {1} …",
        "status_queue_done":       "Fertig. ({0} von {1} URLs)",
        "err_queue_empty":         "Die Warteschlange ist leer.",
        # Kontextmenü
        "ctx_cut":                 "Ausschneiden",
        "ctx_copy":                "Kopieren",
        "ctx_paste":               "Einfügen",
        "ctx_select_all":          "Alles markieren",
        # Status
        "status_ready":            "Bereit.",
        "status_analyzing":        "Analysiere …",
        "status_starting":         "Starte Download …",
        "status_downloading":      "Lade herunter …",
        "status_downloading_n":    "Download {0} von {1} …",
        "status_done":             "Fertig.",
        "status_done_n":           "Fertig. ({0} Videos)",
        "status_cancelled":        "Abgebrochen.",
        "status_error":            "Fehler.",
        # Browser-Info-Zeile
        "cookie_none":             "Keine Cookies",
        "cookie_file_label":       "Cookie-Datei: {0}",
        "cookie_file_none":        "Cookie-Datei: (keine gewählt)",
        "cookie_from":             "Cookies aus: {0}",
        # Fehlermeldungen / Hinweise
        "err_title":               "Fehler",
        "warn_title":              "Hinweis",
        "err_no_url":              "Bitte eine URL eingeben.",
        "err_invalid_url":         "Die URL scheint ungültig zu sein (muss mit http beginnen).",
        "err_no_folder":           "Bitte einen Download-Ordner wählen.",
        "err_unc_invalid":         (
            "Der UNC-Pfad scheint ungültig zu sein:\n{0}\n\n"
            "Bitte im Format \\\\Server\\Freigabe angeben."
        ),
        "smb_dialog_title":        "Netzwerkpfad / UNC-Freigabe",
        "smb_dialog_label":        (
            "UNC-Pfad eingeben:\n"
            "  \\\\Server\\Freigabe\n"
            "  \\\\Server\\Freigabe\\Unterordner"
        ),
        "err_no_ytdlp":            (
            "yt-dlp ist nicht installiert.\n\n"
            "pip install yt-dlp"
        ),
        "warn_no_ffmpeg":          (
            "ffmpeg wurde nicht gefunden.\n"
            "Downloads können funktionieren, aber Merging/MP4-Ausgabe kann scheitern.\n\n"
            "winget install --id=Gyan.FFmpeg -e\n"
            "oder: https://ffmpeg.org/download.html"
        ),
        "err_no_cookie_file":      (
            "Es wurde 'Cookie-Datei' als Modus gewählt,\n"
            "aber keine gültige Datei gefunden.\n\n"
            "Bitte unter 'Browser / Cookies' → 'Cookie-Datei wählen…'\n"
            "eine gültige cookies.txt auswählen."
        ),
        "warn_encrypted_title":    "⚠ Hinweis – App-Bound Encryption",
        "warn_encrypted":          (
            "{0} verwendet seit Version 127 App-Bound Encryption\n"
            "für Cookies. yt-dlp kann diese meist nicht entschlüsseln,\n"
            "auch wenn der Browser geschlossen ist.\n\n"
            "Empfehlung: 'Cookie-Datei wählen…' nutzen.\n"
            "(Anleitung: Menü 'Browser / Cookies' → 'Cookie-Datei-Anleitung')\n\n"
            "Trotzdem mit {0} direkt versuchen?"
        ),
        "err_cookie_locked_title": "Cookie-Import fehlgeschlagen",
        "err_cookie_locked":       (
            "Der Browser-Cookie-Import ist fehlgeschlagen.\n\n"
            "Ursache: App-Bound Encryption (Chrome/Edge ab v127)\n"
            "verhindert den direkten Zugriff auf die Cookie-Datenbank.\n\n"
            "Lösung:\n"
            "1. Menü 'Browser / Cookies' → 'Cookie-Datei-Anleitung'\n"
            "2. Cookies mit der Extension exportieren\n"
            "3. 'Cookie-Datei wählen…' und die .txt auswählen"
        ),
        "err_download_title":      "Fehler beim Download",
        "err_format_unavailable":  (
            "Das gewählte Format ist für dieses Video nicht verfügbar.\n\n"
            "Bitte unter Einstellungen → Videoformat ein anderes Format wählen,\n"
            "z.B. 'Beste Qualität (automatisch)'."
        ),
        "warn_no_download":        (
            "Es wurde nichts heruntergeladen.\n\n"
            "Mögliche Ursachen:\n"
            "- Login erforderlich (Cookies setzen)\n"
            "- Video ist privat oder nicht verfügbar\n"
            "- Geo-Sperre aktiv\n"
            "{0}"
        ),
        # About
        "about_title":             "Über",
        "about_body":              (
            "{name} v{ver}\n{copy}\n\n"
            "Danke an die genutzten Drittanbieter-Projekte:\n"
            "- yt-dlp (yt-dlp Contributors)\n"
            "- FFmpeg (FFmpeg Developers)\n"
            "- Python / Tkinter (Python Software Foundation & Community)\n\n"
            "Hinweis: Dieses Programm ist nicht offiziell mit den oben\n"
            "genannten Projekten verbunden."
        ),
        # Cookie-Anleitung
        "cookie_help_title":       "Cookie-Datei – Anleitung",
        "cookie_help_body":        (
            "Chrome, Edge und andere Chromium-Browser verschlüsseln\n"
            "ihre Cookies seit Version 127 (App-Bound Encryption).\n"
            "yt-dlp kann sie daher nicht mehr direkt lesen.\n\n"
            "So exportierst du deine Cookies als Datei:\n\n"
            "1. Browser-Extension installieren:\n"
            "   → 'Get cookies.txt LOCALLY'\n"
            "      (Chrome Web Store / Edge Add-ons)\n\n"
            "2. YouTube (oder die gewünschte Seite) öffnen\n"
            "   und dort eingeloggt sein.\n\n"
            "3. Extension-Icon klicken → 'Export' → cookies.txt speichern.\n\n"
            "4. Im Menü 'Browser / Cookies' → 'Cookie-Datei wählen…'\n"
            "   und die gespeicherte Datei auswählen."
        ),
        # Datei-Dialog
        "dlg_cookie_title":        "cookies.txt auswählen",
        "dlg_cookie_type":         "Netscape Cookie-Datei",
        "dlg_all_files":           "Alle Dateien",
    },

    "en": {
        # Menu bar
        "menu_file":               "File",
        "menu_close":              "Close",
        "menu_browser":            "Browser / Cookies",
        "menu_cookie_select":      "Select cookie file…",
        "menu_cookie_help":        "Cookie file instructions",
        "menu_no_browser":         "No browser (no cookies)",
        "menu_settings":           "Settings",
        "menu_language":           "Language",
        "menu_lang_de":            "Deutsch",
        "menu_lang_en":            "English",
        "menu_format":             "Video format",
        "menu_help":               "Help",
        "menu_about":              "About",
        # Labels
        "lbl_url":                 "YouTube / Video URL (also playlist):",
        "lbl_folder":              "Download folder:",
        # Buttons
        "btn_folder":              "Select folder",
        "btn_smb":                 "Network / UNC",
        "btn_download":            "Start download",
        "btn_cancel":              "Cancel download",
        "btn_queue_mode_off":      "☰ Queue",
        "btn_queue_mode_on":       "✕ Single URL",
        "btn_queue_add":           "+ Add",
        "btn_queue_remove":        "Remove",
        "btn_queue_clear":         "Clear list",
        "btn_queue_download":      "Download all",
        "lbl_queue":               "Queue ({0} URLs):",
        "status_queue_n":          "Queue {0} of {1} …",
        "status_queue_done":       "Done. ({0} of {1} URLs)",
        "err_queue_empty":         "The queue is empty.",
        # Context menu
        "ctx_cut":                 "Cut",
        "ctx_copy":                "Copy",
        "ctx_paste":               "Paste",
        "ctx_select_all":          "Select all",
        # Status
        "status_ready":            "Ready.",
        "status_analyzing":        "Analyzing …",
        "status_starting":         "Starting download …",
        "status_downloading":      "Downloading …",
        "status_downloading_n":    "Download {0} of {1} …",
        "status_done":             "Done.",
        "status_done_n":           "Done. ({0} videos)",
        "status_cancelled":        "Cancelled.",
        "status_error":            "Error.",
        # Browser info line
        "cookie_none":             "No cookies",
        "cookie_file_label":       "Cookie file: {0}",
        "cookie_file_none":        "Cookie file: (none selected)",
        "cookie_from":             "Cookies from: {0}",
        # Errors / notices
        "err_title":               "Error",
        "warn_title":              "Notice",
        "err_no_url":              "Please enter a URL.",
        "err_invalid_url":         "The URL appears to be invalid (must start with http).",
        "err_no_folder":           "Please select a download folder.",
        "err_unc_invalid":         (
            "The UNC path appears to be invalid:\n{0}\n\n"
            "Please use the format \\\\Server\\Share."
        ),
        "smb_dialog_title":        "Network Path / UNC Share",
        "smb_dialog_label":        (
            "Enter UNC path:\n"
            "  \\\\Server\\Share\n"
            "  \\\\Server\\Share\\Subfolder"
        ),
        "err_no_ytdlp":            (
            "yt-dlp is not installed.\n\n"
            "pip install yt-dlp"
        ),
        "warn_no_ffmpeg":          (
            "ffmpeg was not found.\n"
            "Downloads may work, but merging/MP4 output may fail.\n\n"
            "winget install --id=Gyan.FFmpeg -e\n"
            "or: https://ffmpeg.org/download.html"
        ),
        "err_no_cookie_file":      (
            "Cookie file mode is selected,\n"
            "but no valid file was found.\n\n"
            "Please go to 'Browser / Cookies' → 'Select cookie file…'\n"
            "and choose a valid cookies.txt."
        ),
        "warn_encrypted_title":    "⚠ Notice – App-Bound Encryption",
        "warn_encrypted":          (
            "{0} has used App-Bound Encryption for cookies\n"
            "since version 127. yt-dlp usually cannot decrypt these,\n"
            "even when the browser is closed.\n\n"
            "Recommendation: Use 'Select cookie file…' instead.\n"
            "(Instructions: Menu 'Browser / Cookies' → 'Cookie file instructions')\n\n"
            "Try with {0} directly anyway?"
        ),
        "err_cookie_locked_title": "Cookie import failed",
        "err_cookie_locked":       (
            "The browser cookie import failed.\n\n"
            "Cause: App-Bound Encryption (Chrome/Edge since v127)\n"
            "prevents direct access to the cookie database.\n\n"
            "Solution:\n"
            "1. Menu 'Browser / Cookies' → 'Cookie file instructions'\n"
            "2. Export cookies using the extension\n"
            "3. Select 'Select cookie file…' and choose the .txt file"
        ),
        "err_download_title":      "Download error",
        "err_format_unavailable":  (
            "The selected format is not available for this video.\n\n"
            "Please select a different format under Settings → Video format,\n"
            "e.g. 'Best quality (auto)'."
        ),
        "warn_no_download":        (
            "Nothing was downloaded.\n\n"
            "Possible reasons:\n"
            "- Login required (set cookies)\n"
            "- Video is private or unavailable\n"
            "- Geo-restriction active\n"
            "{0}"
        ),
        # About
        "about_title":             "About",
        "about_body":              (
            "{name} v{ver}\n{copy}\n\n"
            "Thanks to the third-party projects used:\n"
            "- yt-dlp (yt-dlp Contributors)\n"
            "- FFmpeg (FFmpeg Developers)\n"
            "- Python / Tkinter (Python Software Foundation & Community)\n\n"
            "Note: This program is not officially affiliated with\n"
            "the projects listed above."
        ),
        # Cookie help
        "cookie_help_title":       "Cookie file – Instructions",
        "cookie_help_body":        (
            "Chrome, Edge, and other Chromium-based browsers\n"
            "have encrypted their cookies since version 127\n"
            "(App-Bound Encryption). yt-dlp can no longer read them directly.\n\n"
            "How to export your cookies as a file:\n\n"
            "1. Install the browser extension:\n"
            "   → 'Get cookies.txt LOCALLY'\n"
            "      (Chrome Web Store / Edge Add-ons)\n\n"
            "2. Open YouTube (or the desired site)\n"
            "   and make sure you are logged in.\n\n"
            "3. Click the extension icon → 'Export' → save cookies.txt.\n\n"
            "4. In the menu 'Browser / Cookies' → 'Select cookie file…'\n"
            "   and select the saved file."
        ),
        # File dialog
        "dlg_cookie_title":        "Select cookies.txt",
        "dlg_cookie_type":         "Netscape Cookie File",
        "dlg_all_files":           "All Files",
    },
}


def t(key: str, *args, **kwargs) -> str:
    """Gibt den übersetzten String für den aktuellen Sprachmodus zurück."""
    lang = lang_var.get() if "lang_var" in globals() else "de"
    text = STRINGS.get(lang, STRINGS["de"]).get(key, f"[{key}]")
    if kwargs:
        return text.format(**kwargs)
    return text.format(*args) if args else text


# ═══════════════════════════════════════════════════════════
#  Videoformate
# ═══════════════════════════════════════════════════════════

FORMATS: list[dict] = [
    {
        "key":        "best_auto",
        "fmt":        "bv+ba/b/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Beste Qualität (automatisch)",
        "en":         "Best quality (auto)",
    },
    {
        "key":        "best_mp4",
        "fmt":        "bv[ext=mp4]+ba[ext=m4a]/bv+ba/b/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Beste Qualität (MP4)",
        "en":         "Best quality (MP4)",
    },
    {
        "key":        "8k",
        "fmt":        "bv[height<=4320]+ba/b[height<=4320]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 8K (4320p)",
        "en":         "Max. 8K (4320p)",
    },
    {
        "key":        "4k",
        "fmt":        "bv[height<=2160]+ba/b[height<=2160]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 4K (2160p)",
        "en":         "Max. 4K (2160p)",
    },
    {
        "key":        "1440p",
        "fmt":        "bv[height<=1440]+ba/b[height<=1440]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 1440p (2K)",
        "en":         "Max. 1440p (2K)",
    },
    {
        "key":        "1080p",
        "fmt":        "bv[height<=1080]+ba/b[height<=1080]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 1080p",
        "en":         "Max. 1080p",
    },
    {
        "key":        "720p",
        "fmt":        "bv[height<=720]+ba/b[height<=720]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 720p",
        "en":         "Max. 720p",
    },
    {
        "key":        "480p",
        "fmt":        "bv[height<=480]+ba/b[height<=480]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 480p",
        "en":         "Max. 480p",
    },
    {
        "key":        "360p",
        "fmt":        "bv[height<=360]+ba/b[height<=360]/best",
        "merge":      "mp4",
        "audio_only": False,
        "de":         "Maximal 360p",
        "en":         "Max. 360p",
    },
    {
        "key":        "audio_m4a",
        "fmt":        "bestaudio[ext=m4a]/bestaudio",
        "merge":      "m4a",
        "audio_only": True,
        "de":         "Nur Audio (M4A – beste Qualität)",
        "en":         "Audio only (M4A – best quality)",
    },
    {
        "key":        "audio_mp3",
        "fmt":        "bestaudio/best",
        "merge":      "mp3",
        "audio_only": True,
        "de":         "Nur Audio (MP3)",
        "en":         "Audio only (MP3)",
    },
]


# ═══════════════════════════════════════════════════════════
#  Browser-Konfiguration
# ═══════════════════════════════════════════════════════════

SUPPORTED_BROWSERS = [
    ("firefox",  "Firefox"),
    ("chrome",   "Chrome   ⚠"),
    ("edge",     "Edge   ⚠"),
    ("brave",    "Brave   ⚠"),
    ("opera",    "Opera   ⚠"),
    ("chromium", "Chromium   ⚠"),
    ("vivaldi",  "Vivaldi   ⚠"),
]

NO_BROWSER         = ""
COOKIE_FILE_MODE   = "__file__"
ENCRYPTED_BROWSERS = {"chrome", "edge", "brave", "opera", "chromium", "vivaldi"}


# ═══════════════════════════════════════════════════════════
#  Tool-Erkennung
# ═══════════════════════════════════════════════════════════

def find_ffmpeg() -> str | None:
    """
    Sucht ffmpeg im PATH und in typischen Windows-Installationsorten.
    winget installiert nach %LOCALAPPDATA%\\Programs\\ffmpeg\\bin,
    manuelle Installationen oft nach %ProgramFiles%\\ffmpeg\\bin.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found

    extra_dirs = []
    local_app = os.environ.get("LOCALAPPDATA", "")
    prog_files = os.environ.get("ProgramFiles", "")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", "")

    if local_app:
        extra_dirs.append(os.path.join(local_app, "Programs", "ffmpeg", "bin"))
    if prog_files:
        extra_dirs.append(os.path.join(prog_files, "ffmpeg", "bin"))
    if prog_files_x86:
        extra_dirs.append(os.path.join(prog_files_x86, "ffmpeg", "bin"))

    for d in extra_dirs:
        candidate = os.path.join(d, "ffmpeg.exe")
        if os.path.isfile(candidate):
            return candidate

    return None


# ═══════════════════════════════════════════════════════════
#  Playlist-Erkennung
# ═══════════════════════════════════════════════════════════

def _is_playlist_url(url: str) -> bool:
    """
    Erkennt Playlist-URLs anhand typischer Query-Parameter und Pfadmuster.
    Wird genutzt um ignoreerrors nur bei Playlists zu aktivieren –
    bei Einzelvideos sollen Fehler sichtbar sein statt still geschluckt zu werden.
    """
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        # YouTube: ?list= oder /playlist
        if "list" in params:
            return True
        if "playlist" in parsed.path.lower():
            return True
        # Allgemeine Playlist-Parameter anderer Plattformen
        if any(k in params for k in ["playlist_id", "album_id", "set"]):
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════
#  yt-dlp Logger – fängt Fehlermeldungen für die UI auf
# ═══════════════════════════════════════════════════════════

class _YdlLogger:
    """
    Leitet yt-dlp Fehlermeldungen in eine Liste um.
    So gehen keine Fehlerinfos verloren auch wenn quiet=True gesetzt ist.
    ANSI-Escape-Codes (Terminal-Farben) werden herausgefiltert.
    """
    _ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

    def __init__(self):
        self.errors: list[str] = []

    @classmethod
    def _clean(cls, msg: str) -> str:
        return cls._ANSI_RE.sub('', msg).strip()

    def debug(self, msg: str):
        pass

    def warning(self, msg: str):
        pass

    def error(self, msg: str):
        self.errors.append(self._clean(msg))
# ═══════════════════════════════════════════════════════════

def is_unc_path(path: str) -> bool:
    """Gibt True zurück wenn der Pfad ein UNC-Pfad ist (\\\\server\\share)."""
    return path.strip().startswith("\\\\") or path.strip().startswith("//")


def normalize_unc(path: str) -> str:
    """Normalisiert UNC-Pfade: // → \\\\ und Slashes → Backslashes."""
    p = path.strip()
    if p.startswith("//"):
        p = "\\\\" + p[2:].replace("/", "\\")
    return p


def validate_unc_path(path: str) -> tuple[str, str | None]:
    """
    Prüft ob ein UNC-Pfad syntaktisch gültig ist und ob er erreichbar ist.
    Gibt (normalisierter_pfad, fehlermeldung) zurück.
    Gibt (pfad, None) zurück wenn OK.
    """
    p = normalize_unc(path)
    parts = p.lstrip("\\").split("\\", 2)
    server = parts[0] if len(parts) > 0 else ""
    share  = parts[1] if len(parts) > 1 else ""
    if not server or not share:
        return "", t("err_unc_invalid", path)
    if not os.path.exists(p):
        return "", t("err_unc_invalid", p)
    return p, None


def effective_download_path(raw: str) -> tuple[str, str | None]:
    """
    Gibt (effektiver_pfad, fehlermeldung) zurück.
    UNC-Pfade werden normalisiert und validiert.
    Lokale Pfade werden direkt durchgereicht.
    """
    if not raw:
        return "", t("err_no_folder")

    if is_unc_path(raw):
        return validate_unc_path(raw)

    return raw, None


# ═══════════════════════════════════════════════════════════
#  Menü aufbauen / Sprache anwenden
# ═══════════════════════════════════════════════════════════

def build_menus():
    """Baut die gesamte Menüleiste neu auf (bei Sprachänderung)."""
    menubar.delete(0, tk.END)

    # ── Datei / File ──────────────────────────────────────
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label=t("menu_close"), command=close_app)
    menubar.add_cascade(label=t("menu_file"), menu=file_menu)

    # ── Browser / Cookies ─────────────────────────────────
    browser_menu = tk.Menu(menubar, tearoff=0)
    browser_menu.add_command(label=t("menu_cookie_select"), command=select_cookie_file)
    browser_menu.add_command(label=t("menu_cookie_help"),   command=show_cookie_help)
    browser_menu.add_separator()
    browser_menu.add_radiobutton(
        label=t("menu_no_browser"),
        variable=browser_var,
        value=NO_BROWSER,
    )
    browser_menu.add_separator()
    for key, display_name in SUPPORTED_BROWSERS:
        browser_menu.add_radiobutton(
            label=display_name,
            variable=browser_var,
            value=key,
        )
    menubar.add_cascade(label=t("menu_browser"), menu=browser_menu)

    # ── Einstellungen / Settings ───────────────────────────
    settings_menu = tk.Menu(menubar, tearoff=0)

    lang_menu = tk.Menu(settings_menu, tearoff=0)
    lang_menu.add_radiobutton(
        label=t("menu_lang_de"),
        variable=lang_var,
        value="de",
        command=apply_language,
    )
    lang_menu.add_radiobutton(
        label=t("menu_lang_en"),
        variable=lang_var,
        value="en",
        command=apply_language,
    )
    settings_menu.add_cascade(label=t("menu_language"), menu=lang_menu)

    fmt_menu = tk.Menu(settings_menu, tearoff=0)
    lang = lang_var.get()
    for fmt in FORMATS:
        fmt_menu.add_radiobutton(
            label=fmt[lang],
            variable=format_var,
            value=fmt["key"],
        )
    settings_menu.add_cascade(label=t("menu_format"), menu=fmt_menu)

    menubar.add_cascade(label=t("menu_settings"), menu=settings_menu)

    # ── Hilfe / Help ──────────────────────────────────────
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label=t("menu_about"), command=show_about)
    menubar.add_cascade(label=t("menu_help"), menu=help_menu)


def apply_language(*_):
    """Aktualisiert alle UI-Texte nach Sprachwechsel."""
    root.title(f"{APP_NAME} v{APP_VERSION} – {APP_COPYRIGHT}")
    build_menus()
    lbl_url.config(text=t("lbl_url"))
    lbl_folder.config(text=t("lbl_folder"))
    btn_folder.config(text=t("btn_folder"))
    btn_smb.config(text=t("btn_smb"))
    if queue_mode_var.get():
        btn_toggle_queue.config(text=t("btn_queue_mode_on"))
        btn_queue_add.config(text=t("btn_queue_add"))
        btn_queue_remove.config(text=t("btn_queue_remove"))
        btn_queue_clear.config(text=t("btn_queue_clear"))
        if not _download_running:
            btn_download.config(text=t("btn_queue_download"))
        _refresh_queue_label()
    else:
        btn_toggle_queue.config(text=t("btn_queue_mode_off"))
        if not _download_running:
            btn_download.config(text=t("btn_download"))
    set_status(current_status_key, *current_status_args)
    update_browser_info()


# ═══════════════════════════════════════════════════════════
#  Status-Verwaltung
# ═══════════════════════════════════════════════════════════

current_status_key:  str   = "status_ready"
current_status_args: tuple = ()
_download_running:   bool  = False
_cancelled:          bool  = False
_url_queue:          list  = []


def set_status(key: str, *args):
    global current_status_key, current_status_args
    current_status_key  = key
    current_status_args = args
    status_var.set(t(key, *args))


# ═══════════════════════════════════════════════════════════
#  GUI-Helfer
# ═══════════════════════════════════════════════════════════

def select_folder():
    """Lokalen Ordner wählen – startet im aktuellen Pfad wenn sinnvoll."""
    initial = download_path_var.get().strip()
    if initial and os.path.isdir(initial):
        start = initial
    else:
        start = os.path.expanduser("~")
    folder = filedialog.askdirectory(initialdir=start)
    if folder:
        download_path_var.set(folder)


def select_unc_path():
    """
    UNC-Dialog: erlaubt manuelle Eingabe eines Netzwerkpfades.
    Unter Windows sind UNC-Pfade direkt als Pfade nutzbar –
    Windows kümmert sich selbst um Mounting/Credentials.
    """
    dialog = tk.Toplevel(root)
    dialog.title(t("smb_dialog_title"))
    dialog.resizable(False, False)
    dialog.grab_set()

    padx, pady = 12, 6

    tk.Label(dialog, text=t("smb_dialog_label"),
             justify="left").pack(anchor="w", padx=padx, pady=(pady * 2, pady))

    current = download_path_var.get().strip()
    initial = current if is_unc_path(current) else "\\\\"
    entry_var = tk.StringVar(value=initial)
    entry = tk.Entry(dialog, textvariable=entry_var, width=50)
    entry.pack(padx=padx, pady=pady)
    entry.select_range(0, tk.END)
    entry.focus_set()

    def use_manual():
        raw = entry_var.get().strip()
        if not raw:
            return
        if is_unc_path(raw):
            normalized = normalize_unc(raw)
            download_path_var.set(normalized)
        else:
            download_path_var.set(raw)
        dialog.destroy()

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=(pady, pady * 2))
    tk.Button(btn_frame, text="✓ OK",        command=use_manual).pack(side="left", padx=4)
    tk.Button(btn_frame, text="✗ Abbrechen", command=dialog.destroy).pack(side="left", padx=4)

    entry.bind("<Return>", lambda _: use_manual())


def select_cookie_file():
    path = filedialog.askopenfilename(
        title=t("dlg_cookie_title"),
        filetypes=[
            (t("dlg_cookie_type"), "*.txt"),
            (t("dlg_all_files"),   "*.*"),
        ],
    )
    if path:
        cookie_file_var.set(path)
        browser_var.set(COOKIE_FILE_MODE)


def update_browser_info(*_):
    b = browser_var.get()
    if b == COOKIE_FILE_MODE:
        f = cookie_file_var.get()
        label = t("cookie_file_label", os.path.basename(f)) if f else t("cookie_file_none")
    elif not b:
        label = t("cookie_none")
    else:
        display = next((n for k, n in SUPPORTED_BROWSERS if k == b), b)
        label = t("cookie_from", display)
    browser_info_var.set(label)


def show_cookie_help():
    messagebox.showinfo(t("cookie_help_title"), t("cookie_help_body"))


def show_about():
    messagebox.showinfo(
        t("about_title"),
        t("about_body", name=APP_NAME, ver=APP_VERSION, copy=APP_COPYRIGHT),
    )


def cancel_download():
    global _cancelled
    _cancelled = True


# ═══════════════════════════════════════════════════════════
#  Warteschlangen-Modus
# ═══════════════════════════════════════════════════════════

def toggle_queue_mode():
    """Schaltet zwischen Einzellink- und Queue-Modus um."""
    if queue_mode_var.get():
        queue_mode_var.set(False)
        queue_frame.pack_forget()
        btn_toggle_queue.config(text=t("btn_queue_mode_off"))
        lbl_url.config(text=t("lbl_url"))
        btn_download.config(text=t("btn_download"), command=download_video)
    else:
        queue_mode_var.set(True)
        queue_frame.pack(fill="x", padx=10, pady=(0, 6), before=sep_widget)
        btn_toggle_queue.config(text=t("btn_queue_mode_on"))
        btn_queue_add.config(text=t("btn_queue_add"))
        btn_queue_remove.config(text=t("btn_queue_remove"))
        btn_queue_clear.config(text=t("btn_queue_clear"))
        lbl_url.config(text=t("lbl_url"))
        btn_download.config(text=t("btn_queue_download"), command=download_queue)
        _refresh_queue_label()
    root.update_idletasks()


def _refresh_queue_label():
    lbl_queue_count.config(text=t("lbl_queue", len(_url_queue)))


def queue_add_url():
    url = url_var.get().strip()
    if not url:
        messagebox.showerror(t("err_title"), t("err_no_url"))
        return
    if not url.startswith("http"):
        messagebox.showerror(t("err_title"), t("err_invalid_url"))
        return
    _url_queue.append(url)
    queue_listbox.insert(tk.END, url)
    url_var.set("")
    url_entry.focus_set()
    _refresh_queue_label()


def queue_remove_selected():
    sel = queue_listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    queue_listbox.delete(idx)
    del _url_queue[idx]
    _refresh_queue_label()


def queue_clear():
    _url_queue.clear()
    queue_listbox.delete(0, tk.END)
    _refresh_queue_label()


def download_queue():
    """Startet den sequenziellen Download aller URLs in der Queue."""
    global _download_running, _cancelled

    if not _url_queue:
        messagebox.showerror(t("err_title"), t("err_queue_empty"))
        return

    download_path_raw = download_path_var.get().strip()
    download_path, path_err = effective_download_path(download_path_raw)
    if path_err:
        messagebox.showerror(t("err_title"), path_err)
        return

    try:
        import yt_dlp as _check  # noqa: F401
    except ImportError:
        messagebox.showerror(t("err_title"), t("err_no_ytdlp"))
        return

    ffmpeg_path      = find_ffmpeg()
    selected_browser = browser_var.get()
    cookie_file      = cookie_file_var.get().strip()

    if selected_browser == COOKIE_FILE_MODE:
        if not cookie_file or not os.path.isfile(cookie_file):
            messagebox.showerror(t("err_title"), t("err_no_cookie_file"))
            return

    if selected_browser in ENCRYPTED_BROWSERS:
        display_clean = next(
            (n.replace("   ⚠", "") for k, n in SUPPORTED_BROWSERS if k == selected_browser),
            selected_browser,
        )
        if not messagebox.askokcancel(t("warn_encrypted_title"),
                                      t("warn_encrypted", display_clean)):
            return

    fmt_info = next((f for f in FORMATS if f["key"] == format_var.get()), FORMATS[0])
    urls     = list(_url_queue)
    total    = len(urls)

    _cancelled        = False
    _download_running = True
    progress_var.set(0)
    progress_bar.configure(mode="determinate", maximum=100)
    set_status("status_analyzing")
    item_var.set("")
    btn_download.config(text=t("btn_cancel"), command=cancel_download)
    root.update_idletasks()

    outtmpl = os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s")

    def run_queue_worker():
        global _download_running, _cancelled

        done_count  = 0
        error_count = 0

        for i, url in enumerate(urls, start=1):
            if _cancelled:
                break

            def _highlight(idx=i - 1):
                queue_listbox.selection_clear(0, tk.END)
                queue_listbox.selection_set(idx)
                queue_listbox.see(idx)
                set_status("status_queue_n", i, total)
                progress_var.set(0)
                item_var.set("")
            root.after(0, _highlight)

            state = {"current_title": ""}

            def progress_hook(d: dict, _i=i, _total=total):
                if _cancelled:
                    raise _CancelledError()
                if d["status"] != "downloading":
                    return
                info  = d.get("info_dict", {})
                title = info.get("title", "")
                if title:
                    state["current_title"] = title[:80]
                total_b = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                dl_b    = d.get("downloaded_bytes", 0)
                pct     = int(dl_b / total_b * 100) if total_b > 0 else 0
                pct     = min(pct, 99)
                ct      = state["current_title"]

                def _ui(p=pct, ct=ct):
                    progress_var.set(p)
                    item_var.set(ct)
                root.after(0, _ui)

            url_logger   = _YdlLogger()
            url_playlist = _is_playlist_url(url)

            ydl_opts: dict = {
                "format":            fmt_info["fmt"],
                "outtmpl":           outtmpl,
                "restrictfilenames": True,
                "trim_file_name":    150,
                "ignoreerrors":      url_playlist,   # True nur bei Playlists
                "retries":           10,
                "fragment_retries":  10,
                "quiet":             True,
                "no_warnings":       True,
                "logger":            url_logger,
                "progress_hooks":    [progress_hook],
            }
            if fmt_info["merge"] == "mp3":
                ydl_opts["postprocessors"] = [{
                    "key":              "FFmpegExtractAudio",
                    "preferredcodec":   "mp3",
                    "preferredquality": "0",
                }]
            else:
                ydl_opts["merge_output_format"] = fmt_info["merge"]
            if ffmpeg_path:
                ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)
            if selected_browser == COOKIE_FILE_MODE:
                ydl_opts["cookiefile"] = cookie_file
            elif selected_browser:
                ydl_opts["cookiesfrombrowser"] = (selected_browser,)

            was_error = False
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                done_count += 1
            except _CancelledError:
                _cancelled = True
                break
            except Exception:
                error_count += 1
                was_error = True

            def _mark_done(idx=i - 1, ok=not was_error):
                queue_listbox.itemconfig(idx, fg="gray" if ok else "red")
            root.after(0, _mark_done)

        def done_ui():
            global _download_running
            _download_running = False
            btn_download.config(text=t("btn_queue_download"), command=download_queue)
            queue_listbox.selection_clear(0, tk.END)
            item_var.set("")
            if _cancelled:
                progress_var.set(0)
                set_status("status_cancelled")
            else:
                progress_var.set(100)
                set_status("status_queue_done", done_count, total)
        root.after(0, done_ui)

    threading.Thread(target=run_queue_worker, daemon=True).start()


def close_app():
    global _cancelled
    _cancelled = True
    root.quit()
    root.destroy()


# ═══════════════════════════════════════════════════════════
#  Clipboard / Kontextmenü
# ═══════════════════════════════════════════════════════════

def safe_paste(entry: tk.Entry):
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
    """Kontextmenü mit Lazy-Label-Update beim Öffnen (automatisch mehrsprachig)."""
    menu = tk.Menu(entry, tearoff=0)
    menu.add_command(command=lambda: entry.event_generate("<<Cut>>"))
    menu.add_command(command=lambda: entry.event_generate("<<Copy>>"))
    menu.add_command(command=lambda: safe_paste(entry))
    menu.add_separator()
    menu.add_command(command=lambda: (
        entry.selection_range(0, tk.END), entry.icursor(tk.END)
    ))

    def popup(event):
        menu.entryconfigure(0, label=t("ctx_cut"))
        menu.entryconfigure(1, label=t("ctx_copy"))
        menu.entryconfigure(2, label=t("ctx_paste"))
        menu.entryconfigure(4, label=t("ctx_select_all"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    entry.bind("<Button-3>",         popup)
    entry.bind("<Control-Button-1>", popup)


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


# ═══════════════════════════════════════════════════════════
#  Download (yt-dlp Python API)
# ═══════════════════════════════════════════════════════════

class _CancelledError(Exception):
    """Wird im Progress-Hook geworfen, um den laufenden Download abzubrechen."""
    pass


def download_video():
    global _download_running, _cancelled

    url           = url_var.get().strip()
    download_path = download_path_var.get().strip()

    if not url:
        messagebox.showerror(t("err_title"), t("err_no_url"))
        return
    if not url.startswith("http"):
        messagebox.showerror(t("err_title"), t("err_invalid_url"))
        return
    if not download_path:
        messagebox.showerror(t("err_title"), t("err_no_folder"))
        return

    download_path, path_err = effective_download_path(download_path)
    if path_err:
        messagebox.showerror(t("err_title"), path_err)
        return

    try:
        import yt_dlp as _check  # noqa: F401
    except ImportError:
        messagebox.showerror(t("err_title"), t("err_no_ytdlp"))
        return

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        messagebox.showwarning(t("warn_title"), t("warn_no_ffmpeg"))

    selected_browser = browser_var.get()
    cookie_file      = cookie_file_var.get().strip()

    if selected_browser == COOKIE_FILE_MODE:
        if not cookie_file or not os.path.isfile(cookie_file):
            messagebox.showerror(t("err_title"), t("err_no_cookie_file"))
            return

    if selected_browser in ENCRYPTED_BROWSERS:
        display_clean = next(
            (n.replace("   ⚠", "") for k, n in SUPPORTED_BROWSERS if k == selected_browser),
            selected_browser,
        )
        if not messagebox.askokcancel(
            t("warn_encrypted_title"),
            t("warn_encrypted", display_clean),
        ):
            return

    fmt_info = next((f for f in FORMATS if f["key"] == format_var.get()), FORMATS[0])

    _cancelled        = False
    _download_running = True
    progress_var.set(0)
    progress_bar.configure(mode="determinate", maximum=100)
    set_status("status_analyzing")
    item_var.set("")
    btn_download.config(text=t("btn_cancel"), command=cancel_download)
    root.update_idletasks()

    outtmpl = os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s")

    def run_worker():
        global _download_running, _cancelled

        # Playlist-URLs bekommen ignoreerrors=True damit einzelne
        # nicht verfügbare Einträge den Rest nicht abbrechen.
        # Einzelvideos bekommen False – Fehler sollen sichtbar sein.
        is_playlist = _is_playlist_url(url)

        logger = _YdlLogger()

        state = {
            "current_item":  0,
            "total_items":   0,
            "current_title": "",
            "downloaded":    False,   # Wurde mindestens ein Download gestartet?
        }

        def progress_hook(d: dict):
            if _cancelled:
                raise _CancelledError()

            if d["status"] == "downloading":
                state["downloaded"] = True

            if d["status"] != "downloading":
                return

            info = d.get("info_dict", {})

            idx = info.get("playlist_index") or info.get("playlist_autonumber")
            n   = info.get("n_entries")
            if idx:
                state["current_item"] = int(idx)
            if n:
                state["total_items"] = int(n)

            title = info.get("title", "")
            if title:
                state["current_title"] = title[:80]

            total      = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            pct = int(downloaded / total * 100) if total > 0 else 0
            pct = min(pct, 99)

            ci = state["current_item"]
            ti = state["total_items"]
            ct = state["current_title"]

            def _ui_update(p=pct, ci=ci, ti=ti, ct=ct):
                progress_var.set(p)
                if ti > 1:
                    set_status("status_downloading_n", ci, ti)
                else:
                    set_status("status_downloading")
                item_var.set(ct)

            root.after(0, _ui_update)

        ydl_opts: dict = {
            "format":            fmt_info["fmt"],
            "outtmpl":           outtmpl,
            "restrictfilenames": True,
            "trim_file_name":    150,
            "ignoreerrors":      is_playlist,   # True nur bei Playlists
            "retries":           10,
            "fragment_retries":  10,
            "quiet":             True,
            "no_warnings":       True,
            "logger":            logger,        # Fehler auffangen statt verwerfen
            "progress_hooks":    [progress_hook],
        }

        if fmt_info["merge"] == "mp3":
            ydl_opts["postprocessors"] = [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   "mp3",
                "preferredquality": "0",
            }]
        else:
            ydl_opts["merge_output_format"] = fmt_info["merge"]

        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)

        if selected_browser == COOKIE_FILE_MODE:
            ydl_opts["cookiefile"] = cookie_file
        elif selected_browser:
            ydl_opts["cookiesfrombrowser"] = (selected_browser,)

        error_msg     = ""
        was_cancelled = False

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except _CancelledError:
            was_cancelled = True
        except Exception as ex:
            error_msg = _YdlLogger._clean(str(ex))

        total_items   = state["total_items"]
        was_download  = state["downloaded"]
        logged_errors = logger.errors

        def done_ui():
            global _download_running
            _download_running = False
            btn_download.config(text=t("btn_download"), command=download_video)
            item_var.set("")

            if was_cancelled:
                progress_var.set(0)
                set_status("status_cancelled")
                return

            if error_msg:
                progress_var.set(0)
                set_status("status_error")
                if "Could not copy" in error_msg and "cookie database" in error_msg:
                    messagebox.showerror(t("err_cookie_locked_title"), t("err_cookie_locked"))
                elif "Requested format is not available" in error_msg or \
                     "format is not available" in error_msg.lower():
                    messagebox.showerror(t("err_download_title"), t("err_format_unavailable"))
                else:
                    messagebox.showerror(t("err_download_title"), error_msg[-1500:])
                return

            # Kein Download gestartet, kein harter Fehler →
            # Fehlerdetails aus dem Logger anzeigen (z.B. Login required, geo-block)
            if not was_download:
                progress_var.set(0)
                set_status("status_error")
                joined = "\n".join(logged_errors[-3:])
                if "Requested format is not available" in joined or \
                   "format is not available" in joined.lower():
                    messagebox.showerror(t("err_download_title"), t("err_format_unavailable"))
                else:
                    detail = joined if joined else ""
                    messagebox.showwarning(t("warn_title"), t("warn_no_download", detail))
                return

            progress_var.set(100)
            if total_items > 1:
                set_status("status_done_n", total_items)
            else:
                set_status("status_done")

        root.after(0, done_ui)

    threading.Thread(target=run_worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════
#  GUI aufbauen
# ═══════════════════════════════════════════════════════════

root = tk.Tk()
root.title(f"{APP_NAME} v{APP_VERSION} – {APP_COPYRIGHT}")

# ── Globale Variablen ──────────────────────────────────────
lang_var          = tk.StringVar(value="de")
format_var        = tk.StringVar(value="best_auto")
browser_var       = tk.StringVar(value=NO_BROWSER)
cookie_file_var   = tk.StringVar(value="")
url_var           = tk.StringVar()
download_path_var = tk.StringVar()
status_var        = tk.StringVar()
item_var          = tk.StringVar(value="")
browser_info_var  = tk.StringVar()
progress_var      = tk.DoubleVar(value=0)
queue_mode_var    = tk.BooleanVar(value=False)

# ── Menüleiste ────────────────────────────────────────────
menubar = tk.Menu(root)
root.config(menu=menubar)
build_menus()

# ── Widgets ───────────────────────────────────────────────
padx = 10

lbl_url = tk.Label(root, text="")
lbl_url.pack(pady=(10, 0))

_url_row = tk.Frame(root)
_url_row.pack(fill="x", padx=padx, pady=5)

url_entry = tk.Entry(_url_row, textvariable=url_var, width=70)
url_entry.pack(side="left", fill="x", expand=True)

btn_toggle_queue = tk.Button(_url_row, text="", command=toggle_queue_mode)
btn_toggle_queue.pack(side="left", padx=(6, 0))

# Queue-Modus: Listbox + Buttons (anfangs versteckt)
queue_frame = tk.Frame(root)

lbl_queue_count = tk.Label(queue_frame, text="", anchor="w")
lbl_queue_count.pack(fill="x")

_qlist_frame = tk.Frame(queue_frame, bd=1, relief="sunken")
_qlist_frame.pack(fill="x", pady=(2, 4))

queue_listbox = tk.Listbox(_qlist_frame, height=6, width=80,
                           selectmode=tk.SINGLE, activestyle="underline")
queue_listbox.pack(side="left", fill="both", expand=True)
_qsb = tk.Scrollbar(_qlist_frame, orient="vertical", command=queue_listbox.yview)
_qsb.pack(side="right", fill="y")
queue_listbox.config(yscrollcommand=_qsb.set)

_qbtn_frame = tk.Frame(queue_frame)
_qbtn_frame.pack(anchor="w")
btn_queue_add    = tk.Button(_qbtn_frame, text="", command=queue_add_url)
btn_queue_remove = tk.Button(_qbtn_frame, text="", command=queue_remove_selected)
btn_queue_clear  = tk.Button(_qbtn_frame, text="", command=queue_clear)
btn_queue_add.pack(side="left", padx=(0, 4))
btn_queue_remove.pack(side="left", padx=(0, 4))
btn_queue_clear.pack(side="left")

url_entry.bind("<Return>", lambda _: queue_add_url() if queue_mode_var.get() else None)

# Ordner-Zeile
lbl_folder = tk.Label(root, text="")
lbl_folder.pack(pady=(10, 0))

path_entry = tk.Entry(root, textvariable=download_path_var, width=80)
path_entry.pack(padx=padx, pady=5)

_btn_frame = tk.Frame(root)
_btn_frame.pack()
btn_folder = tk.Button(_btn_frame, text="", command=select_folder)
btn_folder.pack(side="left", padx=(0, 6))
btn_smb = tk.Button(_btn_frame, text="", command=select_unc_path)
btn_smb.pack(side="left")

for entry in (url_entry, path_entry):
    add_context_menu_to_entry(entry)
    add_shift_insert_paste(entry)
    add_ctrl_v_safe_paste(entry)

sep_widget = ttk.Separator(root, orient="horizontal")
sep_widget.pack(fill="x", padx=padx, pady=(10, 6))

tk.Label(root, textvariable=browser_info_var, anchor="w",
         justify="left", fg="gray").pack(fill="x", padx=padx)
tk.Label(root, textvariable=status_var, anchor="w",
         justify="left").pack(fill="x", padx=padx, pady=(2, 0))
tk.Label(root, textvariable=item_var, anchor="w",
         justify="left", fg="gray").pack(fill="x", padx=padx, pady=(0, 6))

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=padx, pady=(0, 10))

btn_download = tk.Button(root, text="", command=download_video)
btn_download.pack(pady=(0, 15))

# ── Traces für Browser-Info ────────────────────────────────
browser_var.trace_add("write",     update_browser_info)
cookie_file_var.trace_add("write", update_browser_info)

# ── Initialzustand setzen ─────────────────────────────────
apply_language()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
