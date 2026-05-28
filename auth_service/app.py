from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import time
import secrets

app = Flask(__name__)
CORS(app)

USUARIOS_VALIDOS = {
    "admin": "senha123",
    "usuario": "12345"
}

# token -> dados
TOKENS_VALIDOS = {}

TOKEN_EXPIRATION_SECONDS = 300  # 5 minutos


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()

    if not dados or "username" not in dados or "password" not in dados:
        return jsonify({"erro": "username e password são obrigatórios"}), 400

    username = dados["username"]
    password = dados["password"]

    if USUARIOS_VALIDOS.get(username) != password:
        print(f"[AUTH SERVICE] Falha no login para '{username}'.")
        return jsonify({"erro": "Credenciais inválidas"}), 401

    token = secrets.token_hex(32)

    TOKENS_VALIDOS[token] = {
        "username": username,
        "created_at": time.time()
    }

    print(f"[AUTH SERVICE] Login bem-sucedido para '{username}'.")

    return jsonify({
        "mensagem": "Login realizado com sucesso",
        "token": token,
        "usuario": username,
        "expires_in": TOKEN_EXPIRATION_SECONDS
    }), 200


@app.route("/validate", methods=["GET"])
def validate():
    token = request.args.get("token")

    if not token:
        return jsonify({
            "valid": False,
            "motivo": "Token não fornecido"
        }), 400

    inicio = time.time()

    token_data = TOKENS_VALIDOS.get(token)

    if not token_data:
        duracao_ms = round((time.time() - inicio) * 1000, 4)

        print(f"[AUTH SERVICE] Token inválido. Tempo: {duracao_ms}ms")

        return jsonify({
            "valid": False,
            "motivo": "Token inválido"
        }), 401

    idade_token = time.time() - token_data["created_at"]

    if idade_token > TOKEN_EXPIRATION_SECONDS:
        del TOKENS_VALIDOS[token]

        return jsonify({
            "valid": False,
            "motivo": "Token expirado"
        }), 401

    duracao_ms = round((time.time() - inicio) * 1000, 4)

    print(
        f"[AUTH SERVICE] Token válido para '{token_data['username']}'. "
        f"Validação levou {duracao_ms}ms"
    )

    return jsonify({
        "valid": True,
        "username": token_data["username"]
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "Auth Service online",
        "porta": 5001
    }), 200


if __name__ == "__main__":
    print("[AUTH SERVICE] Iniciando na porta 5001...")
    app.run(host="0.0.0.0", port=5001)
