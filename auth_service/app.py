from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Credenciais fixas e tokens válidos (simulação simples)
USUARIOS_VALIDOS = {
    "admin": "senha123",
    "usuario": "12345"
}

TOKENS_VALIDOS = set()


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()

    if not dados or "username" not in dados or "password" not in dados:
        return jsonify({"erro": "username e password são obrigatórios"}), 400

    username = dados["username"]
    password = dados["password"]

    if USUARIOS_VALIDOS.get(username) == password:
        token = f"token-valido-{username}-abc"
        TOKENS_VALIDOS.add(token)
        print(f"[AUTH SERVICE] Login bem-sucedido para '{username}'. Token gerado: {token}")
        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "token": token,
            "usuario": username
        }), 200
    else:
        print(f"[AUTH SERVICE] Falha no login para '{username}'.")
        return jsonify({"erro": "Credenciais inválidas"}), 401


@app.route("/validate", methods=["GET"])
def validate():
    token = request.args.get("token")

    if not token:
        return jsonify({"valid": False, "motivo": "Token não fornecido"}), 400

    inicio = time.time()

    if token in TOKENS_VALIDOS:
        duracao_ms = round((time.time() - inicio) * 1000, 4)
        print(f"[AUTH SERVICE] Token válido: '{token}'. Validação levou {duracao_ms}ms")
        return jsonify({"valid": True, "token": token}), 200
    else:
        duracao_ms = round((time.time() - inicio) * 1000, 4)
        print(f"[AUTH SERVICE] Token INVÁLIDO: '{token}'. Validação levou {duracao_ms}ms")
        return jsonify({"valid": False, "motivo": "Token inválido ou expirado"}), 401


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Auth Service online", "porta": 5001}), 200


if __name__ == "__main__":
    print("[AUTH SERVICE] Iniciando na porta 5001...")
    app.run(host="0.0.0.0", port=5001, debug=True)
