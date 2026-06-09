; ============================================================================
;  Inno Setup Script – Video Downloader
;  Erzeugt: VideoDownloader_Setup_<Version>.exe
;
;  Features:
;    - Sprachwahl Deutsch / Englisch beim Setup-Start
;    - Lizenz-Zustimmung (MIT, muss akzeptiert werden)
;    - Verweis auf Third-Party-Lizenzen (Seite + Startmenue-Verknuepfung)
;    - Frei waehlbarer Installationspfad
;    - Desktop-Icon (optional), Startmenue, Deinstaller
;    - Buendelt App-EXE + yt-dlp.exe + ffmpeg.exe + ffprobe.exe
;    - Unterstuetzt das Silent-Selbstupdate des Updaters
;      (/SILENT /SUPPRESSMSGBOXES /NORESTART /SP-)
;
;  Kompilieren: in Inno Setup oeffnen und "Compile" (F9),
;  oder Kommandozeile:  iscc VideoDownloader.iss
; ----------------------------------------------------------------------------
;  >>> VOR DEM KOMPILIEREN ANPASSEN: die #define-Werte unten (v.a. BinDir
;      und AppExe muessen zu deinem PyInstaller-Build passen). <<<
; ============================================================================


; ─── Projekt-Konstanten (hier anpassen) ─────────────────────────────────────
#define AppName        "Video Downloader"
#define AppVersion     "1.2.1"
#define AppPublisher   "Lars Kuehn"
#define AppURL         "https://github.com/1Bln21/VideoDownloader"

; Name der fertig kompilierten PyInstaller-EXE (--onefile empfohlen).
; MUSS exakt mit der Datei in BinDir uebereinstimmen.
#define AppExe         "VideoDownloader.exe"

; Ordner mit den fertigen Binaerdateien, die mitinstalliert werden:
;   <BinDir>\VideoDownloader.exe   (PyInstaller-Output)
;   <BinDir>\yt-dlp.exe
;   <BinDir>\ffmpeg.exe
;   <BinDir>\ffprobe.exe
; Pfad relativ zu diesem .iss oder absolut.
#define BinDir         "bin"

; Repo-Root mit den Lizenzdateien (dieser Ordner = Verzeichnis des .iss).
#define LicenseFileMIT       "LICENSE"
#define ThirdPartyLicenses   "THIRD_PARTY_LICENSES.txt"


[Setup]
; Eindeutige, ueber Versionen STABILE App-ID (nicht aendern -> saubere Upgrades).
AppId={{A7F3C2E1-9B4D-4E6A-8C1F-2D5B7E9A4C30}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases

; Standard-Zielpfad in Program Files; Nutzer kann ihn im Wizard aendern.
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=auto

; Lizenz-Zustimmung (MIT). Inno liest die Datei als Klartext, auch ohne .txt.
LicenseFile={#LicenseFileMIT}

; Eigene Info-Seite mit den Drittanbieter-Lizenzen (erscheint nach der
; MIT-Zustimmung, vor der Pfadwahl). Willst du statt der vollen Texte nur
; einen kurzen Verweis zeigen, hier auf eine kurze Hinweisdatei umbiegen.
InfoBeforeFile={#ThirdPartyLicenses}

; Setup benoetigt Adminrechte (Installation nach Program Files).
; Passt zum Updater: dieser elevatet danach selbst pro Update genau einmal.
PrivilegesRequired=admin

; 64-Bit. Bei Inno < 6.3 beide Werte auf "x64" aendern.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Ausgabe: dist_installer\VideoDownloader_Setup_1.2.1.exe
OutputDir=dist_installer
OutputBaseFilename=VideoDownloader_Setup_{#AppVersion}

; Optik / Kompression
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}

; Beim (Silent-)Update laufende App-Instanz schliessen lassen, damit die EXE
; ueberschrieben werden kann. Neustart uebernimmt unser [Run]-Eintrag.
CloseApplications=yes
RestartApplications=no

; Setup-Programm-Icon (das App-EXE-Icon kommt aus der EXE selbst, s.o.)
SetupIconFile={#BinDir}\appicon.ico


[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"


[CustomMessages]
de.ViewThirdParty=Lizenzen Dritter (Third-Party)
en.ViewThirdParty=Third-Party Licenses
de.ThirdPartyInfoCaption=Lizenzen verwendeter Drittanbieter-Software
en.ThirdPartyInfoCaption=Licenses of bundled third-party software
de.ThirdPartyInfoDescription=Bitte zur Kenntnis nehmen
en.ThirdPartyInfoDescription=Please review


[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked


[Files]
; --- Anwendung (PyInstaller --onefile) ---
Source: "{#BinDir}\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

; --- Mitgelieferte Tools ---
Source: "{#BinDir}\yt-dlp.exe";  DestDir: "{app}"; Flags: ignoreversion
Source: "{#BinDir}\ffmpeg.exe";  DestDir: "{app}"; Flags: ignoreversion
Source: "{#BinDir}\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion

; --- Lizenzen / Doku ---
Source: "{#LicenseFileMIT}";     DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "{#ThirdPartyLicenses}"; DestDir: "{app}"; Flags: ignoreversion

; --- Falls du PyInstaller --onedir statt --onefile nutzt, zusaetzlich den
;     _internal-Ordner mitnehmen (Zeile aktivieren, --onefile-Zeile oben dann
;     weiterhin fuer die EXE behalten): ---
; Source: "{#BinDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
Name: "{group}\{#AppName}";                  Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:ViewThirdParty}";         Filename: "{app}\{#ThirdPartyLicenses}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExe}"; Tasks: desktopicon


[Run]
; Nach interaktiver Installation optional starten (Checkbox auf der Fertig-Seite).
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; \
    Flags: nowait postinstall skipifsilent

; Nach stillem Update (Updater startet mit /SILENT) die App automatisch neu starten.
Filename: "{app}\{#AppExe}"; Flags: nowait skipifnotsilent


[UninstallDelete]
; Reste des In-App-Updaters mit entfernen.
Type: files;          Name: "{app}\yt-dlp.exe.old"
Type: filesandordirs; Name: "{app}\__pycache__"
