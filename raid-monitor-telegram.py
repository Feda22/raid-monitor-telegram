#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
from datetime import datetime
import time
import re
import sys
import signal
import subprocess

# ===== IMPORTAR CONFIGURACION =====
try:
    from config import *
except ImportError:
    print("ERROR: No se encuentra config.py", file=sys.stderr)
    print("Debe copiar config.example.py como config.py y editar los valores", file=sys.stderr)
    sys.exit(1)

# ===== ESTADOS PROBLEMATICOS Y SUS DESCRIPCIONES =====
PROBLEM_STATES = {
    'degraded': 'degradado',
    'recovering': 'en recuperacion',
    'resyncing': 'en resincronizacion',
    'failed': 'fallado',
    'not found': 'no encontrado',
    'inactive': 'inactivo',
    'reshape': 'en remodelacion',
    'check': 'en verificacion'
}

SEVERITY_LEVELS = {
    'critical': 'CRITICO',
    'warning': 'ADVERTENCIA',
    'notice': 'NOTICIA',
    'info': 'INFORMACION'
}

running = True

# ===== FUNCIONES AUXILIARES =====
def log_message(message, level="INFO"):
    """Registra mensajes en el archivo de log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} [{level}] - {message}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except IOError as e:
        print(f"No se pudo escribir en el log: {str(e)}", file=sys.stderr)

def send_telegram_alert(message, severity='notice', alert_type='noticias'):
    """Envia alerta a Telegram"""
    severity_prefix = SEVERITY_LEVELS.get(severity, '').upper()
    formatted_msg = f"[{severity_prefix}] {message}" if severity_prefix else message
    
    if alert_type == 'alertas':
        token = TELEGRAM_TOKEN_ALERTAS
        chat_id = TELEGRAM_CHAT_ID_ALERTAS
    else:
        token = TELEGRAM_TOKEN_NOTICIAS
        chat_id = TELEGRAM_CHAT_ID_NOTICIAS
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": formatted_msg,
        "parse_mode": "HTML"
    }
    
    try:
        params = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=params, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                log_message(f"Error Telegram API: {response.read().decode()}", "ERROR")
        return True
    except Exception as e:
        log_message(f"Error enviando a Telegram ({alert_type}): {str(e)}", "ERROR")
        return False

def signal_handler(sig, frame):
    """Maneja la senal de interrupcion"""
    global running
    log_message("Recibida senal de terminacion, finalizando...", "INFO")
    running = False

def get_physical_disks():
    """Obtiene lista de discos fisicos"""
    try:
        result = subprocess.run(['lsblk', '-o', 'NAME', '-d', '-n'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              check=True,
                              universal_newlines=True)
        
        disks = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and (line.startswith(('sd', 'nvme', 'mmcblk', 'vd'))):
                disks.append(line)
        return disks
    except subprocess.CalledProcessError as e:
        log_message(f"Error al listar discos: {e.stderr.strip()}", "ERROR")
        return []
    except Exception as e:
        log_message(f"Error inesperado al obtener discos: {str(e)}", "ERROR")
        return []

# ===== LOGICA PRINCIPAL =====
def parse_mdstat():
    """Analiza /proc/mdstat"""
    try:
        with open(MDSTAT_PATH, "r") as f:
            content = f.read()
    except IOError as e:
        log_message(f"No se pudo leer {MDSTAT_PATH}: {str(e)}", "ERROR")
        return None, {"error": str(e)}
    
    raids = {}
    current_raid = None
    
    for line in content.split('\n'):
        if line.startswith('md'):
            parts = line.split()
            raid_name = parts[0].strip(':')
            raids[raid_name] = {
                'status': 'active' if 'active' in parts else 'inactive',
                'devices': [],
                'state': 'healthy',
                'details': line,
                'last_alert': None,
                'failed_disks': [],
                'resync_info': None
            }
            current_raid = raid_name
        
        elif current_raid and '[' in line and ']' in line:
            state_match = re.search(r'\[(\d+)/(\d+)\] \[([^\]]+)\]', line)
            if state_match:
                raids[current_raid].update({
                    'device_count': int(state_match.group(2)),
                    'active_devices': int(state_match.group(1)),
                    'device_states': state_match.group(3)
                })
                
                if '_' in state_match.group(3) or int(state_match.group(1)) < int(state_match.group(2)):
                    raids[current_raid]['state'] = 'degraded'
        
        elif current_raid and ('raid' in line.lower() or 'md' in line.lower()):
            disk_matches = re.findall(r'(\w+)\[(\d+)\]\(?([FFa-z]+)?\)?', line)
            for disk, index, status in disk_matches:
                if 'F' in (status or ''):
                    raids[current_raid]['failed_disks'].append(disk)
                raids[current_raid]['devices'].append({
                    'name': disk,
                    'index': index,
                    'status': 'failed' if 'F' in (status or '') else 'active'
                })
        
        elif current_raid and ('resync' in line or 'recovery' in line or 'reshape' in line):
            raids[current_raid]['state'] = 'resyncing'
            progress = re.search(r'(\d+\.\d+)%', line)
            if progress:
                raids[current_raid]['resync_info'] = {
                    'progress': progress.group(1),
                    'speed': re.search(r'(\d+)K/sec', line).group(1) if re.search(r'(\d+)K/sec', line) else None,
                    'finish': re.search(r'finish=([\d\.]+min)', line).group(1) if re.search(r'finish=([\d\.]+min)', line) else None
                }
    
    return content, raids

def build_alert_message(raid_name, raid_info, physical_disks):
    """Construye mensaje de alerta"""
    problem = raid_info.get('state', 'unknown')
    description = PROBLEM_STATES.get(problem, problem)
    msg = f"[{HOSTNAME}] ALERTA: {IP_LAN} - /dev/{raid_name} {description}"
    
    if 'device_states' in raid_info:
        msg += f" (Estado: {raid_info['device_states']})"
    
    if raid_info['failed_disks']:
        missing = [d for d in raid_info['failed_disks'] if d not in physical_disks]
        present = [d for d in raid_info['failed_disks'] if d in physical_disks]
        
        if missing:
            msg += f"\nDiscos retirados: {', '.join(missing)}"
        if present:
            msg += f"\nDiscos fallados presentes: {', '.join(present)}"
    
    if raid_info.get('resync_info'):
        resync = raid_info['resync_info']
        msg += f"\nResincronizacion: {resync['progress']}%"
        if resync['speed']:
            msg += f" a {resync['speed']}K/sec"
        if resync['finish']:
            msg += f", estimado: {resync['finish']}"
    
    return msg

def send_recovery_message(raid_name):
    """Envia mensaje de recuperacion"""
    msg = f"[{HOSTNAME}] RECUPERADO: {IP_LAN} - /dev/{raid_name} vuelto a estado normal"
    send_telegram_alert(msg, 'info', 'noticias')
    log_message(msg, "INFO")

def send_initial_status(raids):
    """Envia estado inicial"""
    messages = [f"[{HOSTNAME}] Iniciando monitoreo RAID en {IP_LAN}"]
    
    for raid_name, raid_info in raids.items():
        if raid_info['state'] == 'healthy':
            messages.append(f"RAID {raid_name}: OK (Estado: {raid_info.get('device_states', '')})")
        else:
            problem = PROBLEM_STATES.get(raid_info.get('state', 'unknown'), raid_info.get('state', 'unknown'))
            messages.append(f"RAID {raid_name}: {problem.upper()} (Estado: {raid_info.get('device_states', '')})")
            
            if raid_info['failed_disks']:
                messages.append(f"Discos fallados: {', '.join(raid_info['failed_disks'])}")
            
            if raid_info.get('resync_info'):
                messages.append(f"Progreso resincronizacion: {raid_info['resync_info']['progress']}%")
    
    send_telegram_alert("\n".join(messages), 'info', 'noticias')

def check_raid_status():
    """Funcion principal de monitoreo"""
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    log_message(f"Iniciando monitoreo de RAID en {HOSTNAME} ({IP_LAN})")
    log_message(f"Frecuencias: Alertas={CHECK_INTERVAL_ALERTAS}s, Noticias={CHECK_INTERVAL_NOTICIAS}s, Rescan={CHECK_INTERVAL_RESCAN}s")
    
    _, raids = parse_mdstat()
    if raids and not 'error' in raids:
        send_initial_status(raids)
    else:
        error_msg = raids.get('error', 'No se detectaron dispositivos RAID')
        send_telegram_alert(f"[{HOSTNAME}] ERROR: {IP_LAN} - {error_msg}", 'critical', 'alertas')
        send_telegram_alert(f"[{HOSTNAME}] ERROR: {IP_LAN} - {error_msg}", 'critical', 'noticias')
    
    last_alert_times = {}
    
    while running:
        try:
            current_time = time.time()
            _, raids = parse_mdstat()
            physical_disks = get_physical_disks()
            
            if not raids or 'error' in raids:
                time.sleep(CHECK_INTERVAL_RESCAN)
                continue
            
            for raid_name, raid_info in raids.items():
                problem = None
                if raid_info['status'] != 'active':
                    problem = 'inactive'
                elif raid_info.get('state', 'healthy') != 'healthy':
                    problem = raid_info['state']
                
                if problem:
                    if problem in ['failed', 'inactive']:
                        severity = 'critical'
                        alert_type = 'alertas'
                        check_interval = CHECK_INTERVAL_ALERTAS
                    else:
                        severity = 'warning' if problem != 'resyncing' else 'notice'
                        alert_type = 'noticias'
                        check_interval = CHECK_INTERVAL_NOTICIAS
                    
                    if (raid_name not in last_alert_times or 
                        current_time - last_alert_times[raid_name] >= check_interval):
                        
                        alert_msg = build_alert_message(raid_name, raid_info, physical_disks)
                        
                        if send_telegram_alert(alert_msg, severity, alert_type):
                            last_alert_times[raid_name] = current_time
                elif raid_name in last_alert_times:
                    send_recovery_message(raid_name)
                    del last_alert_times[raid_name]
            
            time.sleep(CHECK_INTERVAL_RESCAN)
            
        except Exception as e:
            log_message(f"Error inesperado: {str(e)}", "ERROR")
            time.sleep(60)
    
    send_telegram_alert(f"[{HOSTNAME}] Monitoreo RAID detenido en {IP_LAN}", 'info', 'noticias')

if __name__ == "__main__":
    try:
        check_raid_status()
    except Exception as e:
        error_msg = f"Error critico: {str(e)}"
        log_message(error_msg, "CRITICAL")
        send_telegram_alert(f"[{HOSTNAME}] ERROR CRITICO: {IP_LAN} - {error_msg}", 'critical', 'alertas')
        send_telegram_alert(f"[{HOSTNAME}] ERROR CRITICO: {IP_LAN} - {error_msg}", 'critical', 'noticias')
        sys.exit(1)
    sys.exit(0)
