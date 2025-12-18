@echo off
REM Batch file to run Discord scraper in DEBUG mode to inspect HTML

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         DISCORD SCRAPER DEBUG MODE - HTML INSPECTION          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Set debug mode
set DEBUG=True

echo ✓ DEBUG=True (environment variable set)
echo.
echo Starting scraper in DEBUG mode...
echo This will capture HTML of messages from Discord channels.
echo.
echo What will happen:
echo   • Scraper will run normally
echo   • First message from each channel will be saved as HTML
echo   • Files: data/message_inspection_*.html
echo   • You'll see logs like: "💾 Saved HTML inspection..."
echo.
echo Once complete, run:
echo   python analyze_html.py
echo.
echo Press any key to start...
pause

REM Run the scraper with debug mode
python app.py

echo.
echo ✓ Scraper finished
echo.
echo Next step: Run this command to analyze the HTML files:
echo   python analyze_html.py
echo.
pause

