#!/usr/bin/env python3
import sys
import subprocess
import datetime
import os
import argparse

# Ruta del archivo de salida (se generará en el directorio actual)
OUTPUT_DIR = "."

def obtener_servicios_sistema():
    """Obtiene la lista de todos los servicios activos o inactivos gestionados por systemd."""
    try:
        result = subprocess.run(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend"],
                                capture_output=True, text=True, check=True)
        servicios = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # El nombre del servicio está en la primera columna
                nombre = line.split()[0]
                if nombre.endswith('.service'):
                    servicios.append(nombre)
        return sorted(set(servicios))
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudieron obtener los servicios: {e}")
        return []

def obtener_estado_servicio(nombre):
    """Obtiene el estado actual de un servicio (active/inactive/failed)."""
    try:
        result = subprocess.run(["systemctl", "is-active", nombre], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def obtener_log_servicio(nombre, num_lineas=5):
    """Obtiene las últimas N líneas del log del servicio."""
    try:
        result = subprocess.run(
            ["journalctl", "-u", nombre, "-n", str(num_lineas), "--no-pager"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        else:
            return ["(Sin entradas recientes en el log)"]
    except Exception as e:
        return [f"(Error al leer log: {e})"]

def guardar_resultado(datos):
    """Guarda el informe en un archivo con marca de tiempo."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"monitor_servicios_{timestamp}.log")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(datos)
    print(f"\n✅ Informe guardado en: {filename}\n")

def formatear_informe(servicios_info):
    """Devuelve un string con el informe formateado."""
    output = []
    output.append("=" * 80)
    output.append("MONITORIZACIÓN DE SERVICIOS DEL SISTEMA")
    output.append(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")

    for nombre, estado, log in servicios_info:
        output.append(f"🔹 Servicio: {nombre}")
        output.append(f"   Estado: {estado.upper()}")
        output.append("   Últimas líneas del log:")
        for linea in log:
            output.append(f"     > {linea}")
        output.append("-" * 60)
        output.append("")

    return "\n".join(output)

def gestionar_servicio(nombre, accion):
    """Arranca o detiene un servicio."""
    if accion == "start":
        cmd = ["systemctl", "start", nombre]
    elif accion == "stop":
        cmd = ["systemctl", "stop", nombre]
    else:
        return False

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Servicio '{nombre}' {accion}ado correctamente.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al {accion}ar el servicio '{nombre}': {e}")
        return False

def monitorizar_servicios(nombres_servicios=None, auto_mode=False):
    """Monitoriza uno o varios servicios y guarda el informe."""
    if nombres_servicios is None:
        todos = obtener_servicios_sistema()
        if not todos:
            print("❌ No se encontraron servicios.")
            return
        nombres_servicios = todos

    servicios_info = []
    for nombre in nombres_servicios:
        estado = obtener_estado_servicio(nombre)
        log = obtener_log_servicio(nombre)
        servicios_info.append((nombre, estado, log))

    informe = formatear_informe(servicios_info)
    print(informe)
    guardar_resultado(informe)

def menu_interactivo():
    print("\n" + "="*50)
    print("🔧 MONITOR DE SERVICIOS - MODO MANUAL")
    print("="*50)
    while True:
        print("\nOpciones:")
        print("1. Arrancar un servicio")
        print("∫2. Parar un servicio")
        print("3. Monitorizar solo un servicio")
        print("4. Monitorizar todos los servicios")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            nombre = input("Nombre del servicio a arrancar: ").strip()
            if nombre:
                gestionar_servicio(nombre, "start")
        elif opcion == "2":
            nombre = input("Nombre del servicio a detener: ").strip()
            if nombre:
                gestionar_servicio(nombre, "stop")
        elif opcion == "3":
            nombre = input("Nombre del servicio a monitorizar: ").strip()
            if nombre:
                monitorizar_servicios([nombre])
        elif opcion == "4":
            monitorizar_servicios()
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("⚠️ Opción no válida.")

def main():
    parser = argparse.ArgumentParser(description="Monitor de servicios del sistema")
    parser.add_argument('--auto', action='store_true', help="Ejecutar en modo automático (monitoriza todos los servicios)")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático activado. Monitorizando todos los servicios...")
        monitorizar_servicios()
    else:
        menu_interactivo()

if __name__ == "__main__":
    main()