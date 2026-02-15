# Video Downloader

**Einfacher, schneller YouTube/Playlist-Downloader mit schöner GUI für Windows**

Version 0.5.1 (15.02.2026)

### Features
- Lädt einzelne Videos und komplette Playlists
- Nutzt **yt-dlp + aria2c** für maximale Geschwindigkeit (oft 60–90+ MB/s bei 1 Gbit)
- Automatischer Merge zu sauberen MP4-Dateien mit FFmpeg
- Schöne Fortschrittsanzeige mit Geschwindigkeit, ETA und Playlist-Status
- Vollständig portable – alles (yt-dlp, aria2c, FFmpeg) wird mitinstalliert
- Windows/OneDrive-freundliche Dateinamen

### Installation
1. Lade die neueste Version herunter: [Releases](../../releases)
2. Führe `VideoDownloader-Setup.exe` aus
3. Fertig. Keine Python-Installation nötig.

### Danksagung / Third-Party Software
Dieses Programm nutzt folgende großartige Open-Source-Projekte:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** – Unlicense + GPLv3 (in der EXE)
- **[FFmpeg](https://ffmpeg.org)** – LGPL/GPL
- **[aria2](https://aria2.github.io)** – GPLv2+
- **[Python](https://www.python.org)** + Tkinter
- **[PyInstaller](https://pyinstaller.org)**

Vollständige Lizenztexte aller verwendeten Komponenten findest du in der Datei [`THIRD_PARTY_LICENSES.txt`](THIRD_PARTY_LICENSES.txt).

### Lizenz
Dieses Programm selbst steht unter der **MIT License** (siehe [LICENSE](LICENSE)).

**Hinweis:** Das Herunterladen von Videos kann gegen die Nutzungsbedingungen der jeweiligen Plattform verstoßen. 
Nutze das Tool verantwortungsvoll und nur für Inhalte, an denen du die entsprechenden Rechte hast.
