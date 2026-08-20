#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/128x128/apps"

mkdir -p "$APPS_DIR"
mkdir -p "$ICON_DIR"
chmod +x "$SCRIPT_DIR/main.py" "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/setup_permissions.sh"

# Install official application icons
cp -f "$SCRIPT_DIR/assets/icons/icon_128x128.png" "$ICON_DIR/wireg.png" 2>/dev/null || cp -f "$SCRIPT_DIR/assets/icon.png" "$ICON_DIR/wireg.png"

# Create .desktop file
cat <<EOF > "$APPS_DIR/wireg.desktop"
[Desktop Entry]
Name=WireG
Comment=Modern WireGuard Client for Linux
Exec=python3 $SCRIPT_DIR/main.py
Icon=$ICON_DIR/wireg.png
Terminal=false
Type=Application
Categories=Network;VPN;Security;
Keywords=wireguard;vpn;tunnel;network;
StartupNotify=true
EOF

chmod +x "$APPS_DIR/wireg.desktop"

echo "✅ WireG has been successfully added to your application menu ($APPS_DIR/wireg.desktop)!"

# Check if wireg-helper is installed in /usr/local/bin
if [ ! -f "/usr/local/bin/wireg-helper" ] || [ ! -f "/etc/sudoers.d/wireg" ]; then
    echo ""
    echo "⚡ Would you like to enable passwordless connection mode now? (Requires sudo once)"
    echo "Running ./setup_permissions.sh..."
    "$SCRIPT_DIR/setup_permissions.sh" || echo "Note: You can configure passwordless mode anytime by running: sudo ./setup_permissions.sh"
fi

echo ""
echo "🎉 Setup complete! Launch WireG with ./run.sh or from your app launcher."
