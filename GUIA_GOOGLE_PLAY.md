# Guia: Publicar tu PWA en Google Play Store

## Resumen
Tu sistema GymAccess ya es una **PWA (Progressive Web App)** funcional. Para publicarla en Google Play Store, usaremos **PWABuilder** que envuelve tu PWA en una **Trusted Web Activity (TWA)** - una app Android que carga tu web sin barras de navegacion.

---

## Requisitos Previos

1. **Cuenta de desarrollador de Google Play** ($25 USD, pago unico)
   - Registrate en: https://play.google.com/console/signup
   
2. **Tu PWA funcionando en HTTPS** (ya lo tienes: `https://app.ingresoqr.com`)

3. **Archivo `assetlinks.json`** (se genera automaticamente con PWABuilder)

---

## Paso 1: Verificar que tu PWA cumple los requisitos

Tu PWA ya tiene:
- [x] `manifest.json` con `name`, `short_name`, `icons`, `start_url`, `display: standalone`
- [x] Service Worker registrado
- [x] HTTPS activo
- [x] Iconos de al menos 512x512 px

---

## Paso 2: Generar el APK/AAB con PWABuilder

1. Ve a **https://www.pwabuilder.com**
2. Ingresa la URL de tu app: `https://app.ingresoqr.com/app/login`
3. PWABuilder analizara tu PWA y mostrara una puntuacion
4. Haz clic en **"Package for stores"** → selecciona **"Android"**
5. Configura las opciones:
   - **Package ID**: `com.ingresoqr.app` (ejemplo)
   - **App name**: `GymAccess`
   - **App version**: `1.0.0`
   - **Launcher name**: `GymAccess`
   - **Start URL**: `/app/login`
   - **Display mode**: `Standalone`
   - **Status bar color**: `#09090B`
   - **Navigation bar color**: `#09090B`
   - **Theme color**: `#09090B`
   - **Background color**: `#09090B`
   - **Icon**: Sube tu logo del gimnasio (512x512 PNG)
6. Descarga el archivo generado (contiene un `.aab` y un archivo `assetlinks.json`)

---

## Paso 3: Subir `assetlinks.json` a tu servidor

PWABuilder generara un archivo `assetlinks.json`. Debes subirlo a:

```
https://app.ingresoqr.com/.well-known/assetlinks.json
```

### En Plesk:
1. Accede al **File Manager** de `app.ingresoqr.com`
2. Crea la carpeta `.well-known` en la raiz del dominio
3. Sube el archivo `assetlinks.json` dentro de esa carpeta
4. Verifica accediendo a `https://app.ingresoqr.com/.well-known/assetlinks.json`

---

## Paso 4: Subir a Google Play Console

1. Accede a https://play.google.com/console
2. Crea una nueva aplicacion:
   - **Nombre**: GymAccess (o el nombre de tu gimnasio)
   - **Idioma**: Espanol
   - **Tipo**: App
   - **Gratis**
3. Completa la informacion requerida:
   - Descripcion corta y larga
   - Capturas de pantalla (telefono y tablet)
   - Icono de alta resolucion
   - Grafico de funciones
   - Politica de privacidad (URL)
   - Categoria: Salud y bienestar
4. Ve a **Production** → **Releases** → **Create new release**
5. Sube el archivo `.aab` generado por PWABuilder
6. Completa el formulario de revision
7. Envia a revision (puede tardar 1-7 dias)

---

## Paso 5: Capturas de pantalla recomendadas

Toma capturas de:
1. Pantalla de login del socio
2. Pantalla principal con QR
3. Vista de clases disponibles
4. Perfil del socio
5. Vista de notificaciones

**Tamanos requeridos por Google Play:**
- Telefono: Al menos 2 capturas, min 320px, max 3840px
- Grafico de funciones: 1024 x 500 px

---

## Alternativa: Usando Bubblewrap (CLI)

Si prefieres la linea de comandos:

```bash
# Instalar bubblewrap
npm install -g @nickersoft/nickerbot
npm install -g @nickersoft/nickerbot

# Usando bubblewrap directamente
npm i -g @nickersoft/nickerbot
npx @nickersoft/nickerbot init --manifest https://app.ingresoqr.com/manifest.json

# O la forma oficial
npm install -g @nickersoft/nickerbot
npx bubblewrap init --manifest=https://app.ingresoqr.com/manifest.json
npx bubblewrap build
```

**Nota**: PWABuilder es mas facil y recomendado si no tienes experiencia con Android Studio.

---

## Importante

- **Actualizaciones**: Al ser una TWA, cuando actualices tu web (`app.ingresoqr.com`), la app de Google Play se actualiza automaticamente. No necesitas subir nuevos APKs.
- **No es necesario reescribir la app**: Tu PWA actual funciona perfectamente como app nativa.
- **Chrome Custom Tabs**: La TWA usa Chrome internamente, asi que el usuario debe tener Chrome instalado.

---

## Soporte

Si necesitas ayuda con alguno de estos pasos, contacta al equipo de desarrollo.
