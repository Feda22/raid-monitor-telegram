# RAID Monitor with Telegram Alerts - Installation Guide

This document explains how to install and run the RAID monitoring script with Telegram notifications on a Linux server.

==================================================
REQUIREMENTS
==================================================

- Linux server with mdadm RAID
- Python 3.6 or newer
- Root privileges
- Two Telegram bots created with @BotFather
- Telegram chat IDs where alerts will be sent

==================================================
INSTALLATION STEPS
==================================================

1. Create installation directory

sudo mkdir -p /opt/raid-scripts
cd /opt/raid-scripts


2. Create configuration file (config.py)

sudo nano /opt/raid-scripts/config.py

Insert the following configuration and modify it according to your environment:

#!/usr/bin/env python3
# config.py - RAID Monitor Configuration

# Telegram Bot 1: Critical alerts (RAID lost or inactive)
TELEGRAM_TOKEN_ALERTAS = "YOUR_ALERT_TOKEN"
TELEGRAM_CHAT_ID_ALERTAS = "YOUR_ALERT_CHAT_ID"

# Telegram Bot 2: Operational notifications
TELEGRAM_TOKEN_NOTICIAS = "YOUR_OPERATIONS_TOKEN"
TELEGRAM_CHAT_ID_NOTICIAS = "YOUR_OPERATIONS_CHAT_ID"

# Server information
HOSTNAME = "SERVER_NAME"
IP_LAN = "192.168.1.X"

# Paths
LOG_FILE = "/var/log/raid_monitor.log"
MDSTAT_PATH = "/proc/mdstat"

# Monitoring intervals (seconds)
CHECK_INTERVAL_ALERTAS = 300
CHECK_INTERVAL_NOTICIAS = 1800
CHECK_INTERVAL_RESCAN = 60


3. Create log file

sudo touch /var/log/raid_monitor.log


4. Copy the monitoring script

sudo cp raid-monitor-telegram.py /opt/raid-scripts/
sudo chmod +x /opt/raid-scripts/raid-monitor-telegram.py


5. Test manual execution

Before installing the service, verify that the script runs correctly.

sudo python3 /opt/raid-scripts/raid-monitor-telegram.py

Press Ctrl+C to stop the script.


6. Create systemd service

sudo nano /etc/systemd/system/raid-monitor.service

Add the following configuration:

[Unit]
Description=RAID Monitor with Telegram Alerts
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/raid-scripts
ExecStart=/usr/bin/python3 /opt/raid-scripts/raid-monitor-telegram.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/var/log/raid_monitor.log
StandardError=inherit

[Install]
WantedBy=multi-user.target


7. Enable and start the service

sudo systemctl daemon-reload
sudo systemctl enable raid-monitor
sudo systemctl start raid-monitor


8. Verify service status

sudo systemctl status raid-monitor


9. Monitor logs in real time

sudo tail -f /var/log/raid_monitor.log


==================================================
USEFUL COMMANDS
==================================================

Start service

sudo systemctl start raid-monitor

Stop service

sudo systemctl stop raid-monitor

Restart service

sudo systemctl restart raid-monitor

Check status

sudo systemctl status raid-monitor

View logs

sudo tail -f /var/log/raid_monitor.log


==================================================
TROUBLESHOOTING
==================================================

Problem: Telegram bot does not send messages  
Solution: Verify that the bot is added to the group and has permission to send messages.

Problem: Permission error when reading /proc/mdstat  
Solution: Run the script with root privileges.

Problem: Test Telegram bot connectivity  

curl "https://api.telegram.org/botYOUR_TOKEN/getMe"


==================================================
SECURITY NOTICE
==================================================

Do not publish real Telegram tokens in public repositories.
Store tokens in configuration files excluded by .gitignore or use environment variables.
