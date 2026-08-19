#!/usr/bin/env bash
# One-time setup script for WireG passwordless connection
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER_SRC="$SCRIPT_DIR/wireg/core/wireg-helper.sh"
HELPER_DST="/usr/local/bin/wireg-helper"
SUDOERS_FILE="/etc/sudoers.d/wireg"
POLKIT_FILE="/etc/polkit-1/rules.d/99-wireg.rules"

echo "🔐 Configuring WireG passwordless WireGuard connection..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Requesting root permission for one-time setup..."
    exec sudo "$0" "$@"
fi

# 1. Install helper script
mkdir -p /usr/local/bin
cp -f "$HELPER_SRC" "$HELPER_DST"
chmod 755 "$HELPER_DST"
chown root:root "$HELPER_DST"

# 2. Configure Sudoers for passwordless execution
mkdir -p /etc/sudoers.d
cat <<EOF > "$SUDOERS_FILE"
# WireG Client - Passwordless WireGuard Management
ALL ALL=(ALL) NOPASSWD: /usr/local/bin/wireg-helper
EOF
chmod 0440 "$SUDOERS_FILE"

# 3. Configure Polkit rule if polkit rules directory exists
if [ -d "/etc/polkit-1/rules.d" ]; then
cat <<EOF > "$POLKIT_FILE"
/* WireG Client PolicyKit Rule */
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.policykit.exec" &&
        action.lookup("program") == "/usr/local/bin/wireg-helper") {
        return polkit.Result.YES;
    }
});
EOF
chmod 644 "$POLKIT_FILE"
fi

# 4. Prepare /etc/wireguard directory
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

echo "✅ Passwordless permissions configured successfully!"
echo "Now WireG can connect and disconnect without ever asking for sudo password."
