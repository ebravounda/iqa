#!/bin/bash
# ============================================
# IngresoQR - Script de Actualizacion
# Ejecutar desde SSH/Terminal de Plesk
# ============================================

BACKEND_DOCKER="/opt/gymaccess/backend"
FRONTEND_HTTPDOCS="/var/www/vhosts/ingresoqr.com/app.ingresoqr.com/httpdocs"
REPO_DIR="/opt/gymaccess/repo"

echo "==========================================="
echo "  IngresoQR - Actualizacion de Produccion"
echo "==========================================="
echo ""

# 1. Clonar o actualizar repositorio
if [ -d "$REPO_DIR/.git" ]; then
    echo "[1/4] Actualizando repositorio..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "[1/4] Clonando repositorio por primera vez..."
    mkdir -p "$REPO_DIR"
    git clone https://github.com/ebravounda/iqa.git "$REPO_DIR"
fi

if [ $? -ne 0 ]; then
    echo "ERROR: git pull fallo."
    exit 1
fi
echo "OK - Codigo descargado"
echo ""

# 2. Actualizar archivos del backend
echo "[2/4] Actualizando backend..."
mkdir -p "$BACKEND_DOCKER"
# Copiar todos los archivos Python del backend
cp -r "$REPO_DIR/backend/"*.py "$BACKEND_DOCKER/" 2>/dev/null
cp -r "$REPO_DIR/backend/routes/" "$BACKEND_DOCKER/routes/" 2>/dev/null
cp -r "$REPO_DIR/backend/models.py" "$BACKEND_DOCKER/" 2>/dev/null
cp "$REPO_DIR/backend/requirements-prod.txt" "$BACKEND_DOCKER/requirements.txt" 2>/dev/null
echo "OK - Archivos backend copiados"
echo ""

# 3. Reiniciar backend Docker
echo "[3/4] Reiniciando backend Docker..."
docker restart gymaccess-api 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Reconstruyendo imagen Docker..."
    cd "$BACKEND_DOCKER"
    docker stop gymaccess-api 2>/dev/null
    docker rm gymaccess-api 2>/dev/null
    docker build -t gymaccess-api .
    docker run -d \
        --name gymaccess-api \
        --restart always \
        -p 8001:8001 \
        --env-file .env \
        gymaccess-api
fi
echo "OK - Backend reiniciado"
echo ""

# 4. Actualizar frontend
echo "[4/4] Sincronizando frontend..."
if [ -d "$REPO_DIR/frontend/build" ]; then
    # Limpiar httpdocs (preservar .htaccess)
    find "$FRONTEND_HTTPDOCS" -mindepth 1 ! -name '.htaccess' -delete 2>/dev/null
    cp -r "$REPO_DIR/frontend/build/"* "$FRONTEND_HTTPDOCS/"
    echo "OK - Frontend copiado a $FRONTEND_HTTPDOCS"
else
    echo "AVISO: No se encontro frontend/build/ en el repo."
    echo "  El build ya debe estar incluido en el repositorio."
fi
echo ""

# Verificar
echo "==========================================="
echo "  Verificando..."
echo "==========================================="
sleep 3
HEALTH=$(curl -s https://c.ingresoqr.com/api/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  Backend: OK"
else
    echo "  Backend: REVISAR (docker logs gymaccess-api)"
fi
echo "  Frontend: https://app.ingresoqr.com"
echo "==========================================="
echo "  Actualizacion completada!"
echo "==========================================="
