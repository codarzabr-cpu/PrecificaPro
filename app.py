from flask import Flask, render_template, request, redirect, url_for, flash
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

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

app.secret_key = "precifica-pro-chave-local"


@app.route("/diagnostico")
def diagnostico():
    return {
        "flask": "funcionando",
        "templates": (BASE_DIR / "templates").exists(),
        "dashboard": (BASE_DIR / "templates" / "dashboard.html").exists(),
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

@app.route("/")
def dashboard():
    dados = carregar_dados()
    orcamentos = [
        o for o in dados["orcamentos"]
        if isinstance(o, dict)
    ]

    faturamento = sum(
        numero(o.get("valor_total", 0))
        for o in orcamentos
    )

    despesas_total = sum(
        numero(v)
        for v in dados["despesas"].values()
    )

    aprovados = sum(
        1 for o in orcamentos
        if o.get("status") == "Aprovado"
    )

    pendentes = sum(
        1 for o in orcamentos
        if o.get("status") == "Pendente"
    )

    meses = {}

    for orc in orcamentos:
        try:
            data = datetime.strptime(
                str(orc["data"]),
                "%Y-%m-%d"
            )

            chave = data.strftime("%m/%Y")

            meses[chave] = (
                meses.get(chave, 0)
                + numero(orc.get("valor_total", 0))
            )

        except (ValueError, KeyError, TypeError):
            logger.warning(
                "Orçamento ignorado no gráfico por data inválida: %r",
                orc
            )

    grafico = sorted(meses.items())[-6:]

    return render_template(
        "dashboard.html",
        dados=dados,
        faturamento=faturamento,
        despesas=despesas_total,
        lucro=faturamento - despesas_total,
        aprovados=aprovados,
        pendentes=pendentes,
        recentes=list(reversed(orcamentos[-5:])),
        grafico_labels=[x[0] for x in grafico],
        grafico_valores=[round(x[1], 2) for x in grafico]
    )


# =========================================================
# DESPESAS
# =========================================================

@app.route("/despesas", methods=["GET", "POST"])
def despesas():
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
    dados = carregar_dados()
    orcamentos = [
        o for o in dados["orcamentos"]
        if isinstance(o, dict)
    ]

    total = sum(
        numero(o.get("valor_total", 0))
        for o in orcamentos
    )

    aprovados = [
        o for o in orcamentos
        if o.get("status") == "Aprovado"
    ]

    receita_aprovada = sum(
        numero(o.get("valor_total", 0))
        for o in aprovados
    )

    despesas_total = sum(
        numero(v)
        for v in dados["despesas"].values()
    )

    return render_template(
        "relatorios.html",
        quantidade=len(orcamentos),
        total=total,
        receita_aprovada=receita_aprovada,
        despesas_total=despesas_total,
        lucro_estimado=receita_aprovada - despesas_total,
        orcamentos_lista=list(reversed(orcamentos))
    )


# =========================================================
# CONFIGURAÇÕES
# =========================================================

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
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
