#!/usr/bin/env python3
import sys
import subprocess
import datetime
import os
import argparse

# Carpeta base para los informes
BASE_DIR = "monitorizacion"

def crear_ruta_salida(fecha_hoy):
    """Crea la ruta: monitorizacion/YYYY-MM-DD/"""
    ruta = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta, exist_ok=True)
    return ruta

def obtener_servicios_sistema():
    """Obtiene la lista de todos los servicios gestionados por systemd."""
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend"],
            capture_output=True, text=True, check=True
        )
        servicios = []
        for line in result.stdout.strip().split('\n'):
            if line:
                nombre = line.split()[0]
                if nombre.endswith('.service'):
                    servicios.append(nombre)
        return sorted(set(servicios))
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudieron obtener los servicios: {e}")
        return []

def obtener_estado_servicio(nombre):
    try:
        result = subprocess.run(["systemctl", "is-active", nombre], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def obtener_log_servicio(nombre, num_lineas=5):
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

def formatear_informe(servicios_info):
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

def guardar_resultado(servicios_info, nombres_monitoreados):
    """Guarda el informe con nombre dinámico y en la carpeta por fecha."""
    ahora = datetime.datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H%M%S")

    # Determinar nombre del archivo
    if len(nombres_monitoreados) == 1:
        nombre_servicio = nombres_monitoreados[0].replace(".service", "")
        nombre_archivo = f"monitor_servicio_{nombre_servicio}_{ahora.strftime('%Y%m%d_%H%M%S')}.log"
    else:
        nombre_archivo = f"monitor_servicios_{ahora.strftime('%Y%m%d_%H%M%S')}.log"

    ruta_salida = crear_ruta_salida(fecha_hoy)
    ruta_completa = os.path.join(ruta_salida, nombre_archivo)

    informe = formatear_informe(servicios_info)
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write(informe)

    print(f"\n✅ Informe guardado en: {ruta_completa}\n")

def gestionar_servicio(nombre, accion):
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

def monitorizar_servicios(nombres_servicios=None):
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

    guardar_resultado(servicios_info, nombres_servicios)

def menu_interactivo():
    print("\n" + "="*50)
    print("🔧 MONITOR DE SERVICIOS - MODO MANUAL")
    print("="*50)
    while True:
        print("\nOpciones:")
        print("1. Arrancar un servicio")
        print("2. Parar un servicio")
        print("3. Monitorizar solo un servicio")
        print("4. Monitorizar todos los servicios")
        print("0. Salir")
        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            nombre = input("Nombre del servicio a arrancar: ").strip()
            if nombre and not nombre.endswith('.service'):
                nombre += '.service'
            if nombre:
                gestionar_servicio(nombre, "start")
        elif opcion == "2":
            nombre = input("Nombre del servicio a detener: ").strip()
            if nombre and not nombre.endswith('.service'):
                nombre += '.service'
            if nombre:
                gestionar_servicio(nombre, "stop")
        elif opcion == "3":
            nombre = input("Nombre del servicio a monitorizar: ").strip()
            if nombre and not nombre.endswith('.service'):
                nombre += '.service'
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