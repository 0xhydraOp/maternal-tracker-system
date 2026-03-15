# Publish Maternal Tracking System to GitHub
# Run: gh auth login   (first time only - follow browser prompts)
# Then run this script: .\publish.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$repoName = "maternal-tracking-system"

Write-Host "`n=== Maternal Tracking System - GitHub Publish ===" -ForegroundColor Cyan
Write-Host ""

# Check if logged in
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "You are not logged into GitHub. Run this first:" -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor White
    Write-Host ""
    Write-Host "Follow the prompts (browser + device code). Then run this script again." -ForegroundColor Gray
    exit 1
}

# Check if remote exists
$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host "Remote 'origin' already exists: $remote" -ForegroundColor Gray
    Write-Host "Pushing to origin/main..." -ForegroundColor Cyan
    git push -u origin main
} else {
    Write-Host "Creating repo '$repoName' on GitHub and pushing..." -ForegroundColor Cyan
    gh repo create $repoName --public --source=. --remote=origin --push
}

if ($LASTEXITCODE -eq 0) {
    $user = (gh api user -q .login)
    Write-Host ""
    Write-Host "Success! Your code is at: https://github.com/$user/$repoName" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "If the repo already exists, add remote and push:" -ForegroundColor Yellow
    Write-Host "  gh repo create $repoName --public --source=. --remote=origin" -ForegroundColor White
    Write-Host "  git push -u origin main" -ForegroundColor White
}
