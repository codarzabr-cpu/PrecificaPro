"""Assistente local determinístico. Nenhum dado é enviado a serviços externos."""
import re
import unicodedata
from datetime import date, timedelta


def brl(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def quote_date(quote):
    try:
        return date.fromisoformat(str(quote.get('data', ''))[:10])
    except (TypeError, ValueError):
        return None


def responder(message, dados, valor_hora, history=None):
    text = unicodedata.normalize('NFKD', message.lower()).encode('ascii', 'ignore').decode()
    history = history or []
    previous_user = next((item.get('content', '') for item in reversed(history)
                          if isinstance(item, dict) and item.get('role') == 'user'), '')
    previous_assistant = next((item.get('content', '') for item in reversed(history)
                               if isinstance(item, dict) and item.get('role') == 'assistant'), '')
    follow_up = bool(re.search(r'\b(pode|poderia|consegue|manda|envia|envie|me passa|me mostre|quero ver|por favor|isso|sim|mais|detalhes|detalhar|completo)\b', text))
    if follow_up and previous_user:
        previous_text = unicodedata.normalize('NFKD', previous_user.lower()).encode('ascii', 'ignore').decode()
        if any(word in previous_text for word in ('relatorio semanal', 'resumo semanal', 'da semana', 'esta semana')):
            text = 'relatorio semanal'
        elif any(word in previous_text for word in ('resumo', 'panorama', 'como esta o negocio')):
            text = 'resumo hoje' if re.search(r'\b(hoje|hj|dia de hoje)\b', previous_text) else 'resumo negocio'
        elif any(word in previous_text for word in ('orcamento', 'proposta', 'quanto cobrar', 'preco')):
            text = previous_text
    if re.fullmatch(r'\s*\d+(?:[.,]\d+)?\s*', message) and re.search(r'quantas horas|horas estimadas', previous_assistant.lower()):
        text = message.strip() + ' horas'
    config = dados['configuracao']
    despesas = dados['despesas']
    total = sum(float(v) for v in despesas.values())
    quotes = [q for q in dados['orcamentos'] if isinstance(q, dict)]
    actions = []
    if re.fullmatch(r'(oi|ola|opa|bom dia|boa tarde|boa noite|e ai|tudo bem)[!.? ]*', text):
        return ('Oi! Posso te ajudar com o Precifica Pro. Você pode pedir um resumo de hoje, consultar orçamentos, '
                'ver despesas ou simular um preço; se faltar alguma informação, eu pergunto.'), []
    if any(w in text for w in ['resumo', 'panorama', 'faturamento', 'receita', 'resultado']) and re.search(r'\b(hoje|hj|dia de hoje|de hoje)\b', text):
        today = date.today()
        today_iso = today.isoformat()
        day_quotes = [q for q in quotes if str(q.get('data', ''))[:10] == today_iso]
        approved_today = [q for q in day_quotes if q.get('status') == 'Aprovado']
        pending_today = [q for q in day_quotes if q.get('status') == 'Pendente']
        declined_today = [q for q in day_quotes if q.get('status') == 'Recusado']
        reply = f'Resumo de hoje ({today.strftime("%d/%m/%Y")}):\n\n'
        if day_quotes:
            reply += (f'• Orçamentos cadastrados: {len(day_quotes)}\n'
                      f'• Aprovados: {len(approved_today)} — {brl(sum(float(q.get("valor_total", 0)) for q in approved_today))}\n'
                      f'• Pendentes: {len(pending_today)} — {brl(sum(float(q.get("valor_total", 0)) for q in pending_today))}\n'
                      f'• Recusados: {len(declined_today)} — {brl(sum(float(q.get("valor_total", 0)) for q in declined_today))}')
        else:
            reply += '• Não encontrei orçamentos cadastrados para hoje.'
        reply += ('\n\nO app registra a data dos orçamentos, mas não acompanha recebimentos ou despesas por dia. '
                  'Então não consigo afirmar quanto entrou no caixa hoje. Quer que eu mostre também o panorama geral?')
        actions = [{'page': 'quotes', 'label': 'Ver orçamentos de hoje'}]
        return reply, actions
    if (re.search(r'\b(semana|semanal)\b', text)
            and any(word in text for word in ['relatorio', 'resumo', 'panorama', 'resultado', 'vendas', 'propostas', 'atividade'])):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        comparison_start = week_start - timedelta(days=7)
        comparison_end = comparison_start + timedelta(days=today.weekday())
        week_quotes = [q for q in quotes if (quote_date(q) is not None and week_start <= quote_date(q) <= today)]
        previous_quotes = [q for q in quotes if (quote_date(q) is not None and comparison_start <= quote_date(q) <= comparison_end)]
        value = lambda items: sum(float(q.get('valor_total', 0) or 0) for q in items)
        approved_week = [q for q in week_quotes if q.get('status') == 'Aprovado']
        pending_week = [q for q in week_quotes if q.get('status') == 'Pendente']
        declined_week = [q for q in week_quotes if q.get('status') == 'Recusado']
        open_pending = [q for q in quotes if q.get('status') == 'Pendente']
        report_end_label = today.strftime('%d/%m/%Y')
        reply = (f'Relatório semanal — {week_start.strftime("%d/%m/%Y")} a {report_end_label} '
                 f'(segunda-feira até hoje)\n\n')
        reply += (f'ATIVIDADE\n• Orçamentos criados: {len(week_quotes)}\n'
                  f'• Valor total proposto: {brl(value(week_quotes))}\n'
                  f'• Ticket médio: {brl(value(week_quotes) / len(week_quotes) if week_quotes else 0)}\n\n')
        approval_rate = len(approved_week) / len(week_quotes) * 100 if week_quotes else 0
        reply += (f'STATUS DOS ORÇAMENTOS DA SEMANA\n'
                  f'• Aprovados: {len(approved_week)} — {brl(value(approved_week))}\n'
                  f'• Pendentes: {len(pending_week)} — {brl(value(pending_week))}\n'
                  f'• Recusados: {len(declined_week)} — {brl(value(declined_week))}\n'
                  f'• Taxa aprovada: {approval_rate:.1f}% dos orçamentos criados no período\n\n')
        if previous_quotes:
            prev_value = value(previous_quotes)
            if prev_value:
                change = (value(week_quotes) - prev_value) / prev_value * 100
                change_text = f'{change:+.1f}% no valor proposto'
            else:
                change_text = 'a semana passada teve propostas sem valor registrado'
            reply += (f'COMPARAÇÃO\n• Mesmo período da semana passada: {len(previous_quotes)} orçamentos, '
                      f'{brl(prev_value)}\n• Variação: {change_text}\n\n')
        else:
            reply += 'COMPARAÇÃO\n• Não há orçamentos registrados no período equivalente da semana passada.\n\n'
        daily_lines = []
        for offset in range((today - week_start).days + 1):
            day = week_start + timedelta(days=offset)
            day_items = [q for q in week_quotes if quote_date(q) == day]
            daily_lines.append(f'• {day.strftime("%d/%m")}: {len(day_items)} orçamento(s) — {brl(value(day_items))}')
        reply += 'MOVIMENTO POR DIA\n' + ('\n'.join(daily_lines) if daily_lines else '• Sem registros.') + '\n\n'
        top_quotes = sorted(week_quotes, key=lambda q: float(q.get('valor_total', 0) or 0), reverse=True)[:3]
        if top_quotes:
            reply += 'MAIORES ORÇAMENTOS DA SEMANA\n' + '\n'.join(
                f'• {q.get("cliente") or "Cliente"} — {q.get("servico") or "Serviço"}: {brl(float(q.get("valor_total", 0) or 0))} ({q.get("status", "Sem status")})'
                for q in top_quotes
            ) + '\n\n'
        reply += f'PENDÊNCIAS ATUAIS\n• {len(open_pending)} orçamento(s) pendente(s) — {brl(value(open_pending))}'
        pending_top = sorted(open_pending, key=lambda q: float(q.get('valor_total', 0) or 0), reverse=True)[:3]
        if pending_top:
            reply += '\n' + '\n'.join(
                f'• {q.get("cliente") or "Cliente"} — {q.get("servico") or "Serviço"}: {brl(float(q.get("valor_total", 0) or 0))}'
                for q in pending_top
            )
        reply += ('\n\nLimite dos dados: o app acompanha datas e status dos orçamentos, mas não registra recebimentos '
                  'nem despesas diárias. Portanto, valores aprovados são propostas aprovadas, não confirmação de dinheiro recebido.')
        actions = [{'page': 'quotes', 'label': 'Abrir orçamentos'}, {'page': 'reports', 'label': 'Ver relatórios'}]
        return reply, actions
    hours = re.search(r'(?<![\d.,-])(\d+(?:[.,]\d+)?)\s*(?:horas?\b|h\b)', text)
    if re.search(r'-\s*\d+(?:[.,]\d+)?\s*(?:horas?\b|h\b)', text):
        return 'Informe uma quantidade de horas maior que zero, como “Simular 10 horas”.', []
    if hours:
        n = float(hours.group(1).replace(',', '.'))
        if n <= 0 or n > 100000:
            return 'Informe uma quantidade de horas entre 0 e 100.000, maior que zero.', []
        # Não ignorar números extras: o simulador permite revisar todos os parâmetros.
        remaining = text[:hours.start()] + text[hours.end():]
        if re.search(r'\d', remaining):
            return ('Para incluir custos extras, descontos ou outro percentual, abra o simulador e revise os campos. '
                    'No chat, calculo apenas as horas com os parâmetros cadastrados.'), [{'page': 'pricing', 'label': 'Abrir simulador'}]
        if valor_hora <= 0:
            return 'Ainda não há uma base de custos para calcular seu preço. Cadastre as despesas mensais e revise as horas produtivas primeiro.', [{'page': 'expenses', 'label': 'Cadastrar despesas'}]
        price = n * valor_hora
        tax = price * float(config['impostos']) / 100
        base = total / float(config['horas_mensais']) * n
        reply = (f'Simulação para {n:g} horas, sem custos extras:\n\n'
                 f'Preço sugerido: {brl(price)}\n'
                 f'Custo proporcional: {brl(base)}\n'
                 f'Impostos estimados: {brl(tax)}\n'
                 f'Lucro estimado após impostos: {brl(price-base-tax)}\n\n'
                 f'Usei {config["margem_lucro"]}% de acréscimo sobre o custo e {config["impostos"]}% de impostos. '
                 'É uma simulação; nenhum orçamento foi criado.')
        actions = [{'page': 'pricing', 'label': 'Revisar e criar orçamento'}]
    elif (any(w in text for w in ['orcamento', 'proposta', 'precificar', 'precificacao', 'quanto cobrar'])
          and any(w in text for w in ['fazer', 'montar', 'criar', 'calcular', 'preciso', 'quero', 'simular'])):
        return ('Claro, eu calculo com você. Qual serviço ou projeto quer orçar e quantas horas estima? '
                'Se houver materiais ou outros custos extras, informe o valor aproximado; posso usar o seu valor/hora cadastrado.'), []
    elif any(w in text for w in ['margem', 'markup', 'calculo', 'valor hora', 'valor/hora', 'minha hora']):
        reply = (f'Seu valor por hora é {brl(valor_hora)}.\n\n'
                 f'Cálculo: despesas mensais ({brl(total)}) ÷ horas produtivas ({config["horas_mensais"]}) '
                 f'× (1 + {config["margem_lucro"]}% de acréscimo) ÷ (1 − {config["impostos"]}% de impostos).\n\n'
                 'O percentual configurado é um acréscimo sobre o custo (markup), não a margem sobre o preço de venda. '
                 'Por exemplo: custo 100 + 30% = preço 130, com margem de 23,08% antes dos impostos.')
        actions = [{'page': 'settings', 'label': 'Revisar parâmetros'}]
    elif any(w in text for w in ['despesa', 'custo', 'gasto']):
        rows = sorted(despesas.items(), key=lambda x: float(x[1]), reverse=True)[:5]
        reply = 'Suas despesas mensais somam ' + brl(total) + '.\n\n'
        reply += '\n'.join(f'• {name}: {brl(float(v))} ({float(v)/total*100:.1f}% do total)' for name, v in rows) if total else 'Nenhuma despesa cadastrada. Comece pelos custos recorrentes do negócio.'
        actions = [{'page': 'expenses', 'label': 'Ver despesas'}]
    elif any(w in text for w in ['pendente', 'negociacao', 'orcamento', 'proposta']):
        pending = [q for q in quotes if q.get('status') == 'Pendente']
        reply = f'Você tem {len(pending)} propostas pendentes, no total de {brl(sum(float(q.get("valor_total", 0)) for q in pending))}.\n\n'
        reply += '\n'.join(f'• {q.get("cliente", "Cliente")}: {brl(float(q.get("valor_total", 0)))} — {q.get("servico", "Serviço")}' for q in pending[-5:])
        if len(pending) > 5:
            reply += '\nMostrando as 5 últimas. Veja todas na página de orçamentos.'
        if not pending:
            reply += 'Nenhuma proposta aguardando resposta no momento.'
        actions = [{'page': 'quotes', 'label': 'Abrir orçamentos'}]
    elif 'cliente' in text:
        reply = f'Você tem {len(dados["clientes"])} clientes cadastrados. Acesse Clientes para buscar contatos ou adicionar um novo cadastro.'
        actions = [{'page': 'clients', 'label': 'Ver clientes'}]
    elif any(w in text for w in ['resumo', 'negocio', 'faturamento', 'receita', 'resultado']):
        approved = [q for q in quotes if q.get('status') == 'Aprovado']
        revenue = sum(float(q.get('valor_total', 0)) for q in approved)
        reply = (f'Aqui está seu panorama:\n\n• {len(dados["clientes"])} clientes\n'
                 f'• {len(quotes)} propostas no histórico\n• {len(approved)} aprovadas, somando {brl(revenue)}\n'
                 f'• Despesas mensais: {brl(total)}\n• Valor/hora: {brl(valor_hora)}\n\n'
                 'As propostas aprovadas são do histórico completo e não comprovam recebimento. '
                 'As despesas são uma base mensal; não subtraio esses períodos diferentes para calcular lucro.')
        actions = [{'page': 'reports', 'label': 'Ver relatórios'}]
    else:
        return None
    return reply, actions
