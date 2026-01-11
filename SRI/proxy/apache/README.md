# Configuración de Proxy en Apache

A continuación se describe brevemente la configuración de proxy presente en el archivo Apache.

## Directivas principales

### ServerName

```
ServerName valles.ddns.net
```

Define el nombre del servidor que se utiliza para identificarse:
- Se usa al crear URLs de redirección
- En hosts virtuales, especifica qué nombre de host debe aparecer en la cabecera `Host:` de la solicitud

### ServerAdmin

```
ServerAdmin webmaster@localhost
```

Especifica la dirección de correo del administrador del servidor:
- Aparece en algunas páginas de error generadas por Apache

## Configuración del Proxy

### Ejemplo simple (único backend)

```apache
<Location "/">
  ProxyPass "http://10.0.2.31/"
  ProxyPassReverse "http://10.0.2.31/"
</Location>
```

### Ejemplo con balanceador (extraído de `Configuracion.conf`)

```apache
<VirtualHost *:80>
    ServerName valles.ddns.net

    # Definir el grupo de servidores backend (balanceador)
    <Proxy "balancer://servidores">
        BalancerMember http://10.0.2.31:80
        BalancerMember http://10.0.2.106:80
    </Proxy>

    # Enviar todo el tráfico al balanceador
    ProxyPass "/" "balancer://servidores/"
    ProxyPassReverse "/" "balancer://servidores/"

    # Opcional: panel de estado del balanceador (solo para admins)
    <Location "/balancer-manager">
        SetHandler balancer-manager
        Require local
    </Location>
</VirtualHost>
```

### ProxyPass / Balanceador

- `ProxyPass` puede apuntar a un backend único o a un `balancer://` que agrupa varios `BalancerMember`.
- El `<Proxy "balancer://servidores">` define el grupo de servidores que recibirán las peticiones.
- `BalancerMember` lista las instancias backend que participan en el balanceo.
- `ProxyPassReverse` ajusta cabeceras de respuesta y redirecciones para que las rutas expuestas al cliente sean correctas.
- El `balancer-manager` permite ver y administrar el estado del balanceador (restringir su acceso en producción).


## Configuración de Logs

```apache
ErrorLog ${APACHE_LOG_DIR}/error.log
CustomLog ${APACHE_LOG_DIR}/access.log combined
```

- **ErrorLog**: Especifica la ubicación del archivo de registro de errores
- **CustomLog**: Define el archivo de registro de acceso con el formato "combined" (incluye información detallada de cada petición)

## Funcionamiento general

Esta configuración establece Apache como un proxy inverso que:

- Recibe peticiones en `valles.ddns.net`
- Reenvía todas las solicitudes a uno o varios servidores backend (directo o mediante un balanceador)
- Retorna las respuestas del backend al cliente original
- Mantiene registros de errores y accesos para monitoreo

Este tipo de configuración es útil para:

- Balanceo de carga
- Seguridad (ocultando la infraestructura backend)
- Servir aplicaciones que no tienen capacidades web nativas
- SSL/TLS terminación

---

## Módulos necesarios (Debian/Ubuntu) 🔧

Para que la configuración funcione correctamente, habilita los módulos necesarios:

```bash
sudo a2enmod proxy proxy_balancer proxy_http lbmethod_byrequests proxy_wstunnel headers ssl
sudo systemctl reload apache2
```

Comprueba que los módulos estén activos:

```bash
apache2ctl -M | grep proxy
```

## Habilitación y comprobaciones básicas ✅

- Verifica la sintaxis de la configuración:

```bash
sudo apachectl configtest
```

- Reinicia o recarga Apache después de los cambios:

```bash
sudo systemctl restart apache2
sudo systemctl reload apache2
```

- Revisa los logs en tiempo real para detectar errores:

```bash
journalctl -u apache2 -f
tail -f /var/log/apache2/error.log
```

## Seguridad del `balancer-manager` 🔐

No expongas el panel de estado a Internet. Restríngelo por IP o usa autenticación básica:

```apache
<Location "/balancer-manager">
    SetHandler balancer-manager
    AuthType Basic
    AuthName "Balancer Manager"
    AuthUserFile "/etc/apache2/.htpasswd"
    Require valid-user
    # O bien limitar por red:
    # Require ip 192.168.0.0/24
</Location>
```

Crear usuario para acceso:

```bash
sudo htpasswd -c /etc/apache2/.htpasswd admin
```

## Métodos de balanceo y opciones avanzadas ⚙️

- Métodos comunes: `byrequests`, `bybusyness`, `bytraffic` (usar con `ProxySet lbmethod=`).
- Para sesiones pegajosas (sticky sessions) se puede usar `stickysession` o rutas de sesión, por ejemplo:

```apache
<Proxy "balancer://servidores">
    BalancerMember http://10.0.2.31:80 route=node1
    BalancerMember http://10.0.2.106:80 route=node2
    ProxySet lbmethod=byrequests stickysession=JSESSIONID
</Proxy>
```

- Health checks (si está disponible en tu versión de Apache) con `mod_proxy_hcheck` pueden mejorar la detección de nodos caídos.

## SSL/TLS terminación 🔒

Si vas a terminar TLS en Apache, habilita `mod_ssl` y configura un `VirtualHost *:443` con tus certificados y `ProxyPreserveHost On` para mantener el `Host` original:

```apache
<VirtualHost *:443>
    ServerName valles.ddns.net
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/yourcert.pem
    SSLCertificateKeyFile /etc/ssl/private/yourkey.pem

    ProxyPreserveHost On
    ProxyPass "/" "balancer://servidores/"
    ProxyPassReverse "/" "balancer://servidores/"
</VirtualHost>
```

## Logs y depuración 🔍

Durante pruebas, puedes aumentar el nivel de log para `mod_proxy` y `mod_proxy_balancer`:

```apache
LogLevel warn proxy:debug proxy_balancer:debug
```

Recuerda volver a valores normales una vez resuelto el problema para evitar logs excesivos.

## Pruebas y comprobaciones 🧪

- Petición simple:

```bash
curl -I -H "Host: valles.ddns.net" http://127.0.0.1/
```

- Prueba de carga (ejemplo con `ab` o `wrk`):

```bash
ab -n 100 -c 10 http://valles.ddns.net/
```

- Comprueba conectividad entre proxy y backends y que los puertos estén abiertos en el firewall.

## Notas finales ⚠️

- Asegúrate de que el proxy puede acceder a los backends por IP y puerto.
- Protege el acceso al `balancer-manager` y monitorea los logs.
- Mantén actualizadas las reglas de firewall y certificados TLS.

---


