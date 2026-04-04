#!/bin/bash
# IngresoQR - Diagnóstico Rápido
# Uso: bash /opt/gymaccess/diagnostico.sh

echo "========================================="
echo "  DIAGNOSTICO INGRESOQR - $(date)"
echo "========================================="
echo ""

# 1. Backend API
echo "--- BACKEND API ---"
STATUS=$(systemctl is-active gymaccess-api)
if [ "$STATUS" = "active" ]; then
  echo "[OK] Servicio gymaccess-api: ACTIVO"
else
  echo "[ERROR] Servicio gymaccess-api: $STATUS"
  echo "  -> Revisar: journalctl -u gymaccess-api --no-pager -n 20"
fi

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8001/api/health)
if [ "$HEALTH" = "200" ]; then
  echo "[OK] API responde: 200"
else
  echo "[ERROR] API no responde (HTTP: $HEALTH)"
fi

# 2. Apache
echo ""
echo "--- APACHE ---"
APACHE=$(systemctl is-active httpd)
if [ "$APACHE" = "active" ]; then
  echo "[OK] Apache: ACTIVO"
else
  echo "[ERROR] Apache: $APACHE"
fi

# 3. MongoDB
echo ""
echo "--- MONGODB ---"
MONGO=$(systemctl is-active mongod)
if [ "$MONGO" = "active" ]; then
  echo "[OK] MongoDB: ACTIVO"
else
  echo "[ERROR] MongoDB: $MONGO"
  echo "  -> Revisar: journalctl -u mongod --no-pager -n 20"
fi

# 4. Dominios
echo ""
echo "--- DOMINIOS ---"
for DOMAIN in app.ingresoqr.com c.ingresoqr.com; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://$DOMAIN")
  if [ "$CODE" = "200" ] || [ "$CODE" = "301" ] || [ "$CODE" = "302" ]; then
    echo "[OK] $DOMAIN: $CODE"
  else
    echo "[ERROR] $DOMAIN: $CODE"
  fi
done

# 5. Disco
echo ""
echo "--- DISCO ---"
DISK_USE=$(df -h / | awk 'NR==2{print $5}' | tr -d '%')
echo "Uso: ${DISK_USE}%"
if [ "$DISK_USE" -gt 90 ]; then
  echo "[ALERTA] Disco casi lleno!"
fi

# 6. RAM
echo ""
echo "--- MEMORIA ---"
free -h | awk 'NR==2{printf "Total: %s | Usada: %s | Libre: %s\n", $2, $3, $4}'

# 7. Ultimos errores del backend
echo ""
echo "--- ULTIMOS ERRORES BACKEND (5 min) ---"
journalctl -u gymaccess-api --since "5 min ago" --no-pager | grep -i "error\|traceback\|exception" | tail -5
if [ $? -ne 0 ] || [ -z "$(journalctl -u gymaccess-api --since '5 min ago' --no-pager | grep -i 'error\|traceback\|exception')" ]; then
  echo "[OK] Sin errores recientes"
fi

echo ""
echo "========================================="
echo "  FIN DIAGNOSTICO"
echo "========================================="
