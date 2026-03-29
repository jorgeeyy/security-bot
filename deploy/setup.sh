#!/bin/bash
set -e

# Usage:
#   sudo bash deploy/setup.sh          → run all steps
#   sudo bash deploy/setup.sh 3        → start from step 3
#   sudo bash deploy/setup.sh 3 5      → run steps 3 to 5 only

START_FROM=${1:-1}
END_AT=${2:-8}

# Must run as root
if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo ./setup.sh"
  exit 1
fi

echo "▶ Running steps $START_FROM to $END_AT"
echo ""

run_step() {
  local step=$1
  if [[ $step -ge $START_FROM && $step -le $END_AT ]]; then
    return 0  # should run
  fi
  return 1    # skip
}

# ─────────────────────────────────────────────
if run_step 1; then
  echo "[1/8] Installing system dependencies..."
  apt update && apt install -y fail2ban socat python3-venv python3-pip rsync
fi

# ─────────────────────────────────────────────
if run_step 2; then
  echo "[2/8] Creating system user..."
  useradd --system --no-create-home --shell /usr/sbin/nologin security-bot || true
fi

# ─────────────────────────────────────────────
if run_step 3; then
  echo "[3/8] Deploying bot files..."
  mkdir -p /opt/security-bot
  rsync -av --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' \
    . /opt/security-bot/
fi

# ─────────────────────────────────────────────
if run_step 4; then
  echo "[4/8] Setting ownership..."
  chown -R security-bot:security-bot /opt/security-bot
  
  echo "Granting sudo access to fail2ban-client without password..."
  echo "security-bot ALL=(root) NOPASSWD: /usr/bin/fail2ban-client" > /etc/sudoers.d/security-bot
  chmod 0440 /etc/sudoers.d/security-bot
fi

# ─────────────────────────────────────────────
if run_step 5; then
  echo "[5/8] Creating virtualenv and installing dependencies..."
  sudo -u security-bot python3 -m venv /opt/security-bot/venv
  sudo -u security-bot /opt/security-bot/venv/bin/pip install \
    -r /opt/security-bot/requirements.txt
fi

# ─────────────────────────────────────────────
if run_step 6; then
  echo "[6/8] Configuring socket directory (survives reboots)..."
  echo "d /run/security-bot 0750 security-bot security-bot -" \
    > /etc/tmpfiles.d/security-bot.conf
  systemd-tmpfiles --create /etc/tmpfiles.d/security-bot.conf
fi

# ─────────────────────────────────────────────
if run_step 7; then
  echo "[7/8] Installing service and fail2ban configs..."
  cp deploy/security-bot.service /etc/systemd/system/
  cp deploy/telegram-notify.conf /etc/fail2ban/action.d/
  cp deploy/jail.local /etc/fail2ban/jail.local
  systemctl daemon-reload
fi

# ─────────────────────────────────────────────
if run_step 8; then
  echo "[8/8] Enabling services..."
  systemctl enable --now fail2ban
  systemctl restart fail2ban
  systemctl enable --now security-bot

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
fi

echo ""
echo "Done (steps $START_FROM–$END_AT)."