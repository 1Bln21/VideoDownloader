#   - Video Downloader mit yt-dlp.exe (Subprocess) + Tkinter
#   - Copyright 2026 by Lars Kuehn
#   - Version 1.2.0-win (16.04.2026)
#   - Licensed under the MIT License
#   - https://github.com/1Bln21/VideoDownloader
#   - Zielplattform: Windows 10 / 11
#
#   - Voraussetzungen:
#       yt-dlp.exe  im App-Verzeichnis (wird vom Installer mitgeliefert)
#       ffmpeg.exe  im App-Verzeichnis (wird vom Installer mitgeliefert)
#       Python 3.11+ mit Tkinter (Standardinstallation Windows)
#
#   - Änderungshistorie:
#       1.0.0  Erstveröffentlichung (Windows, yt-dlp + aria2 als EXE)
#       1.1.0  Linux-Port (CachyOS/Arch), yt-dlp als Python-Modul
#       1.1.1  SMB/Netzwerkfreigaben, Queue-Modus
#       1.1.2  Windows-Port zurück, UNC-Pfade, Installer
#       1.1.3  8K-Support, robustere Format-Strings, ignoreerrors smart,
#              ANSI-Filter, Fehlererkennung verbessert
#       1.1.4  Node.js JS-Runtime für YouTube n-Challenge (experimentell)
#       1.2.0  KOMPLETTE NEUFASSUNG der Download-Engine:
#              - yt-dlp.exe als Subprocess statt Python-Modul
#              - EJS/Challenge-Solver bereits in yt-dlp.exe eingebaut
#              - Kein Python-Paket-Versions-Chaos mehr
#              - Fortschritt via stdout-Parsing (--progress --newline)
#              - yt-dlp.exe wird vom Installer aus GitHub Releases gezogen
#              - Automatischer Update-Check für yt-dlp.exe beim Start

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import subprocess
import os
import re
import shutil
import urllib.parse
import urllib.request
import json


APP_NAME      = "Video Downloader"
APP_VERSION   = "1.2.0-win"
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
        "status_downloading":      "Lade herunter …",
        "status_downloading_n":    "Download {0} von {1} …",
        "status_merging":          "Zusammenführen …",
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
            "yt-dlp.exe wurde nicht gefunden.\n\n"
            "Erwartet in:\n{0}\n\n"
            "Bitte den Installer erneut ausführen oder\n"
            "yt-dlp.exe manuell von https://github.com/yt-dlp/yt-dlp/releases\n"
            "in den App-Ordner kopieren."
        ),
        "warn_no_ffmpeg":          (
            "ffmpeg.exe wurde nicht gefunden.\n"
            "Merging/MP4-Ausgabe kann scheitern.\n\n"
            "ffmpeg.exe in den App-Ordner kopieren\n"
            "oder: winget install --id=Gyan.FFmpeg -e"
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
        # Updater
        "menu_check_updates":      "Auf Updates prüfen…",
        "upd_title":               "Update-Prüfung",
        "upd_checking":            "Prüfe Versionen …",
        "upd_current":             "Installiert",
        "upd_latest":              "Verfügbar",
        "upd_uptodate":            "✓ Aktuell",
        "upd_available":           "↑ Update verfügbar",
        "upd_unknown":             "?  Unbekannt",
        "upd_not_found":           "Nicht installiert",
        "upd_btn_update":          "Auswahl aktualisieren",
        "upd_btn_close":           "Schließen",
        "upd_downloading":         "Wird heruntergeladen …",
        "upd_installing":          "Wird installiert …",
        "upd_done":                "Update abgeschlossen.",
        "upd_err_network":         "Netzwerkfehler – GitHub nicht erreichbar.",
        "upd_err_download":        "Download fehlgeschlagen: {0}",
        "upd_no_selection":        "Bitte mindestens eine Komponente auswählen.",
        "upd_app_restart":         (
            "Die App wurde aktualisiert.\n\n"
            "Der Installer wird jetzt gestartet.\n"
            "Die App wird danach automatisch neu gestartet."
        ),
        "upd_app_name":            "Video Downloader (App)",
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
        "status_downloading":      "Downloading …",
        "status_downloading_n":    "Download {0} of {1} …",
        "status_merging":          "Merging …",
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
            "yt-dlp.exe was not found.\n\n"
            "Expected at:\n{0}\n\n"
            "Please re-run the installer or\n"
            "copy yt-dlp.exe manually from https://github.com/yt-dlp/yt-dlp/releases\n"
            "into the app folder."
        ),
        "warn_no_ffmpeg":          (
            "ffmpeg.exe was not found.\n"
            "Merging/MP4 output may fail.\n\n"
            "Copy ffmpeg.exe into the app folder\n"
            "or: winget install --id=Gyan.FFmpeg -e"
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
        # Updater
        "menu_check_updates":      "Check for updates…",
        "upd_title":               "Update Check",
        "upd_checking":            "Checking versions …",
        "upd_current":             "Installed",
        "upd_latest":              "Available",
        "upd_uptodate":            "✓ Up to date",
        "upd_available":           "↑ Update available",
        "upd_unknown":             "?  Unknown",
        "upd_not_found":           "Not installed",
        "upd_btn_update":          "Update selection",
        "upd_btn_close":           "Close",
        "upd_downloading":         "Downloading …",
        "upd_installing":          "Installing …",
        "upd_done":                "Update complete.",
        "upd_err_network":         "Network error – GitHub not reachable.",
        "upd_err_download":        "Download failed: {0}",
        "upd_no_selection":        "Please select at least one component.",
        "upd_app_restart":         (
            "The app has been updated.\n\n"
            "The installer will now start.\n"
            "The app will restart automatically afterwards."
        ),
        "upd_app_name":            "Video Downloader (App)",
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

def _app_dir() -> str:
    """Gibt das Verzeichnis der laufenden EXE / des Scripts zurück."""
    if getattr(__import__("sys"), "frozen", False):
        return os.path.dirname(__import__("sys").executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_ytdlp() -> str | None:
    """
    Sucht yt-dlp.exe zuerst im App-Verzeichnis (vom Installer platziert),
    dann im PATH als Fallback.
    """
    # App-Verzeichnis hat Vorrang – dort legt der Installer yt-dlp.exe ab
    local = os.path.join(_app_dir(), "yt-dlp.exe")
    if os.path.isfile(local):
        return local
    # PATH-Fallback für Entwickler-Umgebungen
    return shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")


def find_ffmpeg() -> str | None:
    """
    Sucht ffmpeg.exe zuerst im App-Verzeichnis,
    dann in typischen Windows-Installationsorten und PATH.
    """
    local = os.path.join(_app_dir(), "ffmpeg.exe")
    if os.path.isfile(local):
        return local

    found = shutil.which("ffmpeg")
    if found:
        return found

    extra_dirs = []
    local_app      = os.environ.get("LOCALAPPDATA", "")
    prog_files     = os.environ.get("ProgramFiles", "")
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
#  Versions-Erkennung & Updater
# ═══════════════════════════════════════════════════════════

def _get_local_ytdlp_version() -> str:
    """Ermittelt die lokale yt-dlp.exe Version via --version."""
    exe = find_ytdlp()
    if not exe:
        return ""
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_local_ffmpeg_version() -> str:
    """Ermittelt die lokale ffmpeg.exe Version."""
    exe = find_ffmpeg()
    if not exe:
        return ""
    try:
        result = subprocess.run(
            [exe, "-version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # Erste Zeile: "ffmpeg version N.N.N ..."
        first = result.stdout.splitlines()[0] if result.stdout else ""
        m = re.search(r'version\s+([\S]+)', first)
        return m.group(1) if m else first[:30]
    except Exception:
        return ""


def _fetch_github_release(repo: str) -> dict | None:
    """
    Ruft die neueste GitHub-Release-Info ab.
    repo z.B. 'yt-dlp/yt-dlp' oder 'GyanD/codexffmpeg'
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VideoDownloader-Updater"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _find_asset_url(release: dict, name: str) -> str:
    """Sucht in den Release-Assets nach einer Datei mit dem angegebenen Namen."""
    for asset in release.get("assets", []):
        if asset.get("name", "") == name:
            return asset.get("browser_download_url", "")
    return ""


def _download_to_file(url: str, dest: str) -> bool:
    """Lädt eine Datei herunter — einfacher urllib-Download."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VideoDownloader-Updater"})
        with urllib.request.urlopen(req, timeout=120) as resp, \
             open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception:
        return False


def show_updater():
    """
    Öffnet den Update-Dialog.
    Prüft yt-dlp.exe und ffmpeg.exe gegen GitHub Releases
    und ermöglicht das manuelle Aktualisieren einzelner Komponenten.
    """
    dialog = tk.Toplevel(root)
    dialog.title(t("upd_title"))
    dialog.resizable(False, False)
    dialog.grab_set()

    padx, pady = 14, 6

    # ── Status-Label ──────────────────────────────────────
    status_lbl = tk.Label(dialog, text=t("upd_checking"), anchor="w", fg="gray")
    status_lbl.pack(fill="x", padx=padx, pady=(pady * 2, pady))

    # ── Tabelle ───────────────────────────────────────────
    table = tk.Frame(dialog)
    table.pack(fill="x", padx=padx, pady=pady)

    headers = ["", "Komponente", t("upd_current"), t("upd_latest"), "Status"]
    col_widths = [3, 14, 18, 18, 18]
    for col, (h, w) in enumerate(zip(headers, col_widths)):
        tk.Label(table, text=h, font=(None, 9, "bold"), width=w, anchor="w").grid(
            row=0, column=col, padx=2, pady=2, sticky="w")

    # Checkboxen und Zeilendaten
    ytdlp_var  = tk.BooleanVar(value=False)
    ffmpeg_var = tk.BooleanVar(value=False)
    app_var    = tk.BooleanVar(value=False)

    rows = {
        "app":    {"name": t("upd_app_name"), "var": app_var,    "row": 1},
        "ytdlp":  {"name": "yt-dlp.exe",      "var": ytdlp_var,  "row": 2},
        "ffmpeg": {"name": "ffmpeg.exe",       "var": ffmpeg_var, "row": 3},
    }

    labels = {}
    for key, info in rows.items():
        chk = tk.Checkbutton(table, variable=info["var"])
        chk.grid(row=info["row"], column=0, padx=2, pady=3, sticky="w")
        tk.Label(table, text=info["name"], width=col_widths[1], anchor="w").grid(
            row=info["row"], column=1, padx=2, pady=3, sticky="w")
        lbl_cur = tk.Label(table, text="…", width=col_widths[2], anchor="w", fg="gray")
        lbl_cur.grid(row=info["row"], column=2, padx=2, pady=3, sticky="w")
        lbl_lat = tk.Label(table, text="…", width=col_widths[3], anchor="w", fg="gray")
        lbl_lat.grid(row=info["row"], column=3, padx=2, pady=3, sticky="w")
        lbl_sts = tk.Label(table, text="…", width=col_widths[4], anchor="w", fg="gray")
        lbl_sts.grid(row=info["row"], column=4, padx=2, pady=3, sticky="w")
        labels[key] = {"cur": lbl_cur, "lat": lbl_lat, "sts": lbl_sts, "chk": chk}

    ttk.Separator(dialog, orient="horizontal").pack(fill="x", padx=padx, pady=pady)

    # ── Fortschrittsbalken ────────────────────────────────
    upd_progress = ttk.Progressbar(dialog, mode="indeterminate")
    upd_progress.pack(fill="x", padx=padx, pady=(0, pady))

    # ── Buttons ───────────────────────────────────────────
    btn_frame  = tk.Frame(dialog)
    btn_frame.pack(pady=(0, pady * 2))
    btn_update = tk.Button(btn_frame, text=t("upd_btn_update"),
                           state="disabled", width=20)
    btn_update.pack(side="left", padx=4)
    tk.Button(btn_frame, text=t("upd_btn_close"),
              command=dialog.destroy, width=10).pack(side="left", padx=4)

    # ── Versions-Daten (werden im Thread befüllt) ─────────
    version_data = {}

    def _check_worker():
        """Läuft im Thread — fragt lokale Versionen und GitHub API ab."""
        # Lokale Versionen
        local_ytdlp  = _get_local_ytdlp_version()
        local_ffmpeg = _get_local_ffmpeg_version()
        local_app    = APP_VERSION.replace("-win", "")

        # GitHub Releases
        rel_ytdlp  = _fetch_github_release("yt-dlp/yt-dlp")
        rel_ffmpeg = _fetch_github_release("GyanD/codexffmpeg")
        rel_app    = _fetch_github_release("1Bln21/VideoDownloader")

        latest_ytdlp  = rel_ytdlp.get("tag_name", "").lstrip("v")  if rel_ytdlp  else ""
        latest_ffmpeg = rel_ffmpeg.get("tag_name", "").lstrip("v") if rel_ffmpeg else ""
        latest_app    = rel_app.get("tag_name", "").lstrip("v")    if rel_app    else ""

        url_ytdlp  = _find_asset_url(rel_ytdlp,  "yt-dlp.exe") if rel_ytdlp  else ""

        # ffmpeg: essentials-ZIP suchen
        url_ffmpeg = ""
        if rel_ffmpeg:
            for asset in rel_ffmpeg.get("assets", []):
                name = asset.get("name", "")
                if "essentials_build" in name and name.endswith(".zip"):
                    url_ffmpeg = asset.get("browser_download_url", "")
                    break

        # App-Installer suchen — Name: VideoDownloader_Setup_X.Y.Z.exe
        url_app = ""
        if rel_app:
            for asset in rel_app.get("assets", []):
                name = asset.get("name", "")
                if name.startswith("VideoDownloader_Setup") and name.endswith(".exe"):
                    url_app = asset.get("browser_download_url", "")
                    break

        version_data["ytdlp"]  = {
            "local":  local_ytdlp  or t("upd_not_found"),
            "latest": latest_ytdlp or t("upd_unknown"),
            "url":    url_ytdlp,
            "type":   "exe",
        }
        version_data["ffmpeg"] = {
            "local":  local_ffmpeg or t("upd_not_found"),
            "latest": latest_ffmpeg or t("upd_unknown"),
            "url":    url_ffmpeg,
            "type":   "zip_ffmpeg",
        }
        version_data["app"] = {
            "local":  local_app,
            "latest": latest_app or t("upd_unknown"),
            "url":    url_app,
            "type":   "installer",
        }

        def _update_ui():
            upd_progress.stop()
            upd_progress.configure(mode="determinate", value=0)

            any_update = False
            for key, data in version_data.items():
                lbl = labels[key]
                lbl["cur"].config(text=data["local"][:17],  fg="black")
                lbl["lat"].config(text=data["latest"][:17], fg="black")

                if not data["url"]:
                    lbl["sts"].config(text=t("upd_unknown"), fg="gray")
                    lbl["chk"].config(state="disabled")
                elif data["local"] == t("upd_not_found"):
                    lbl["sts"].config(text=t("upd_not_found"), fg="orange")
                    any_update = True
                elif data["local"].split()[0] == data["latest"].split()[0]:
                    lbl["sts"].config(text=t("upd_uptodate"), fg="green")
                    lbl["chk"].config(state="disabled")
                else:
                    lbl["sts"].config(text=t("upd_available"), fg="blue")
                    any_update = True

            if any_update:
                btn_update.config(state="normal")
                status_lbl.config(text="", fg="gray")
            else:
                status_lbl.config(text=t("upd_uptodate"), fg="green")

        dialog.after(0, _update_ui)

    def _do_update():
        """Startet den eigentlichen Download der ausgewählten Komponenten."""
        selected = {k: v for k, v in version_data.items()
                    if rows[k]["var"].get() and v.get("url")}
        if not selected:
            messagebox.showwarning(t("warn_title"), t("upd_no_selection"), parent=dialog)
            return

        btn_update.config(state="disabled")
        upd_progress.configure(mode="indeterminate")
        upd_progress.start(10)

        def _worker():
            import tempfile, zipfile
            errors      = []
            do_restart  = False

            for key, data in selected.items():
                url      = data["url"]
                typ      = data.get("type", "exe")
                name     = rows[key]["name"]
                dialog.after(0, lambda n=name: status_lbl.config(
                    text=f"{t('upd_downloading')} {n}", fg="gray"))
                try:
                    suffix = ".zip" if typ in ("zip_ffmpeg",) else ".exe"
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                        tmp_path = tmp.name

                    if not _download_to_file(url, tmp_path):
                        errors.append(name)
                        continue

                    dialog.after(0, lambda n=name: status_lbl.config(
                        text=f"{t('upd_installing')} {n}", fg="gray"))

                    dest_dir = _app_dir()

                    if typ == "installer":
                        # App-Update: Installer silent starten, App beendet sich danach
                        do_restart = True
                        installer_path = os.path.join(
                            os.environ.get("TEMP", dest_dir),
                            "VideoDownloader_Update.exe"
                        )
                        shutil.copy2(tmp_path, installer_path)

                    elif typ == "exe":
                        dest = os.path.join(dest_dir, "yt-dlp.exe")
                        old  = dest + ".old"
                        try:
                            os.replace(dest, old)
                        except Exception:
                            pass
                        try:
                            shutil.copy2(tmp_path, dest)
                            if os.path.exists(old):
                                os.remove(old)
                        except Exception as ex:
                            errors.append(f"yt-dlp.exe: {ex}")

                    elif typ == "zip_ffmpeg":
                        try:
                            with zipfile.ZipFile(tmp_path, "r") as zf:
                                for member in zf.namelist():
                                    base = os.path.basename(member)
                                    if base in ("ffmpeg.exe", "ffprobe.exe"):
                                        with zf.open(member) as src, \
                                             open(os.path.join(dest_dir, base), "wb") as dst:
                                            shutil.copyfileobj(src, dst)
                        except Exception as ex:
                            errors.append(f"ffmpeg.exe: {ex}")

                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

                except Exception as ex:
                    errors.append(f"{name}: {ex}")

            def _done():
                upd_progress.stop()
                upd_progress.configure(mode="determinate", value=100)

                if do_restart and not errors:
                    # Installer starten und App beenden
                    messagebox.showinfo(t("upd_title"), t("upd_app_restart"),
                                        parent=dialog)
                    installer = os.path.join(
                        os.environ.get("TEMP", _app_dir()),
                        "VideoDownloader_Update.exe"
                    )
                    try:
                        subprocess.Popen(
                            [installer,
                             "/SILENT", "/SUPPRESSMSGBOXES",
                             "/NORESTART", "/SP-"],
                            creationflags=subprocess.DETACHED_PROCESS |
                                          subprocess.CREATE_NEW_PROCESS_GROUP,
                        )
                    except Exception:
                        pass
                    close_app()
                    return

                if errors:
                    status_lbl.config(
                        text=t("upd_err_download", ", ".join(errors)), fg="red")
                else:
                    status_lbl.config(text=t("upd_done"), fg="green")

                btn_update.config(state="normal")
                threading.Thread(target=_check_worker, daemon=True).start()

            dialog.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    btn_update.config(command=_do_update)

    # Prüfung starten
    upd_progress.start(10)
    threading.Thread(target=_check_worker, daemon=True).start()
# ═══════════════════════════════════════════════════════════

def _is_playlist_url(url: str) -> bool:
    """Erkennt Playlist-URLs anhand typischer Query-Parameter."""
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "list" in params:
            return True
        if "playlist" in parsed.path.lower():
            return True
        if any(k in params for k in ["playlist_id", "album_id", "set"]):
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════
#  ANSI-Cleaner
# ═══════════════════════════════════════════════════════════

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

def _clean(msg: str) -> str:
    return _ANSI_RE.sub('', msg).strip()


# ═══════════════════════════════════════════════════════════
#  UNC / Netzwerkpfad-Hilfsfunktionen
# ═══════════════════════════════════════════════════════════

def is_unc_path(path: str) -> bool:
    return path.strip().startswith("\\\\") or path.strip().startswith("//")


def normalize_unc(path: str) -> str:
    p = path.strip()
    if p.startswith("//"):
        p = "\\\\" + p[2:].replace("/", "\\")
    return p


def validate_unc_path(path: str) -> tuple[str, str | None]:
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
    if not raw:
        return "", t("err_no_folder")
    if is_unc_path(raw):
        return validate_unc_path(raw)
    return raw, None


# ═══════════════════════════════════════════════════════════
#  Menü aufbauen / Sprache anwenden
# ═══════════════════════════════════════════════════════════

def build_menus():
    menubar.delete(0, tk.END)

    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label=t("menu_close"), command=close_app)
    menubar.add_cascade(label=t("menu_file"), menu=file_menu)

    browser_menu = tk.Menu(menubar, tearoff=0)
    browser_menu.add_command(label=t("menu_cookie_select"), command=select_cookie_file)
    browser_menu.add_command(label=t("menu_cookie_help"),   command=show_cookie_help)
    browser_menu.add_separator()
    browser_menu.add_radiobutton(label=t("menu_no_browser"), variable=browser_var, value=NO_BROWSER)
    browser_menu.add_separator()
    for key, display_name in SUPPORTED_BROWSERS:
        browser_menu.add_radiobutton(label=display_name, variable=browser_var, value=key)
    menubar.add_cascade(label=t("menu_browser"), menu=browser_menu)

    settings_menu = tk.Menu(menubar, tearoff=0)
    lang_menu = tk.Menu(settings_menu, tearoff=0)
    lang_menu.add_radiobutton(label=t("menu_lang_de"), variable=lang_var, value="de", command=apply_language)
    lang_menu.add_radiobutton(label=t("menu_lang_en"), variable=lang_var, value="en", command=apply_language)
    settings_menu.add_cascade(label=t("menu_language"), menu=lang_menu)

    fmt_menu = tk.Menu(settings_menu, tearoff=0)
    lang = lang_var.get()
    for fmt in FORMATS:
        fmt_menu.add_radiobutton(label=fmt[lang], variable=format_var, value=fmt["key"])
    settings_menu.add_cascade(label=t("menu_format"), menu=fmt_menu)
    menubar.add_cascade(label=t("menu_settings"), menu=settings_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label=t("menu_check_updates"), command=show_updater)
    help_menu.add_separator()
    help_menu.add_command(label=t("menu_about"), command=show_about)
    menubar.add_cascade(label=t("menu_help"), menu=help_menu)


def apply_language(*_):
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
_current_process:    None  = None   # Läuft als subprocess.Popen


def set_status(key: str, *args):
    global current_status_key, current_status_args
    current_status_key  = key
    current_status_args = args
    status_var.set(t(key, *args))


# ═══════════════════════════════════════════════════════════
#  GUI-Helfer
# ═══════════════════════════════════════════════════════════

def select_folder():
    initial = download_path_var.get().strip()
    start = initial if (initial and os.path.isdir(initial)) else os.path.expanduser("~")
    folder = filedialog.askdirectory(initialdir=start)
    if folder:
        download_path_var.set(folder)


def select_unc_path():
    dialog = tk.Toplevel(root)
    dialog.title(t("smb_dialog_title"))
    dialog.resizable(False, False)
    dialog.grab_set()
    padx, pady = 12, 6
    tk.Label(dialog, text=t("smb_dialog_label"), justify="left").pack(anchor="w", padx=padx, pady=(pady * 2, pady))
    current = download_path_var.get().strip()
    entry_var = tk.StringVar(value=current if is_unc_path(current) else "\\\\")
    entry = tk.Entry(dialog, textvariable=entry_var, width=50)
    entry.pack(padx=padx, pady=pady)
    entry.select_range(0, tk.END)
    entry.focus_set()

    def use_manual():
        raw = entry_var.get().strip()
        if not raw:
            return
        download_path_var.set(normalize_unc(raw) if is_unc_path(raw) else raw)
        dialog.destroy()

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=(pady, pady * 2))
    tk.Button(btn_frame, text="✓ OK",        command=use_manual).pack(side="left", padx=4)
    tk.Button(btn_frame, text="✗ Abbrechen", command=dialog.destroy).pack(side="left", padx=4)
    entry.bind("<Return>", lambda _: use_manual())


def select_cookie_file():
    path = filedialog.askopenfilename(
        title=t("dlg_cookie_title"),
        filetypes=[(t("dlg_cookie_type"), "*.txt"), (t("dlg_all_files"), "*.*")],
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
    messagebox.showinfo(t("about_title"),
        t("about_body", name=APP_NAME, ver=APP_VERSION, copy=APP_COPYRIGHT))


def cancel_download():
    global _cancelled, _current_process
    _cancelled = True
    if _current_process and _current_process.poll() is None:
        try:
            _current_process.terminate()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  Warteschlangen-Modus
# ═══════════════════════════════════════════════════════════

def toggle_queue_mode():
    if queue_mode_var.get():
        queue_mode_var.set(False)
        queue_frame.pack_forget()
        btn_toggle_queue.config(text=t("btn_queue_mode_off"))
        btn_download.config(text=t("btn_download"), command=download_video)
    else:
        queue_mode_var.set(True)
        queue_frame.pack(fill="x", padx=10, pady=(0, 6), before=sep_widget)
        btn_toggle_queue.config(text=t("btn_queue_mode_on"))
        btn_queue_add.config(text=t("btn_queue_add"))
        btn_queue_remove.config(text=t("btn_queue_remove"))
        btn_queue_clear.config(text=t("btn_queue_clear"))
        btn_download.config(text=t("btn_queue_download"), command=download_queue)
        _refresh_queue_label()
    root.update_idletasks()


def _refresh_queue_label():
    lbl_queue_count.config(text=t("lbl_queue", len(_url_queue)))


def queue_add_url():
    url = url_var.get().strip()
    if not url:
        messagebox.showerror(t("err_title"), t("err_no_url")); return
    if not url.startswith("http"):
        messagebox.showerror(t("err_title"), t("err_invalid_url")); return
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


def close_app():
    global _cancelled
    _cancelled = True
    if _current_process and _current_process.poll() is None:
        try:
            _current_process.terminate()
        except Exception:
            pass
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
    menu = tk.Menu(entry, tearoff=0)
    menu.add_command(command=lambda: entry.event_generate("<<Cut>>"))
    menu.add_command(command=lambda: entry.event_generate("<<Copy>>"))
    menu.add_command(command=lambda: safe_paste(entry))
    menu.add_separator()
    menu.add_command(command=lambda: (entry.selection_range(0, tk.END), entry.icursor(tk.END)))

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
    entry.bind("<Shift-Insert>", lambda _e: (safe_paste(entry), "break")[1])


def add_ctrl_v_safe_paste(entry: tk.Entry):
    def _h(_e):
        safe_paste(entry)
        return "break"
    entry.bind("<Control-v>", _h)
    entry.bind("<Control-V>", _h)


# ═══════════════════════════════════════════════════════════
#  Download-Engine: yt-dlp.exe als Subprocess
# ═══════════════════════════════════════════════════════════

# Fortschritts-Parser für yt-dlp --newline Output:
# [download]  42.3% of  123.45MiB at  3.21MiB/s ETA 00:30
_PROGRESS_RE = re.compile(
    r'\[download\]\s+([\d.]+)%'           # Prozent
    r'(?:\s+of\s+[\d.]+\s*\S+)?'         # Größe optional
    r'(?:\s+at\s+([\d.]+\s*\S+/s))?'     # Geschwindigkeit optional
    r'(?:\s+ETA\s+(\S+))?',              # ETA optional
    re.IGNORECASE
)
# Playlist-Fortschritt: [download] Downloading item 3 of 10
_PLAYLIST_RE = re.compile(
    r'\[download\]\s+Downloading\s+item\s+(\d+)\s+of\s+(\d+)',
    re.IGNORECASE
)
# Merge-Zeile
_MERGE_RE = re.compile(r'\[Merger\]|\[ffmpeg\]', re.IGNORECASE)


def _build_ytdlp_cmd(
    url:              str,
    download_path:    str,
    fmt_info:         dict,
    ffmpeg_path:      str | None,
    selected_browser: str,
    cookie_file:      str,
    is_playlist:      bool,
) -> list[str]:
    """Baut die yt-dlp.exe Kommandozeile zusammen."""
    ytdlp = find_ytdlp()
    cmd = [ytdlp]

    # Format
    cmd += ["-f", fmt_info["fmt"]]

    # Ausgabe-Template
    outtmpl = os.path.join(download_path, "%(title).150B [%(id)s].%(ext)s")
    cmd += ["-o", outtmpl]

    # Merge-Format
    if fmt_info["merge"] == "mp3":
        cmd += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        cmd += ["--merge-output-format", fmt_info["merge"]]

    # ffmpeg-Pfad
    if ffmpeg_path:
        cmd += ["--ffmpeg-location", os.path.dirname(ffmpeg_path)]

    # Playlist-Fehlerbehandlung
    if is_playlist:
        cmd.append("--ignore-errors")

    # Fortschritt für stdout-Parsing
    cmd += ["--progress", "--newline", "--no-warnings"]

    # Dateinamen-Bereinigung
    cmd += ["--restrict-filenames", "--trim-filenames", "150"]

    # Retries
    cmd += ["--retries", "10", "--fragment-retries", "10"]

    # Cookies
    if selected_browser == COOKIE_FILE_MODE:
        cmd += ["--cookies", cookie_file]
    elif selected_browser:
        cmd += ["--cookies-from-browser", selected_browser]

    cmd.append(url)
    return cmd


def _run_download(
    urls:             list[str],
    download_path:    str,
    fmt_info:         dict,
    ffmpeg_path:      str | None,
    selected_browser: str,
    cookie_file:      str,
    queue_mode:       bool,
):
    """
    Führt den Download durch — läuft im Worker-Thread.
    Parst stdout von yt-dlp.exe und schiebt UI-Updates via root.after().
    """
    global _download_running, _cancelled, _current_process

    total      = len(urls)
    done_count = 0

    for i, url in enumerate(urls, start=1):
        if _cancelled:
            break

        is_playlist = _is_playlist_url(url)

        # Queue-Listbox aktualisieren
        if queue_mode:
            def _highlight(idx=i - 1):
                queue_listbox.selection_clear(0, tk.END)
                queue_listbox.selection_set(idx)
                queue_listbox.see(idx)
                set_status("status_queue_n", i, total)
                progress_var.set(0)
                item_var.set("")
            root.after(0, _highlight)
        else:
            root.after(0, lambda: set_status("status_analyzing"))

        cmd = _build_ytdlp_cmd(
            url, download_path, fmt_info,
            ffmpeg_path, selected_browser, cookie_file, is_playlist
        )

        error_lines   = []
        was_download  = False
        was_cancelled = False
        pl_current    = 0
        pl_total      = 0

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            _current_process = proc

            for line in proc.stdout:
                if _cancelled:
                    proc.terminate()
                    was_cancelled = True
                    break

                line = _clean(line)

                # Playlist-Fortschritt
                pm = _PLAYLIST_RE.search(line)
                if pm:
                    pl_current = int(pm.group(1))
                    pl_total   = int(pm.group(2))
                    def _pl_ui(c=pl_current, tot=pl_total):
                        set_status("status_downloading_n", c, tot)
                        progress_var.set(0)
                    root.after(0, _pl_ui)
                    continue

                # Download-Fortschritt
                dm = _PROGRESS_RE.search(line)
                if dm:
                    pct   = float(dm.group(1))
                    speed = dm.group(2) or ""
                    was_download = True
                    def _dl_ui(p=pct, s=speed):
                        progress_var.set(min(p, 99))
                        if not queue_mode or pl_total <= 1:
                            set_status("status_downloading")
                        item_var.set(s)
                    root.after(0, _dl_ui)
                    continue

                # Merge-Phase
                if _MERGE_RE.search(line):
                    root.after(0, lambda: set_status("status_merging"))
                    continue

                # Fehler sammeln
                if line.lower().startswith("error"):
                    error_lines.append(line)

            proc.wait()
            if proc.returncode == 0:
                done_count += 1

        except Exception as ex:
            error_lines.append(str(ex))

        finally:
            _current_process = None

        # Queue-Eintrag markieren
        if queue_mode:
            ok = (proc.returncode == 0) if not was_cancelled else False
            def _mark(idx=i - 1, success=ok):
                queue_listbox.itemconfig(idx, fg="gray" if success else "red")
            root.after(0, _mark)

        if was_cancelled:
            break

        # Fehlerauswertung für Einzelvideo
        if not queue_mode:
            _handle_single_result(error_lines, was_download)
            return

    # ── Abschluss ──────────────────────────────────────────
    def done_ui():
        global _download_running
        _download_running = False
        if queue_mode:
            btn_download.config(text=t("btn_queue_download"), command=download_queue)
            queue_listbox.selection_clear(0, tk.END)
        else:
            btn_download.config(text=t("btn_download"), command=download_video)
        item_var.set("")

        if _cancelled:
            progress_var.set(0)
            set_status("status_cancelled")
            return

        progress_var.set(100)
        if queue_mode:
            set_status("status_queue_done", done_count, total)
        elif total > 1:
            set_status("status_done_n", total)
        else:
            set_status("status_done")

    root.after(0, done_ui)


def _handle_single_result(error_lines: list[str], was_download: bool):
    """Wertet das Ergebnis eines Einzelvideo-Downloads aus und zeigt ggf. Fehler."""
    joined = "\n".join(error_lines)

    def ui():
        global _download_running
        _download_running = False
        btn_download.config(text=t("btn_download"), command=download_video)
        item_var.set("")

        if _cancelled:
            progress_var.set(0)
            set_status("status_cancelled")
            return

        if not was_download and error_lines:
            progress_var.set(0)
            set_status("status_error")
            if "Requested format is not available" in joined or \
               "format is not available" in joined.lower():
                messagebox.showerror(t("err_download_title"), t("err_format_unavailable"))
            elif "Could not copy" in joined and "cookie database" in joined:
                messagebox.showerror(t("err_cookie_locked_title"), t("err_cookie_locked"))
            elif "Sign in" in joined or "bot" in joined.lower():
                messagebox.showwarning(t("warn_title"),
                    t("warn_no_download", "\n" + joined[-800:]))
            else:
                messagebox.showerror(t("err_download_title"), joined[-1500:])
            return

        if not was_download:
            progress_var.set(0)
            set_status("status_error")
            messagebox.showwarning(t("warn_title"), t("warn_no_download", ""))
            return

        progress_var.set(100)
        set_status("status_done")

    root.after(0, ui)


# ═══════════════════════════════════════════════════════════
#  Download starten (Einzelvideo)
# ═══════════════════════════════════════════════════════════

def download_video():
    global _download_running, _cancelled

    url           = url_var.get().strip()
    download_path = download_path_var.get().strip()

    if not url:
        messagebox.showerror(t("err_title"), t("err_no_url")); return
    if not url.startswith("http"):
        messagebox.showerror(t("err_title"), t("err_invalid_url")); return
    if not download_path:
        messagebox.showerror(t("err_title"), t("err_no_folder")); return

    download_path, path_err = effective_download_path(download_path)
    if path_err:
        messagebox.showerror(t("err_title"), path_err); return

    ytdlp_path = find_ytdlp()
    if not ytdlp_path:
        messagebox.showerror(t("err_title"),
            t("err_no_ytdlp", os.path.join(_app_dir(), "yt-dlp.exe"))); return

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        messagebox.showwarning(t("warn_title"), t("warn_no_ffmpeg"))

    selected_browser = browser_var.get()
    cookie_file      = cookie_file_var.get().strip()

    if selected_browser == COOKIE_FILE_MODE:
        if not cookie_file or not os.path.isfile(cookie_file):
            messagebox.showerror(t("err_title"), t("err_no_cookie_file")); return

    if selected_browser in ENCRYPTED_BROWSERS:
        display_clean = next(
            (n.replace("   ⚠", "") for k, n in SUPPORTED_BROWSERS if k == selected_browser),
            selected_browser)
        if not messagebox.askokcancel(t("warn_encrypted_title"),
                                      t("warn_encrypted", display_clean)):
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

    threading.Thread(
        target=_run_download,
        args=([url], download_path, fmt_info, ffmpeg_path,
              selected_browser, cookie_file, False),
        daemon=True,
    ).start()


# ═══════════════════════════════════════════════════════════
#  Download starten (Queue)
# ═══════════════════════════════════════════════════════════

def download_queue():
    global _download_running, _cancelled

    if not _url_queue:
        messagebox.showerror(t("err_title"), t("err_queue_empty")); return

    download_path_raw = download_path_var.get().strip()
    download_path, path_err = effective_download_path(download_path_raw)
    if path_err:
        messagebox.showerror(t("err_title"), path_err); return

    ytdlp_path = find_ytdlp()
    if not ytdlp_path:
        messagebox.showerror(t("err_title"),
            t("err_no_ytdlp", os.path.join(_app_dir(), "yt-dlp.exe"))); return

    ffmpeg_path      = find_ffmpeg()
    selected_browser = browser_var.get()
    cookie_file      = cookie_file_var.get().strip()

    if selected_browser == COOKIE_FILE_MODE:
        if not cookie_file or not os.path.isfile(cookie_file):
            messagebox.showerror(t("err_title"), t("err_no_cookie_file")); return

    if selected_browser in ENCRYPTED_BROWSERS:
        display_clean = next(
            (n.replace("   ⚠", "") for k, n in SUPPORTED_BROWSERS if k == selected_browser),
            selected_browser)
        if not messagebox.askokcancel(t("warn_encrypted_title"),
                                      t("warn_encrypted", display_clean)):
            return

    fmt_info = next((f for f in FORMATS if f["key"] == format_var.get()), FORMATS[0])
    urls     = list(_url_queue)

    _cancelled        = False
    _download_running = True
    progress_var.set(0)
    progress_bar.configure(mode="determinate", maximum=100)
    set_status("status_analyzing")
    item_var.set("")
    btn_download.config(text=t("btn_cancel"), command=cancel_download)
    root.update_idletasks()

    threading.Thread(
        target=_run_download,
        args=(urls, download_path, fmt_info, ffmpeg_path,
              selected_browser, cookie_file, True),
        daemon=True,
    ).start()


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

# Queue-Panel (anfangs versteckt)
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

# ── Traces ────────────────────────────────────────────────
browser_var.trace_add("write",     update_browser_info)
cookie_file_var.trace_add("write", update_browser_info)

# ── Initialzustand ────────────────────────────────────────
apply_language()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
