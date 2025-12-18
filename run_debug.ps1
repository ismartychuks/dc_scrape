# PowerShell script to run scraper in DEBUG mode properly

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     DISCORD SCRAPER - DEBUG MODE (HTML INSPECTION)            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set DEBUG in this session
$env:DEBUG = 'True'
Write-Host "✓ DEBUG=True set for this session" -ForegroundColor Green
Write-Host ""
Write-Host "Starting scraper in DEBUG mode..." -ForegroundColor Yellow
Write-Host ""
Write-Host "This will:" -ForegroundColor Cyan
Write-Host "  • Scan your Discord channels normally"
Write-Host "  • Save HTML of messages to: data/message_inspection_*.html"
Write-Host "  • Display log messages like: '💾 Saved HTML inspection...'"
Write-Host ""
Write-Host "Wait for scraper to finish (1-2 minutes)..."
Write-Host ""

# Run the app
python app.py

Write-Host ""
Write-Host "✓ Scraper finished!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step:" -ForegroundColor Cyan
Write-Host "  python analyze_html.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will show you what was extracted from the HTML."
Write-Host ""
