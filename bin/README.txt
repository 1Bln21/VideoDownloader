In diesen Ordner gehoeren VOR dem Kompilieren des Installers die fertigen
Binaerdateien:

    VideoDownloader.exe   <- PyInstaller-Output (--onefile empfohlen)
    yt-dlp.exe            <- aktuelle Release-EXE von yt-dlp
    ffmpeg.exe            <- aus dem GyanD/codexffmpeg essentials-Build
    ffprobe.exe           <- aus dem GyanD/codexffmpeg essentials-Build

Der Dateiname der App-EXE muss exakt mit #define AppExe im VideoDownloader.iss
uebereinstimmen (Standard: VideoDownloader.exe).

PyInstaller-Beispiel (im Repo-Root):
    pyinstaller --onefile --noconsole --name VideoDownloader video-downloader.py
    -> dist\VideoDownloader.exe  hierher (bin\) kopieren.

Dieser Ordner-Inhalt (ausser dieser README) gehoert NICHT ins Git-Repo.
