#!/usr/bin/env bash
# WireG Helper Script for managing WireGuard interfaces without password
set -e

ACTION="$1"
CONF_SRC="$2"
IFACE="wireg0"
SYS_CONF="/etc/wireguard/${IFACE}.conf"

case "$ACTION" in
    up)
        if [ -z "$CONF_SRC" ] || [ ! -f "$CONF_SRC" ]; then
            echo "Error: Source config file '$CONF_SRC' does not exist." >&2
            exit 1
        fi
        
        # Ensure /etc/wireguard directory exists and is secured
        mkdir -p /etc/wireguard
        chmod 700 /etc/wireguard
        
        # Copy to /etc/wireguard/wireg0.conf
        cp -f "$CONF_SRC" "$SYS_CONF"
        chmod 600 "$SYS_CONF"
        
        # If interface is already up, bring down cleanly first
        if ip link show "$IFACE" >/dev/null 2>&1; then
            /usr/bin/wg-quick down "$IFACE" 2>/dev/null || true
        fi
        
        exec /usr/bin/wg-quick up "$IFACE"
        ;;
        
    down)
        if ip link show "$IFACE" >/dev/null 2>&1; then
            /usr/bin/wg-quick down "$IFACE"
        fi
        rm -f "$SYS_CONF"
        ;;
        
    status)
        if ip link show "$IFACE" >/dev/null 2>&1; then
            echo "UP"
            exit 0
        else
            echo "DOWN"
            exit 1
        fi
        ;;
        
    *)
        echo "Usage: $0 {up <config_file>|down|status}" >&2
        exit 1
        ;;
esac
