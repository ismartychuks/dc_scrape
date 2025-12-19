# VPS Migration Plan (Ubuntu)

Migrate the project from Windows to a Contabo Ubuntu VPS to save on licensing costs (€18.45 -> Included) while maintaining the ability to solve complex captchas.

## User Review Required
> [!IMPORTANT]
> To solve captchas on Ubuntu, you will need to either use the built-in Web UI in `app.py` or install a lightweight Desktop Environment + XRDP (Remote Desktop).

## Proposed Changes

### [Component] Server Infrastructure
- **Provider**: Contabo
- **Plan**: Cloud VPS S (€6.66/month)
- **OS**: Ubuntu 22.04 LTS (Included)

### [Component] Setup Steps
1. **Install Python & Dependencies**:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv
   ```
2. **Install Playwright Browsers**:
   ```bash
   pip install playwright
   playwright install --with-deps chromium
   ```
3. **Setup GUI for Captchas (Optional)**:
   If you want a Windows-like Remote Desktop experience:
   ```bash
   sudo apt install -y xfce4 xfce4-goodies xrdp
   sudo systemctl enable xrdp
   ```
   *Then connect via Windows Remote Desktop (RDP) to the VPS IP.*

## Verification Plan
1. **Connectivity**: Verify the Flask web interface is accessible on port 5000.
2. **Functionality**: Run `app.py` in non-headless mode (if using RDP) or headless mode (using the built-in web viewer).
3. **Performance**: Monitor RAM usage to ensure 8GB is sufficient (it will be).
