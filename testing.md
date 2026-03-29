# 🧪 Testing Guide (Fail2Ban Architecture)

Since the `security-bot` is now tightly coupled natively to the Linux Host Kernel via `fail2ban`, testing behaves slightly differently than isolated Docker containers. This guide demonstrates how to safely trigger, observe, and validate the bot's features in your staging or production VPS environment.

---

## ☎️ 1. Testing Telegram Communications

Before triggering a ban, ensure your Long Polling loop is effectively talking to Telegram.
1. Open your Telegram App.
2. Send `/status` to your Bot.
3. You should see an instant reply detailing your Fail2ban Jail Statuses (e.g. `sshd`, `nginx-botsearch`).
4. Send `/whitelist 1.1.1.1` and ensure it responds positively.

---

## 🚀 2. Testing NGINX Log Anomalies

Your Python bot watches `/var/log/nginx/access.log` to execute immediate auto-bans when it spots scrapers or ratelimit violations.

### The "Sensitive Path" Test
Trigger the log parser natively by trying to scrape a protected file endpoint from your laptop. 
On your local machine terminal, run:
```bash
curl http://YOUR_VPS_IP/.env
```
**Expected Result:** 
- The Python Bot tails the log, spies the `/.env` pattern, and seamlessly invokes `sudo fail2ban-client set nginx-botsearch banip [YOUR_IP]`.
- You will receive a ⚡ Telegram Alert that an IP was auto-banned.
- Your laptop will now timeout if you try to make an HTTP request again!

### The "Rate Limit Spider" Test
First, unban yourself via Telegram: `/unban YOUR_IP`.
Then, spam the server faster than the `100 requests / 30 seconds` default bound:
```bash
for i in {1..110}; do curl -s http://YOUR_VPS_IP/ > /dev/null; done
```
**Expected Result:** 
- The `defaultdict` matrix hits the bounds cap and instantly strikes Fail2ban.
- You get a telegram alert denoted "Reason: Rate Spike".

---

## 🛡️ 3. Testing Pure Fail2Ban (SSH Brute Force)

Fail2Ban manages standard SSH Brute forcing natively. When it traps an IP, the `telegram-notify.conf` Action pushes data through the `/run/security-bot/bot.sock` UNIX Socket to your Python app.

### Simulating a brute-force
Instead of physically brute-forcing your server, we can artificially "Fail" an SSH login inside the authentication logs.

On your VPS terminal:
```bash
# Inject 5 fake failures over a few seconds:
for i in {1..5}; do 
  echo "Mar 29 12:00:00 server sshd[123]: Failed password for root from 9.9.9.9 port 22 ssh2" | sudo tee -a /var/log/auth.log
done
```
**Expected Result:**
- Fail2ban catches the anomaly natively.
- Fail2ban runs the UNIX SOCKET configuration defined in `jail.local`.
- Your Python bot reads the socket JSON and pushes an Alert to your Telegram explicitly declaring `Jail: sshd`!

---

## 🛠️ 4. Debugging & Observability

If your `/unban` command doesn't work, or your bot isn't starting, use the host's native `journalctl` utility!

```bash
# Watch the live stdout prints from your Python bot natively
sudo journalctl -u security-bot -f

# Check Fail2Ban's native brain to see why it isn't triggering bans
sudo fail2ban-client status
sudo tail -f /var/log/fail2ban.log
```
