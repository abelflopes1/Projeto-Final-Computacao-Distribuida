#!/bin/bash
# ── Teste de Carga + Demo Isolamento de Falhas ────────────────────────────────

echo "=============================================="
echo "  PASSO 1: Fazendo login para obter token"
echo "=============================================="

RESPOSTA_LOGIN=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}')

TOKEN=$(echo $RESPOSTA_LOGIN | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
echo "Token obtido: $TOKEN"

echo ""
echo "=============================================="
echo "  PASSO 2: Teste de Carga (50 requisições)"
echo "=============================================="

TOTAL=50
SUCESSO=0
FALHA=0

for i in $(seq 1 $TOTAL); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "http://localhost:5002/profile/admin")

  if [ "$HTTP_CODE" == "200" ]; then
    SUCESSO=$((SUCESSO + 1))
    echo -n "."
  else
    FALHA=$((FALHA + 1))
    echo -n "X($HTTP_CODE)"
  fi
done

echo ""
echo ""
echo "  Sucesso: $SUCESSO / $TOTAL"
echo "  Falhas:  $FALHA / $TOTAL"

echo ""
echo "=============================================="
echo "  PASSO 3: DEMO — Isolamento de Falhas"
echo "=============================================="
echo "Derrubando o profile-service..."
docker stop profile-service

sleep 1

echo ""
echo "Auth Service ainda responde? (deve ser SIM)"
AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}')

if [ "$AUTH_CODE" == "200" ]; then
  echo "  ✅ Auth Service: $AUTH_CODE — ONLINE. Isolamento confirmado!"
else
  echo "  ❌ Auth Service: $AUTH_CODE"
fi

echo ""
echo "Subindo profile-service novamente..."
docker start profile-service
echo "Done."
