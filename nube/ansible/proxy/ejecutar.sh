#!/bin/bash

# ============================================================================
# Script de Ejecución Rápida - Proxy/Gateway Playbook
# ============================================================================
# Proporciona formas rápidas de ejecutar el playbook con diferentes opciones

# Colores
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
AZUL='\033[0;34m'
NC='\033[0m'

# Variables
DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOK="$DIR_SCRIPT/proxy.yml"
INVENTARIO="$DIR_SCRIPT/host.ini"

mostrar_menu() {
    echo -e "\n${AZUL}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${AZUL}║     EJECUTOR DE PLAYBOOK - PROXY/GATEWAY AWS               ║${NC}"
    echo -e "${AZUL}╚════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${VERDE}opciones disponibles:${NC}\n"
    echo -e "  ${AMARILLO}1${NC}) Ejecutar playbook completo"
    echo -e "  ${AMARILLO}2${NC}) Ejecutar con verbose (debugging)"
    echo -e "  ${AMARILLO}3${NC}) Ejecutar solo para host específico"
    echo -e "  ${AMARILLO}4${NC}) Ejecutar paso específico (tag)"
    echo -e "  ${AMARILLO}5${NC}) Hacer syntax check del playbook"
    echo -e "  ${AMARILLO}6${NC}) Listar tasks del playbook"
    echo -e "  ${AMARILLO}7${NC}) Validar configuración post-ejecución"
    echo -e "  ${AMARILLO}8${NC}) Ver configuración de Ansible"
    echo -e "  ${AMARILLO}0${NC}) Salir\n"
}

ejecutar_playbook_completo() {
    echo -e "\n${VERDE}Ejecutando playbook completo...${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO"
}

ejecutar_con_verbose() {
    echo -e "\n${VERDE}Ejecutando playbook con verbose (debugging)...${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO" -vvv
}

ejecutar_host_especifico() {
    echo -e "\n${AMARILLO}Hosts disponibles:${NC}"
    grep -v "^\[" "$INVENTARIO" | grep -v "^$" | nl
    
    echo -e "\n${AMARILLO}Ingresa el número del host (o escribe la IP directamente):${NC}"
    read -p "> " host_entrada
    
    # Si es un número, obtener el host de la lista
    if [[ "$host_entrada" =~ ^[0-9]+$ ]]; then
        host=$(grep -v "^\[" "$INVENTARIO" | grep -v "^$" | sed -n "${host_entrada}p")
    else
        host=$host_entrada
    fi
    
    if [ -z "$host" ]; then
        echo -e "${ROJO}Host no válido${NC}"
        return
    fi
    
    echo -e "\n${VERDE}Ejecutando playbook para host: $host${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO" --limit "$host"
}

ejecutar_paso_especifico() {
    echo -e "\n${AMARILLO}Pasos disponibles:${NC}"
    echo -e "  1) PASO 1 - Actualización del sistema"
    echo -e "  2) PASO 2 - Configuración de gateway"
    echo -e "  3) PASO 3 - Instalación de servicios"
    echo -e "  4) PASO 4 - Copia de configuraciones"
    echo -e "  5) PASO 5 - Clonación del repositorio"
    echo -e "  6) PASO 6 - Copia de claves SSH"
    echo -e "  7) PASO 7 - Activación de Caddy"
    echo -e "  8) PASO 8 - Instalación de Ansible"
    echo -e "  9) PASO 9 - Ejecución de playbooks internos"
    
    echo -e "\n${AMARILLO}Ingresa el número del paso:${NC}"
    read -p "> " paso_num
    
    case $paso_num in
        1) paso="PASO 1" ;;
        2) paso="PASO 2" ;;
        3) paso="PASO 3" ;;
        4) paso="PASO 4" ;;
        5) paso="PASO 5" ;;
        6) paso="PASO 6" ;;
        7) paso="PASO 7" ;;
        8) paso="PASO 8" ;;
        9) paso="PASO 9" ;;
        *) echo -e "${ROJO}Opción no válida${NC}"; return ;;
    esac
    
    echo -e "\n${VERDE}Ejecutando $paso...${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO" --tags "$paso"
}

syntax_check() {
    echo -e "\n${VERDE}Verificando sintaxis del playbook...${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO" --syntax-check
}

listar_tasks() {
    echo -e "\n${VERDE}Tasks del playbook:${NC}\n"
    ansible-playbook "$PLAYBOOK" -i "$INVENTARIO" --list-tasks
}

validar_config() {
    echo -e "\n${VERDE}Validando configuración...${NC}\n"
    
    if [ -f "$DIR_SCRIPT/validar.sh" ]; then
        bash "$DIR_SCRIPT/validar.sh"
    else
        echo -e "${ROJO}Script de validación no encontrado${NC}"
    fi
}

ver_configuracion() {
    echo -e "\n${VERDE}Configuración de Ansible:${NC}\n"
    echo -e "${AZUL}Inventario:${NC} $INVENTARIO"
    echo -e "${AZUL}Playbook:${NC} $PLAYBOOK\n"
    
    echo -e "${AZUL}Contenido de host.ini:${NC}"
    cat "$INVENTARIO"
    
    echo -e "\n${AZUL}Configuración de ansible.cfg:${NC}"
    cat "$DIR_SCRIPT/ansible.cfg"
}

# ============================================================================
# MENÚ PRINCIPAL
# ============================================================================

while true; do
    mostrar_menu
    read -p "Selecciona una opción: " opcion
    
    case $opcion in
        1) ejecutar_playbook_completo ;;
        2) ejecutar_con_verbose ;;
        3) ejecutar_host_especifico ;;
        4) ejecutar_paso_especifico ;;
        5) syntax_check ;;
        6) listar_tasks ;;
        7) validar_config ;;
        8) ver_configuracion ;;
        0) 
            echo -e "\n${VERDE}¡Hasta luego!${NC}\n"
            exit 0
            ;;
        *)
            echo -e "\n${ROJO}Opción no válida. Por favor, intenta de nuevo.${NC}"
            ;;
    esac
    
    read -p "Presiona Enter para continuar..."
done
