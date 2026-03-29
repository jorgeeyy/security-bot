#!/bin/bash
set -e

# Must run as root
if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo ./setup.sh"
  exit 1
fi

echo "[1/8] Installing system dependencies..."
apt update && apt install -y fail2ban socat python3-venv python3-pip rsync

echo "[2/8] Creating system user..."
useradd --system --no-create-home --shell /usr/sbin/nologin security-bot || true

echo "[3/8] Deploying bot files..."
mkdir -p /opt/security-bot
rsync -av --exclude='.git' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.env' \
  . /opt/security-bot/

echo "[4/8] Creating virtualenv and installing dependencies..."
sudo -u security-bot python3 -m venv /opt/security-bot/venv
sudo -u security-bot /opt/security-bot/venv/bin/pip install \
  -r /opt/security-bot/requirements.txt

echo "[5/8] Setting ownership..."
chown -R security-bot:security-bot /opt/security-bot

echo "[6/8] Configuring socket directory (survives reboots)..."
echo "d /run/security-bot 0750 security-bot security-bot -" \
  > /etc/tmpfiles.d/security-bot.conf
systemd-tmpfiles --create /etc/tmpfiles.d/security-bot.conf

echo "[7/8] Installing service and fail2ban configs..."
cp deploy/security-bot.service /etc/systemd/system/
cp deploy/telegram-notify.conf /etc/fail2ban/action.d/
cp deploy/jail.local /etc/fail2ban/jail.local
systemctl daemon-reload

echo "[8/8] Enabling services..."
systemctl enable --now fail2ban
systemctl restart fail2ban
systemctl enable --now security-bot

# Warn if config still has placeholder values
if grep -q "your-token-here" /opt/security-bot/config.py; then
  echo ""
  echo "⚠️  WARNING: config.py still has placeholder values."
  echo "   Edit /opt/security-bot/config.py then run:"
  echo "   systemctl restart security-bot"
else
  echo ""
  echo "✅ Setup complete. Security bot is running."
  echo "   Check status: systemctl status security-bot"
  echo "   View logs:    journalctl -u security-bot -f"
fi
