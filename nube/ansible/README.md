# Playbook Ansible: Deploy Docker y MariaDB

Este playbook automatiza la instalación de Docker, Docker Compose y despliegue de MariaDB en una instancia Ubuntu en AWS.

## Requisitos

- Ansible instalado en tu máquina local
- Acceso SSH a la instancia Ubuntu en AWS
- Archivo de clave privada SSH (.pem)

## Instalación de Ansible (si no lo tienes)

```bash
# En macOS
brew install ansible

# En Ubuntu/Debian
sudo apt-get install ansible

# En otros sistemas
pip install ansible
```

## Configuración

### 1. Configura el inventario

Edita `inventory.ini` con los datos de tu instancia:

```ini
[aws_ubuntu]
my-server ansible_host=TU_IP_O_DOMINIO ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/tu-clave.pem
```

### 2. Configura el playbook

En `deploy-docker-mariadb.yml`, actualiza las variables:

```yaml
vars:
  github_repo: "https://github.com/tu-usuario/tu-repositorio.git"
  repo_directory: "/opt/docker-compose"
  compose_directory: "{{ repo_directory }}/ruta-a-tu-docker-compose"
```

- `github_repo`: URL de tu repositorio con el docker-compose.yml
- `repo_directory`: Directorio donde se clonará el repo
- `compose_directory`: Ruta exacta donde está tu docker-compose.yml dentro del repo

### 3. Permisos SSH

Asegúrate de que tu clave SSH tiene permisos correctos:

```bash
chmod 600 ~/.ssh/tu-clave.pem
```

## Ejecución

### Ejecutar el playbook completo

```bash
ansible-playbook -i inventory.ini deploy-docker-mariadb.yml
```

### Ejecución con modo verbose (para ver más detalles)

```bash
ansible-playbook -i inventory.ini deploy-docker-mariadb.yml -v
```

### Ejecución con prompt de contraseña sudo (si es necesario)

```bash
ansible-playbook -i inventory.ini deploy-docker-mariadb.yml -K
```

## ¿Qué hace el playbook?

1. **Actualiza el sistema** - `apt update` y `apt upgrade -dist`
2. **Instala Docker** - Agrega repositorio oficial y instala Docker Engine
3. **Instala Docker Compose** - Descarga la última versión
4. **Clona tu repositorio** - Descarga tu código desde GitHub
5. **Ejecuta docker-compose up -d** - Inicia los contenedores en segundo plano

## Troubleshooting

### "Permission denied (publickey)"
- Verifica que tu clave SSH sea correcta
- Asegúrate de que el usuario 'ubuntu' existe en tu instancia
- Verifica que el Security Group permite SSH (puerto 22)

### "Docker command not found"
- El playbook ha fallado en instalar Docker
- Ejecuta con `-v` para ver detalles del error

### "Repository not found"
- Verifica que la URL de GitHub es correcta
- Asegúrate de que el acceso público está habilitado (o configura credenciales de GitHub)

## Variables personalizables

Puedes sobrescribir variables desde la línea de comandos:

```bash
ansible-playbook -i inventory.ini deploy-docker-mariadb.yml \
  -e "github_repo=https://github.com/otro-usuario/otro-repo.git" \
  -e "compose_directory=/opt/docker-compose/subfolder"
```

## Próximos pasos

Después de ejecutar el playbook:

1. Verifica que los contenedores estén corriendo:
   ```bash
   ssh ubuntu@TU_IP "docker ps"
   ```

2. Revisa los logs del contenedor:
   ```bash
   ssh ubuntu@TU_IP "docker logs nombre-contenedor"
   ```

3. Accede a MariaDB si es necesario:
   ```bash
   ssh ubuntu@TU_IP "docker exec -it nombre-contenedor mysql -u root -p"
   ```
