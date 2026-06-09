# ============================================================================
#  build.ps1 - Baut die EXE und (optional) den Installer fuer Video Downloader
#
#  Aufruf:
#     .\build.ps1            # nur die EXE bauen und nach bin\ kopieren
#     .\build.ps1 -Installer # zusaetzlich den Inno-Setup-Installer kompilieren
#
#  Hintergrund / Stolperfalle:
#     Es gibt zwei Python-Versionen (3.13 und 3.14). Mit 3.14 erzeugte
#     PyInstaller-Builds starten nicht (0xC0000139). Daher wird bewusst der
#     ausgereifte Interpreter 'py -3.13' verwendet (dort: pip install pyinstaller).
# ============================================================================

param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$AppName    = "VideoDownloader"          # muss zu #define AppExe im .iss passen
$Source     = "video-downloader.py"
$Python     = "py"
$PyArgs     = @("-3.13")                  # Interpreter mit PyInstaller (3.14 erzeugt defekte EXE)
$BinDir     = Join-Path $PSScriptRoot "bin"
$IconPath   = Join-Path $BinDir "appicon.ico"

# Icon nur uebergeben, wenn vorhanden
$iconArgs = @()
if (Test-Path $IconPath) {
    $iconArgs = @("--icon", $IconPath)
    Write-Host "Icon: $IconPath" -ForegroundColor DarkGray
} else {
    Write-Host "Kein Icon (bin\appicon.ico fehlt) - baue ohne Icon." -ForegroundColor Yellow
}

Write-Host "=== 1) EXE bauen (PyInstaller) ===" -ForegroundColor Cyan
& $Python @PyArgs -m PyInstaller `
    --onefile `
    --noconsole `
    --name $AppName `
    @iconArgs `
    --distpath "dist" `
    --workpath "build" `
    --specpath "build" `
    --noconfirm `
    $Source
if ($LASTEXITCODE -ne 0) { throw "PyInstaller fehlgeschlagen (Exit $LASTEXITCODE)." }

$builtExe = Join-Path $PSScriptRoot "dist\$AppName.exe"
if (-not (Test-Path $builtExe)) { throw "Erwartete EXE nicht gefunden: $builtExe" }

Write-Host "=== 2) EXE nach bin\ kopieren ===" -ForegroundColor Cyan
if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir | Out-Null }
Copy-Item $builtExe (Join-Path $BinDir "$AppName.exe") -Force
Write-Host "  -> bin\$AppName.exe" -ForegroundColor Green

Write-Host "=== 3) Mitgelieferte Tools pruefen ===" -ForegroundColor Cyan
$tools   = @("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe")
$missing = @()
foreach ($t in $tools) {
    if (Test-Path (Join-Path $BinDir $t)) {
        Write-Host "  [OK]     bin\$t" -ForegroundColor Green
    } else {
        Write-Host "  [FEHLT]  bin\$t" -ForegroundColor Yellow
        $missing += $t
    }
}
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Lege diese Dateien nach bin\, bevor du den Installer baust:" -ForegroundColor Yellow
    Write-Host "  yt-dlp.exe  : https://github.com/yt-dlp/yt-dlp/releases" -ForegroundColor Yellow
    Write-Host "  ffmpeg/ffprobe: GyanD/codexffmpeg essentials_build" -ForegroundColor Yellow
}

if ($Installer) {
    if ($missing.Count -gt 0) {
        throw "Installer-Build abgebrochen: es fehlen Tools in bin\ ($($missing -join ', '))."
    }
    Write-Host "=== 4) Installer kompilieren (Inno Setup) ===" -ForegroundColor Cyan
    $iscc = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $iscc) { throw "ISCC.exe nicht gefunden - Inno Setup 6 installiert?" }
    & $iscc "VideoDownloader.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup Compile fehlgeschlagen (Exit $LASTEXITCODE)." }
    Write-Host "  -> dist_installer\VideoDownloader_Setup_*.exe" -ForegroundColor Green
}

Write-Host ""
Write-Host "Fertig." -ForegroundColor Green
