import os
import time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# O Docker Compose passará a URL dinâmica. Se rodar local, usa localhost.
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")

# Banco de dados simulado (Em conformidade com os nomes do Artigo)
PROFILES = {
    "admin": {"nome": "Administrador do Sistema", "email": "admin@empresa.com", "cargo": "Tech Lead"},
    "usuario": {"nome": "Usuário Padrão", "email": "usuario@email.com", "cargo": "Desenvolvedor"}
}

@app.route("/profile/<username>", methods=["GET"])
def get_profile(username):
    # Captura o token enviado pelo cliente no cabeçalho Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"erro": "Token não fornecido no cabeçalho Authorization"}), 400
    
    # Extrai apenas o valor do token (removendo o prefixo 'Bearer ' se existir)
    token = auth_header.replace("Bearer ", "").strip()

    # 1. MEDIÇÃO DA LATÊNCIA (Ponto Crítico do Artigo)
    inicio_rede = time.time()
    
    try:
        # Faz a chamada HTTP interna para o Auth Service enviando o token na Query String
        resposta_auth = requests.get(f"{AUTH_SERVICE_URL}/validate", params={"token": token}, timeout=3)
        status_code = resposta_auth.status_code
        dados_auth = resposta_auth.json()
    except requests.exceptions.RequestException as e:
        # Tolerância a falhas / Isolamento (Se o Auth Service cair)
        print(f"[PROFILE SERVICE] Erro Crítico de Rede ao contactar Auth Service: {e}")
        return jsonify({
            "erro": "Serviço de Autenticação indisponível.",
            "diagnostico_distribuido": "Falha Parcial Isolada detectada pelo Circuit Breaker simulado."
        }), 503

    fim_rede = time.time()
    duracao_rede_ms = round((fim_rede - inicio_rede) * 1000, 2)
    
    # Imprime no log do terminal o Overhead de Rede calculado
    print(f"\n[DISTRIBUTED LOG] Overhead de Rede para validação: {duracao_rede_ms} ms (Status Auth: {status_code})")

    # 2. SE O TOKEN FOR VÁLIDO, RETORNA OS DADOS DO PERFIL
    if status_code == 200 and dados_auth.get("valid"):
        perfil = PROFILES.get(username)
        if perfil:
            # Retorna o perfil adicionando a métrica de latência para o cliente ver
            return jsonify({
                "dados_perfil": perfil,
                "overhead_rede_detectado": f"{duracao_rede_ms} ms"
            }), 200
        return jsonify({"erro": "Perfil não encontrado no banco de dados"}), 404
    
    return jsonify({"erro": "Não autorizado. Token inválido ou expirado no Auth Service"}), 401

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Profile Service online", "porta": 5002}), 200

if __name__ == "__main__":
    print("[PROFILE SERVICE] Iniciando na porta 5002...")
    app.run(host="0.0.0.0", port=5002, debug=True)