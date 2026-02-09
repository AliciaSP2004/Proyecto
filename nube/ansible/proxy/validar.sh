#!/bin/bash

# ============================================================================
# Script de Validación - Proxy/Gateway AWS
# ============================================================================
# Este script verifica que todas las configuraciones del playbook se
# completaron correctamente en las máquinas remotas.
# ============================================================================

set -e

# Colores para output
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
AZUL='\033[0;34m'
NC='\033[0m' # No Color

# Variables
USUARIO="ubuntu"
DIRECTORIO_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVO_INVENTARIO="$DIRECTORIO_SCRIPT/host.ini"

# Funciones de utilidad
imprimir_titulo() {
    echo -e "\n${AZUL}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${AZUL}║ $1${NC}"
    echo -e "${AZUL}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

imprimir_ok() {
    echo -e "${VERDE}✓ $1${NC}"
}

imprimir_error() {
    echo -e "${ROJO}✗ $1${NC}"
}

imprimir_atencion() {
    echo -e "${AMARILLO}⚠ $1${NC}"
}

verificar_conexion() {
    local host=$1
    echo -e "${AZUL}Verificando conexión a $host...${NC}"
    
    if ping -c 1 "$host" &> /dev/null; then
        imprimir_ok "Conexión a $host exitosa"
        return 0
    else
        imprimir_error "No hay conexión a $host"
        return 1
    fi
}

verificar_servicio() {
    local host=$1
    local servicio=$2
    local estado_esperado=$3
    
    local estado=$(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USUARIO@$host "systemctl is-active $servicio" 2>/dev/null || echo "unknown")
    
    if [ "$estado" = "$estado_esperado" ]; then
        imprimir_ok "$servicio en $host está $estado_esperado"
    else
        imprimir_error "$servicio en $host está $estado (se esperaba: $estado_esperado)"
    fi
}

verificar_comando() {
    local host=$1
    local comando=$2
    local descripcion=$3
    
    local resultado=$(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USUARIO@$host "$comando" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        imprimir_ok "$descripcion"
        if [ ! -z "$resultado" ]; then
            echo "  → $resultado"
        fi
    else
        imprimir_error "$descripcion"
    fi
}

verificar_archivo() {
    local host=$1
    local ruta=$2
    local descripcion=$3
    
    if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USUARIO@$host "test -f $ruta" 2>/dev/null; then
        imprimir_ok "$descripcion existe: $ruta"
    else
        imprimir_error "$descripcion NO existe: $ruta"
    fi
}

verificar_directorio() {
    local host=$1
    local ruta=$2
    local descripcion=$3
    
    if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USUARIO@$host "test -d $ruta" 2>/dev/null; then
        imprimir_ok "$descripcion existe: $ruta"
    else
        imprimir_error "$descripcion NO existe: $ruta"
    fi
}

# ============================================================================
# INICIO DEL SCRIPT
# ============================================================================

imprimir_titulo "VALIDACIÓN DE CONFIGURACIÓN - PROXY/GATEWAY AWS"

# Leer hosts del inventario
if [ ! -f "$ARCHIVO_INVENTARIO" ]; then
    imprimir_error "Archivo de inventario no encontrado: $ARCHIVO_INVENTARIO"
    exit 1
fi

# Extraer hosts (saltando líneas que empiezan con [)
HOSTS=$(grep -v "^\[" "$ARCHIVO_INVENTARIO" | grep -v "^$" | grep -v "^#")

for HOST in $HOSTS; do
    imprimir_titulo "VALIDANDO HOST: $HOST"
    
    # 1. Verificar conectividad
    echo -e "${AZUL}─ Conectividad${NC}"
    if ! verificar_conexion "$HOST"; then
        imprimir_atencion "No se puede alcanzar $HOST, saltando validaciones"
        continue
    fi
    
    # 2. Verificar actualización del sistema
    echo -e "\n${AZUL}─ Actualización del Sistema${NC}"
    verificar_comando "$HOST" "apt list --upgradable 2>/dev/null | wc -l" "Verificar paquetes actualizables"
    
    # 3. Verificar IP Forwarding
    echo -e "\n${AZUL}─ Configuración de Puerta de Enlace${NC}"
    verificar_comando "$HOST" "sysctl net.ipv4.ip_forward" "IP Forwarding"
    verificar_comando "$HOST" "sudo iptables -t nat -L POSTROUTING 2>/dev/null | head -5" "Reglas NAT de iptables"
    
    # 4. Verificar Instalación de Servicios
    echo -e "\n${AZUL}─ Servicios Instalados${NC}"
    verificar_comando "$HOST" "apache2ctl -v 2>&1 | head -1" "Versión de Apache"
    verificar_comando "$HOST" "nginx -v 2>&1" "Versión de Nginx"
    verificar_comando "$HOST" "caddy version" "Versión de Caddy"
    
    # 5. Verificar Estado de Servicios
    echo -e "\n${AZUL}─ Estado de Servicios${NC}"
    verificar_servicio "$HOST" "apache2" "inactive"
    verificar_servicio "$HOST" "nginx" "inactive"
    verificar_servicio "$HOST" "caddy" "active"
    
    # 6. Verificar Configuraciones
    echo -e "\n${AZUL}─ Archivos de Configuración${NC}"
    verificar_directorio "$HOST" "/etc/caddy" "Directorio Caddy"
    verificar_directorio "$HOST" "/etc/apache2" "Directorio Apache"
    verificar_directorio "$HOST" "/etc/nginx" "Directorio Nginx"
    
    # 7. Verificar Clonación del Repositorio
    echo -e "\n${AZUL}─ Repositorio Clonado${NC}"
    verificar_directorio "$HOST" "/home/ubuntu/Proyecto" "Directorio del Proyecto"
    verificar_directorio "$HOST" "/home/ubuntu/Proyecto/.git" "Repositorio Git"
    
    # 8. Verificar Claves SSH
    echo -e "\n${AZUL}─ Claves SSH del Laboratorio${NC}"
    verificar_directorio "$HOST" "/home/ubuntu/.ssh" "Directorio SSH"
    
    # 9. Verificar Ansible
    echo -e "\n${AZUL}─ Ansible Instalado${NC}"
    verificar_comando "$HOST" "ansible --version 2>&1 | head -1" "Versión de Ansible"
    
    # 10. Información de Red
    echo -e "\n${AZUL}─ Información de Red${NC}"
    verificar_comando "$HOST" "hostname -I" "Dirección IP"
    verificar_comando "$HOST" "netstat -rn | grep -E '(Destination|default)'" "Tabla de rutas"
    
    # 11. Verificar puertos
    echo -e "\n${AZUL}─ Puertos Escuchados${NC}"
    verificar_comando "$HOST" "sudo netstat -tlnp 2>/dev/null | grep -E '(80|443|22)'" "Puertos 22, 80, 443"
    
done

# Resumen Final
imprimir_titulo "RESUMEN DE VALIDACIÓN"
echo -e "${VERDE}Validación completada.${NC}"
echo -e "Revisa los resultados anteriores para cualquier error o advertencia.\n"

