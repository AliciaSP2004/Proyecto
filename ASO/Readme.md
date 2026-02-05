# Documentación del Script `ScriptLogs.py`

## Descripción General
Script avanzado de monitorización de servicios críticos en sistemas Linux con **systemd**.  
Forma parte del **Proyecto Intermodular ASO** (Administración de Sistemas Operativos).

- **Modos de ejecución**: Manual (menú interactivo) y Automático (para cron con `--auto`)
- **Funcionalidades**: Monitoriza servicios web, bases de datos, caché, servicios del sistema, puerto 80, respuesta HTTP y recursos del sistema (CPU, RAM, Disco).
- **Salidas**: Genera informes en formato **JSON** y **.log**  organizados por fecha.
- **Estado global**: OK | WARN | CRIT según umbrales definidos.

### 📦 Dependencias

El script requiere **Python 3** y las siguientes librerías:

- `psutil` — Monitorización de recursos de hardware  
- `requests` — Comprobaciones de respuesta HTTP
### 🖥 Gestión Manual
Incluye un menú interactivo para:

- Arrancar servicios web
- Parar servicios web
- Reiniciar servicios web
### 📊 Estado de Recursos
Supervisa el consumo del sistema comparándolo con umbrales configurables:

- CPU
- Memoria RAM
- Disco
### 📝 Generación de Informes
- Archivos **`.json`** → Pensados para procesamiento automático
- Archivos **`.log`** → Formato legible para administradores
## Configuración Principal
La siguiente sección define las rutas y parámetros globales utilizados por el script.
```python
BASE_DIR = "/var/log/Proyecto/monitorizacion" 
```
Define el directorio base donde se almacenarán todos los archivos de salida.

Dentro de este directorio se crearán automáticamente:

Subdirectorios diarios (YYYY-MM-DD)

Archivos .log y .json

El archivo persistente acciones_manuales.log
## 📂 Salida de Datos

Los resultados se organizan por **carpetas diarias** dentro del directorio de logs:

- **Archivo `.log`**  
  Resumen legible con iconos de estado (🔹).

- **Archivo `.json`**  
  Estructura de datos completa que incluye:
  - Hostname
  - Dirección IP
  - Estado de cada chequeo
  - Estado global del sistema

- **acciones_manuales.log**  
  Historial de todas las acciones de gestión (`start` / `stop`) realizadas desde el menú interactivo.

---



# Configuración para Automatizar la Ejecución de un Script Python con Cron en Linux

La configuración realizada para automatizar la ejecución de un script Python (ScriptLogs.py) utilizando cron en un sistema Linux. Se basa en los principios estándar de cron y crontab, adaptados al proyecto de monitorización de servicios. El objetivo es ejecutar el script cada 5 minutos en modo automático, guardando logs en una ruta específica.

## Pasos para Configurar

1. Edita el crontab: `crontab -e`.
2. Añade la línea anterior.
3. Guarda y verifica: `crontab -l`.
4. Revisa logs del sistema: `grep CRON /var/log/syslog` para confirmar ejecuciones.

## Configuración Realizada en el Proyecto

Para automatizar el script ScriptLogs.py (que monitoriza servicios web y críticos, guardando informes en `/var/log/Proyecto/monitorizacion/`), se añadió la siguiente línea al crontab del usuario ubuntu:
```
*/5 * * * * /usr/bin/python3 /home/ubuntu/Proyecto/ScriptLogs.py --auto >> /var/log/Proyecto/monitorizacion/cron.log 2>&1
```
### Desglose

- `*/5 * * * *`: Ejecuta cada 5 minutos.
- `/usr/bin/python3 ... --auto`: Llama a Python con el script en modo automático.
- `>> /var/log/Proyecto/monitorizacion/cron.log 2>&1`: Redirige la salida estándar y errores a un log para depuración.