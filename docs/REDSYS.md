# Integración Redsys TPV Virtual - IngresoQR

## Descripción
Integración completa con Redsys TPV Virtual para cobrar membresías a los socios a través de la PWA. Cada negocio (gym) configura sus propias credenciales de Redsys proporcionadas por su banco.

---

## 1. Configurar Redsys en el Panel del Banco

Accede al panel de administración de tu TPV Virtual (ej: sis-t.redsys.es para sandbox, sis.redsys.es para producción).

### Datos a configurar en el panel Redsys:

| Campo | Valor |
|-------|-------|
| **URL del comercio** | `https://app.ingresoqr.com` |
| **Notificación online** | HTTP y Email Comercio |
| **URL de notificación** | `https://c.ingresoqr.com/api/redsys/notification` |
| **Sincronización** | Síncrona |

### Datos que necesitas del panel Redsys:

| Dato | Dónde encontrarlo |
|------|-------------------|
| **Código de comercio (FUC)** | Aparece en la esquina superior izquierda (ej: 181049164) |
| **Terminal** | Aparece junto al código (ej: 100) |
| **Clave de firma (SHA-256)** | Botón "Ver clave de firma" en la gestión del comercio |

---

## 2. Activar Redsys en IngresoQR (Super Admin)

Solo el **Super Admin** puede activar Redsys para cada negocio.

### Pasos:

1. Inicia sesión como **Super Admin** en `app.ingresoqr.com/admin/login`
2. Ve a **Negocios** en el menú lateral
3. Haz clic en **"Administrar"** en el gym que quieres configurar (esto te hace "impersonar" ese gym)
4. Ve a **Configuración** en el menú lateral
5. Busca la sección **"TPV Virtual (Redsys)"**
6. Rellena los campos:
   - **Código de Comercio (FUC)**: El número de tu banco (ej: 181049164)
   - **Terminal**: El número de terminal (ej: 100)
   - **Clave Secreta (SHA-256)**: La clave de firma de Redsys
   - **Entorno**: Sandbox (pruebas) o Producción (real)
7. Haz clic en **"Activar y Guardar Redsys"**

### Verificación:
- El badge cambiará a verde: "Redsys Configurado"
- Mostrará el código de comercio enmascarado y el terminal

---

## 3. Flujo de Pago del Socio

1. El socio accede a la PWA (`app.ingresoqr.com/app/membership`)
2. Selecciona un plan
3. Se redirige automáticamente al TPV Virtual de Redsys
4. Introduce los datos de su tarjeta en la página segura de Redsys
5. Redsys procesa el pago y envía una notificación a `c.ingresoqr.com/api/redsys/notification`
6. El backend verifica la firma HMAC SHA256, activa la membresía y marca el pago como completado
7. El socio es redirigido de vuelta a la PWA con un mensaje de éxito

---

## 4. Seguridad

- Los datos de tarjeta **nunca pasan por nuestro servidor** (cumple PCI DSS)
- Todas las peticiones se firman con **HMAC SHA256 + 3DES**
- Las notificaciones de Redsys se verifican con firma criptográfica antes de activar membresías
- Las credenciales se almacenan en MongoDB por cada gym de forma independiente
- Solo el Super Admin puede configurar/modificar credenciales de Redsys

---

## 5. Arquitectura Técnica

### Backend (FastAPI)

| Archivo | Descripción |
|---------|-------------|
| `backend/redsys_utils.py` | Funciones de firma HMAC SHA256, 3DES, codificación de parámetros |
| `backend/routes/redsys_routes.py` | Endpoints de configuración, iniciación de pago, y callback |

### Endpoints API

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/api/gyms/{gym_id}/redsys-config` | Ver estado de configuración | Super Admin |
| PUT | `/api/gyms/{gym_id}/redsys-config` | Guardar/actualizar credenciales | Super Admin |
| POST | `/api/redsys/initiate` | Generar formulario de pago | Público (socio) |
| POST | `/api/redsys/notification` | Callback server-to-server de Redsys | Redsys servers |
| GET | `/api/redsys/status/{order}` | Consultar estado de un pago | Público |

### Frontend (React)

| Archivo | Descripción |
|---------|-------------|
| `frontend/src/pages/admin/AdminSettings.js` | Sección de configuración Redsys (solo Super Admin) |
| `frontend/src/pages/pwa/MemberMembership.js` | Flujo de pago: intenta Redsys, si no hay config usa Stripe |
| `frontend/src/lib/api.js` | Funciones API: getRedsysConfig, updateRedsysConfig, initiateRedsysPayment |

### Campos en MongoDB (colección `gyms`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `redsys_enabled` | Boolean | Si Redsys está activo para este gym |
| `redsys_merchant_code` | String | Código de comercio (FUC) |
| `redsys_terminal` | String | Número de terminal |
| `redsys_secret_key` | String | Clave de firma SHA-256 |
| `redsys_environment` | String | "sandbox" o "production" |

---

## 6. URLs por Entorno

### Sandbox (Pruebas)
- TPV Virtual: `https://sis-t.redsys.es:25443/sis/realizarPago`
- Panel Admin: `https://sis-t.redsys.es:25443/admincanales-web/`

### Producción
- TPV Virtual: `https://sis.redsys.es/sis/realizarPago`
- Panel Admin: Proporcionado por tu banco

---

## 7. Códigos de Respuesta Redsys

| Código | Significado |
|--------|------------|
| 0000-0099 | Transacción aprobada |
| 0101 | Tarjeta caducada |
| 0102 | Tarjeta bloqueada |
| 0129 | CVV incorrecto |
| 0190 | Denegación sin especificar |
| 0913 | Pedido repetido |
| 9915 | Pago cancelado por el usuario |

---

## 8. Troubleshooting

### "Redsys no está habilitado para este gimnasio"
→ El Super Admin debe activar Redsys en Configuración del gym

### El pago se completa pero la membresía no se activa
→ Verificar que la URL de notificación (`https://c.ingresoqr.com/api/redsys/notification`) está correctamente configurada en el panel de Redsys

### Error de firma inválida
→ Verificar que la clave secreta en IngresoQR coincide con la "clave de firma" del panel Redsys
