import os
import time
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

AUTH_SERVICE_URL = os.environ.get(
    "AUTH_SERVICE_URL",
    "http://localhost:5001"
)

PROFILES = {
    "admin": {
        "nome": "Administrador do Sistema",
        "email": "admin@empresa.com",
        "cargo": "Tech Lead"
    },
    "usuario": {
        "nome": "Usuário Padrão",
        "email": "usuario@email.com",
        "cargo": "Desenvolvedor"
    }
}

# Circuit breaker simplificado
FALHAS_CONSECUTIVAS = 0
CIRCUIT_OPEN = False
ULTIMA_FALHA = 0

MAX_FALHAS = 3
CIRCUIT_TIMEOUT = 10


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile/<username>", methods=["GET"])
def get_profile(username):
    global FALHAS_CONSECUTIVAS
    global CIRCUIT_OPEN
    global ULTIMA_FALHA

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({
            "erro": "Token não fornecido"
        }), 400

    token = auth_header.replace("Bearer ", "").strip()

    # Circuit breaker
    if CIRCUIT_OPEN:
        tempo_desde_falha = time.time() - ULTIMA_FALHA

        if tempo_desde_falha < CIRCUIT_TIMEOUT:
            return jsonify({
                "erro": "Circuit breaker OPEN",
                "fallback": "Auth Service temporariamente indisponível"
            }), 503
        else:
            CIRCUIT_OPEN = False
            FALHAS_CONSECUTIVAS = 0

    inicio_rede = time.time()

    try:
        resposta_auth = requests.get(
            f"{AUTH_SERVICE_URL}/validate",
            params={"token": token},
            timeout=3
        )

        dados_auth = resposta_auth.json()

    except requests.exceptions.RequestException as e:
        print(f"[PROFILE SERVICE] Falha de rede: {e}")

        FALHAS_CONSECUTIVAS += 1
        ULTIMA_FALHA = time.time()

        if FALHAS_CONSECUTIVAS >= MAX_FALHAS:
            CIRCUIT_OPEN = True

        return jsonify({
            "erro": "Auth Service indisponível",
            "falhas_consecutivas": FALHAS_CONSECUTIVAS,
            "circuit_breaker": "OPEN" if CIRCUIT_OPEN else "CLOSED"
        }), 503

    fim_rede = time.time()

    duracao_rede_ms = round(
        (fim_rede - inicio_rede) * 1000,
        2
    )

    if not dados_auth.get("valid"):
        return jsonify({
            "erro": "Token inválido"
        }), 401

    username_token = dados_auth.get("username")

    # CORREÇÃO CRÍTICA DE SEGURANÇA
    if username_token != username:
        return jsonify({
            "erro": "Acesso negado ao perfil solicitado"
        }), 403

    perfil = PROFILES.get(username)

    if not perfil:
        return jsonify({
            "erro": "Perfil não encontrado"
        }), 404

    FALHAS_CONSECUTIVAS = 0

    return jsonify({
        "dados_perfil": perfil,
        "usuario_autenticado": username_token,
        "overhead_rede_detectado": f"{duracao_rede_ms} ms",
        "circuit_breaker": "CLOSED"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "Profile Service online",
        "porta": 5002
    }), 200


@app.route("/auth-status", methods=["GET"])
def auth_status():
    try:
        r = requests.get(
            f"{AUTH_SERVICE_URL}/health",
            timeout=2
        )

        return jsonify({
            "online": True,
            "status": r.json()
        }), 200

    except requests.exceptions.RequestException:
        return jsonify({
            "online": False,
            "status": "Auth Service não responde"
        }), 200


if __name__ == "__main__":
    print("[PROFILE SERVICE] Iniciando na porta 5002...")
    app.run(host="0.0.0.0", port=5002)