#!/bin/bash

# Script para configurar y ejecutar el playbook con Vockey

echo "=========================================="
echo "Setup Ansible para Vockey"
echo "=========================================="

# Verificar si Ansible está instalado
if ! command -v ansible &> /dev/null; then
    echo "❌ Ansible no está instalado"
    echo "Instalando Ansible..."
    sudo apt-get update
    sudo apt-get install -y ansible
fi

echo "✅ Ansible está instalado"
ansible --version

# Crear carpeta de claves SSH si no existe
if [ ! -d ~/.ssh ]; then
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
fi

# Instrucciones para la clave
echo ""
echo "=========================================="
echo "IMPORTANTE: Clave SSH de Vockey"
echo "=========================================="
echo "Debes descargar la clave .pem desde Vockey y guardarla aquí:"
echo "  ~/.ssh/vockey.pem"
echo ""
echo "Luego ejecuta:"
echo "  chmod 600 ~/.ssh/vockey.pem"
echo ""

# Verificar si la clave existe
if [ ! -f ~/.ssh/vockey.pem ]; then
    echo "⚠️  La clave vockey.pem NO se encuentra en ~/.ssh/"
    echo "Por favor descárgala desde Vockey y colócala ahí"
    exit 1
fi

echo "✅ Clave encontrada: ~/.ssh/vockey.pem"
chmod 600 ~/.ssh/vockey.pem

# Verificar conexión SSH
echo ""
echo "Probando conexión SSH a Vockey..."
if ssh -o StrictHostKeyChecking=accept-new -i ~/.ssh/vockey.pem ubuntu@34.203.210.170 "echo 'Conexión exitosa'"; then
    echo "✅ Conexión SSH funcionando"
else
    echo "❌ Error en conexión SSH"
    exit 1
fi

# Ejecutar el playbook
echo ""
echo "=========================================="
echo "Ejecutando playbook..."
echo "=========================================="
ansible-playbook -i inventory.ini deploy-docker-mariadb.yml

echo ""
echo "✅ Proceso completado"
