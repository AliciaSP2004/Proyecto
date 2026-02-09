#!/bin/bash
set -e

echo "Añadiendo repositorio oficial de HashiCorp y clave GPG..."
sudo apt-get update
sudo apt-get install -y gnupg software-properties-common curl
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

echo "Actualizando índices e instalando Terraform..."
sudo apt-get update
sudo apt-get install -y terraform

echo "Instalación completada. Versión de Terraform:"
terraform --version
