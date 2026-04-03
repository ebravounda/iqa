# Guia de Integracion WHMCS + IngresoQR

## Resumen
Esta integracion permite gestionar los negocios (gyms, condominios, hoteles, coworkings) desde WHMCS:
- **Crear** negocio automaticamente cuando el cliente compra un plan
- **Suspender** negocio automaticamente cuando no paga
- **Reactivar** negocio cuando regulariza el pago
- **Eliminar** negocio cuando cancela el servicio
- **Ver info** del negocio desde WHMCS (socios activos, capacidad, etc.)

---

## Paso 1: Instalar el modulo en WHMCS

1. Descarga el codigo con "Download Code" en Emergent
2. Copia la carpeta `whmcs_module/ingresoqr/` a tu servidor WHMCS:
   ```
   /path/to/whmcs/modules/servers/ingresoqr/
   ```
   Debe quedar asi:
   ```
   modules/servers/ingresoqr/ingresoqr.php
   ```

---

## Paso 2: Configurar la API Key

En tu servidor de IngresoQR, agrega esta variable al archivo `.env`:

```
WHMCS_API_KEY=oDdI1c6Yh727TaddcOBlAuZmIE6bGcXgU9lnPpRrrMU
```

Reinicia el backend:
```bash
sudo systemctl restart gymaccess-api
```

---

## Paso 3: Crear el servidor en WHMCS

1. Ve a **Setup > Products/Services > Servers**
2. Click **Add New Server**
3. Configura:
   - **Name**: IngresoQR API
   - **Hostname**: c.ingresoqr.com
   - **Secure**: Si (marcar checkbox de SSL)
   - **Access Hash**: `oDdI1c6Yh727TaddcOBlAuZmIE6bGcXgU9lnPpRrrMU`
4. Click **Save Changes**

---

## Paso 4: Crear productos/planes en WHMCS

1. Ve a **Setup > Products/Services > Products/Services**
2. Click **Create a New Product**
3. Configura:
   - **Product Type**: Other
   - **Product Group**: (crea uno llamado "IngresoQR" o "Control de Acceso")
   - **Product Name**: Ej: "Plan Gimnasio Basico"
   - **Pricing**: Configura el precio mensual/anual

4. En la pestana **Module Settings**:
   - **Module Name**: ingresoqr
   - **Server**: IngresoQR API
   - **Tipo de Negocio**: Gimnasio / Condominio / Hotel / Coworking
   - **Max Socios/Residentes**: 100 (o el limite del plan)
   - **Nombre del Plan**: Basico

5. En **Automatic Setup**: Selecciona "Automatically setup the product as soon as the first payment is received"

6. Click **Save Changes**

---

## Paso 5: Probar

1. Crea un pedido de prueba en WHMCS para un cliente
2. Acepta el pedido y marca el pago
3. WHMCS llamara automaticamente a IngresoQR y creara el negocio
4. Verifica en el panel de IngresoQR que aparezca el nuevo negocio

---

## Acciones automaticas

| Evento en WHMCS | Accion en IngresoQR |
|-----------------|---------------------|
| Pago recibido | Crea el negocio + admin |
| Factura impaga (suspension) | Suspende el negocio |
| Pago recibido tras suspension | Reactiva el negocio |
| Cancelacion del servicio | Marca como terminado |

---

## Boton "Ver Info del Negocio"

En WHMCS, dentro del servicio del cliente, aparecera un boton **"Ver Info del Negocio"** que muestra:
- Nombre del negocio
- Tipo (Gimnasio/Condominio/Hotel/Coworking)
- Estado (Activo/Suspendido)
- Socios activos
- Total socios
- Capacidad maxima

---

## Endpoints de la API

Todos los endpoints requieren el header `x-whmcs-key` con la API key.

| Endpoint | Funcion |
|----------|---------|
| POST /api/whmcs/provision | Crear negocio + admin |
| POST /api/whmcs/suspend | Suspender negocio |
| POST /api/whmcs/unsuspend | Reactivar negocio |
| POST /api/whmcs/terminate | Terminar negocio |
| POST /api/whmcs/info | Ver informacion del negocio |

---

## Notas importantes

- La API key debe ser la misma en WHMCS (Access Hash) y en IngresoQR (.env)
- El email del cliente en WHMCS se usa como email del admin del negocio
- El campo "Domain" en el pedido de WHMCS se usa como nombre del negocio
- Si no se especifica "Domain", se usa el nombre del cliente
