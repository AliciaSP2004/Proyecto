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
    proxy_pass http://mis_apps;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
```

## Upstream y balanceo

```nginx
upstream mis_apps {
    server 10.0.2.31:80;
    server 10.0.2.106:80;
    # Opcional: añadir weights, max_fails, fail_timeout:
    # server 10.0.2.31:80 weight=3 max_fails=2 fail_timeout=30s;
}
```

- Por defecto Nginx usa **round-robin**. Otras opciones: `least_conn` (conexiones activas más bajas) y `ip_hash` (sticky por IP):

```nginx
# Sticky por IP
upstream mis_apps {
    ip_hash;
    server 10.0.2.31:80;
    server 10.0.2.106:80;
}
```

- No apuntes `proxy_pass` al propio `server_name` (p. ej. `valles.ddns.net`) ya que puede crear un bucle: usa el nombre del `upstream` o una IP directa.

## SSL/TLS y terminación HTTPS 🔒

Configura un `server` en `*:443` y activa certificados (Let's Encrypt o comerciales). Ejemplo:

```nginx
server {
    listen 443 ssl;
    server_name valles.ddns.net;

    ssl_certificate /etc/letsencrypt/live/valles.ddns.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/valles.ddns.net/privkey.pem;

    location / {
        proxy_pass http://mis_apps;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Comprobaciones y despliegue ✅

- Verifica la configuración antes de recargar:

```bash
sudo nginx -t
```

- Recarga Nginx sin cortar conexiones:

```bash
sudo systemctl reload nginx
```

- Revisa logs de error y acceso:

```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

## Health checks y disponibilidad ❤️

- Nginx Open Source no trae health checks activas avanzadas por defecto; considera usar `nginx_upstream_check_module` o `nginx-plus` para health checks activas.
- Como alternativa, configura `max_fails` y `fail_timeout` en los `server` del `upstream` para una detección pasiva de fallos.

## Pruebas y depuración 🔍

- Petición simple:

```bash
curl -I -H "Host: valles.ddns.net" http://127.0.0.1/
```

- Prueba de carga (ejemplo con `ab` o `wrk`):

```bash
ab -n 100 -c 10 http://valles.ddns.net/
```

- Comprueba conectividad con los backends:

```bash
nc -vz 10.0.2.31 80
nc -vz 10.0.2.106 80
```

## Buenas prácticas y notas finales ⚠️

- Protege accesos administrativos y usa HTTPS para servicios expuestos.
- Monitorea los logs y ajusta `LogLevel` / `error_log` según necesites.
- Evita referencias circulares en `proxy_pass` (usar `upstream` evita este problema).

---

