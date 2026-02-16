# Arquitectura del Proyecto - Proxy/Gateway + Servidores Internos

## 📊 Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────────────┐
│                        INTERNET                            │
└────────────────────────────────────────────────────────────┘
                             │
                             │ Puerto 80/443
                             │
        ┌────────────────────▼───────────────────┐
        │  MÁQUINA PROXY/GATEWAY (100.31.158.188)│
        │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
        │  • Ubuntu                              │
        │  • Caddy (Reverse Proxy)               │
        │  • IP Forwarding habilitado            │
        │  • NAT configurado                     │
        │  • Ansible                             │
        └────────────────┬───────────────────────┘
                         │ Red Interna (10.x.x.x)
        ┌────────────────┴────────────────┐
        │                                 │
    ┌───▼────────────────┐    ┌──────────▼──────────┐
    │  SERVIDOR APACHE 1 │    │  SERVIDOR APACHE 2  │
    │ (98.93.36.19)      │    │  (IP Interna)       │
    │ ━━━━━━━━━━━━━━━━━━│    │ ━━━━━━━━━━━━━━━━━━  │
    │ • Ubuntu           │    │ • Ubuntu            │
    │ • Apache2          │    │ • Apache2           │
    │ • Monitores BD     │    │ • Monitores BD      │
    └────────────────────┘    └─────────────────────┘
```

## 🔄 Flujo de Configuración

### Fase 1: Preparación (Máquina Local)
```
┌─────────────────────────────────────────────────────────┐
│ 1. Verificar que tienes:                                │
│    - Clave SSH en: /home/ubuntu/Proyecto/nube/proxy/.ssh│
│    - Archivos de config en: /home/usuario/Proyecto/SRI  │
│    - Inventario actualizado en: host.ini                │
│                                                         │
│ 2. Ejecutar comando:                                    │
│    ansible-playbook proxy.yml                           │
└─────────────────────────────────────────────────────────┘
```

### Fase 2: Ejecución del Playbook (Máquina Proxy)
```
┌─────────────────────────────────────────────────────────┐
│ PASO 1: Actualizar Sistema                              │
│ └→ apt update && apt upgrade                            │
│                                                         │
│ PASO 2: Configurar Gateway                              │
│ └→ IP Forwarding activado                              │
│ └→ NAT configurado con iptables                         │
│                                                         │
│ PASO 3: Instalar Servicios                              │
│ └→ Apache2 instalado                                    │
│ └→ Nginx instalado                                      │
│ └→ Caddy instalado                                      │
│                                                         │
│ PASO 4: Copiar Configuraciones                          │
│ └→ /etc/caddy/    ← caddy/                              │
│ └→ /etc/apache2/  ← apache/                             │
│ └→ /etc/nginx/    ← nginx/                              │
│                                                         │
│ PASO 5: Clonar Repositorio                              │
│ └→ /home/ubuntu/Proyecto <- GitHub                      │
│                                                         │
│ PASO 6: Copiar Claves SSH                               │
│ └→ /home/ubuntu/.ssh/ ← claves del laboratorio          │
│                                                         │
│ PASO 7: Activar Solo Caddy                              │
│ └→ Apache2 (detenido)                                   │
│ └→ Nginx (detenido)                                     │
│ └→ Caddy (activo)                                       │
│                                                         │
│ PASO 8: Instalar Ansible                                │
│ └→ ansible instalado en máquina remota                  │
│                                                         │
│ PASO 9: Ejecutar Playbooks Internos                     │
│ └→ setup_web.yml (Apache)                               │
│ └→ mariadb.yml (Monitoreo BD)                           │
└─────────────────────────────────────────────────────────┘
```

### Fase 3: Resultado Final

```
┌─────────────────────────────────────────────────────────┐
│ MÁQUINA PROXY CONFIGURADA:                              │
│ ✓ Sistema actualizado                                   │
│ ✓ Gateway con forwarding activo                         │
│ ✓ Caddy corriendo como reverse proxy                    │
│ ✓ Repositorio clonado                                   │
│ ✓ Claves SSH disponibles                                │
│ ✓ Ansible instalado para ejecutar playbooks internos    │
│                                                         │
│ MÁQUINAS INTERNAS CONFIGURADAS:                         │
│ ✓ Apache instalado y configurado                        │
│ ✓ Monitoreo de BD activo                                │
│ ✓ Comunicación con máquina proxy establecida            │
└─────────────────────────────────────────────────────────┘
```

## 🔐 Flujo de Comunicación

### Conexión Entrante (Internet → Proxy → Internos)

```
1. Usuario accede a ejemplo.com (80/443)
   ↓
2. Caddy en Proxy recibe la solicitud
   ↓
3. Caddy revisa su configuración
   ↓
4. Caddy hace forwarding a servidor Apache interno
   ↓
5. Apache responde
   ↓
6. Caddy retorna respuesta a usuario
```

## 📁 Estructura de Directorios

```
/home/usuario/Proyecto/nube/ansible/proxy/
│
├── proxy.yml                    ← Playbook principal (9 PASOS)
├── host.ini                     ← Inventario con IPs
├── ansible.cfg                  ← Configuración de Ansible
├── validar.sh                   ← Script de validación post-ejecución
├── README.md                    ← Documentación de uso
└── .ssh/
    └── ansible.pem              ← Clave SSH privada para AWS

Archivos de Configuración (origen):
/home/usuario/Proyecto/SRI/proxy/
├── caddy/
│   ├── http
│   └── https
├── apache/
│   └── Configuracion.conf
└── nginx/
    └── default

Playbooks Internos:
/home/usuario/Proyecto/nube/ansible/
├── Apaches/
│   └── setup_web.yml            ← Playbook para Apache
└── MonitoreoBd/
    └── mariadb.yml              ← Playbook para Monitoreo BD
```

## ⚙️ Configuración de Red

### Interfaces de Red

**Máquina Proxy:**
- eth0: IP pública (100.31.158.188)
- Actúa como gateway para máquinas internas

**Máquinas Internas:**
- eth0: IP privada (p.ej. 10.0.1.x)
- Ruta por defecto → Máquina proxy

### Reglas de Firewall Configuradas

```bash
# IP Forwarding habilitado
net.ipv4.ip_forward = 1

# Regla NAT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Persistencia de reglas
Instalado: iptables-persistent
```

## 🔧 Mantenimiento y Troubleshooting

### Verificación Después de Ejecutar

```bash
# 1. SSH a la máquina proxy
ssh ubuntu@100.31.158.188

# 2. Verificar IP Forwarding
sysctl net.ipv4.ip_forward

# 3. Ver reglas NAT
sudo iptables -t nat -L -n

# 4. Estado de Caddy
sudo systemctl status caddy

# 5. Logs de Caddy
sudo journalctl -u caddy -f

# 6. Conectividad entre máquinas
ping 98.93.36.19 (desde proxy)
```

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "Connection refused" | Caddy no está corriendo | `sudo systemctl restart caddy` |
| "No route to host" | IP Forwarding deshabilitado | `sysctl -w net.ipv4.ip_forward=1` |
| "Permission denied" | Clave SSH incorrecta | Verificar permisos: `chmod 600 .ssh/ansible.pem` |
| "timeout on operation" | Firewall bloqueando | Verificar security groups en AWS |
| "Port already in use" | Apache/Nginx en conflicto | Ya están detenidos por el playbook |

## 📊 Estado de Servicios Esperado

### Máquina Proxy

| Servicio | Estado | Observaciones |
|----------|--------|---------------|
| apache2 | ❌ Inactive | Detenido para evitar conflictos |
| nginx | ❌ Inactive | Detenido para evitar conflictos |
| caddy | ✅ Active | Corriendo como reverse proxy |
| sshd | ✅ Active | Para conexiones remotas |
| networking | ✅ Active | Para IP forwarding |

### Máquinas Internas

| Servicio | Estado | Observaciones |
|----------|--------|---------------|
| apache2 | ✅ Active | Configurado por setup_web.yml |
| mariadb (si aplica) | ✅ Active | Configurado por mariadb.yml |
| monitors | ✅ Active | Monitoreo BD activo |
| sshd | ✅ Active | Para conexiones remotas |

## 🚀 Próximos Pasos

1. **Ejecutar el playbook**:
   ```bash
   cd /home/usuario/Proyecto/nube/ansible/proxy
   ansible-playbook proxy.yml
   ```

2. **Validar la configuración**:
   ```bash
   bash validar.sh
   ```

3. **Testear conectividad**:
   ```bash
   ssh ubuntu@100.31.158.188 "curl http://localhost"
   ```

4. **Monitorear en tiempo real**:
   ```bash
   ssh ubuntu@100.31.158.188 "sudo journalctl -u caddy -f"
   ```

## 📝 Notas Importantes

⚠️ **Seguridad**:
- Las claves SSH deben ser privadas (600 permisos)
- El archivo host.ini contiene IPs sensibles
- Mantén las claves seguras en /home/ubuntu/Proyecto/nube/proxy/.ssh

⚠️ **Performance**:
- IP Forwarding puede consumir CPU en tráfico alto
- Considera usar hardware con suficientes recursos

⚠️ **Persistencia**:
- Las reglas iptables se guardan automáticamente
- Caddy se reinicia automáticano en reboot

---

**Última actualización**: 9 de febrero de 2026
