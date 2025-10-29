#!/bin/bash
# Quick helper script to copy hotspot configs into place.
set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Run this script with sudo" >&2
  exit 1
fi

CONFIG_SRC="$(dirname "$0")/.."

install -m 600 "$CONFIG_SRC/config/hostapd.conf" /etc/hostapd/hostapd.conf
install -m 600 "$CONFIG_SRC/config/dnsmasq.conf" /etc/dnsmasq.d/levyfeeder.conf
install -m 600 "$CONFIG_SRC/config/dhcpcd_ap.conf" /etc/dhcpcd.conf

rfkill unblock wlan || true
systemctl stop hostapd || true
systemctl stop dnsmasq || true
systemctl restart dhcpcd
systemctl start hostapd
systemctl start dnsmasq

cat <<INFO
Hotspot configuration installed. Connect to SSID "LevyFeeder" with the password from hostapd.conf.
INFO
