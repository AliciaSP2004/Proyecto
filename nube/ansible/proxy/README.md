# Playbook Proxy/Gateway AWS

## Descripción General

Este playbook configura una máquina proxy en AWS que actúa como **puerta de enlace** para una red interna con 2 servidores Apache. Es un playbook completo que realiza todas las configuraciones necesarias de forma automatizada.

## Requisitos Previos

1. **Máquina local Ansible**:
   - Ansible instalado (v2.9 o superior)
   - Acceso SSH a las máquinas en AWS

2. **Máquinas en AWS**:
   - Ubuntu 20.04 o superior
   - Acceso SSH habilitado
   - Clave privada en: `/home/ubuntu/Proyecto/nube/proxy/.ssh/`

3. **Archivos de configuración**:
   - Caddy: `/home/usuario/Proyecto/SRI/proxy/caddy/`
   - Apache: `/home/usuario/Proyecto/SRI/proxy/apache/`
   - Nginx: `/home/usuario/Proyecto/SRI/proxy/nginx/`

## Estructura del Playbook

El playbook se ejecuta en **9 pasos principales**:

### Paso 1: Actualización del Sistema
- Actualiza lista de paquetes
- Instala actualizaciones de seguridad
- Instala paquetes esenciales (curl, wget, git, vim, net-tools, htop)

### Paso 2: Configuración de Puerta de Enlace
- Habilita IP forwarding en kernel
- Configura NAT con iptables
- Instala iptables-persistent para persistencia de reglas

### Paso 3: Instalación de Servicios
- Instala Apache2
- Instala Nginx
- Instala Caddy

### Paso 4: Copia de Configuraciones
- Copia configuración de Caddy a `/etc/caddy/`
- Copia configuración de Apache a `/etc/apache2/`
- Copia configuración de Nginx a `/etc/nginx/`

### Paso 5: Clonación del Repositorio
- Clona repositorio GitHub: `https://AsierRodriguezO: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@github.com/AliciaSP2004/Proyecto.git`
- Se descarga en `/home/ubuntu/Proyecto`

### Paso 6: Copia de Claves del Laboratorio
- Copia claves SSH desde `/home/ubuntu/Proyecto/nube/proxy/.ssh/`
- Establece permisos correctos (600 para archivos, 700 para directorio)

### Paso 7: Activación de Solo Caddy
- **Detiene** Apache2
- **Detiene** Nginx
- **Reinicia** Caddy
- Desactiva Apache y Nginx del inicio automático

### Paso 8: Instalación de Ansible
- Instala Ansible en la máquina remota
- Verifica la versión instalada

### Paso 9: Ejecución de Playbooks Internos
- Ejecuta playbook de Apache para máquinas internas
- Ejecuta playbook de Monitoreo BD

## Cómo Ejecutar

### Opción 1: Ejecutar Todo el Playbook
```bash
cd /home/usuario/Proyecto/nube/ansible/proxy
ansible-playbook proxy.yml
```

### Opción 2: Ejecutar solo para Host Específico
```bash
ansible-playbook proxy.yml -i host.ini --limit "100.31.158.188"
```

### Opción 3: Ejecutar con Verbose (para debugging)
```bash
ansible-playbook proxy.yml -vvv
```

### Opción 4: Ejecutar pasos específicos (tags)
```bash
# Solo actualizar sistema
ansible-playbook proxy.yml --tags "PASO 1"

# Solo configurar gateway
ansible-playbook proxy.yml --tags "PASO 2"

# Solo instalar servicios
ansible-playbook proxy.yml --tags "PASO 3"
```

## Variables Utilizadas

| Variable | Valor |
|----------|-------|
| `directorio_repositorio_local` | `/home/usuario/Proyecto/SRI/proxy` |
| `directorio_configuracion_caddy` | `/home/usuario/Proyecto/SRI/proxy/caddy` |
| `directorio_configuracion_apache` | `/home/usuario/Proyecto/SRI/proxy/apache` |
| `directorio_configuracion_nginx` | `/home/usuario/Proyecto/SRI/proxy/nginx` |
| `directorio_claves` | `/home/ubuntu/Proyecto/nube/proxy/.ssh` |
| `ruta_destino_caddy` | `/etc/caddy` |
| `ruta_destino_apache` | `/etc/apache2` |
| `ruta_destino_nginx` | `/etc/nginx` |
| `ruta_destino_proyecto` | `/home/ubuntu/Proyecto` |
| `url_repositorio` | `https://AsierRodriguezO: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@github.com/AliciaSP2004/Proyecto.git` |

## Verificación Post-Ejecución

Después de ejecutar el playbook, verifica:

### 1. Estado de Caddy
```bash
ssh ubuntu@100.31.158.188 "systemctl status caddy"
```

### 2. IP Forwarding Habilitado
```bash
ssh ubuntu@100.31.158.188 "sysctl net.ipv4.ip_forward"
# Debería retornar: net.ipv4.ip_forward = 1
```

### 3. Servicio Apache Detenido
```bash
ssh ubuntu@100.31.158.188 "systemctl status apache2"
# Debería mostrar: inactive (disabled)
```

### 4. Servicio Nginx Detenido
```bash
ssh ubuntu@100.31.158.188 "systemctl status nginx"
# Debería mostrar: inactive (disabled)
```

### 5. Repositorio Clonado
```bash
ssh ubuntu@100.31.158.188 "ls -la /home/ubuntu/Proyecto"
```

### 6. Claves SSH Copiadas
```bash
ssh ubuntu@100.31.158.188 "ls -la /home/ubuntu/.ssh"
```

### 7. Tabla de Rutas (Gateway)
```bash
ssh ubuntu@100.31.158.188 "netstat -rn"
```

## Archivos Importantes

```
/home/usuario/Proyecto/nube/ansible/proxy/
├── proxy.yml              # Playbook principal
├── host.ini              # Inventario con IPs de máquinas
├── ansible.cfg           # Configuración de Ansible
└── .ssh/                 # Claves privadas para SSH
    └── ansible.pem       # Clave SSH a máquinas AWS
```

## Solución de Problemas

### Error: "Permission denied (publickey)"
- Verifica que la clave privada existe en `.ssh/ansible.pem`
- Comprueba permisos: `chmod 600 .ssh/ansible.pem`

### Error: "Caddy no inicia"
- Verifica logs: `journalctl -u caddy -n 50`
- Revisa archivo de configuración de Caddy

### Error: "No module named 'ansible'"
- Instala Ansible en máquina local: `pip install ansible`

### Error: "Connection refused" en ejecución de playbooks internos
- Verifica que máquinas internas están en el inventario correcto
- Asegúrate que SSH está configurado correctamente

## Mantenimiento Post-Instalación

### Reiniciar Caddy después de cambios
```bash
ssh ubuntu@100.31.158.188 "sudo systemctl restart caddy"
```

### Ver logs de Caddy
```bash
ssh ubuntu@100.31.158.188 "sudo journalctl -u caddy -f"
```

### Verificar puerto 80 y 443
```bash
ssh ubuntu@100.31.158.188 "sudo netstat -tlnp | grep LISTEN"
```

## Notas Importantes

⚠️ **IP Forwarding**: Una vez habilitado, permite que la máquina actúe como router/gateway.

⚠️ **NAT**: La configuración de iptables realiza traducción de direcciones de red (Network Address Translation).

⚠️ **Persistencia de reglas iptables**: Se guardan automáticamente con `iptables-persistent`.

⚠️ **Servicios Apache y Nginx**: Se desactivan únicamente para evitar conflictos con Caddy. Se pueden reactivar manualmente si es necesario.

## Contacto y Apoyo

Para problemas o preguntas sobre este playbook, revisa la documentación en:
- [Documentación de Ansible](https://docs.ansible.com/)
- [Documentación de Caddy](https://caddyserver.com/docs/)

---

**Última actualización**: 9 de febrero de 2026
