# Precifica Pro

Sistema web local para organizar clientes, registrar despesas fixas,
calcular o valor-hora de trabalho, criar orçamentos e acompanhar
resultados financeiros.

O aplicativo foi desenvolvido em Python com Flask e utiliza páginas
HTML, CSS e JavaScript. Ele roda no próprio computador e é acessado pelo
navegador; não precisa de hospedagem para uso local.

## Sumário

-   [1. O que o sistema faz](#1-o-que-o-sistema-faz)
-   [2. Requisitos](#2-requisitos)
-   [3. Como executar a versão pronta no
    Windows](#3-como-executar-a-versão-pronta-no-windows)
-   [4. Como executar pelo
    código-fonte](#4-como-executar-pelo-código-fonte)
-   [5. Primeiro uso recomendado](#5-primeiro-uso-recomendado)
-   [6. Como usar cada área](#6-como-usar-cada-área)
-   [7. Como o cálculo do valor-hora
    funciona](#7-como-o-cálculo-do-valor-hora-funciona)
-   [8. Onde os dados ficam salvos](#8-onde-os-dados-ficam-salvos)
-   [9. Backup e restauração](#9-backup-e-restauração)
-   [10. Solução de problemas](#10-solução-de-problemas)
-   [11. Estrutura do projeto](#11-estrutura-do-projeto)
-   [12. Observações e limitações](#12-observações-e-limitações)

## 1. O que o sistema faz

O Precifica Pro reúne as seguintes funcionalidades:

-   **Dashboard:** visão geral dos orçamentos, despesas, valores totais
    e propostas recentes.
-   **Clientes:** cadastro e exclusão de clientes com nome, e-mail e
    telefone.
-   **Despesas fixas:** cadastro e remoção de custos mensais.
-   **Orçamentos:** criação de propostas com cliente, serviço e horas
    estimadas; o valor total é calculado automaticamente.
-   **Status dos orçamentos:** acompanhamento como `Pendente`,
    `Aprovado` ou `Recusado`.
-   **Relatórios:** consulta dos valores propostos, receita aprovada,
    despesas cadastradas e resultado estimado; permite imprimir a
    página.
-   **Configurações:** ajuste das horas disponíveis por mês, margem de
    lucro e percentual estimado de impostos.

## 2. Requisitos

### Para usar a versão pronta

-   Windows compatível com o executável fornecido.
-   Os arquivos da aplicação extraídos do ZIP para uma pasta local.
-   Um navegador, como Microsoft Edge, Google Chrome ou Firefox.

A versão empacotada inclui o runtime e as bibliotecas necessárias. Em
condições normais, não é necessário instalar Python ou Flask para
executar o `.exe`.

### Para executar pelo código-fonte

-   Python instalado.
-   `pip`, que normalmente acompanha a instalação do Python.
-   Navegador web.
-   Dependência Python: Flask 3.x (`Flask>=3.0,<4.0`).

## 3. Como executar a versão pronta no Windows

1.  Extraia o arquivo `trabalho_final.zip`. Não execute o aplicativo
    diretamente de dentro do ZIP.

2.  Abra a pasta extraída `trabalho_final`.

3.  Para a versão empacotada com seus arquivos internos, abra
    `dist\MeuSistema\` e execute `MeuSistema.exe`.

4.  Se o Windows exibir um aviso de segurança, confirme a origem do
    arquivo antes de permitir a execução.

5.  Aguarde alguns segundos. O programa inicia um servidor local e tenta
    abrir o navegador automaticamente.

6.  Se o navegador não abrir sozinho, digite este endereço na barra de
    endereços:

    `http://127.0.0.1:5000`

7.  Mantenha a janela do programa aberta enquanto estiver usando o
    sistema. Fechar o processo encerra o servidor local.

**Importante:** o endereço `127.0.0.1` é local, ou seja, o sistema foi
configurado para uso no próprio computador. Não é um site publicado na
internet.

O ZIP contém mais de uma compilação/executável de versões ou nomes
diferentes. Para uma execução mais previsível, comece por
`dist\MeuSistema\MeuSistema.exe`, que vem acompanhado da pasta
`_internal`. Evite mover o `.exe` para fora da pasta dele, pois os
arquivos internos precisam permanecer junto da aplicação.

## 4. Como executar pelo código-fonte

Use este modo se quiser estudar ou alterar o projeto.

1.  Instale o Python.

2.  Abra o terminal (PowerShell ou Prompt de Comando) dentro da pasta
    `trabalho_final`, onde está o arquivo `app.py`.

3.  (Recomendado) Crie e ative um ambiente virtual:

    ``` powershell
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    Se a política do PowerShell impedir a ativação, você pode executar o
    Python do ambiente virtual diretamente ou usar o Prompt de Comando.

4.  Instale as dependências:

    ``` powershell
    py -m pip install -r requirements.txt
    ```

5.  Inicie a aplicação:

    ``` powershell
    py app.py
    ```

6.  Abra `http://127.0.0.1:5000` no navegador.

Para encerrar, volte ao terminal e pressione `Ctrl+C`. Se estiver usando
o executável, feche a janela/processo do aplicativo.

### Verificação de funcionamento

O endereço abaixo apresenta um diagnóstico simples da aplicação:

`http://127.0.0.1:5000/diagnostico`

Quando tudo estiver funcionando, a resposta deve indicar que o Flask
está funcionando e informar se os templates e o arquivo de dados foram
encontrados. O campo de existência dos dados pode ser verdadeiro depois
da primeira inicialização, pois o aplicativo cria o arquivo
automaticamente.

## 5. Primeiro uso recomendado

Para obter cálculos coerentes, configure o sistema antes de criar os
primeiros orçamentos:

1.  Abra **Configurações** e informe quantas horas por mês você
    realmente pretende vender.
2.  Defina a margem de lucro desejada e a estimativa de impostos.
3.  Entre em **Despesas fixas** e cadastre os custos mensais que o
    negócio precisa cobrir.
4.  Entre em **Clientes** e cadastre os clientes que deseja manter
    organizados.
5.  Entre em **Orçamentos** e crie uma proposta informando cliente,
    serviço e horas estimadas.
6.  Atualize o status da proposta conforme a resposta do cliente.
7.  Consulte **Dashboard** e **Relatórios** para acompanhar os
    registros.

Os valores que aparecem no ZIP podem conter dados de exemplo ou testes.
Antes de usar o sistema com dados reais, revise os cadastros e as
despesas já existentes.

## 6. Como usar cada área

### 6.1 Dashboard

É a página inicial. Apresenta indicadores calculados a partir dos dados
registrados, incluindo:

-   soma dos valores de todos os orçamentos;
-   total das despesas fixas cadastradas;
-   diferença entre o valor total orçado e as despesas;
-   quantidade de orçamentos aprovados e pendentes;
-   propostas recentes;
-   gráfico com os valores dos orçamentos por mês.

**Atenção:** o valor total dos orçamentos não significa necessariamente
dinheiro recebido. Para analisar propostas aceitas, consulte a receita
aprovada na página Relatórios.

### 6.2 Clientes

1.  Acesse **Clientes**.
2.  Preencha o nome do cliente, que é obrigatório.
3.  Preencha e-mail e telefone, se desejar.
4.  Salve o cadastro.
5.  Para remover um registro, use o botão de exclusão correspondente e
    confirme quando solicitado.

Ao criar um orçamento, o campo de cliente sugere nomes já cadastrados.
Também é possível digitar um nome diretamente no orçamento; o formulário
não exige que o nome exista previamente no cadastro.

### 6.3 Despesas fixas

Use esta área para registrar os custos mensais do negócio, por exemplo:

-   internet;
-   aluguel;
-   energia;
-   assinaturas de software;
-   ferramentas de trabalho;
-   contabilidade;
-   outros custos recorrentes.

Para cadastrar, informe uma descrição e um valor mensal maior que zero.
O sistema soma os itens para calcular o total mensal. Para remover um
item, use o botão de exclusão na linha correspondente.

**Dica:** cadastre cada despesa uma única vez. O sistema usa a soma de
todas elas no cálculo do valor-hora.

### 6.4 Orçamentos

Para criar uma proposta:

1.  Acesse **Orçamentos**.
2.  Informe ou selecione o cliente.
3.  Descreva o serviço ou projeto.
4.  Informe a quantidade de horas estimadas, maior que zero.
5.  Clique em **Gerar orçamento**.

O sistema registra a data, o valor-hora usado naquele momento e o total
calculado. O status inicial é `Pendente`.

Para atualizar uma proposta, altere o seletor de status na própria
linha. As opções disponíveis são:

-   **Pendente:** aguardando resposta.
-   **Aprovado:** cliente aceitou a proposta.
-   **Recusado:** cliente não aceitou a proposta.

O sistema permite excluir um orçamento. A exclusão remove o registro do
arquivo de dados; não há uma lixeira ou função de desfazer.

**Importante:** o valor-hora do orçamento é guardado no momento da
criação. Se você mudar as configurações ou as despesas posteriormente,
os orçamentos antigos não são recalculados automaticamente. Novas
propostas usarão o novo valor-hora.

### 6.5 Relatórios

A página reúne:

-   **Valor total proposto:** soma de todos os orçamentos registrados,
    independentemente do status.
-   **Receita aprovada:** soma dos orçamentos marcados como `Aprovado`.
-   **Despesas mensais:** soma das despesas fixas cadastradas
    atualmente.
-   **Resultado estimado:** receita aprovada menos as despesas mensais
    atuais.

Use o campo de pesquisa para localizar propostas. O botão de impressão
abre a janela de impressão do navegador; nela, você pode selecionar uma
impressora ou, se disponível, salvar como PDF.

O resultado é uma estimativa gerencial simples, não um demonstrativo
contábil. Ele não confirma pagamentos efetivamente recebidos e compara
valores de propostas com as despesas mensais atuais.

### 6.6 Configurações

Os campos disponíveis são:

-   **Horas disponíveis por mês:** número de horas que você pretende
    dedicar a trabalhos remunerados. Precisa ser maior que zero.
-   **Margem de lucro (%):** percentual aplicado ao custo da hora. Por
    exemplo, `30` significa 30%.
-   **Impostos estimados (%):** percentual estimado da receita destinado
    a impostos. Deve ser maior ou igual a zero e menor que 100%.

Clique em **Salvar configurações** para aplicar os parâmetros aos
próximos orçamentos. A margem aceita valores a partir de zero; o
formulário da interface sugere até 1000%. Para impostos, o limite é
inferior a 100%.

## 7. Como o cálculo do valor-hora funciona

O sistema utiliza esta fórmula:

``` text
Custo por hora = Total das despesas mensais / Horas disponíveis por mês

Valor-hora = Custo por hora × (1 + Margem de lucro / 100)
             / (1 - Impostos / 100)

Valor do orçamento = Horas estimadas × Valor-hora
```

### Exemplo ilustrativo

Considere:

-   despesas mensais: R\$ 4.000,00;
-   horas disponíveis por mês: 100;
-   margem de lucro: 30%;
-   impostos estimados: 10%.

Então:

``` text
Custo por hora = 4.000 / 100 = R$ 40,00

Valor-hora = 40 × 1,30 / 0,90
           ≈ R$ 57,78

Orçamento de 20 horas = 20 × 57,78
                      ≈ R$ 1.155,56
```

O sistema calcula com valores numéricos e apresenta o dinheiro no
formato brasileiro (`R$ 1.234,56`). Pequenas diferenças de centavos
podem ocorrer devido ao arredondamento.

**Observação:** trata-se do método de precificação implementado no
programa. Ele não substitui uma análise financeira ou tributária
profissional e não inclui automaticamente custos variáveis, comissões,
inadimplência, férias ou outras categorias que não tenham sido
cadastradas como despesas.

## 8. Onde os dados ficam salvos

O aplicativo salva os dados fora da pasta do projeto, em uma pasta de
usuário do Windows:

`%LOCALAPPDATA%\PrecificaPro\dados_precificacao.json`

Normalmente, esse caminho corresponde a algo semelhante a:

`C:\Users\SEU_USUARIO\AppData\Local\PrecificaPro\dados_precificacao.json`

O arquivo contém configurações, despesas, clientes e orçamentos. Os
erros registrados pelo programa ficam em:

`%LOCALAPPDATA%\PrecificaPro\precifica_pro_erros.log`

A pasta pode ser aberta pelo Explorador de Arquivos digitando
`%LOCALAPPDATA%\PrecificaPro` na barra de endereço.

**Atenção ao arquivo `dados_precificacao.json` que aparece na raiz do
projeto:** o código da aplicação usa o caminho em
`%LOCALAPPDATA%\PrecificaPro` para ler e salvar os dados. Portanto,
editar apenas o JSON que acompanha o projeto não altera necessariamente
os dados que o programa está usando.

## 9. Backup e restauração

### Fazer backup

1.  Encerre o aplicativo antes de copiar o arquivo.
2.  Abra `%LOCALAPPDATA%\PrecificaPro`.
3.  Copie `dados_precificacao.json` para uma pasta segura, unidade
    externa ou armazenamento confiável.
4.  Dê à cópia um nome que identifique a data, por exemplo
    `backup-2026-10-29.json`.

### Restaurar um backup

1.  Encerre o aplicativo.
2.  Faça uma cópia de segurança do arquivo atual, se ele existir.
3.  Copie o backup desejado para `%LOCALAPPDATA%\PrecificaPro`.
4.  Renomeie-o para `dados_precificacao.json`, substituindo o arquivo
    atual somente depois de confirmar que o backup é o correto.
5.  Inicie novamente o aplicativo.

O arquivo precisa ser um JSON válido e conter a estrutura esperada pelo
programa. Não edite nem substitua o arquivo enquanto o aplicativo
estiver em execução, pois alterações podem ser sobrescritas.

## 10. Solução de problemas

### O navegador não abriu

Abra manualmente `http://127.0.0.1:5000`. Confirme que o aplicativo
ainda está em execução.

### A página não pode ser acessada

-   Confirme que o processo do aplicativo não foi encerrado.
-   Verifique se a porta `5000` já está sendo usada por outro programa.
-   Tente encerrar outras instâncias do Precifica Pro antes de iniciar
    novamente.
-   Consulte o arquivo `precifica_pro_erros.log`.

### O Windows informa que faltam arquivos ou o aplicativo não inicia

Execute o `.exe` dentro da pasta completa `dist\MeuSistema`, mantendo
`_internal` junto dele. Extraia novamente o ZIP se algum arquivo tiver
sido removido ou colocado em quarentena. Só permita a execução se
confiar na origem do arquivo.

### Erro ao executar `py app.py`

-   Confirme que o terminal está na pasta onde `app.py` está localizado.
-   Verifique a instalação do Python com `py --version`.
-   Instale as dependências com `py -m pip install -r requirements.txt`.
-   Confirme que o Flask foi instalado no mesmo ambiente Python usado
    para iniciar o programa.

### Os dados desapareceram ou não correspondem aos dados do ZIP

Verifique `%LOCALAPPDATA%\PrecificaPro\dados_precificacao.json`. Esse é
o arquivo usado pelo aplicativo. O JSON na raiz do projeto pode ser
apenas um arquivo de exemplo ou de distribuição.

### A tela apresenta erro interno

Consulte o terminal em que o aplicativo foi iniciado e o arquivo de log
em `%LOCALAPPDATA%\PrecificaPro\precifica_pro_erros.log`. Ao solicitar
suporte, compartilhe a mensagem de erro relevante, mas remova e-mails,
telefones ou outros dados pessoais que não sejam necessários.

### A porta 5000 está ocupada

Feche outra instância do sistema ou outro programa que esteja usando a
porta. O aplicativo está configurado para iniciar em `127.0.0.1:5000`;
não é necessário expô-lo à rede para uso local.

## 11. Estrutura do projeto

Os principais arquivos e pastas são:

``` text
trabalho_final/
├── app.py                    # Aplicação Flask, rotas e regras de negócio
├── requirements.txt          # Dependências Python
├── dados_precificacao.json   # JSON presente na distribuição; não é o caminho ativo padrão
├── templates/
│   ├── base.html             # Estrutura compartilhada das páginas
│   ├── dashboard.html        # Painel inicial
│   ├── clientes.html         # Cadastro/listagem de clientes
│   ├── despesas.html         # Controle de despesas
│   ├── orcamentos.html       # Criação e acompanhamento de propostas
│   ├── relatorios.html       # Indicadores e impressão
│   └── configuracoes.html    # Parâmetros de cálculo
├── static/
│   └── css/
│       ├── style.css         # Estilos da interface
│       └── js/
│           └── app.js        # Comportamentos da interface
├── dist/
│   └── MeuSistema/
│       ├── MeuSistema.exe    # Executável empacotado
│       └── _internal/        # Bibliotecas e recursos necessários
└── build/                    # Arquivos intermediários da compilação
```

A pasta `build` contém arquivos gerados durante o empacotamento e
normalmente não é necessária para a utilização cotidiana. Para executar
a versão distribuída, mantenha os arquivos da pasta `dist\MeuSistema`
juntos.

## 12. Observações e limitações

-   A aplicação foi configurada para funcionar localmente, em
    `127.0.0.1`, na porta `5000`.
-   Os dados são mantidos em um arquivo JSON local, não em um banco de
    dados.
-   O aplicativo não implementa login ou controle de usuários. Use-o
    apenas em um computador e ambiente confiáveis.
-   Não há sincronização automática entre computadores nem backup
    automático.
-   Excluir clientes, despesas ou orçamentos remove os registros
    correspondentes; faça backup antes de alterações importantes.
-   A impressão é feita pelo navegador, não por um gerador dedicado de
    PDF.
-   Os relatórios são estimativas baseadas nos registros existentes. Não
    representam necessariamente fluxo de caixa, pagamentos recebidos ou
    lucro contábil.
-   Proteja o arquivo de dados, pois ele pode conter informações de
    clientes e valores comerciais.
