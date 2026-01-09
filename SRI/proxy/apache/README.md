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

```apache
<Location "/">
  ProxyPass "http://10.0.2.31/"
  ProxyPassReverse "http://10.0.2.31/"
</Location>
```

### ProxyPass

- Redirige todas las solicitudes recibidas en la raíz (`/`) al servidor backend en `http://10.0.2.31/`
- Actúa como un proxy inverso, recibiendo peticiones y reenviándolas al servidor destino

### ProxyPassReverse

- Modifica las cabeceras HTTP de respuesta del servidor backend
- Asegura que las redirecciones, ubicaciones y URLs generadas por el backend sean correctas desde la perspectiva del cliente
- Reemplaza las referencias al backend con las del proxy

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
- Reenvía todas las solicitudes a un servidor backend en la IP `10.0.2.31`
- Retorna las respuestas del backend al cliente original
- Mantiene registros de errores y accesos para monitoreo

Este tipo de configuración es útil para:

- Balanceo de carga
- Seguridad (ocultando la infraestructura backend)
- Servir aplicaciones que no tienen capacidades web nativas
- SSL/TLS terminación

