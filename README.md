# Precifica Pro 5 — Clarity

Aplicativo local de precificação com visual claro, detalhamento de custos e orçamento, e assistente configurável com IA.

## Abrir no Windows

1. Extraia o ZIP para uma pasta.
2. Instale Python 3.10 ou superior, com “Add Python to PATH”.
3. Execute `iniciar_precifica_pro.bat`.
4. Acesse `http://127.0.0.1:5000`.

A interface já vem compilada. Na primeira execução, o programa instala o Flask. Não é necessário instalar Node para usar.

Os registros são mantidos em `%LOCALAPPDATA%\PrecificaPro\dados_precificacao.json`. Eles continuam no mesmo lugar ao atualizar o programa. Feche o app antes de substituir a pasta; faça uma cópia desse JSON antes da atualização.

## Assistente

O modo local continua disponível sem internet e responde às consultas básicas dos registros. Para conversar sobre outros assuntos, abra **Configurações → Inteligência artificial**, selecione OpenAI ou Groq, cole uma chave criada no provedor escolhido e escolha um modelo disponível nessa conta. Os padrões sugeridos são `gpt-4.1-mini` para OpenAI e `openai/gpt-oss-20b` para Groq. A disponibilidade e eventuais limites dependem da conta do provedor. A utilização da API pode gerar cobrança separada; ela não está incluída por ter ChatGPT Plus.

A chave é digitada na tela do aplicativo e fica apenas na memória do processo Python. Ela não é escrita em arquivos, registros de log ou armazenamento do navegador. Fechar o app remove a chave; será preciso configurá-la novamente na próxima execução. Como alternativa, defina `OPENAI_API_KEY` ou `GROQ_API_KEY` no Windows antes de abrir o programa. Para definir modelos por ambiente, use `PRECIFICA_OPENAI_MODEL` ou `PRECIFICA_GROQ_MODEL`. O histórico do chat fica na memória da tela e some ao recarregá-la.

No modo IA, a mensagem e até 20 mensagens anteriores da conversa são enviadas à API. O resumo numérico do negócio só acompanha a solicitação se você marcar a opção no chat. Ele inclui horas, impostos, markup, valor/hora, total mensal de despesas e contagens/valores de propostas por status; não inclui nomes, e-mails ou telefones. O aplicativo usa a Responses API com `store: false` ao escolher OpenAI. Para Groq, usa a API padrão Chat Completions, mantendo o histórico de conversa no próprio aplicativo. Isso impede a recuperação da resposta pelo identificador da API, mas não altera os controles de retenção aplicáveis à conta do cliente. A IA não acessa registros sem o resumo autorizado, não modifica cadastros e não pesquisa na internet.

## O que mudou

- Logo PP própria no aplicativo e ícone atualizados.
- Tema claro com superfícies suaves e verde; responsivo no computador e celular.
- Composição detalhada da precificação: custos, impostos, lucro, preço de equilíbrio, margem sobre venda e comparação de três cenários.
- Detalhes por proposta, com os valores efetivamente registrados. Orçamentos antigos mostram quando faltam dados de composição.
- Assistente Pro com modo local e modo IA de propósito geral, conversa com histórico temporário, respostas formatadas, cópia, exportação e controle explícito do contexto do negócio.

## Fórmula de preço

Custo do projeto = (despesas mensais ÷ horas produtivas mensais × horas do projeto) + custos extras.

Preço = custo do projeto × (1 + markup / 100) ÷ (1 − impostos / 100).

Lucro estimado = preço − impostos sobre o preço − custo do projeto. Markup sobre custo difere de margem sobre venda. Propostas aprovadas não comprovam recebimentos; o total histórico de propostas não deve ser apresentado como lucro do mesmo período das despesas mensais.

## Desenvolvimento

Backend: `python -m pip install -r requirements.txt` e `python app.py`.

Frontend (Node.js 20+): na pasta `frontend`, execute `npm ci` e `npm run dev`. Após alterações, compile com `npm run build` para atualizar a interface servida pelo Flask.

## Base de conhecimento do assistente

O arquivo `data/base_conhecimento.xlsx` é a base editável do Assistente Pro. Ele vem com 100 exemplos em português, na aba `Conversas`, e uma aba `Como usar`.

- O app procura até quatro exemplos relacionados a cada pergunta e usa a resposta como referência.
- O modo IA envia os exemplos recuperados junto da mensagem à API configurada. O modo local pode responder diretamente com o exemplo mais relacionado.
- Para adicionar uma regra ou resposta, acrescente uma linha na aba `Conversas`; mantenha os cinco cabeçalhos e defina `Ativa` como `Sim`.
- Defina `Ativa` como `Não` para tirar uma linha da consulta. As alterações são lidas na próxima pergunta.
- A planilha fornece contexto; não altera nem retreina os pesos do modelo. Não inclua dados pessoais ou segredos de clientes.
