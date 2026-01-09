# Configuración de Proxy en Nginx

Este archivo documenta la configuración de proxy inverso realizada en Nginx para `valles.ddns.net`.

## Configuración del Servidor

```nginx
server {
    listen 80;
    server_name valles.ddns.net;
```

- **listen 80**: El servidor escucha en el puerto 80 (HTTP)
- **server_name**: Define el nombre de dominio `valles.ddns.net`

## Configuración del Proxy Inverso

```nginx
location / {
    proxy_pass http://10.0.2.31/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
```

### Directivas principales

- **proxy_pass**: Redirige todas las solicitudes al servidor backend en `http://10.0.2.31/`
- **proxy_set_header Host**: Mantiene el nombre del host original en las cabeceras
- **proxy_set_header X-Real-IP**: Preserva la IP real del cliente
- **proxy_set_header X-Forwarded-For**: Incluye la cadena de IPs de clientes proxy
- **proxy_set_header X-Forwarded-Proto**: Preserva el protocolo original (HTTP/HTTPS)
- **proxy_redirect off**: No reescribe las redirecciones del servidor backend

## Funcionamiento

Esta configuración establece Nginx como un proxy inverso que:

1. Recibe peticiones en `valles.ddns.net:80`
2. Reenvía todas las solicitudes al servidor backend en `10.0.2.31`
3. Preserva información del cliente original en las cabeceras HTTP
4. Retorna las respuestas del backend al cliente

## Ventajas de esta configuración

- **Seguridad**: Oculta la infraestructura del servidor backend
- **Rendimiento**: Nginx es ligero y rápido en la gestión de proxies
- **Transparencia de cliente**: Las cabeceras preservan la información original del cliente
- **Flexibilidad**: Fácilmente configurable para añadir más funcionalidades
