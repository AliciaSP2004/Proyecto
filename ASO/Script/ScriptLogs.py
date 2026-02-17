#!/usr/bin/env python3
"""
Monitor avanzado de servicios críticos (web + sistema) con modo manual y automático.
Cumple completamente con los requisitos del proyecto intermodular ASO.
Incluye monitorización de servicio web y servicios críticos adicionales.
"""

# Comentarios generales:
# - Este módulo ofrece checks remotos (vía SSH) y locales para monitorizar servicios web
#   y componentes críticos (BD, cache, sistema). También permite acciones manuales
#   (start/stop/restart) y guarda informes tanto en texto legible como en JSON.
# - Las funciones están organizadas en: configuración, auxiliares (SSH/IO), checks,
#   orquestador/guardado y una UI simple por menú para uso interactivo.

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
import paramiko

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# Sección de configuración: constantes y listas que definen qué comprobar,
# umbrales y servidores a monitorizar. Centralizar la configuración facilita
# adaptar el script a distintos entornos sin tocar la lógica.
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

# Lista de servidores remotos a monitorizar
SERVIDORES = [
    {"nombre": "Servidor (10.0.2.31)", "ip": "10.0.2.31", "usuario": "ubuntu", "clave_privada": "/home/ubuntu/Proyecto/nube/ansible/Apaches/.ssh/ansible.pem"},
    {"nombre": "Servidor (10.0.2.106)", "ip": "10.0.2.106", "usuario": "ubuntu", "clave_privada": "/home/ubuntu/Proyecto/nube/ansible/Apaches/.ssh/ansible.pem"},
]

PUERTO_WEB = 80
LOG_ACCIONES_MANUAL = os.path.join(BASE_DIR, "acciones_manuales.log")

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def registrar_accion_manual(accion, resultado):
    # Propósito: almacenar un histórico de acciones manuales (arrancar/detener/reiniciar)
    # Por qué: auditoría y trazabilidad de operaciones realizadas desde el menú.
    """Registra acciones manuales en un log acumulado."""
    os.makedirs(BASE_DIR, exist_ok=True)
    ahora = datetime.datetime.now().isoformat()
    linea = f"[{ahora}] {accion} -> {resultado}\n"
    with open(LOG_ACCIONES_MANUAL, "a", encoding="utf-8") as f:
        f.write(linea)
    print(f"   📌 Acción registrada: {resultado}")

def ejecutar_comando_sudo_remoto(ssh, comando, servicio_nombre=""):
    # Propósito: ejecutar comandos que requieren privilegios remotos sin interacción.
    # Por qué: usar `sudo -n` evita prompts de contraseña que romperían la automatización.
    """Ejecuta comando con sudo y siempre devuelve mensaje claro."""
    cmd = f"sudo -n {comando}"
    resultado = ejecutar_comando_remoto(ssh, cmd)
    exito = "Error" not in resultado
    if exito and not resultado.strip():
        resultado = f"✅ {servicio_nombre} ejecutado correctamente"
    elif not exito:
        resultado = f"❌ {resultado}"
    return exito, resultado

def conectar_ssh(servidor):
    # Propósito: establecer una sesión SSH reutilizable.
    # Por qué: centralizar conexión y manejo de errores para no repetir código.
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(servidor["ip"], username=servidor["usuario"], key_filename=servidor["clave_privada"])
        return ssh
    except Exception as e:
        print(f"Error SSH a {servidor['nombre']}: {e}")
        return None

def ejecutar_comando_remoto(ssh, comando):
    # Propósito: ejecutar un comando en el host remoto y normalizar la salida.
    # Por qué: un punto único de lectura de stdout/stderr facilita detección de errores.
    try:
        stdin, stdout, stderr = ssh.exec_command(comando)
        salida = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        return salida if not error else f"Error: {error}"
    except Exception as e:
        return f"Error ejecución remota: {e}"

# ==============================================================================
# FUNCIONES DE CHECK
# ==============================================================================

def servicio_instalado_remoto(ssh, nombre):
    # Propósito: comprobar si una unidad systemd está registrada en el sistema remoto.
    # Por qué: evita intentar checks sobre servicios que no están presentes.
    cmd = f"systemctl list-unit-files {nombre}"
    salida = ejecutar_comando_remoto(ssh, cmd)
    return nombre in salida and ("enabled" in salida or "disabled" in salida or "static" in salida)

def detectar_servicios_instalados_remoto(ssh, lista_candidatos):
    # Propósito: filtrar la lista de candidatos y devolver solo los instalados.
    return [svc for svc in lista_candidatos if servicio_instalado_remoto(ssh, svc)]

def check_estado_servicio_remoto(ssh, nombre):
    # Propósito: determinar si un servicio systemd está `active`.
    # Por qué: el estado del servicio es la base para decidir `OK` o `CRIT`.
    salida = ejecutar_comando_remoto(ssh, f"systemctl is-active {nombre}")
    estado = salida.strip()
    activo = (estado == "active")
    return activo, "OK" if activo else "CRIT", f"Estado: {estado}"

def check_puerto_escuchando_remoto(servidor_ip, puerto=80):
    # Propósito: verificar a nivel de TCP si el puerto está aceptando conexiones.
    # Por qué: un puerto abierto no garantiza servicio HTTP funcional, pero es un chequeo rápido.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex((servidor_ip, puerto))
            escuchando = (result == 0)
            return escuchando, "OK" if escuchando else "CRIT", f"Puerto {puerto} {'escuchando' if escuchando else 'NO escuchando'}"
    except Exception as e:
        return False, "CRIT", f"Error: {e}"

def check_respuesta_http_remoto(servidor_ip, timeout=10, max_time=3.0):
    # Propósito: solicitar la URL principal y medir código HTTP y latencia.
    # Por qué: comprueba funcionalidad de la aplicación web, no solo conectividad TCP.
    url = f"http://{servidor_ip}"
    try:
        start = datetime.datetime.now()
        response = requests.get(url, timeout=timeout)
        tiempo = (datetime.datetime.now() - start).total_seconds()
        codigo = response.status_code
        detalles = f"HTTP {codigo}, tiempo: {tiempo:.2f}s"
        estado = "OK" if codigo == 200 else ("CRIT" if 400 <= codigo < 600 else "WARN")
        if tiempo > max_time:
            estado = "WARN" if estado == "OK" else estado
        return estado, detalles
    except requests.exceptions.Timeout:
        return "CRIT", "Timeout HTTP"
    except Exception as e:
        return "CRIT", f"Error HTTP: {e}"

def check_recursos_sistema_remoto(ssh):
    # Propósito: obtener métricas de CPU/RAM/Disco desde el host remoto y compararlas
    # con umbrales definidos.
    # Por qué: recursos saturados suelen ser causa de degradación o fallos de servicio.
    try:
        cpu = float(ejecutar_comando_remoto(ssh, "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'") or 0)
        ram = float(ejecutar_comando_remoto(ssh, "free | grep Mem | awk '{print $3/$2 * 100.0}'") or 0)
        disco = float(ejecutar_comando_remoto(ssh, "df -h / | tail -1 | awk '{print $5}' | sed 's/%//'" ) or 0)
        estado = "OK"
        if cpu > UMBRALES["cpu_percent"] or ram > UMBRALES["ram_percent"]:
            estado = "WARN"
        if disco > UMBRALES["disk_percent"]:
            estado = "CRIT"
        detalles = f"CPU: {cpu:.1f}%, RAM: {ram:.1f}%, Disco: {disco:.1f}%"
        return estado, detalles
    except Exception as e:
        return "CRIT", f"Error recursos: {e}"

def obtener_info_sistema_local():
    # Propósito: obtener hostname e IP local (para incluir en informes).
    # Por qué: facilita identificar el origen del informe cuando se revisan logs.
    hostname = platform.node()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    return hostname, ip

def obtener_info_sistema_remoto(ssh):
    # Propósito: recuperar hostname e IP del host remoto vía SSH.
    # Por qué: metadatos útiles para el informe y diagnóstico remoto.
    hostname = ejecutar_comando_remoto(ssh, "hostname")
    ip = ejecutar_comando_remoto(ssh, "hostname -I | awk '{print $1}'")
    return hostname, ip

# ==============================================================================
# CHECK GLOBAL Y GUARDADO
# ==============================================================================

def monitorizar_servidor(servidor, modo_auto=False, checks_selectivos=None):
    # Propósito: orquestar todos los checks para un servidor y guardar el resultado.
    # Por qué: centraliza la lógica de monitorización y determina el estado global.
    ssh = conectar_ssh(servidor)
    if not ssh:
        return {"estado_global": "CRIT", "checks": {"ssh": {"estado": "CRIT", "detalles": "Conexión SSH fallida"}}}

    hostname_remoto, ip_remoto = obtener_info_sistema_remoto(ssh)

    checks = {}
    estados = []

    todos_candidatos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
    instalados = detectar_servicios_instalados_remoto(ssh, todos_candidatos)
    web_detectado = next((s for s in SERVICIOS_WEB if s in instalados), None)

    if checks_selectivos is None or "servicios" in checks_selectivos:
        for svc in instalados:
            activo, estado, detalles = check_estado_servicio_remoto(ssh, svc)
            checks[svc] = {"estado": estado, "detalles": detalles}
            estados.append(estado)

    if web_detectado:
        checks["servicio_web_detectado"] = {"estado": "INFO", "detalles": f"Servicio web activo: {web_detectado}"}

    if checks_selectivos is None or "puerto" in checks_selectivos:
        escuchando, estado_p, detalles_p = check_puerto_escuchando_remoto(servidor["ip"], PUERTO_WEB)
        checks["puerto_web"] = {"estado": estado_p, "detalles": detalles_p}
        estados.append(estado_p)

    if checks_selectivos is None or "http" in checks_selectivos:
        estado_h, detalles_h = check_respuesta_http_remoto(servidor["ip"], UMBRALES["http_timeout"], UMBRALES["http_max_time"])
        checks["respuesta_http"] = {"estado": estado_h, "detalles": detalles_h}
        estados.append(estado_h)

    if checks_selectivos is None or "recursos" in checks_selectivos:
        estado_r, detalles_r = check_recursos_sistema_remoto(ssh)
        checks["recursos_sistema"] = {"estado": estado_r, "detalles": detalles_r}
        estados.append(estado_r)

    estado_global = "CRIT" if "CRIT" in estados else ("WARN" if "WARN" in estados else "OK")

    guardar_resultado({
        "checks": checks,
        "estado_global": estado_global,
        "servidor": servidor["nombre"],
        "hostname_remoto": hostname_remoto,
        "ip_remoto": ip_remoto
    }, modo_auto=modo_auto)

    ssh.close()

    return estado_global

def crear_ruta_salida(fecha_hoy):
    # Propósito: crear una carpeta organizada por fecha para guardar informes.
    ruta = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta, exist_ok=True)
    return ruta

def guardar_resultado(resultado, modo_auto=False):
    # Propósito: serializar y persistir el resultado del check en JSON y texto.
    # Por qué: mantener histórico legible (log) y estructurado (JSON) para análisis.
    ahora = datetime.datetime.now()
    fecha_iso = ahora.isoformat()
    hostname_local, ip_local = obtener_info_sistema_local()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y%m%d_%H%M%S")
    sufijo = {"CRIT": "CRIT", "WARN": "WARN"}.get(resultado["estado_global"], "OK")
    modo_str = "auto" if modo_auto else "manual"

    nombre_base = f"monitor_web_{modo_str}_{timestamp}_{sufijo}"

    ruta = crear_ruta_salida(fecha_hoy)
    json_path = os.path.join(ruta, f"{nombre_base}.json")
    txt_path = os.path.join(ruta, f"{nombre_base}.log")

    datos_json = {
        "fecha_hora": fecha_iso,
        "hostname_local": hostname_local,
        "ip_local": ip_local,
        "hostname_servidor": resultado["hostname_remoto"],
        "ip_servidor": resultado["ip_remoto"],
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
        f"Fecha/hora: {fecha_iso}",
        f"Host: {resultado["hostname_remoto"]} ({resultado["ip_remoto"]})",
        f"Modo: {'Automático' if modo_auto else 'Manual'}",
        f"Estado global: {resultado['estado_global']}",
        "-" * 70,
    ]
    for check, info in resultado["checks"].items():
        lines.append(f"🔹 {check}: {info['estado']} — {info['detalles']}")
    lines.extend(["-" * 70, f"ESTADO GLOBAL: {resultado['estado_global']}", "=" * 70])

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    # Por qué: se informa al operador de la ubicación de los ficheros generados.
    print(f"\n✅ Informe guardado en: {txt_path}")
    print(f"📊 JSON en: {json_path}\n")

# ==============================================================================
# MENÚ INTERACTIVO (SOLO SE MODIFICÓ LA OPCIÓN 3 y 5)
# ==============================================================================

def menu_interactivo():
    # Propósito: interfaz CLI básica para operaciones manuales y diagnósticos.
    # Por qué: permite al operador ejecutar acciones y checks sin cron ni automatización.
    print("\n" + "="*60)
    print("🔧 MONITOR DE SERVICIOS CRÍTICOS")
    print("="*60)

    while True:
        print("\nOpciones:")
        print("1. Comprobar conexión SSH")
        print("2. Monitorización selectiva")
        print("3. Iniciar Nginx y verificar estado")
        print("4. Detener Nginx y verificar estado")
        print("5. Reiniciar servicio web")
        print("6. Monitorizar servicios críticos")
        print("7. Ver uso de recursos")
        print("8. Listar servicios críticos instalados")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            for servidor in SERVIDORES:
                ssh = conectar_ssh(servidor)
                if ssh:
                    print(f"✅ Conexión SSH a {servidor['nombre']} exitosa.")
                    ssh.close()
                else:
                    print(f"❌ Conexión SSH a {servidor['nombre']} fallida.")
        elif opcion == "2":
            print("\nSelecciona servidor:")
            for i, srv in enumerate(SERVIDORES, 1):
                print(f"{i}. {srv['nombre']}")
            sel_srv = int(input("Número (0 para todos): ")) 
            if sel_srv == 0:
                for servidor in SERVIDORES:
                    print("\nSelecciona checks para " + servidor['nombre'] + " (separados por coma, o 'todos'): servicios, puerto, http, recursos")
                    checks_input = input("Checks: ").strip()
                    checks_selectivos = None if checks_input.lower() == "todos" else [c.strip() for c in checks_input.split(",")]
                    monitorizar_servidor(servidor, modo_auto=False, checks_selectivos=checks_selectivos)
            else:
                servidor = SERVIDORES[sel_srv - 1]
                print("\nSelecciona checks (separados por coma, o 'todos'): servicios, puerto, http, recursos")
                checks_input = input("Checks: ").strip()
                checks_selectivos = None if checks_input.lower() == "todos" else [c.strip() for c in checks_input.split(",")]
                monitorizar_servidor(servidor, modo_auto=False, checks_selectivos=checks_selectivos)
        elif opcion == "4":
            print("\nSelecciona servidor:")
            for i, srv in enumerate(SERVIDORES, 1):
                print(f"{i}. {srv['nombre']}")
            sel_srv = int(input("Número (0 para todos): ")) 
            if sel_srv == 0:
                for servidor in SERVIDORES:
                    ssh = conectar_ssh(servidor)
                    if not ssh:
                        continue
                    exito, msg = ejecutar_comando_sudo_remoto(ssh, "systemctl stop nginx.service", "nginx.service")
                    registrar_accion_manual(f"DETENER nginx.service en {servidor['nombre']}", msg)
                    print(msg)
                    _, estado, detalles = check_estado_servicio_remoto(ssh, "nginx.service")
                    print(f"Estado de nginx.service en {servidor['nombre']}: {detalles}")
                    ssh.close()
            else:
                servidor = SERVIDORES[sel_srv - 1]
                ssh = conectar_ssh(servidor)
                if not ssh:
                    continue
                exito, msg = ejecutar_comando_sudo_remoto(ssh, "systemctl stop nginx.service", "nginx.service")
                registrar_accion_manual(f"DETENER nginx.service en {servidor['nombre']}", msg)
                print(msg)
                _, estado, detalles = check_estado_servicio_remoto(ssh, "nginx.service")
                print(f"Estado de nginx.service en {servidor['nombre']}: {detalles}")
                ssh.close()
        elif opcion in ["3", "5", "6", "7", "8"]:
            print("\nSelecciona servidor:")
            for i, srv in enumerate(SERVIDORES, 1):
                print(f"{i}. {srv['nombre']}")
            sel_srv = int(input("Número (0 para todos): ")) 
            if sel_srv == 0:
                for servidor in SERVIDORES:
                    ssh = conectar_ssh(servidor)
                    if not ssh:
                        continue
                    if opcion in ["3", "5"]:
                        if opcion == "3":
                            servicio_web = "nginx.service"                     # ← FORZADO nginx
                        else:
                            web_instalados = detectar_servicios_instalados_remoto(ssh, SERVICIOS_WEB)
                            servicio_web = next(iter(web_instalados), None)
                        if servicio_web:
                            if opcion == "3":
                                exito, msg = ejecutar_comando_sudo_remoto(ssh, f"systemctl start {servicio_web}", servicio_web)
                                registrar_accion_manual(f"ARRANCAR {servicio_web} en {servidor['nombre']}", msg)
                            elif opcion == "5":
                                exito, msg = ejecutar_comando_sudo_remoto(ssh, f"systemctl restart {servicio_web}", servicio_web)
                                registrar_accion_manual(f"REINICIAR {servicio_web} en {servidor['nombre']}", msg)
                            print(msg)
                            # ← NUEVA VERIFICACIÓN DE ESTADO
                            _, estado, detalles = check_estado_servicio_remoto(ssh, servicio_web)
                            print(f"Estado de {servicio_web} en {servidor['nombre']}: {detalles}")
                    elif opcion == "6":
                        monitorizar_servidor(servidor, modo_auto=False)
                    elif opcion == "7":
                        estado, detalles = check_recursos_sistema_remoto(ssh)
                        print(f"\n📊 Recursos en {servidor['nombre']}: {detalles} → Estado: {estado}\n")
                    elif opcion == "8":
                        todos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
                        instalados = detectar_servicios_instalados_remoto(ssh, todos)
                        print(f"\n✅ Servicios críticos instalados en {servidor['nombre']}:")
                        for s in instalados or ["Ninguno detectado"]:
                            print(f"  - {s}")
                        print()
                    ssh.close()
            else:
                servidor = SERVIDORES[sel_srv - 1]
                ssh = conectar_ssh(servidor)
                if not ssh:
                    continue
                if opcion in ["3", "5"]:
                    if opcion == "3":
                        servicio_web = "nginx.service"                     # ← FORZADO nginx
                    else:
                        web_instalados = detectar_servicios_instalados_remoto(ssh, SERVICIOS_WEB)
                        servicio_web = next(iter(web_instalados), None)
                    if not servicio_web:
                        print("⚠️ No se detectó ningún servicio web (apache2/nginx) instalado.")
                        ssh.close()
                        continue
                    if opcion == "3":
                        exito, msg = ejecutar_comando_sudo_remoto(ssh, f"systemctl start {servicio_web}", servicio_web)
                        registrar_accion_manual(f"ARRANCAR {servicio_web} en {servidor['nombre']}", msg)   # ← corregido
                    elif opcion == "5":
                        exito, msg = ejecutar_comando_sudo_remoto(ssh, f"systemctl restart {servicio_web}", servicio_web)
                        registrar_accion_manual(f"REINICIAR {servicio_web} en {servidor['nombre']}", msg)   # ← corregido
                    print(msg)
                    # ← NUEVA VERIFICACIÓN DE ESTADO
                    _, estado, detalles = check_estado_servicio_remoto(ssh, servicio_web)
                    print(f"Estado de {servicio_web} en {servidor['nombre']}: {detalles}")
                elif opcion == "6":
                    monitorizar_servidor(servidor, modo_auto=False)
                elif opcion == "7":
                    estado, detalles = check_recursos_sistema_remoto(ssh)
                    print(f"\n📊 Recursos: {detalles} → Estado: {estado}\n")
                elif opcion == "8":
                    todos = SERVICIOS_WEB + SERVICIOS_BASE_DATOS + SERVICIOS_CACHE + SERVICIOS_SISTEMA
                    instalados = detectar_servicios_instalados_remoto(ssh, todos)
                    print("\n✅ Servicios críticos instalados:")
                    for s in instalados or ["Ninguno detectado"]:
                        print(f"  - {s}")
                    print()
                ssh.close()
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("⚠️ Opción no válida.")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Propósito: punto de entrada; soporta modo automático para cron o modo interactivo.
    parser = argparse.ArgumentParser(description="Monitor avanzado de servicios críticos")
    parser.add_argument('--auto', action='store_true', help="Modo automático para cron")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático ejecutándose...")
        for servidor in SERVIDORES:
            monitorizar_servidor(servidor, modo_auto=True)
    else:
        menu_interactivo()

if __name__ == "__main__":
    try:
        import psutil, requests, paramiko  # noqa: F401
    except ImportError as e:
        print(f"❌ Falta dependencia: {e.name if hasattr(e, 'name') else e}")
        print("Instala con: sudo apt install python3-psutil python3-requests python3-paramiko")
        print("O con pip: pip3 install --user psutil requests paramiko")
        sys.exit(1)
    main()