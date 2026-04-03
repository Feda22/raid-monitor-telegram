# RAID Monitor con Alertas en Telegram - Guía de Instalación

Este documento explica cómo instalar y ejecutar el script de monitoreo de RAID con notificaciones a Telegram en un servidor Linux.

=============================================
REQUISITOS
=============================================

- Servidor Linux con RAID administrado por mdadm
- Python 3.6 o superior
- Acceso root
- Dos bots de Telegram creados con @BotFather
- Chat IDs de Telegram donde se enviarán las alertas

=============================================
PASOS DE INSTALACIÓN
=============================================

1. Crear directorio de instalación

sudo mkdir -p /opt/raid-scripts
cd /opt/raid-scripts


2. Crear archivo de configuración (config.py)

sudo nano /opt/raid-scripts/config.py

Insertar la siguiente configuración y modificarla según el entorno:

#!/usr/bin/env python3
# config.py - Configuración del monitor RAID

# Telegram Bot 1: Alertas críticas (RAID perdido o inactivo)
TELEGRAM_TOKEN_ALERTAS = "YOUR_ALERT_TOKEN"
TELEGRAM_CHAT_ID_ALERTAS = "YOUR_ALERT_CHAT_ID"

# Telegram Bot 2: Notificaciones operativas
TELEGRAM_TOKEN_NOTICIAS = "YOUR_OPERATIONS_TOKEN"
TELEGRAM_CHAT_ID_NOTICIAS = "YOUR_OPERATIONS_CHAT_ID"

# Información del servidor
HOSTNAME = "SERVER_NAME"
IP_LAN = "192.168.1.X"

# Rutas
LOG_FILE = "/var/log/raid_monitor.log"
MDSTAT_PATH = "/proc/mdstat"

# Intervalos de monitoreo (segundos)
CHECK_INTERVAL_ALERTAS = 300
CHECK_INTERVAL_NOTICIAS = 1800
CHECK_INTERVAL_RESCAN = 60


3. Crear archivo de log

sudo touch /var/log/raid_monitor.log


4. Copiar el script de monitoreo

sudo cp raid-monitor-telegram.py /opt/raid-scripts/
sudo chmod +x /opt/raid-scripts/raid-monitor-telegram.py


5. Probar ejecución manual

Antes de instalar el servicio, verificar que el script funcione correctamente.

sudo python3 /opt/raid-scripts/raid-monitor-telegram.py

Presionar Ctrl+C para detener el script.


6. Crear servicio systemd

sudo nano /etc/systemd/system/raid-monitor.service

Agregar la siguiente configuración:

[Unit]
Description=RAID Monitor con Alertas en Telegram
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


7. Habilitar e iniciar el servicio

sudo systemctl daemon-reload
sudo systemctl enable raid-monitor
sudo systemctl start raid-monitor


8. Verificar estado del servicio

sudo systemctl status raid-monitor


9. Monitorear logs en tiempo real

sudo tail -f /var/log/raid_monitor.log


===============================================
COMANDOS ÚTILES
===============================================

Iniciar servicio

sudo systemctl start raid-monitor

Detener servicio

sudo systemctl stop raid-monitor

Reiniciar servicio

sudo systemctl restart raid-monitor

Ver estado

sudo systemctl status raid-monitor

Ver logs

sudo tail -f /var/log/raid_monitor.log


======================================================
SOLUCIÓN DE PROBLEMAS
======================================================

Problema: El bot de Telegram no envía mensajes  
Solución: Verificar que el bot esté agregado al grupo y tenga permisos para enviar mensajes.

Problema: Error de permisos al leer /proc/mdstat  
Solución: Ejecutar el script con privilegios root.

Problema: Probar conectividad con la API de Telegram

curl "https://api.telegram.org/botYOUR_TOKEN/getMe"


=====================================================
NOTA DE SEGURIDAD
=====================================================

No publicar tokens reales de Telegram en repositorios públicos.

Guardar los tokens en archivos de configuración excluidos por `.gitignore`
o utilizar variables de entorno.
