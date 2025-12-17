#!/usr/bin/env python3
"""
Monitor avanzado de servicios web (Apache/Nginx) con modo manual y automático.
Cumple con todos los requisitos funcionales mínimos del proyecto.
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

def verificar_dependencias():
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"❌ ERROR: Falta la librería {e.name}.")
        print("👉 Ejecuta: python3 -m pip install psutil requests")
        sys.exit(1)

if __name__ == "__main__":
    verificar_dependencias()
    main()
# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Carpeta base de salida
BASE_DIR = "monitorizacion"

# Servicios web a monitorizar (ajustable)
SERVICIOS_WEB = ["apache2.service", "nginx.service"]

# Umbrales para alertas (ajustables)
UMBRALES = {
    "cpu_percent": 85,      # >85% → WARN
    "ram_percent": 90,      # >90% → WARN
    "disk_percent": 95,     # >95% → CRIT
    "http_timeout": 10,     # segundos
    "http_max_time": 3.0,   # segundos
}

# Puerto predeterminado del servicio web
PUERTO_WEB = 80

# ==============================================================================
# FUNCIONES DE CHECK (modulares y reutilizables)
# ==============================================================================

def check_estado_servicio(nombre):
    """Verifica si el servicio está activo."""
    try:
        result = subprocess.run(["systemctl", "is-active", nombre], capture_output=True, text=True, timeout=10)
        estado = result.stdout.strip()
        activo = (estado == "active")
        detalles = f"Estado: {estado}"
        return activo, "OK", detalles
    except Exception as e:
        return False, "CRIT", f"Error al comprobar estado: {e}"

def check_puerto_escuchando(puerto=80):
    """Verifica si el puerto 80 está escuchando localmente."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(("127.0.0.1", puerto))
            escuchando = (result == 0)
            detalles = f"Puerto {puerto} {'escuchando' if escuchando else 'NO escuchando'}"
            estado = "OK" if escuchando else "CRIT"
            return escuchando, estado, detalles
    except Exception as e:
        return False, "CRIT", f"Error al comprobar puerto: {e}"

def check_respuesta_http(url="http://localhost", timeout=10, max_time=3.0):
    """Hace una petición HTTP y devuelve código, tiempo y estado."""
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
        return False, "CRIT", "Timeout en petición HTTP", timeout, None
    except Exception as e:
        return False, "CRIT", f"Error HTTP: {e}", 0, None

def check_recursos_sistema():
    """Obtiene uso de CPU, RAM y disco."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent

        checks = []
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
        return False, "CRIT", f"Error al obtener recursos: {e}", {}

def obtener_info_sistema():
    """Obtiene hostname e IP local principal."""
    hostname = platform.node()
    try:
        # IP de la interfaz principal
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    return hostname, ip

# ==============================================================================
# FUNCIONES DE EVALUACIÓN GLOBAL
# ==============================================================================

def determinar_estado_global(estados_checks):
    """Determina estado global: CRIT > WARN > OK"""
    if "CRIT" in estados_checks:
        return "CRIT"
    elif "WARN" in estados_checks:
        return "WARN"
    else:
        return "OK"

# ==============================================================================
# FUNCIONES DE SALIDA
# ==============================================================================

def crear_ruta_salida(fecha_hoy):
    ruta = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta, exist_ok=True)
    return ruta

def guardar_resultado(resultado, modo_auto=False):
    """Guarda el resultado en JSON y en informe legible."""
    ahora = datetime.datetime.now()
    fecha_iso = ahora.isoformat()
    hostname, ip = obtener_info_sistema()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y%m%d_%H%M%S")

    # Nombre del archivo
    if modo_auto:
        nombre_base = f"monitor_web_auto_{timestamp}"
    else:
        nombre_base = f"monitor_web_{timestamp}"

    ruta = crear_ruta_salida(fecha_hoy)
    json_path = os.path.join(ruta, f"{nombre_base}.json")
    txt_path = os.path.join(ruta, f"{nombre_base}.log")

    # Datos completos para JSON
    datos_json = {
        "fecha_hora": fecha_iso,
        "hostname": hostname,
        "ip": ip,
        "modo": "automatico" if modo_auto else "manual",
        "checks": resultado["checks"],
        "estado_global": resultado["estado_global"]
    }

    # Guardar JSON (procesable)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(datos_json, f, indent=2, ensure_ascii=False)

    # Generar informe legible
    lines = []
    lines.append("=" * 70)
    lines.append("MONITORIZACIÓN DE SERVICIO WEB")
    lines.append("=" * 70)
    lines.append(f"Fecha/hora: {fecha_iso}")
    lines.append(f"Host: {hostname} ({ip})")
    lines.append(f"Modo: {'Automático' if modo_auto else 'Manual'}")
    lines.append("-" * 70)

    for check, info in resultado["checks"].items():
        lines.append(f"🔹 {check}: {info['estado']} — {info['detalles']}")

    lines.append("-" * 70)
    lines.append(f"✅ ESTADO GLOBAL: {resultado['estado_global']}")
    lines.append("=" * 70)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n✅ Informe guardado en: {txt_path}")
    print(f"📊 Datos en: {json_path}\n")

def ejecutar_monitorizacion(modo_auto=False):
    """Ejecuta todos los checks y genera el informe."""
    print("🔍 Iniciando monitorización del servicio web...")
    checks_result = {}
    estados = []

    # 1. Encontrar servicio web activo
    servicio_activo = None
    for svc in SERVICIOS_WEB:
        activo, estado, detalles = check_estado_servicio(svc)
        if activo:
            servicio_activo = svc
            checks_result["servicio"] = {"estado": estado, "detalles": detalles}
            estados.append(estado)
            break
    if not servicio_activo:
        # Si ninguno está activo, registra el último chequeado
        svc = SERVICIOS_WEB[0]
        _, estado, detalles = check_estado_servicio(svc)
        checks_result["servicio"] = {"estado": estado, "detalles": detalles}
        estados.append(estado)

    # 2. Puerto escuchando
    escuchando, estado, detalles = check_puerto_escuchando(PUERTO_WEB)
    checks_result["puerto"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    # 3. Respuesta HTTP
    exito, estado, detalles, tiempo, codigo = check_respuesta_http(
        timeout=UMBRALES["http_timeout"],
        max_time=UMBRALES["http_max_time"]
    )
    checks_result["http"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    # 4. Recursos del sistema
    exito, estado, detalles, recursos = check_recursos_sistema()
    checks_result["recursos"] = {"estado": estado, "detalles": detalles}
    estados.append(estado)

    # Estado global
    estado_global = determinar_estado_global(estados)

    resultado = {
        "checks": checks_result,
        "estado_global": estado_global
    }

    guardar_resultado(resultado, modo_auto=modo_auto)
    return estado_global

# ==============================================================================
# MENÚ INTERACTIVO (≥5 opciones)
# ==============================================================================

def menu_interactivo():
    print("\n" + "="*50)
    print("🔧 MONITOR WEB - MODO MANUAL")
    print("="*50)
    while True:
        print("\nOpciones:")
        print("1. Arrancar servicio web")
        print("2. Parar servicio web")
        print("3. Reiniciar servicio web")
        print("4. Monitorizar servicio web")
        print("5. Ver estado del sistema (CPU/RAM/DISCO)")
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
            print(f"\n📊 Recursos del sistema: {detalles} → Estado: {estado}\n")
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("⚠️ Opción no válida.")

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Monitor avanzado de servicio web")
    parser.add_argument('--auto', action='store_true', help="Ejecutar en modo automático (para cron)")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático: ejecutando chequeo completo...")
        ejecutar_monitorizacion(modo_auto=True)
    else:
        menu_interactivo()

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"❌ Error: dependencia faltante: {e}")
        print("Instala con: pip install psutil requests")
        sys.exit(1)

    main()