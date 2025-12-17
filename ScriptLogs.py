#!/usr/bin/env python3
"""
Monitor avanzado de servicios críticos (web + sistema) con modo manual y automático.
Incluye: Apache/Nginx, MySQL/MariaDB, PostgreSQL, Redis, SSH, Cron.
"""

import sys
import subprocess
import datetime
import os
import socket
import requests
import psutil
import shutil
import json
import argparse
import platform

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
BASE_DIR = "monitorizacion"

# Servicios web y críticos (se detectan dinámicamente)
SERVICIOS_WEB = ["apache2.service", "nginx.service"]
SERVICIOS_BASE_DATOS = ["mysql.service", "mariadb.service", "postgresql.service"]
SERVICIOS_CACHE = ["redis-server.service"]
SERVICIOS_SISTEMA = ["ssh.service", "sshd.service", "cron.service", "crond.service"]

# Umbrales para alertas
UMBRALES = {
    "cpu_percent": 85,
    "ram_percent": 90,
    "disk_percent": 95,
    "http_timeout": 10,
    "http_max_time": 3.0,
}

PUERTO_WEB = 80

# ==============================================================================
# FUNCIONES DE CHECK
# ==============================================================================

def check_estado_servicio(nombre):
    """Verifica si el servicio está activo."""
    try:
        result = subprocess.run(["systemctl", "is-active", nombre], 
                                capture_output=True, text=True, timeout=10)
        estado = result.stdout.strip()
        activo = (estado == "active")
        detalles = f"Estado: {estado}"
        return activo, "OK" if activo else "CRIT", detalles
    except Exception as e:
        return False, "CRIT", f"Error al comprobar {nombre}: {e}"

def check_puerto_escuchando(puerto=80):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(("127.0.0.1", puerto))
            escuchando = (result == 0)
            detalles = f"Puerto {puerto} {'escuchando' if escuchando else 'NO escuchando'}"
            estado = "OK" if escuchando else "CRIT"
            return escuchando, estado, detalles
    except Exception as e:
        return False, "CRIT", f"Error puerto: {e}"

def check_respuesta_http(url="http://localhost", timeout=10, max_time=3.0):
    try:
        start = datetime.datetime.now()
        response = requests.get(url, timeout=timeout)
        tiempo = (datetime.datetime.now() - start).total_seconds()
        codigo = response.status_code
        detalles = f"HTTP {codigo}, tiempo: {tiempo:.2f}s"
        if codigo == 200:
            estado = "OK"
        elif 400 <= codigo < 600:
            estado = "CRIT"
        else:
            estado = "WARN"
        if tiempo > max_time:
            estado = "WARN" if estado == "OK" else estado
        return True, estado, detalles, tiempo, codigo
    except requests.exceptions.Timeout:
        return False, "CRIT", "Timeout HTTP", timeout, None
    except Exception as e:
        return False, "CRIT", f"Error HTTP: {e}", 0, None

def check_recursos_sistema():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent
        estado_global = "OK"
        if cpu > UMBRALES["cpu_percent"]:
            estado_global = "WARN"
        if ram > UMBRALES["ram_percent"]:
            estado_global = "WARN"
        if disco > UMBRALES["disk_percent"]:
            estado_global = "CRIT"
        detalles = f"CPU: {cpu:.1f}%, RAM: {ram:.1f}%, Disco: {disco:.1f}%"
        return True, estado_global, detalles, {"cpu": cpu, "ram": ram, "disco": disco}
    except Exception as e:
        return False, "CRIT", f"Error recursos: {e}", {}

def obtener_info_sistema():
    hostname = platform.node()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    return hostname, ip

# ==============================================================================
# DETECCIÓN DINÁMICA DE SERVICIOS INSTALADOS
# ==============================================================================

def listar_servicios_instalados(candidatos):
    """Devuelve lista de servicios candidatos que están instalados (existen en systemd)."""
    instalados = []
    try:
        for svc in candidatos:
            result = subprocess.run(["systemctl", "list-unit-files", "--type=service", "--no-pager"],
                                    capture_output=True, text=True, timeout=10)
            if svc in result.stdout:
                instalados.append(svc)
    except Exception:
        pass
    return instalados

def check_servicios_criticos():
    """Verifica estado de todos los servicios críticos instalados."""
    todos_servicios = (
        SERVICIOS_WEB + SERVICIOS_BASE_DATOS + 
        SERVICIOS_CACHE + SERVICIOS_SISTEMA
    )
    servicios_instalados = listar_servicios_instalados(todos_servicios)
    resultados = {}
    estados = []

    for svc in servicios_instalados:
        activo, estado, detalles = check_estado_servicio(svc)
        resultados[svc] = {"estado": estado, "detalles": detalles}
        estados.append(estado)

    if not servicios_instalados:
        resultados["ninguno"] = {"estado": "WARN", "detalles": "No se encontraron servicios críticos instalados"}
        estados = ["WARN"]

    estado_global = "OK"
    if "CRIT" in estados:
        estado_global = "CRIT"
    elif "WARN" in estados:
        estado_global = "WARN"

    return resultados, estado_global

# ==============================================================================
# EVALUACIÓN GLOBAL
# ==============================================================================

def determinar_estado_global(estados_lista):
    if "CRIT" in estados_lista:
        return "CRIT"
    elif "WARN" in estados_lista:
        return "WARN"
    else:
        return "OK"

# ==============================================================================
# SALIDA
# ==============================================================================

def crear_ruta_salida(fecha_hoy):
    ruta = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta, exist_ok=True)
    return ruta

def guardar_resultado(resultado, modo_auto=False):
    """Guarda el resultado con nombre que siempre incluye 'web' y el estado al final."""
    ahora = datetime.datetime.now()
    fecha_iso = ahora.isoformat()
    hostname, ip = obtener_info_sistema()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y%m%d_%H%M%S")
    
    # Determinar sufijo de estado
    estado_global = resultado["estado_global"]
    sufijo = {"CRIT": "CRIT", "WARN": "WARN"}.get(estado_global, "OK")

    # Nombre base: SIEMPRE empieza por "monitor_web_", incluso si se monitorean otros servicios
    if modo_auto:
        nombre_base = f"monitor_web_auto_{timestamp}_{sufijo}"
    else:
        nombre_base = f"monitor_web_{timestamp}_{sufijo}"

    ruta = crear_ruta_salida(fecha_hoy)
    json_path = os.path.join(ruta, f"{nombre_base}.json")
    txt_path = os.path.join(ruta, f"{nombre_base}.log")

    # Datos JSON
    datos_json = {
        "fecha_hora": fecha_iso,
        "hostname": hostname,
        "ip": ip,
        "modo": "automatico" if modo_auto else "manual",
        "checks": resultado["checks"],
        "estado_global": estado_global
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(datos_json, f, indent=2, ensure_ascii=False)

    # Informe legible
    lines = []
    lines.append("=" * 70)
    lines.append("MONITORIZACIÓN DE SERVICIOS WEB Y CRÍTICOS")
    lines.append("=" * 70)
    lines.append(f"Fecha/hora: {fecha_iso}")
    lines.append(f"Host: {hostname} ({ip})")
    lines.append(f"Modo: {'Automático' if modo_auto else 'Manual'}")
    lines.append(f"Estado global: {estado_global}")
    lines.append("-" * 70)
    for check, info in resultado["checks"].items():
        lines.append(f"🔹 {check}: {info['estado']} — {info['detalles']}")
    lines.append("-" * 70)
    lines.append(f"✅ ESTADO GLOBAL: {estado_global}")
    lines.append("=" * 70)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n✅ Informe guardado en: {txt_path}")
    print(f"📊 Datos en: {json_path}\n")
# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================

def ejecutar_monitorizacion(modo_auto=False):
    print("🔍 Iniciando monitorización de servicios críticos...")
    checks_result = {}
    estados = []

    # 1. Servicios críticos
    servicios_checks, estado_servicios = check_servicios_criticos()
    checks_result["servicios_criticos"] = {
        "estado": estado_servicios,
        "detalles": f"{len(servicios_checks)} servicios verificados"
    }
    estados.append(estado_servicios)

    # 2. Puerto web
    escuchando, estado, detalles = check_puerto_escuchando(PUERTO_WEB)
    checks_result["puerto_web"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    # 3. HTTP
    exito, estado, detalles, tiempo, codigo = check_respuesta_http(
        timeout=UMBRALES["http_timeout"], max_time=UMBRALES["http_max_time"]
    )
    checks_result["http"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    # 4. Recursos
    exito, estado, detalles, recursos = check_recursos_sistema()
    checks_result["recursos_sistema"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    estado_global = determinar_estado_global(estados)
    resultado = {
        "checks": checks_result,
        "estado_global": estado_global
    }

    guardar_resultado(resultado, modo_auto=modo_auto)
    return estado_global

# ==============================================================================
# MENÚ INTERACTIVO
# ==============================================================================

def menu_interactivo():
    print("\n" + "="*50)
    print("🔧 MONITOR DE SERVICIOS CRÍTICOS - MODO MANUAL")
    print("="*50)
    while True:
        print("\nOpciones:")
        print("1. Arrancar servicio (web)")
        print("2. Parar servicio (web)")
        print("3. Reiniciar servicio (web)")
        print("4. Monitorizar servicios críticos")
        print("5. Ver uso de recursos (CPU/RAM/DISCO)")
        print("6. Listar servicios instalados")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            for svc in SERVICIOS_WEB:
                try:
                    subprocess.run(["sudo", "systemctl", "start", svc], check=True)
                    print(f"✅ {svc} arrancado.")
                    break
                except subprocess.CalledProcessError:
                    continue
        elif opcion == "2":
            for svc in SERVICIOS_WEB:
                try:
                    subprocess.run(["sudo", "systemctl", "stop", svc], check=True)
                    print(f"🛑 {svc} detenido.")
                    break
                except subprocess.CalledProcessError:
                    continue
        elif opcion == "3":
            for svc in SERVICIOS_WEB:
                try:
                    subprocess.run(["sudo", "systemctl", "restart", svc], check=True)
                    print(f"🔄 {svc} reiniciado.")
                    break
                except subprocess.CalledProcessError:
                    continue
        elif opcion == "4":
            ejecutar_monitorizacion(modo_auto=False)
        elif opcion == "5":
            _, estado, detalles, _ = check_recursos_sistema()
            print(f"\n📊 Recursos: {detalles} → Estado: {estado}\n")
        elif opcion == "6":
            todos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
            instalados = listar_servicios_instalados(todos)
            print("\n✅ Servicios instalados detectados:")
            for s in instalados:
                print(f"  - {s}")
            if not instalados:
                print("  (ninguno detectado)")
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("⚠️ Opción no válida.")

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Monitor avanzado de servicios críticos")
    parser.add_argument('--auto', action='store_true', help="Ejecutar en modo automático (para cron)")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático: ejecutando chequeo completo...")
        ejecutar_monitorizacion(modo_auto=True)
    else:
        menu_interactivo()

if __name__ == "__main__":
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"❌ Error: dependencia faltante: {e}")
        print("Instala con: pip install psutil requests")
        sys.exit(1)
    main()