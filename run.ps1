# Simple script to run the Discord scraper with DEBUG enabled
# No need to manually set environment variables - it's in .env now!

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Discord Scraper with HTML Inspection Enabled            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ DEBUG=True is set in .env file" -ForegroundColor Green
Write-Host "✓ Starting scraper..." -ForegroundColor Green
Write-Host ""
Write-Host "WHAT TO EXPECT:" -ForegroundColor Yellow
Write-Host "  1. You'll see: '🐛 DEBUG MODE ENABLED' in logs" -ForegroundColor Gray
Write-Host "  2. You'll see: '💾 Saved HTML inspection: data/message_inspection_*.html'" -ForegroundColor Gray
Write-Host "  3. After scraper finishes, run: python analyze_html.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting scraper..." -ForegroundColor Cyan
Write-Host ""

python app.py
