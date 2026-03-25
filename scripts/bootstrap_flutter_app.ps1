$ErrorActionPreference = 'Stop'

$projectName = 'luna_vis_mobile'
$projectPath = Join-Path (Get-Location) $projectName

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    Write-Error 'Flutter CLI not found. Install Flutter and ensure it is on PATH, then run this script again.'
}

Write-Host 'Running flutter doctor...'
flutter doctor

if (-not (Test-Path $projectPath)) {
    Write-Host "Creating Flutter project: $projectName"
    flutter create $projectName
} else {
    Write-Host "Project already exists: $projectPath"
}

Push-Location $projectPath
try {
    Write-Host 'Adding dependencies...'
    flutter pub add dio flutter_secure_storage intl

    Write-Host ''
    Write-Host 'Bootstrap complete.'
    Write-Host 'Next steps:'
    Write-Host '1. Start Django: python manage.py runserver 0.0.0.0:8000'
    Write-Host '2. Run app (Android emulator): flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000'
    Write-Host '3. Follow docs/flutter-app-setup.md for API wiring.'
} finally {
    Pop-Location
}
