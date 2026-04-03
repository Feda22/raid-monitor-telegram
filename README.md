# RAID Monitor with Telegram Alerts

Version: 1.0  
Author: Felix Iñiguez

Script en Python para monitorear RAIDs software en Linux y enviar alertas a Telegram.

El script lee `/proc/mdstat` periódicamente, detecta estados como RAID degradado, discos fallados o resincronizaciones, y notifica a través de dos canales de Telegram según la severidad del evento.

==================================================
TABLA DE CONTENIDOS
==================================================

- Objetivo principal
- Características
- Arquitectura
- Requisitos
- Quick Start
- Instalación
- Configuración
- Uso
- Estructura del proyecto
- Logs
- Licencia

==================================================
OBJETIVO PRINCIPAL
==================================================

Monitorear el estado de RAIDs software en Linux y enviar notificaciones automáticas a Telegram, separando alertas críticas (RAID perdido) de notificaciones operativas (degradado, resincronización).

==================================================
CARACTERÍSTICAS
==================================================

- Monitoreo continuo de `/proc/mdstat`
- Detección de RAID degradado, discos fallados y procesos de resincronización
- Dos canales de Telegram:
  - Alertas críticas: RAID inactivo o fallado
  - Notificaciones operativas: degradado, resincronización, recuperación
- Detección inteligente: diferencia discos fallados físicamente presentes vs retirados
- Logging local para trazabilidad
- Intervalos configurables por tipo de alerta
- Integración con systemd

==================================================
ARQUITECTURA
==================================================

Servidor Linux -> /proc/mdstat -> Script Python -> Telegram API  
                                    |  
                                    v  
                            /var/log/raid_monitor.log

El script corre como daemon mediante systemd, lee el estado del RAID cada 60 segundos y envía notificaciones a Telegram según las reglas configuradas.

==================================================
REQUISITOS
==================================================

- Linux con mdadm
- Python 3.6 o superior
- Acceso a /proc/mdstat (requiere root)
- Comando lsblk (generalmente preinstalado)
- Dos bots de Telegram (crear con @BotFather)

Dependencias Python:

El proyecto utiliza únicamente librerías estándar de Python, por lo que no requiere paquetes externos.

==================================================
QUICK START
==================================================

Instalación rápida para probar el script manualmente:

```
cp config.example.py config.py
nano config.py
python3 raid-monitor-telegram.py
```

==================================================
INSTALACIÓN
==================================================

Para instrucciones completas consultar el archivo:

INSTALLATION.md

Resumen de instalación:

```
sudo mkdir -p /opt/raid-scripts
cd /opt/raid-scripts

sudo cp raid-monitor-telegram.py /opt/raid-scripts/
sudo cp config.example.py /opt/raid-scripts/config.py

sudo nano /opt/raid-scripts/config.py

sudo nano /etc/systemd/system/raid-monitor.service

sudo systemctl daemon-reload
sudo systemctl enable raid-monitor
sudo systemctl start raid-monitor
```

==================================================
CONFIGURACIÓN
==================================================

Editar el archivo config.py con los siguientes valores:

Variable                              Descripción
TELEGRAM_TOKEN_ALERTAS                Token del bot para alertas críticas
TELEGRAM_CHAT_ID_ALERTAS              Chat ID del grupo de alertas
TELEGRAM_TOKEN_NOTICIAS               Token del bot para notificaciones
TELEGRAM_CHAT_ID_NOTICIAS             Chat ID del grupo de noticias
HOSTNAME                              Nombre del servidor
IP_LAN                                IP del servidor
LOG_FILE                              Ruta del archivo de log
CHECK_INTERVAL_ALERTAS                Intervalo alertas críticas (segundos)
CHECK_INTERVAL_NOTICIAS               Intervalo notificaciones (segundos)
CHECK_INTERVAL_RESCAN                 Frecuencia de chequeo (segundos)

==================================================
USO
==================================================

Ejecución manual:

```
sudo python3 /opt/raid-scripts/raid-monitor-telegram.py
```

Gestión del servicio:

```
sudo systemctl start raid-monitor
sudo systemctl stop raid-monitor
sudo systemctl restart raid-monitor
sudo systemctl status raid-monitor
```

Ver logs:

```
sudo tail -f /var/log/raid_monitor.log
```

==================================================
ESTRUCTURA DEL PROYECTO
==================================================

```
raid-monitor-telegram/
├── raid-monitor-telegram.py    # Script principal
├── config.example.py           # Ejemplo de configuración
├── config.py                   # Configuración real (no se sube a GitHub)
├── README.md                   # Documentación principal
├── INSTALLATION.md             # Guía de instalación
├── LICENSE                     # Licencia MIT
└── .gitignore                  # Archivos excluidos
```

==================================================
LOGS
==================================================

El script genera logs en la ubicación definida por LOG_FILE.

Ejemplo de log:

```
2026-01-16 11:28:32 [INFO] - Iniciando monitoreo de RAID en HOSTNAME (IP)
2026-01-16 11:28:32 [INFO] - Frecuencias: Alertas=300s, Noticias=1800s, Rescan=60s
2026-01-18 01:11:35 [INFO] - [HOSTNAME] RECUPERADO: IP - /dev/md127 vuelto a estado normal
```

Niveles de log:

- INFO → eventos normales (inicio, recuperación)
- ERROR → errores de comunicación con Telegram o lectura de archivos
- CRITICAL → errores fatales que detienen el script

==================================================
LICENCIA
==================================================

MIT License.

Ver archivo LICENSE para más detalles.
