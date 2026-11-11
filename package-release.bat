@echo off
REM Package clean Undertale MiaUI release zip - game-free (no data.win/UNDERTALE files).
REM v1.1 fix: the v1.0.0 zip shipped out\libasound.so* (alsa-lib 1.2.12,
REM compiled-in datadir /opt/arm-alsa-glibc) + share\alsa. With launch.sh's
REM LD_LIBRARY_PATH=$PWD that copy shadowed the SYSTEM /usr/lib/libasound.so.2
REM (alsa-lib 1.2.10) on every fresh install -> SDL_OpenAudio "No available
REM audio device" -> no music. The author's own device never had the bundled
REM lib (only butterscotch + libSDL were pushed during debugging), which is why
REM it always worked there. v1.1 ships NO libasound and NO share\alsa.
REM Output: out\Undertale_MiaUI-release-v1.1.zip with Undertale.pak\ layout.
setlocal
set D=%~dp0
set OUT=%~dp0out
set PAK=%OUT%\Undertale.pak
if not exist "%D%out\butterscotch" (
  echo Missing out\butterscotch - run build.bat first
  exit /b 1
)
mkdir "%PAK%" 2>nul
del /Q "%PAK%\*" 2>nul
rmdir /S /Q "%PAK%\share" 2>nul
copy /Y "%D%launch.sh" "%PAK%\launch.sh" >nul
copy /Y "%D%out\butterscotch" "%PAK%\butterscotch" >nul
copy /Y "%D%out\libSDL-1.2.so.0" "%PAK%\" >nul
copy /Y "%D%out\libSDL-1.2.so.0.11.4" "%PAK%\" >nul
copy /Y "%D%out\gamecontrollerdb.txt" "%PAK%\" >nul
copy /Y "%D%LICENSE" "%PAK%\LICENSE" >nul
copy /Y "%D%NOTICE.MiaUI" "%PAK%\NOTICE.MiaUI" >nul
copy /Y "%D%README.md" "%PAK%\README.md" >nul
echo === Staged pak (must NOT contain libasound or game data) ===
dir "%PAK%"
where powershell >nul 2>&1
REM NOTE: -Include only filters with -Path wildcards (dir\*), NOT -LiteralPath.
REM A match exits 1 so errorlevel below actually fails the packaging.
powershell -NoProfile -Command "$bad = @(Get-ChildItem -Path '%PAK%\*' -Recurse -Include 'libasound*','data.win','UNDERTALE.exe','*.ogg','*.wav'); if ($bad.Count -gt 0) { $bad | ForEach-Object { Write-Host ('LEAK: ' + $_.FullName) }; exit 1 }; if (Test-Path -LiteralPath '%PAK%\share') { Write-Host 'LEAK: bundled share\alsa in pak'; exit 1 }; Compress-Archive -Path '%PAK%' -DestinationPath '%OUT%\Undertale_MiaUI-release-v1.1.zip' -Force; Get-ChildItem '%OUT%\Undertale_MiaUI-release-v1.1.zip'"
if errorlevel 1 (
  echo Package failed
  exit /b 1
)
echo.
echo Done: out\Undertale_MiaUI-release-v1.1.zip (game-free, no bundled libasound)
echo Install: extract so the pak ends up at /userdata/Ports/Undertale.pak/ + your Steam files
endlocal
