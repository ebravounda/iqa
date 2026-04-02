#!/bin/bash
# ============================================
# IngresoQR - Script de Actualizacion
# Ejecutar desde SSH en el servidor Plesk
# ============================================

# Configuracion - AJUSTA ESTAS RUTAS SI ES NECESARIO
REPO_DIR="/var/www/vhosts/ingresoqr.com/c.ingresoqr.com"
FRONTEND_HTTPDOCS="/var/www/vhosts/ingresoqr.com/app.ingresoqr.com/httpdocs"
BACKEND_SERVICE="gymapi"

echo "==========================================="
echo "  IngresoQR - Actualizacion de Produccion"
echo "==========================================="
echo ""

# 1. Ir al repositorio y hacer pull
echo "[1/4] Descargando cambios de GitHub..."
cd "$REPO_DIR" || { echo "ERROR: No se encontro $REPO_DIR"; exit 1; }
git pull origin main
if [ $? -ne 0 ]; then
    echo "ERROR: git pull fallo. Revisa credenciales o conflictos."
    exit 1
fi
echo "OK - Codigo actualizado"
echo ""

# 2. Instalar dependencias backend si hay cambios
echo "[2/4] Verificando dependencias backend..."
cd "$REPO_DIR/backend"
pip install -r requirements.txt --quiet 2>/dev/null
pip install -r requirements-prod.txt --quiet 2>/dev/null
echo "OK - Dependencias verificadas"
echo ""

# 3. Sincronizar frontend build a httpdocs
echo "[3/4] Sincronizando frontend a app.ingresoqr.com..."
if [ -d "$REPO_DIR/frontend/build" ]; then
    # Limpiar httpdocs (excepto .htaccess si existe)
    find "$FRONTEND_HTTPDOCS" -mindepth 1 ! -name '.htaccess' -delete 2>/dev/null
    # Copiar build
    cp -r "$REPO_DIR/frontend/build/"* "$FRONTEND_HTTPDOCS/"
    echo "OK - Frontend sincronizado ($FRONTEND_HTTPDOCS)"
else
    echo "AVISO: No se encontro frontend/build/. Sube el build manualmente."
fi
echo ""

# 4. Reiniciar backend
echo "[4/4] Reiniciando backend..."
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    sudo systemctl restart "$BACKEND_SERVICE"
    echo "OK - Servicio $BACKEND_SERVICE reiniciado"
elif command -v pm2 &>/dev/null; then
    pm2 restart all
    echo "OK - PM2 reiniciado"
else
    echo "AVISO: No se encontro servicio '$BACKEND_SERVICE'. Reinicia manualmente."
    echo "  Opciones: sudo systemctl restart gymapi"
    echo "            pm2 restart all"
    echo "            kill + reiniciar uvicorn"
fi
echo ""

echo "==========================================="
echo "  Actualizacion completada!"
echo "  Backend: https://c.ingresoqr.com"
echo "  Frontend: https://app.ingresoqr.com"
echo "==========================================="
