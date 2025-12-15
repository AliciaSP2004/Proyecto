#!/usr/bin/env python3
"""
Script para monitorear servicios del sistema en Linux (con systemd).
Ofrece dos modos:
  - Modo manual: menú interactivo para gestionar y monitorizar servicios.
  - Modo automático: ideal para ejecutar con cron; monitoriza todos los servicios.

Además:
  - Genera un informe resumido legible por humanos.
  - Guarda logs detallados de cada servicio en una subcarpeta 'logs'.
  - Organiza todo en una estructura de carpetas por fecha.
"""

import sys
import subprocess          # Para ejecutar comandos del sistema (systemctl, journalctl)
import datetime            # Para obtener fecha y hora actual
import os                  # Para gestionar rutas y crear directorios
import argparse            # Para manejar argumentos de línea de comandos (--auto)

# ==============================================================================
# CONFIGURACIÓN GLOBAL
# ==============================================================================

# Carpeta base donde se guardarán todos los informes y logs
BASE_DIR = "monitorizacion"

# Número de líneas del log que se guardarán en los archivos detallados (logs/)
LOG_LINES = 100  # Puedes ajustar este valor si necesitas más o menos contexto

# ==============================================================================
# FUNCIONES DE GESTIÓN DE RUTAS Y CARPETAS
# ==============================================================================

def crear_ruta_salida(fecha_hoy):
    """
    Crea la carpeta del día (si no existe) y devuelve su ruta.
    Ejemplo: monitorizacion/2025-04-05/
    """
    ruta_dia = os.path.join(BASE_DIR, fecha_hoy)
    os.makedirs(ruta_dia, exist_ok=True)  # exist_ok=True evita error si ya existe
    return ruta_dia

def crear_ruta_logs(fecha_hoy):
    """
    Crea la subcarpeta 'logs' dentro de la carpeta del día.
    Ejemplo: monitorizacion/2025-04-05/logs/
    """
    ruta_logs = os.path.join(BASE_DIR, fecha_hoy, "logs")
    os.makedirs(ruta_logs, exist_ok=True)
    return ruta_logs

# ==============================================================================
# FUNCIONES DE OBTENCIÓN DE DATOS DEL SISTEMA
# ==============================================================================

def obtener_servicios_sistema():
    """
    Obtiene la lista completa de servicios gestionados por systemd.
    Filtra solo las líneas que terminan en '.service' para evitar basura.
    Retorna una lista ordenada y sin duplicados.
    """
    try:
        # Ejecuta: systemctl list-units --type=service --all --no-pager --no-legend
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend"],
            capture_output=True, text=True, check=True
        )
        servicios = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # El primer campo es el nombre del servicio
                nombre = line.split()[0]
                if nombre.endswith('.service'):
                    servicios.append(nombre)
        return sorted(set(servicios))  # Elimina duplicados y ordena
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudieron obtener los servicios: {e}")
        return []

def obtener_estado_servicio(nombre):
    """
    Devuelve el estado actual de un servicio: active, inactive, failed, etc.
    Usa: systemctl is-active <servicio>
    """
    try:
        result = subprocess.run(["systemctl", "is-active", nombre], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def obtener_log_completo_servicio(nombre, num_lineas=LOG_LINES):
    """
    Obtiene las últimas 'num_lineas' del log del servicio usando journalctl.
    Retorna el contenido como una cadena de texto.
    """
    try:
        result = subprocess.run(
            ["journalctl", "-u", nombre, "-n", str(num_lineas), "--no-pager"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return result.stdout.strip()
        else:
            return "(Sin entradas recientes en el log)"
    except Exception as e:
        return f"(Error al leer log: {e})"

def obtener_log_resumen(nombre, num_lineas=5):
    """
    Obtiene solo las últimas 5 líneas del log para incluirlas en el informe resumido.
    """
    log_texto = obtener_log_completo_servicio(nombre, num_lineas)
    return log_texto.split('\n')

# ==============================================================================
# FUNCIONES DE GUARDADO DE ARCHIVOS
# ==============================================================================

def guardar_logs_individuales(nombres_servicios, fecha_hoy):
    """
    Guarda un archivo de log por cada servicio en la carpeta 'logs' del día.
    El nombre del archivo es: servicio_nombre.log
    """
    ruta_logs = crear_ruta_logs(fecha_hoy)
    for nombre in nombres_servicios:
        contenido = obtener_log_completo_servicio(nombre)
        nombre_limpio = nombre.replace(".service", "")  # Elimina .service del nombre
        archivo_log = os.path.join(ruta_logs, f"servicio_{nombre_limpio}.log")
        with open(archivo_log, 'w', encoding='utf-8') as f:
            f.write(contenido)
    print(f"📁 Logs individuales guardados en: {ruta_logs}")

def formatear_informe(servicios_info):
    """
    Genera un informe legible en texto plano con el estado y un resumen del log
    de cada servicio monitorizado.
    """
    output = []
    output.append("=" * 80)
    output.append("MONITORIZACIÓN DE SERVICIOS DEL SISTEMA")
    output.append(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")

    for nombre, estado, log_resumen in servicios_info:
        output.append(f"🔹 Servicio: {nombre}")
        output.append(f"   Estado: {estado.upper()}")
        output.append("   Últimas líneas del log:")
        for linea in log_resumen:
            output.append(f"     > {linea}")
        output.append("-" * 60)
        output.append("")

    return "\n".join(output)

def guardar_resultado(servicios_info, nombres_monitoreados):
    """
    Guarda el informe resumido en la carpeta del día, con nombre dinámico:
      - Si es un solo servicio: monitor_servicio_NOMBRE_YYYYMMDD_HHMMSS.log
      - Si son todos:         monitor_servicios_YYYYMMDD_HHMMSS.log
    También llama a guardar los logs detallados.
    """
    ahora = datetime.datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")

    # Decidir nombre del archivo según si es uno o varios servicios
    if len(nombres_monitoreados) == 1:
        nombre_servicio = nombres_monitoreados[0].replace(".service", "")
        nombre_archivo = f"monitor_servicio_{nombre_servicio}_{ahora.strftime('%Y%m%d_%H%M%S')}.log"
    else:
        nombre_archivo = f"monitor_servicios_{ahora.strftime('%Y%m%d_%H%M%S')}.log"

    # Ruta completa del informe
    ruta_dia = crear_ruta_salida(fecha_hoy)
    ruta_informe = os.path.join(ruta_dia, nombre_archivo)

    # Escribir informe
    informe = formatear_informe(servicios_info)
    with open(ruta_informe, 'w', encoding='utf-8') as f:
        f.write(informe)

    print(f"\n✅ Informe guardado en: {ruta_informe}")

    # Guardar logs detallados en subcarpeta 'logs'
    guardar_logs_individuales(nombres_monitoreados, fecha_hoy)

# ==============================================================================
# FUNCIONES DE GESTIÓN DE SERVICIOS (start/stop)
# ==============================================================================

def gestionar_servicio(nombre, accion):
    """
    Ejecuta systemctl start o systemctl stop según la acción solicitada.
    Muestra mensaje de éxito o error.
    """
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

# ==============================================================================
# FUNCIONES PRINCIPALES DE MONITORIZACIÓN Y MENÚ
# ==============================================================================

def monitorizar_servicios(nombres_servicios=None):
    """
    Monitoriza uno o varios servicios:
      - Obtiene estado y resumen del log.
      - Guarda informe y logs detallados.
    Si no se pasa lista, monitoriza todos los servicios del sistema.
    """
    if nombres_servicios is None:
        todos = obtener_servicios_sistema()
        if not todos:
            print("❌ No se encontraron servicios.")
            return
        nombres_servicios = todos

    # Recopilar información de cada servicio
    servicios_info = []
    for nombre in nombres_servicios:
        estado = obtener_estado_servicio(nombre)
        log_resumen = obtener_log_resumen(nombre)
        servicios_info.append((nombre, estado, log_resumen))

    # Guardar resultados
    guardar_resultado(servicios_info, nombres_monitoreados=nombres_servicios)

def menu_interactivo():
    """
    Muestra un menú en consola para que el usuario elija acciones manualmente.
    Asegura que los nombres de servicio terminen en '.service'.
    """
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

# ==============================================================================
# PUNTO DE ENTRADA DEL SCRIPT
# ==============================================================================

def main():
    """
    Detecta si se ejecuta en modo automático (--auto) o manual (menú).
    """
    parser = argparse.ArgumentParser(description="Monitor de servicios del sistema")
    parser.add_argument('--auto', action='store_true', help="Ejecutar en modo automático (monitoriza todos los servicios)")
    args = parser.parse_args()

    if args.auto:
        print("▶ Modo automático activado. Monitorizando todos los servicios...")
        monitorizar_servicios()
    else:
        menu_interactivo()

# ==============================================================================
# EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    main()