# Run this script AFTER completing GitHub login in your browser
# (Use the code shown when you ran: gh auth login)

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Set-Location $PSScriptRoot

Write-Host "Creating GitHub repo and pushing..." -ForegroundColor Cyan

# Create repo on GitHub (0xhydraOp) and push
gh repo create maternal_tracking --public --source=. --remote=origin --push

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccess! Your code is now at: https://github.com/0xhydraOp/maternal_tracking" -ForegroundColor Green
} else {
    Write-Host "`nIf repo already exists, run: git push -u origin main" -ForegroundColor Yellow
}
