# Configuración de Proxy en Caddy

Este directorio contiene la configuración de proxy inverso realizada en Caddy. Se incluyen dos configuraciones: una para HTTP y otra para HTTPS.

## Archivo: http

```caddy
:80 {
    reverse_proxy 10.0.2.31
}
```

### Descripción

- **:80**: Caddy escucha en el puerto 80 (HTTP) en todas las interfaces
- **reverse_proxy 10.0.2.31**: Reenvía todas las solicitudes al servidor backend en `10.0.2.31`

Este archivo maneja las peticiones HTTP no encriptadas.

## Archivo: https

```caddy
valles.ddns.net {
    reverse_proxy 10.0.2.31
}
```

### Descripción

- **valles.ddns.net**: Caddy escucha en el dominio `valles.ddns.net` (automáticamente en HTTPS con certificado SSL/TLS)
- **reverse_proxy 10.0.2.31**: Reenvía todas las solicitudes al servidor backend en `10.0.2.31`

Este archivo maneja las peticiones HTTPS encriptadas. Caddy genera y gestiona automáticamente los certificados SSL/TLS.

## Funcionamiento General

Caddy actúa como un proxy inverso que:

1. **HTTP**: Recibe peticiones en el puerto 80 y las reenvía al backend
2. **HTTPS**: Recibe peticiones en `valles.ddns.net` (puerto 443) de forma segura y las reenvía al backend
3. Preserva automáticamente las cabeceras HTTP necesarias
4. Gestiona certificados SSL/TLS automáticamente

## Características de Caddy

- **Simplicidad**: Configuración más concisa que Nginx o Apache
- **HTTPS automático**: Genera y renueva certificados SSL/TLS sin intervención manual
- **Rendimiento**: Servidor web moderno y eficiente
- **Zero-downtime reloads**: Recarga de configuración sin interrumpir el servicio
- **Proxy inteligente**: Maneja automáticamente cabeceras y redirecciones

## HTTPS y TLS en Caddy

### Funcionamiento Automático

Caddy gestiona automáticamente los certificados SSL/TLS cuando detecta un dominio en la configuración:

1. **Obtención automática**: Caddy obtiene certificados de Let's Encrypt de forma automática
2. **Renovación automática**: Los certificados se renuevan automáticamente antes de expirar
3. **Sin configuración manual**: No requiere ninguna intervención del usuario para gestionar certificados
4. **Validación ACME**: Utiliza el protocolo ACME (Automated Certificate Management Environment) de Let's Encrypt

### Almacenamiento de Certificados y Claves

Los certificados y las claves privadas se almacenan en el directorio de datos de Caddy:

**Ubicación por defecto:**
```
~/.local/share/caddy/
```

**Estructura del directorio:**
```
~/.local/share/caddy/
├── certificates/          # Certificados generados
│   └── acme/            # Certificados de Let's Encrypt
│       └── acme-v02.api.letsencrypt.org/
├── caddy.lock           # Archivo de bloqueo
└── config/              # Configuración y estado
```

### Variables de Entorno

Se puede personalizar la ubicación del almacenamiento con la variable de entorno:

```bash
CADDY_DATA_DIR=/ruta/personalizada
```

### Seguridad de las Claves

- Las **claves privadas** nunca se transmiten ni se exponen
- Se almacenan con permisos restringidos (solo lectura del usuario)
- Caddy mantiene las claves en memoria durante la operación
- Los certificados se pueden revocar si es necesario

### Certificados en Producción

Para `valles.ddns.net`:
- Se genera un certificado válido de Let's Encrypt
- Se renueva automáticamente 30 días antes de la expiración
- El dominio debe ser accesible desde internet para la validación ACME

## Nota

Existe una referencia comentada (`#10.0.2.106`) que podría ser un servidor backend alternativo o histórico.
