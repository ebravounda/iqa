# Guia para Agregar Dominios Personalizados en IngresoQR

## Requisitos Previos
- Acceso al panel de Plesk del servidor
- Acceso a Cloudflare (o panel DNS del cliente)
- Acceso SSH al servidor (terminal de Plesk o PuTTY)
- Acceso como Super Admin en IngresoQR

---

## Paso 1: Crear el dominio en Plesk

1. Ir a **Plesk -> Websites & Domains**
2. Click en **"Add Domain"**
3. Escribir el dominio completo (ej: `clientegym.com`)
4. Completar el formulario y click **OK**
5. Activar **SSL con Let's Encrypt** para el nuevo dominio

---

## Paso 2: Configurar DNS en Cloudflare

En el panel de Cloudflare del dominio del cliente:

| Tipo | Nombre | Contenido | Proxy |
|------|--------|-----------|-------|
| A | @ | 54.225.240.9 | Proxied (nube naranja) |

**Configurar SSL/TLS en Cloudflare:**
- Ir a **SSL/TLS -> Informacion general**
- Modo de cifrado: **Completo (Full)**

---

## Paso 3: Copiar archivos del frontend (SSH)

Abrir la terminal SSH del servidor y ejecutar estos 3 comandos (reemplazar `DOMINIO.COM` por el dominio real):

```bash
rm -rf /var/www/vhosts/DOMINIO.COM/httpdocs/*

cp -r /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/* /var/www/vhosts/DOMINIO.COM/httpdocs/

chown -R USUARIO:psaserv /var/www/vhosts/DOMINIO.COM/httpdocs/
```

> **Nota:** Reemplaza `USUARIO` por el usuario del sistema que Plesk asigno al dominio. Para verlo, ejecuta:
> ```bash
> ls -la /var/www/vhosts/DOMINIO.COM/
> ```
> El usuario aparece en la columna de permisos (ej: `botwtsp`, `clientegym`, etc.)

---

## Paso 4: Crear el archivo .htaccess

Este archivo es necesario para que las rutas de React funcionen correctamente (/admin, /app, etc.):

```bash
echo 'Options -MultiViews
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.html [QSA,L]' > /var/www/vhosts/DOMINIO.COM/httpdocs/.htaccess

chown USUARIO:psaserv /var/www/vhosts/DOMINIO.COM/httpdocs/.htaccess
```

---

## Paso 5: Configurar en IngresoQR

1. Entrar al panel como **Super Admin**
2. Ir a **Negocios**
3. Click en el menu (3 puntos) del negocio -> **Editar**
4. En el campo **"Dominio Personalizado"** escribir el dominio (ej: `clientegym.com`)
5. Click **Guardar Cambios**

---

## Paso 6: Verificar

1. Abrir **https://DOMINIO.COM** en el navegador
2. Debe aparecer la pantalla de login con el logo y colores del negocio
3. Probar **https://DOMINIO.COM/admin** para acceso administrativo
4. Probar **https://DOMINIO.COM/app** para acceso de socios

---

## Desmarcar Restriccion de Symlinks (Solo primera vez)

Si es la primera vez que configuras un dominio personalizado:

1. Ir a **Plesk -> botwtsp.com -> Apache & Nginx Settings**
2. **Desmarcar** "Restrict the ability to follow symbolic links"
3. Click **OK**

> Esta configuracion solo se hace una vez por dominio.

---

## Script Rapido para Nuevos Dominios

Copia y pega este bloque completo en SSH, cambiando las 2 variables al inicio:

```bash
DOMINIO="clientegym.com"
USUARIO="clientegym"

rm -rf /var/www/vhosts/$DOMINIO/httpdocs/*
cp -r /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/* /var/www/vhosts/$DOMINIO/httpdocs/
chown -R $USUARIO:psaserv /var/www/vhosts/$DOMINIO/httpdocs/
echo 'Options -MultiViews
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.html [QSA,L]' > /var/www/vhosts/$DOMINIO/httpdocs/.htaccess
chown $USUARIO:psaserv /var/www/vhosts/$DOMINIO/httpdocs/.htaccess
echo "Dominio $DOMINIO configurado correctamente"
```

---

## Actualizar Frontend en Todos los Dominios

Cuando actualices el frontend de IngresoQR, ejecuta este script para copiar a todos los dominios personalizados. Agrega cada dominio nuevo a la lista:

```bash
DOMINIOS=("botwtsp.com" "clientegym.com")
USUARIOS=("botwtsp" "clientegym")

for i in "${!DOMINIOS[@]}"; do
  D=${DOMINIOS[$i]}
  U=${USUARIOS[$i]}
  rm -rf /var/www/vhosts/$D/httpdocs/*
  cp -r /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/* /var/www/vhosts/$D/httpdocs/
  chown -R $U:psaserv /var/www/vhosts/$D/httpdocs/
  echo 'Options -MultiViews
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.html [QSA,L]' > /var/www/vhosts/$D/httpdocs/.htaccess
  chown $U:psaserv /var/www/vhosts/$D/httpdocs/.htaccess
  echo "Actualizado: $D"
done
echo "Todos los dominios actualizados"
```

---

## Resumen de Pasos

| # | Donde | Accion |
|---|-------|--------|
| 1 | Plesk | Crear dominio + SSL Let's Encrypt |
| 2 | Cloudflare | Registro A -> 54.225.240.9 (Proxied) + SSL Full |
| 3 | SSH | Copiar archivos + .htaccess |
| 4 | IngresoQR | Asignar dominio al negocio |
| 5 | Navegador | Verificar que carga correctamente |
