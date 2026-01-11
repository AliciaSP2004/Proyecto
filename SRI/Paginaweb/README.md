# Configuración del VirtualHost: `valles.ddns.net`

Descripción breve

Este documento explica la configuración definida en `ConfFinal.conf` (VirtualHost *:80) y recoge pasos prácticos para habilitar módulos, pruebas y medidas de seguridad.

---

## Contenido del VirtualHost (extracto)

```apache
<VirtualHost *:80>
    ServerName valles.ddns.net
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html/wordpress
    DirectoryIndex index.html index.cgi index.pl index.php index.xhtml index.htm

    <Directory /var/www/html/wordpress>
        AllowOverride All
    </Directory>

    Alias "/mipagina" "/var/www/mipagina"

    <Directory "/var/www/mipagina">
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    <Directory "/var/www/mipagina">
        AuthType Basic
        AuthName "Área restringida"
        AuthUserFile /etc/apache2/.htpasswd
        Require valid-user
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html
        AddOutputFilterByType DEFLATE text/css
        AddOutputFilterByType DEFLATE text/plain
        AddOutputFilterByType DEFLATE text/xml
        AddOutputFilterByType DEFLATE application/javascript
        AddOutputFilterByType DEFLATE application/json
        AddOutputFilterByType DEFLATE application/xml
        AddOutputFilterByType DEFLATE application/xhtml+xml
    </IfModule>
</VirtualHost>
```

---

## Explicación por secciones

- **ServerName / ServerAdmin**: Nombre público del sitio y contacto del admin.
- **DocumentRoot**: Ruta donde está WordPress (`/var/www/html/wordpress`).
- **DirectoryIndex**: Ficheros que Apache considera por defecto.
- **AllowOverride All**: Necesario para que WordPress gestione permalinks via `.htaccess` (requiere `mod_rewrite`).
- **Alias `/mipagina`**: Mapea `/mipagina` a `/var/www/mipagina`.
- **Autenticación básica**: Protege `/mipagina` con `.htpasswd` (mod_auth_basic).
- **Logs**: `ErrorLog` y `CustomLog` para monitoreo.
- **Compresión (mod_deflate)**: Reduce el tamaño de las respuestas para tipos comunes.

---

## Módulos recomendados (Debian/Ubuntu) 🔧

```bash
sudo a2enmod rewrite alias auth_basic deflate headers ssl
sudo systemctl reload apache2
```

- `mod_rewrite`: Permalinks de WordPress
- `mod_auth_basic`: Autenticación básica
- `mod_deflate`: Compresión
- `mod_headers`: Gestión de cabeceras (caching, seguridad)

---

## Seguridad y permisos 🔐

- Protege el fichero `/etc/apache2/.htpasswd` con permisos restrictivos y propietario `root`.

```bash
sudo htpasswd -c /etc/apache2/.htpasswd usuario
sudo chown root:root /etc/apache2/.htpasswd
sudo chmod 640 /etc/apache2/.htpasswd
```

- Evita dejar `Options Indexes` en directorios públicos si no quieres listar ficheros.
- Si sólo WordPress necesita `.htaccess`, limita `AllowOverride` a ese directorio y revisa su contenido.
- Considera activar HTTPS y redirigir tráfico HTTP a HTTPS.

---

## Pruebas y comprobaciones ✅

- Sintaxis de Apache:

```bash
sudo apachectl configtest
```

- Reiniciar/Recargar:

```bash
sudo systemctl restart apache2
sudo systemctl reload apache2
```

- Revisar logs:

```bash
tail -f /var/log/apache2/error.log
tail -f /var/log/apache2/access.log
```

- Petición simple y comprobación de host:

```bash
curl -I -H "Host: valles.ddns.net" http://127.0.0.1/
```

- Comprobar compresión:

```bash
curl -I -H "Accept-Encoding: gzip" http://127.0.0.1/
```

- Probar autenticación básica en `/mipagina`:

```bash
curl -u usuario http://127.0.0.1/mipagina
```

---

## Notas WordPress ⚠️

- Asegúrate de que `AllowOverride All` esté en la carpeta de WordPress si necesitas permalinks.
- Ajusta propietarios y permisos (`www-data` en Debian/Ubuntu) y evita permisos 777.
- Revisa plugins de cache y seguridad y configura cabeceras adecuadas (HSTS, X-Frame-Options, X-Content-Type-Options).

---

## Mejoras opcionales

- Añadir `mod_expires` / `mod_headers` para caching estático.
- Habilitar HTTPS con `Let's Encrypt` y configurar redirección desde 80 → 443.
- Añadir tests automáticos o un script de comprobación (ping, curl, check ports).

---

Si quieres, creo un script de verificación (`scripts/check_paginaweb.sh`) y un checklist breve al principio del README. Dime si lo añado. 
