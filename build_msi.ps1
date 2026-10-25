# Build script for Gjat Downloader! Windows MSI Installer
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Gjat Downloader! - MSI Installer Builder" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Cyan

$wixExe = "C:\Program Files\WiX Toolset v7.0\bin\wix.exe"
if (-not (Test-Path $wixExe)) {
    $found = Get-Command wix -ErrorAction SilentlyContinue
    if ($found) {
        $wixExe = $found.Source
    } else {
        Write-Error "WiX CLI not found. Please install WiX Toolset."
        exit 1
    }
}

$exePath = "dist\GjatDownloader\GjatDownloader.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "dist\GjatDownloader\GjatDownloader.exe not found! Please compile the executable first."
    exit 1
}

$iconPath = "app_icon.ico"
if (-not (Test-Path $iconPath)) {
    Write-Error "app_icon.ico not found!"
    exit 1
}

$outputMsi = "dist\GjatDownloader-Setup.msi"
if (Test-Path $outputMsi) {
    Remove-Item -Force $outputMsi
}

Write-Host "`n[1/2] Compiling Windows Installer (.msi) with WiX v7..." -ForegroundColor Yellow
& $wixExe build Package.wxs -ext WixToolset.UI.wixext -o $outputMsi

if (Test-Path $outputMsi) {
    $msiSize = (Get-Item $outputMsi).Length / 1MB
    Write-Host "`n[2/2] MSI Package created successfully!" -ForegroundColor Green
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Output File: $outputMsi" -ForegroundColor White
    Write-Host "File Size  : $([math]::Round($msiSize, 2)) MB" -ForegroundColor White
    Write-Host "Installer  : Native Windows Installer package" -ForegroundColor White
    Write-Host "Shortcuts  : Desktop & Start Menu" -ForegroundColor White
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
} else {
    Write-Error "Failed to generate MSI package."
    exit 1
}
