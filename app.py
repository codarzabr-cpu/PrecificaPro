from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from pathlib import Path
from datetime import datetime
from werkzeug.exceptions import HTTPException
import json
import uuid
import os
import sys
import threading
import webbrowser
import logging
import math
from assistente import responder
import ia
import os
import smtplib
from email.message import EmailMessage
from html import escape

# =========================================================
# CAMINHOS
# =========================================================

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DADOS_DIR = Path(
    os.environ.get("LOCALAPPDATA", str(Path.home()))
) / "PrecificaPro"

DADOS_DIR.mkdir(parents=True, exist_ok=True)

ARQUIVO_DADOS = DADOS_DIR / "dados_precificacao.json"
ARQUIVO_LOG = DADOS_DIR / "precifica_pro_erros.log"


# =========================================================
# LOGS
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
    ],
    force=True
)

logger = logging.getLogger("precifica_pro")


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__, template_folder=None, static_folder=None)

app.secret_key = "precifica-pro-chave-local"


@app.route("/diagnostico")
def diagnostico():
    return {
        "flask": "funcionando",
        "frontend_react_compilado": (BASE_DIR / "frontend" / "dist" / "index.html").exists(),
        "api": "disponivel",
        "dados_existem": ARQUIVO_DADOS.exists()
    }
# =========================================================
# DADOS PADRÃO
# =========================================================

PADRAO = {
    "configuracao": {
        "horas_mensais": 160,
        "margem_lucro": 30,
        "impostos": 6
    },
    "despesas": {},
    "clientes": [],
    "orcamentos": []
}


def copiar_padrao():
    return json.loads(json.dumps(PADRAO))


def normalizar_dados(dados):
    if not isinstance(dados, dict):
        dados = {}

    dados_padrao = copiar_padrao()

    configuracao = dados.get("configuracao", {})

    if not isinstance(configuracao, dict):
        configuracao = {}

    for chave, valor in dados_padrao["configuracao"].items():
        configuracao.setdefault(chave, valor)

    dados["configuracao"] = configuracao

    if not isinstance(dados.get("despesas"), dict):
        dados["despesas"] = {}

    if not isinstance(dados.get("clientes"), list):
        dados["clientes"] = []

    if not isinstance(dados.get("orcamentos"), list):
        dados["orcamentos"] = []

    return dados


# =========================================================
# CARREGAMENTO E SALVAMENTO
# =========================================================

def carregar_dados():
    if not ARQUIVO_DADOS.exists():
        dados = copiar_padrao()
        salvar_dados(dados)
        return dados

    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return normalizar_dados(dados)

    except (json.JSONDecodeError, OSError):
        logger.exception("Erro ao carregar o arquivo JSON de dados.")
        return copiar_padrao()


def salvar_dados(dados):
    dados = normalizar_dados(dados)
    temporario = ARQUIVO_DADOS.with_suffix(".tmp")

    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            indent=4,
            ensure_ascii=False
        )

    temporario.replace(ARQUIVO_DADOS)


# =========================================================
# UTILITÁRIOS
# =========================================================

def numero(valor, padrao=0.0):
    try:
        if isinstance(valor, str):
            valor = valor.strip().replace(",", ".")

        resultado = float(valor)

        if not math.isfinite(resultado):
            return float(padrao)

        return resultado

    except (ValueError, TypeError, OverflowError):
        return float(padrao)


def dinheiro(valor):
    valor = numero(valor)

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


app.jinja_env.filters["dinheiro"] = dinheiro


def calcular_valor_hora(dados):
    dados = normalizar_dados(dados)
    config = dados["configuracao"]

    horas = numero(config.get("horas_mensais", 0))
    margem = numero(config.get("margem_lucro", 0)) / 100
    impostos = numero(config.get("impostos", 0)) / 100

    despesas_total = sum(
        numero(valor)
        for valor in dados["despesas"].values()
    )

    if horas <= 0 or impostos < 0 or impostos >= 1:
        return 0.0

    custo_hora = despesas_total / horas

    return custo_hora * (1 + margem) / (1 - impostos)


@app.context_processor
def dados_globais():
    dados = carregar_dados()

    return {
        "valor_hora": calcular_valor_hora(dados),
        "ano_atual": datetime.now().year
    }


# =========================================================
# TRATAMENTO DE ERROS
# =========================================================

@app.errorhandler(Exception)
def registrar_erro(erro):
    if isinstance(erro, HTTPException):
        return erro

    logger.exception("Erro interno durante uma requisição Flask.")

    return (
        "Ocorreu um erro interno no Precifica Pro. "
        "Consulte o terminal ou o arquivo de log: "
        + str(ARQUIVO_LOG),
        500
    )


# =========================================================
# DASHBOARD
# =========================================================

def servir_react():
    """Entrega a SPA React e impede fallback para telas Jinja antigas."""
    frontend_dist = BASE_DIR / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    if not index_file.exists():
        return (
            "A interface React ainda não foi compilada. Execute "
            "iniciar_precifica_pro.bat na pasta raiz do projeto.",
            503,
            {"Content-Type": "text/plain; charset=utf-8"}
        )
    return send_from_directory(frontend_dist, "index.html")


@app.route("/")
def dashboard():
    return servir_react()


# =========================================================
# DESPESAS
# =========================================================

@app.route("/despesas", methods=["GET", "POST"])
def despesas():
    if request.method == "GET":
        return servir_react()

    dados = carregar_dados()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        try:
            valor = numero(request.form.get("valor", "0"))

            if not nome or valor <= 0:
                raise ValueError

            dados["despesas"][nome] = round(valor, 2)
            salvar_dados(dados)

            flash("Despesa cadastrada com sucesso.", "success")

        except ValueError:
            flash(
                "Informe uma descrição e um valor maior que zero.",
                "error"
            )

        return redirect(url_for("despesas"))

    return render_template(
        "despesas.html",
        despesas_lista=dados["despesas"].items(),
        total=sum(
            numero(v)
            for v in dados["despesas"].values()
        )
    )


@app.post("/despesas/excluir/<path:nome>")
def excluir_despesa(nome):
    dados = carregar_dados()

    if nome in dados["despesas"]:
        del dados["despesas"][nome]
        salvar_dados(dados)
        flash("Despesa removida.", "success")

    return redirect(url_for("despesas"))


# =========================================================
# CLIENTES
# =========================================================

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "GET":
        return servir_react()

    dados = carregar_dados()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()

        if not nome:
            flash("O nome do cliente é obrigatório.", "error")
        else:
            dados["clientes"].append({
                "id": str(uuid.uuid4()),
                "nome": nome,
                "email": email,
                "telefone": telefone
            })

            salvar_dados(dados)
            flash("Cliente cadastrado.", "success")

        return redirect(url_for("clientes"))

    return render_template(
        "clientes.html",
        clientes_lista=dados["clientes"]
    )


@app.post("/clientes/excluir/<cliente_id>")
def excluir_cliente(cliente_id):
    dados = carregar_dados()

    dados["clientes"] = [
        cliente
        for cliente in dados["clientes"]
        if not isinstance(cliente, dict)
        or cliente.get("id") != cliente_id
    ]

    salvar_dados(dados)
    flash("Cliente removido.", "success")

    return redirect(url_for("clientes"))

def enviar_email_orcamento(orcamento, email_cliente):
    """Envia um orçamento por SMTP usando credenciais do ambiente."""

    remetente = os.getenv("PRECIFICA_EMAIL")
    senha = os.getenv("PRECIFICA_EMAIL_SENHA")
    nome_empresa = os.getenv("PRECIFICA_EMPRESA", "Precifica Pro")
    servidor = os.getenv("PRECIFICA_SMTP_SERVIDOR", "smtp.gmail.com")
    porta = int(os.getenv("PRECIFICA_SMTP_PORTA", "587"))

    if not remetente or not senha:
        raise RuntimeError(
            "Configure PRECIFICA_EMAIL e PRECIFICA_EMAIL_SENHA."
        )

    if not email_cliente or "@" not in email_cliente:
        raise ValueError("O cliente não possui um e-mail válido cadastrado.")

    servico = str(orcamento.get("servico", "Serviço"))
    horas = numero(orcamento.get("horas", 0))
    valor_hora = numero(orcamento.get("valor_hora", 0))
    valor_total = numero(orcamento.get("valor_total", 0))

    mensagem = EmailMessage()
    mensagem["Subject"] = f"Orçamento #{str(orcamento.get('id', ''))[:8]} - {nome_empresa}"
    mensagem["From"] = f"{nome_empresa} <{remetente}>"
    mensagem["To"] = email_cliente

    mensagem.set_content(
        f"""Olá!

Segue o resumo do orçamento preparado para você.

Serviço: {servico}
Resumo: {servico}
Quantidade estimada: {horas:g} horas
Valor por hora: R$ {valor_hora:.2f}
Valor total do orçamento: R$ {valor_total:.2f}

Este orçamento está sujeito à confirmação entre as partes.

Atenciosamente,
{nome_empresa}
"""
    )

    with smtplib.SMTP(servidor, porta, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(remetente, senha)
        smtp.send_message(mensagem)



# =========================================================
# ORÇAMENTOS
# =========================================================

@app.route("/orcamentos", methods=["GET", "POST"])
def orcamentos():
    if request.method == "GET":
        return servir_react()

    dados = carregar_dados()

    if request.method == "POST": 
        cliente = request.form.get("cliente", "").strip()
        servico = request.form.get("servico", "").strip()

        try:
            horas = numero(request.form.get("horas", "0"))
            valor_hora_atual = calcular_valor_hora(dados)

            if not cliente or not servico or horas <= 0:
                raise ValueError

            orcamento = {
                "id": str(uuid.uuid4()),
                "cliente": cliente,
                "servico": servico,
                "horas": horas,
                "valor_hora": round(valor_hora_atual, 2),
                "valor_total": round(
                    horas * valor_hora_atual, 2
                ),
                "status": "Pendente",
                "data": datetime.now().strftime("%Y-%m-%d")
            }

            dados["orcamentos"].append(orcamento)
            salvar_dados(dados)

            flash("Orçamento criado com sucesso.", "success")

        except ValueError:
            flash(
                "Preencha os campos e informe uma quantidade de horas válida.",
                "error"
            )

        return redirect(url_for("orcamentos"))

    return render_template(
        "orcamentos.html",
        orcamentos_lista=[
            o for o in reversed(dados["orcamentos"])
            if isinstance(o, dict)
        ],
        clientes_lista=dados["clientes"]
    )


@app.post("/orcamentos/status/<orcamento_id>")
def atualizar_status(orcamento_id):
    dados = carregar_dados()
    status = request.form.get("status")

    permitidos = {"Pendente", "Aprovado", "Recusado"}

    if status in permitidos:
        for orc in dados["orcamentos"]:
            if isinstance(orc, dict) and orc.get("id") == orcamento_id:
                orc["status"] = status
                salvar_dados(dados)
                flash("Status atualizado.", "success")
                break

    return redirect(url_for("orcamentos"))


@app.post("/orcamentos/excluir/<orcamento_id>")
def excluir_orcamento(orcamento_id):
    dados = carregar_dados()

    dados["orcamentos"] = [
        orc for orc in dados["orcamentos"]
        if not isinstance(orc, dict)
        or orc.get("id") != orcamento_id
    ]

    salvar_dados(dados)
    flash("Orçamento removido.", "success")

    return redirect(url_for("orcamentos"))


# =========================================================
# RELATÓRIOS
# =========================================================

@app.route("/relatorios")
def relatorios():
    return servir_react()


# =========================================================
# CONFIGURAÇÕES
# =========================================================

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if request.method == "GET":
        return servir_react()

    dados = carregar_dados()

    if request.method == "POST":
        try:
            horas = numero(
                request.form.get("horas_mensais", "160")
            )

            margem = numero(
                request.form.get("margem_lucro", "30")
            )

            impostos = numero(
                request.form.get("impostos", "6")
            )

            if (
                horas <= 0
                or margem < 0
                or not 0 <= impostos < 100
            ):
                raise ValueError

            dados["configuracao"] = {
                "horas_mensais": horas,
                "margem_lucro": margem,
                "impostos": impostos
            }

            salvar_dados(dados)
            flash("Configurações salvas.", "success")

        except ValueError:
            flash("Confira os valores informados.", "error")

        return redirect(url_for("configuracoes"))

    return render_template(
        "configuracoes.html",
        config=dados["configuracao"]
    )


@app.get("/precificacao")
def pagina_precificacao():
    return servir_react()


# =========================================================
# API REST PARA O FRONTEND REACT
# =========================================================

@app.get("/api/state")
def api_state():
    dados = carregar_dados()
    orcamentos = [o for o in dados["orcamentos"] if isinstance(o, dict)]
    despesas_total = sum(numero(v) for v in dados["despesas"].values())
    faturamento = sum(numero(o.get("valor_total", 0)) for o in orcamentos if o.get("status") == "Aprovado")
    total_orcado = sum(numero(o.get("valor_total", 0)) for o in orcamentos)
    aprovados = sum(1 for o in orcamentos if o.get("status") == "Aprovado")
    pendentes = sum(1 for o in orcamentos if o.get("status") == "Pendente")
    recusados = sum(1 for o in orcamentos if o.get("status") == "Recusado")
    meses = {}
    for item in orcamentos:
        try:
            dt = datetime.strptime(str(item.get("data", "")), "%Y-%m-%d")
            key = dt.strftime("%b/%y")
            meses[key] = meses.get(key, 0) + numero(item.get("valor_total", 0))
        except (ValueError, TypeError):
            pass
    chart = [{"month": k, "value": round(v, 2)} for k, v in sorted(meses.items(), key=lambda x: datetime.strptime(x[0], "%b/%y"))[-6:]]
    return jsonify({
        "configuracao": dados["configuracao"],
        "despesas": dados["despesas"],
        "clientes": dados["clientes"],
        "orcamentos": list(reversed(orcamentos)),
        "metricas": {"faturamento": round(faturamento, 2), "total_orcado": round(total_orcado, 2), "despesas": round(despesas_total, 2), "lucro": round(faturamento-despesas_total, 2), "aprovados": aprovados, "pendentes": pendentes, "recusados": recusados, "taxa_aprovacao": round((aprovados / len(orcamentos) * 100) if orcamentos else 0, 1), "valor_hora": round(calcular_valor_hora(dados), 2)},
        "grafico": chart
    })

@app.put("/api/configuracoes")
def api_configuracoes():
    payload = request.get_json(silent=True) or {}
    horas = numero(payload.get("horas_mensais"), -1)
    margem = numero(payload.get("margem_lucro"), -1)
    impostos = numero(payload.get("impostos"), -1)
    if horas <= 0 or margem < 0 or not 0 <= impostos < 100:
        return jsonify({"erro": "Confira horas, margem e impostos."}), 400
    dados = carregar_dados()
    dados["configuracao"] = {"horas_mensais": horas, "margem_lucro": margem, "impostos": impostos}
    salvar_dados(dados)
    return jsonify({"mensagem": "Configurações atualizadas."})

@app.post("/api/despesas")
def api_criar_despesa():
    payload = request.get_json(silent=True) or {}
    nome = str(payload.get("nome", "")).strip()
    valor = numero(payload.get("valor"), 0)
    if not nome or valor <= 0:
        return jsonify({"erro": "Informe descrição e valor maior que zero."}), 400
    dados = carregar_dados()
    dados["despesas"][nome] = round(valor, 2)
    salvar_dados(dados)
    return jsonify({"mensagem": "Despesa salva."}), 201

@app.delete("/api/despesas/<path:nome>")
def api_excluir_despesa(nome):
    dados = carregar_dados()
    if nome not in dados["despesas"]:
        return jsonify({"erro": "Despesa não encontrada."}), 404
    del dados["despesas"][nome]
    salvar_dados(dados)
    return jsonify({"mensagem": "Despesa removida."})

@app.post("/api/clientes")
def api_criar_cliente():
    payload = request.get_json(silent=True) or {}
    nome = str(payload.get("nome", "")).strip()
    if not nome:
        return jsonify({"erro": "O nome é obrigatório."}), 400
    dados = carregar_dados()
    cliente = {"id": str(uuid.uuid4()), "nome": nome, "email": str(payload.get("email", "")).strip(), "telefone": str(payload.get("telefone", "")).strip()}
    dados["clientes"].append(cliente)
    salvar_dados(dados)
    return jsonify(cliente), 201

@app.delete("/api/clientes/<cliente_id>")
def api_excluir_cliente(cliente_id):
    dados = carregar_dados()
    antes = len(dados["clientes"])
    dados["clientes"] = [c for c in dados["clientes"] if c.get("id") != cliente_id]
    if len(dados["clientes"]) == antes:
        return jsonify({"erro": "Cliente não encontrado."}), 404
    salvar_dados(dados)
    return jsonify({"mensagem": "Cliente removido."})

@app.post("/api/orcamentos")
def api_criar_orcamento():
    payload = request.get_json(silent=True) or {}
    cliente = str(payload.get("cliente", "")).strip()
    servico = str(payload.get("servico", "")).strip()
    horas = numero(payload.get("horas"), 0)
    dados = carregar_dados()
    extras = numero(payload.get("custos_extras", 0), -1)
    margem = numero(payload.get("margem_lucro", dados["configuracao"]["margem_lucro"]), -1)
    imposto = numero(dados["configuracao"]["impostos"]) / 100
    horas_mes = numero(dados["configuracao"]["horas_mensais"])
    if not cliente or not servico or horas <= 0 or extras < 0 or margem < 0 or horas_mes <= 0 or not 0 <= imposto < 1:
        return jsonify({"erro": "Confira cliente, serviço, horas, custos extras e parâmetros."}), 400
    custo_hora = sum(numero(v) for v in dados["despesas"].values()) / horas_mes
    custo = custo_hora * horas + extras
    valor_hora_atual = custo_hora * (1 + margem/100) / (1-imposto)
    valor_total = custo * (1 + margem/100) / (1-imposto)
    if not math.isfinite(valor_total) or valor_total <= 0:
        return jsonify({"erro": "Cadastre despesas ou custos extras válidos para formar o preço."}), 400
    orcamento = {
        "id": str(uuid.uuid4()), "cliente": cliente, "servico": servico,
        "horas": horas, "valor_hora": round(valor_hora_atual, 2),
        "custos_extras": extras, "margem_lucro": margem,
        "impostos": round(imposto * 100, 4), "custo_total": round(custo, 2),
        "valor_total": round(valor_total, 2),
        "lucro_estimado": round(valor_total * (1-imposto) - custo, 2),
        "status": "Pendente", "data": datetime.now().strftime("%Y-%m-%d")
    }
    dados["orcamentos"].append(orcamento)
    salvar_dados(dados)
    return jsonify(orcamento), 201

@app.patch("/api/orcamentos/<orcamento_id>")
def api_atualizar_orcamento(orcamento_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in {"Pendente", "Aprovado", "Recusado"}:
        return jsonify({"erro": "Status inválido."}), 400
    dados = carregar_dados()
    for item in dados["orcamentos"]:
        if item.get("id") == orcamento_id:
            item["status"] = status
            salvar_dados(dados)
            return jsonify(item)
    return jsonify({"erro": "Orçamento não encontrado."}), 404

@app.delete("/api/orcamentos/<orcamento_id>")
def api_excluir_orcamento(orcamento_id):
    dados = carregar_dados()
    antes = len(dados["orcamentos"])
    dados["orcamentos"] = [o for o in dados["orcamentos"] if o.get("id") != orcamento_id]
    if len(dados["orcamentos"]) == antes:
        return jsonify({"erro": "Orçamento não encontrado."}), 404
    salvar_dados(dados)
    return jsonify({"mensagem": "Orçamento removido."})

@app.get("/assistente")
def pagina_assistente():
    return servir_react()


@app.get("/api/ia/status")
def api_ia_status():
    return jsonify(ia.status())


@app.post("/api/ia/config")
def api_ia_config():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"erro": "Envie uma configuração válida."}), 400
    try:
        return jsonify(ia.configure(payload))
    except ValueError as error:
        return jsonify({"erro": str(error)}), 400


@app.post("/api/chat")
def api_chat():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
        return jsonify({"erro": "Envie uma mensagem de texto."}), 400
    message = payload["message"].strip()
    if not message or len(message) > 6000:
        return jsonify({"erro": "A mensagem deve ter entre 1 e 6.000 caracteres."}), 400
    mode = payload.get('mode', 'local')
    if mode not in ('local', 'ai'):
        return jsonify({"erro": "Modo de conversa inválido."}), 400
    if not isinstance(payload.get('include_business', False), bool):
        return jsonify({"erro": "Opção de contexto inválida."}), 400
    history = payload.get('history', [])
    if not isinstance(history, list) or len(history) > 20:
        return jsonify({"erro": "O histórico deve conter até 20 mensagens."}), 400
    for item in history:
        if (not isinstance(item, dict) or item.get('role') not in ('user', 'assistant')
                or not isinstance(item.get('content'), str) or not 1 <= len(item['content']) <= 12000):
            return jsonify({"erro": "Histórico de conversa inválido."}), 400
    if sum(len(x['content']) for x in history) > 32000:
        return jsonify({"erro": "Histórico muito longo. Inicie uma nova conversa."}), 400
    if mode == 'ai':
        context = None
        if payload.get('include_business'):
            dados = carregar_dados()
            context = ia.summary(dados, calcular_valor_hora(dados))
        knowledge = ia.retrieve_knowledge(message)
        try:
            return jsonify(ia.answer(message, history, context, knowledge))
        except ia.AIError as error:
            return jsonify({"erro": str(error)}), error.code
    dados = carregar_dados()
    local_result = responder(message, dados, calcular_valor_hora(dados), history)
    if local_result is not None:
        reply, actions = local_result
        return jsonify({"reply": reply, "actions": actions, "mode": "local"})
    knowledge = ia.retrieve_knowledge(message, limit=1)
    if knowledge:
        return jsonify({"reply": knowledge[0]["answer"], "actions": [], "mode": "local", "knowledge_count": 1})
    return jsonify({"reply": "Ainda não entendi o que você quer fazer. Pode me contar um pouco mais? No modo local, consigo consultar orçamentos, despesas e simular preços. Para conversar sobre assuntos gerais, ative IA no seletor do chat.", "actions": [], "mode": "local"})


@app.get("/assets/<path:filename>")
def react_assets(filename):
    return send_from_directory(BASE_DIR / "frontend" / "dist" / "assets", filename)


# =========================================================
# INICIALIZAÇÃO
# =========================================================

if __name__ == "__main__":
    logger.info("Iniciando Precifica Pro")
    logger.info("Pasta do aplicativo: %s", BASE_DIR)
    logger.info("Pasta de dados: %s", DADOS_DIR)
    logger.info("Arquivo de log: %s", ARQUIVO_LOG)
    logger.info("Templates: %s", BASE_DIR / "templates")
    logger.info("Arquivos estáticos: %s", BASE_DIR / "static")

    def abrir_navegador():
        webbrowser.open("http://127.0.0.1:5000")

    threading.Timer(1.5, abrir_navegador).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )
