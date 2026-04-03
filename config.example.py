#!/usr/bin/env python3
# config.example.py - Ejemplo de configuración
# Copiar este archivo como config.py y completar con datos reales

# ===== TELEGRAM =====
# Bot 1: Alertas críticas (RAID perdido/inactivo)
# Crear bot en Telegram con @BotFather
TELEGRAM_TOKEN_ALERTAS = "TU_TOKEN_ALERTAS_AQUI"
TELEGRAM_CHAT_ID_ALERTAS = "TU_CHAT_ID_ALERTAS_AQUI"

# Bot 2: Notificaciones operativas
TELEGRAM_TOKEN_NOTICIAS = "TU_TOKEN_NOTICIAS_AQUI"
TELEGRAM_CHAT_ID_NOTICIAS = "TU_CHAT_ID_NOTICIAS_AQUI"

# ===== SERVIDOR =====
HOSTNAME = "NOMBRE_DEL_SERVIDOR"
IP_LAN = "192.168.1.X"

# ===== RUTAS =====
LOG_FILE = "/var/log/raid_monitor.log"
MDSTAT_PATH = "/proc/mdstat"

# ===== INTERVALOS (segundos) =====
CHECK_INTERVAL_ALERTAS = 300    # 5 minutos para alertas críticas
CHECK_INTERVAL_NOTICIAS = 1800  # 30 minutos para notificaciones
CHECK_INTERVAL_RESCAN = 60      # 60 segundos para revisar estado