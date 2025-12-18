#!/usr/bin/env python3
"""
Monitor avanzado de servicios críticos (web + sistema) con modo manual y automático.
Cumple completamente con los requisitos del proyecto intermodular ASO.
Incluye monitorización de servicio web y servicios críticos adicionales.
"""

import sys
import subprocess
import datetime
import os
import socket
import requests
import psutil
import json
import argparse
import platform

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
BASE_DIR = "monitorizacion"

# Servicios a monitorizar
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
LOG_ACCIONES_MANUAL = os.path.join(BASE_DIR, "acciones_manuales.log")

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def registrar_accion_manual(accion, resultado):
    """Registra acciones manuales en un log acumulado."""
    os.makedirs(BASE_DIR, exist_ok=True)
    ahora = datetime.datetime.now().isoformat()
    linea = f"[{ahora}] {accion} -> {resultado}\n"
    with open(LOG_ACCIONES_MANUAL, "a", encoding="utf-8") as f:
        f.write(linea)
    print(f"   📌 Acción registrada: {resultado}")

def ejecutar_comando_sudo(comando, servicio_nombre=""):
    """Ejecuta comando con sudo y captura éxito/error."""
    try:
        subprocess.run(["sudo"] + comando, check=True, capture_output=True)
        resultado = f"{servicio_nombre or 'Servicio'} ejecutado correctamente"
        return True, resultado
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode().strip() if e.stderr else "Error desconocido"
        resultado = f"Error al ejecutar {' '.join(comando)}: {err}"
        return False, resultado

# ==============================================================================
# FUNCIONES DE CHECK
# ==============================================================================

def servicio_instalado(nombre):
    """Comprueba si un servicio systemd está instalado."""
    try:
        result = subprocess.run(["systemctl", "list-unit-files", nombre],
                                capture_output=True, text=True, timeout=5)
        return nombre in result.stdout and ("enabled" in result.stdout or "disabled" in result.stdout or "static" in result.stdout)
    except:
        return False

def detectar_servicios_instalados(lista_candidatos):
    return [svc for svc in lista_candidatos if servicio_instalado(svc)]

def check_estado_servicio(nombre):
    try:
        result = subprocess.run(["systemctl", "is-active", nombre],
                                capture_output=True, text=True, timeout=10)
        estado = result.stdout.strip()
        activo = (estado == "active")
        detalles = f"Estado: {estado}"
        return activo, "OK" if activo else "CRIT", detalles
    except Exception as e:
        return False, "CRIT", f"Error: {e}"

def check_puerto_escuchando(puerto=80):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(("127.0.0.1", puerto))
            escuchando = (result == 0)
            detalles = f"Puerto {puerto} {'escuchando' if escuchando else 'NO escuchando'}"
            return escuchando, "OK" if escuchando else "CRIT", detalles
    except Exception as e:
        return False, "CRIT", f"Error: {e}"

def check_respuesta_http(url="http://localhost", timeout=10, max_time=3.0):
    try:
        start = datetime.datetime.now()
        response = requests.get(url, timeout=timeout)
        tiempo = (datetime.datetime.now() - start).total_seconds()
        codigo = response.status_code
        detalles = f"HTTP {codigo}, tiempo: {tiempo:.2f}s"
        estado = "OK" if codigo == 200 else ("CRIT" if 400 <= codigo < 600 else "WARN")
        if tiempo > max_time:
            estado = "WARN" if estado == "OK" else estado
        return True, estado, detalles, tiempo, codigo
    except requests.exceptions.Timeout:
        return False, "CRIT", "Timeout HTTP", timeout, None
    except Exception as e:
        return False, "CRIT", f"Error HTTP: {e}"

def check_recursos_sistema():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent
        estado = "OK"
        if cpu > UMBRALES["cpu_percent"] or ram > UMBRALES["ram_percent"]:
            estado = "WARN"
        if disco > UMBRALES["disk_percent"]:
            estado = "CRIT"
        detalles = f"CPU: {cpu:.1f}%, RAM: {ram:.1f}%, Disco: {disco:.1f}%"
        return True, estado, detalles
    except Exception as e:
        return False, "CRIT", f"Error recursos: {e}"

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
# CHECK GLOBAL Y GUARDADO
# ==============================================================================

def ejecutar_monitorizacion(modo_auto=False):
    print("🔍 Iniciando monitorización...")
    checks = {}
    estados = []

    # Servicios críticos
    todos_candidatos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
    instalados = detectar_servicios_instalados(todos_candidatos)
    web_detectado = next((s for s in SERVICIOS_WEB if s in instalados), None)

    for svc in instalados:
        activo, estado, detalles = check_estado_servicio(svc)
        checks[svc] = {"estado": estado, "detalles": detalles}
        estados.append(estado)

    if web_detectado:
        checks["servicio_web_detectado"] = {"estado": "INFO", "detalles": f"Servicio web activo: {web_detectado}"}

    # Puerto y HTTP
    escuchando, estado_p, detalles_p = check_puerto_escuchando(PUERTO_WEB)
    checks["puerto_web"] = {"estado": estado_p, "detalles": detalles_p}
    estados.append(estado_p)

    exito, estado_h, detalles_h, _, _ = check_respuesta_http(
        timeout=UMBRALES["http_timeout"], max_time=UMBRALES["http_max_time"])
    checks["respuesta_http"] = {"estado": estado_h, "detalles": detalles_h}
    estados.append(estado_h)

    # Recursos
    _, estado_r, detalles_r = check_recursos_sistema()
    checks["recursos_sistema"] = {"estado": estado_r, "detalles": detalles_r}
    estados.append(estado_r)

    # Estado global
    estado_global = "CRIT" if "CRIT" in estados else ("WARN" if "WARN" in estados else "OK")

    # Guardar
    guardar_resultado({
        "checks": checks,
        "estado_global": estado_global,
        "servicio_web": web_detectado
    }, modo_auto=modo_auto)

    return estado_global

def crear_ruta_salida(fecha_hoy):
    ruta = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta, exist_ok=True)
    return ruta

def guardar_resultado(resultado, modo_auto=False):
    ahora = datetime.datetime.now()
    fecha_iso = ahora.isoformat()
    hostname, ip = obtener_info_sistema()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y%m%d_%H%M%S")
    sufijo = {"CRIT": "CRIT", "WARN": "WARN"}.get(resultado["estado_global"], "OK")
    modo_str = "auto" if modo_auto else "manual"

    # Nombre descriptivo: incluye web y críticos
    nombre_base = f"monitor_web_criticos_{modo_str}_{timestamp}_{sufijo}"

    ruta = crear_ruta_salida(fecha_hoy)
    json_path = os.path.join(ruta, f"{nombre_base}.json")
    txt_path = os.path.join(ruta, f"{nombre_base}.log")

    datos_json = {
        "fecha_hora": fecha_iso,
        "hostname": hostname,
        "ip": ip,
        "modo": "automatico" if modo_auto else "manual",
        "checks": resultado["checks"],
        "estado_global": resultado["estado_global"]
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(datos_json, f, indent=2, ensure_ascii=False)

    lines = [
        "=" * 70,
        "MONITORIZACIÓN DE SERVICIOS WEB Y CRÍTICOS",
        "=" * 70,
        "Fecha/hora: " + fecha_iso,
        f"Host: {hostname} ({ip})",
        f"Modo: {'Automático' if modo_auto else 'Manual'}",
        f"Estado global: {resultado['estado_global']}",
        "-" * 70,
    ]
    for check, info in resultado["checks"].items():
        lines.append(f"🔹 {check}: {info['estado']} — {info['detalles']}")
    lines.extend(["-" * 70, f"ESTADO GLOBAL: {resultado['estado_global']}", "=" * 70])

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n✅ Informe guardado en: {txt_path}")
    print(f"📊 JSON en: {json_path}\n")

# ==============================================================================
# MENÚ INTERACTIVO (SIN PARÉNTESIS CON NOMBRE DEL SERVICIO)
# ==============================================================================

def menu_interactivo():
    print("\n" + "="*60)
    print("🔧 MONITOR DE SERVICIOS CRÍTICOS - MODO MANUAL")
    print("="*60)

    web_instalados = detectar_servicios_instalados(SERVICIOS_WEB)
    servicio_web = next(iter(web_instalados), None)

    while True:
        print("\nOpciones:")
        print("1. Arrancar servicio web")
        print("2. Parar servicio web")
        print("3. Reiniciar servicio web")
        print("4. Monitorizar servicios críticos")
        print("5. Ver uso de recursos")
        print("6. Listar servicios críticos instalados")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ").strip()

        if opcion in ["1", "2", "3"] and not servicio_web:
            print("⚠️ No se detectó ningún servicio web (apache2/nginx) instalado.")
            continue

        if opcion == "1":
            exito, msg = ejecutar_comando_sudo(["systemctl", "start", servicio_web], servicio_web)
            registrar_accion_manual(f"ARRANCAR {servicio_web}", msg)
        elif opcion == "2":
            exito, msg = ejecutar_comando_sudo(["systemctl", "stop", servicio_web], servicio_web)
            registrar_accion_manual(f"PARAR {servicio_web}", msg)
        elif opcion == "3":
            exito, msg = ejecutar_comando_sudo(["systemctl", "restart", servicio_web], servicio_web)
            registrar_accion_manual(f"REINICIAR {servicio_web}", msg)
        elif opcion == "4":
            ejecutar_monitorizacion(modo_auto=False)
        elif opcion == "5":
            _, estado, detalles = check_recursos_sistema()
            print(f"\n📊 Recursos: {detalles} → Estado: {estado}\n")
        elif opcion == "6":
            todos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
            instalados = detectar_servicios_instalados(todos)
            print("\n✅ Servicios críticos instalados:")
            for s in instalados or ["Ninguno detectado"]:
                print(f"  - {s}")
            print()
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("⚠️ Opción no válida.")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Monitor avanzado de servicios críticos")
    parser.add_argument('--auto', action='store_true', help="Modo automático para cron")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático ejecutándose...")
        ejecutar_monitorizacion(modo_auto=True)
    else:
        menu_interactivo()

if __name__ == "__main__":
    try:
        import psutil, requests  # noqa: F401
    except ImportError as e:
        print(f"❌ Falta dependencia: {e.name if hasattr(e, 'name') else e}")
        print("Instala con: sudo apt install python3-psutil python3-requests")
        print("O con pip: pip3 install --user psutil requests")
        sys.exit(1)
    main()