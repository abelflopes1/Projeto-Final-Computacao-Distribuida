import os
import time
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")

PROFILES = {
    "admin": {"nome": "Administrador do Sistema", "email": "admin@empresa.com", "cargo": "Tech Lead"},
    "usuario": {"nome": "Usuário Padrão", "email": "usuario@email.com", "cargo": "Desenvolvedor"}
}

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile/<username>", methods=["GET"])
def get_profile(username):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"erro": "Token não fornecido no cabeçalho Authorization"}), 400

    token = auth_header.replace("Bearer ", "").strip()

    inicio_rede = time.time()

    try:
        resposta_auth = requests.get(f"{AUTH_SERVICE_URL}/validate", params={"token": token}, timeout=3)
        status_code = resposta_auth.status_code
        dados_auth = resposta_auth.json()
    except requests.exceptions.RequestException as e:
        print(f"[PROFILE SERVICE] Erro Crítico de Rede ao contactar Auth Service: {e}")
        return jsonify({
            "erro": "Serviço de Autenticação indisponível.",
            "circuit_breaker": "Falha isolada detectada — Auth Service fora do ar. Profile Service continua funcionando."
        }), 503

    fim_rede = time.time()
    duracao_rede_ms = round((fim_rede - inicio_rede) * 1000, 2)

    print(f"\n[DISTRIBUTED LOG] Overhead de Rede para validação: {duracao_rede_ms} ms (Status Auth: {status_code})")

    if status_code == 200 and dados_auth.get("valid"):
        perfil = PROFILES.get(username)
        if perfil:
            return jsonify({
                "dados_perfil": perfil,
                "overhead_rede_detectado": f"{duracao_rede_ms} ms"
            }), 200
        return jsonify({"erro": "Perfil não encontrado no banco de dados"}), 404

    return jsonify({"erro": "Não autorizado. Token inválido ou expirado no Auth Service"}), 401


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Profile Service online", "porta": 5002}), 200


@app.route("/auth-status", methods=["GET"])
def auth_status():
    """Verifica se o Auth Service está no ar — usado pelo Circuit Breaker demo"""
    try:
        r = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=2)
        return jsonify({"online": True, "status": r.json()}), 200
    except requests.exceptions.RequestException:
        return jsonify({"online": False, "status": "Auth Service não responde"}), 200


if __name__ == "__main__":
    print("[PROFILE SERVICE] Iniciando na porta 5002...")
    app.run(host="0.0.0.0", port=5002, debug=True)
