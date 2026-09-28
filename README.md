# LexiFlow AI

## Visão geral

O **LexiFlow AI** é um MVP de IA Generativa desenvolvido para apoiar a **triagem e a consulta de documentos corporativos** da empresa fictícia **NovaLex Serviços Corporativos**.

A solução foi desenhada para lidar principalmente com os seguintes tipos documentais:

- contratos de prestação de serviços
- políticas internas
- acordos de confidencialidade (NDAs)
- aditivos contratuais

O sistema permite que o usuário envie documentos em **PDF** ou **TXT**, extraia o texto, gere um **resumo executivo**, realize **extração estruturada de campos relevantes** e faça **perguntas e respostas com base em evidência**, utilizando uma abordagem de **RAG (Retrieval-Augmented Generation)**.

Além disso, o projeto reconhece documentos **fora do escopo** do MVP e trata esses casos de forma segura, evitando consultas indevidas em documentos não suportados.

---

## Objetivo do projeto

O objetivo do LexiFlow AI é reduzir o esforço manual envolvido na leitura inicial de documentos corporativos, aumentando:

- a eficiência operacional
- a consistência da triagem documental
- a reutilização do conhecimento extraído
- a velocidade de resposta para consultas internas

A solução **não substitui análise humana especializada**. Seu papel é atuar como um **assistente inteligente de apoio à análise documental inicial**.

---

## Problema de negócio

Em muitos contextos corporativos, contratos, políticas, aditivos e documentos relacionados precisam ser lidos manualmente para identificar informações como:

- vigência
- multa
- cláusulas de confidencialidade
- menção a dados pessoais
- obrigações principais
- alterações contratuais

Esse processo consome tempo, gera retrabalho e dificulta a padronização da triagem inicial. O LexiFlow AI foi criado para atacar essa dor, automatizando a leitura inicial e organizando as informações de forma mais estruturada.

---

## Escopo do MVP

O MVP foi calibrado para os seguintes tipos documentais:

- `contrato_prestacao_servicos`
- `politica_interna`
- `nda`
- `aditivo_contratual`

Quando o documento enviado não se enquadra claramente em nenhuma dessas categorias, o sistema o classifica como:

- `fora_escopo`

Nesses casos, o documento é salvo no histórico, mas a funcionalidade de perguntas e respostas é bloqueada.

---

## Principais funcionalidades

### 1. Processamento de documentos
- upload de arquivos PDF e TXT
- extração de texto
- pré-processamento do conteúdo

### 2. Análise com IA
- classificação documental
- geração de resumo executivo
- extração estruturada de campos relevantes
- identificação de alertas

### 3. Persistência e histórico
- armazenamento dos documentos processados em SQLite
- visualização posterior de resumo, texto e análise estruturada

### 4. Recuperação semântica e consulta
- indexação vetorial com Chroma
- recuperação de trechos relevantes
- perguntas e respostas com base em contexto recuperado

### 5. Tratamento de documentos fora do escopo
- classificação como `fora_escopo`
- exibição de aviso na interface
- bloqueio da funcionalidade de perguntas

---

## Arquitetura resumida

O fluxo principal da solução é:

1. upload do documento
2. extração do texto
3. pré-processamento
4. análise com LLM
5. complementação por regras de negócio
6. persistência em banco local
7. indexação vetorial
8. consulta posterior com RAG

A arquitetura combina:

- **Streamlit** para interface
- **SQLite** para persistência estruturada
- **Chroma** para indexação vetorial e recuperação semântica
- **OpenAI API** para classificação, resumo, extração e respostas geradas por LLM

---

## Stack tecnológica

O projeto foi construído com:

- **Python**
- **Streamlit**
- **SQLite**
- **Chroma**
- **OpenAI API**
- **python-dotenv**
- **pypdf**
- **reportlab** (geração do relatório executivo em PDF)
- **Pydantic** (validação da saída do LLM)
- **pytest / unittest** (testes automatizados)
- **bcrypt** (hash de senhas)
- **pandas** (tabelas/gráficos da Visão geral)
- **cryptography** (criptografia em repouso do texto dos documentos)

---

## Estrutura do projeto

A estrutura principal esperada do projeto é semelhante a esta:

```text
lexiflow-ai/
├── app/
│   └── streamlit_app.py
├── services/
│   ├── schemas.py            # validação/normalização da saída do LLM
│   ├── document_classifier.py  # classificação por palavras-chave (cross-check do LLM)
│   ├── grounding.py           # validação das evidências citadas pelo LLM
│   └── ...
├── rag/
├── data/
├── sample_docs/
├── tests/                     # suíte de testes unitários
├── eval/                      # gabarito estruturado + harness de avaliação fim a fim
│   ├── gabarito.json
│   ├── run_eval.py
│   └── results/
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## Requisitos

Para executar o projeto localmente, você precisa de:

- Python 3.12+
- Git
- acesso à internet
- chave válida da OpenAI API

> Observação: o projeto foi desenvolvido e testado localmente em Python 3.14.4.

---

## Instalação e execução local

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd lexiflow-ai
```

### 2. Criar o ambiente virtual

No Windows / PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 4. Criar o arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env` com este conteúdo:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Use o arquivo `.env.example` como referência.

### 5. Rodar o aplicativo

```bash
python -m streamlit run app/streamlit_app.py
```

No Windows, você também pode usar:

```powershell
python -m streamlit run app\streamlit_app.py
```

---

## Configuração da API

O projeto utiliza a **OpenAI API** para:

- classificação documental
- resumo executivo
- extração estruturada
- perguntas e respostas com RAG

A variável necessária é:

```env
OPENAI_API_KEY=sua_chave_aqui
```

### Importante
- não suba o arquivo `.env` para o GitHub
- a chave real deve ficar apenas no ambiente local ou nos secrets do deploy
- o arquivo `.env.example` serve apenas como modelo de configuração

---

## Autenticação e perfis de acesso

O sistema exige login antes de qualquer uso. Existem dois perfis:

- **basic**: processa documentos e só visualiza/consulta o que ele mesmo processou.
- **admin**: visualiza documentos de todos os usuários, cria novos usuários e é o único que enxerga o botão **Reindexar documentos salvos** na barra lateral.

Na primeira execução (banco `data/lexiflow.db` vazio), o sistema cria automaticamente um usuário `admin` com senha `admin123` (ou o valor da variável de ambiente `LEXIFLOW_DEFAULT_ADMIN_PASSWORD`, se definida).

> ⚠️ **Importante:** troque essa senha (criando um novo usuário admin e desativando/renomeando o padrão, ou definindo `LEXIFLOW_DEFAULT_ADMIN_PASSWORD` antes da primeira execução) antes de expor a aplicação publicamente — por exemplo, antes de publicar no Streamlit Community Cloud. Senhas são sempre armazenadas como hash bcrypt, nunca em texto plano.

Novos usuários são criados pelo próprio admin, na barra lateral, em **Administração → Criar novo usuário**.

Documentos processados antes da autenticação existir (histórico legado) são automaticamente atribuídos ao primeiro usuário admin criado, para não desaparecerem do histórico.

### Sessão persistente

Dar refresh na página, ou abrir a mesma URL em outra aba, não desloga mais o
usuário. `st.session_state` do Streamlit é por conexão de navegador e não
sobrevive a um reload — para contornar isso, o login gera um token de
sessão (`services/auth_service.py`, `create_session`/`validate_session`,
256 bits aleatórios, tabela `sessions` no SQLite com expiração) e o
propaga via `st.query_params` (aparece como `?session=...` na URL). O token é
validado contra o banco no primeiro carregamento da página **e** periodicamente
a cada `SESSION_REVALIDATION_INTERVAL_SECONDS` (5 min por padrão) enquanto a
aba permanece aberta — sem essa revalidação periódica, uma sessão revogada
(logout em outro lugar, TTL expirado, usuário excluído) continuaria sendo
aceita indefinidamente numa aba já aberta, já que `st.session_state`
sobrevive a reruns dentro da mesma conexão. No logout, a sessão é apagada do
banco e o parâmetro removido da URL — reabrir um link antigo depois do
logout não funciona mais.

Trade-off deliberado: o token trafega na URL, não num cookie `httpOnly` —
mais simples e 100% nativo do Streamlit (sem componente JS de terceiros,
que se mostrou pouco confiável em teste), mas com um perfil de exposição
diferente de um cookie (visível na barra de endereço, histórico do
navegador). Mitigado por: token opaco (não revela nada sozinho), expiração
em `SESSION_TTL_HOURS` (12h por padrão) e revogação no logout. Razoável
para uma ferramenta interna; não seria a escolha certa para uma aplicação
pública sensível a fraude.

---

## Proteção de dados pessoais

O sistema já identificava quando um documento menciona dados pessoais
(`personal_data_mentions`), mas identificar não é o mesmo que proteger.
Duas camadas foram adicionadas para isso:

**1. Criptografia em repouso.** O texto integral do documento
(`document_text`) e a análise estruturada (`full_analysis_json`) — que pode
conter `personal_data_details` citado verbatim — ficam cifrados no SQLite
(`services/encryption_service.py`, `Fernet`/AES simétrico). As demais
colunas (resumo, tipo, alertas) continuam em texto plano, para permitir
listagem/dashboard sem precisar decifrar em massa.

A chave vem de `LEXIFLOW_ENCRYPTION_KEY` (recomendado em produção — defina
nos secrets do Streamlit Community Cloud) ou, se ausente, é gerada
automaticamente na primeira execução e salva em `data/.encryption_key`
(fora do controle de versão). **Se essa chave for perdida, os documentos já
salvos ficam permanentemente ilegíveis** — em produção, prefira sempre a
variável de ambiente a depender do arquivo local, especialmente em hospedagem
com filesystem efêmero. Registros salvos antes desta camada existir
continuam legíveis normalmente (fallback automático para texto plano).

**2. Exclusão permanente (direito de eliminação).** Antes não havia nenhuma
forma de remover um documento já processado. Agora, tanto o dono do
documento quanto um admin podem excluí-lo permanentemente na tela de
Consultar histórico (com confirmação em duas etapas) — remove o registro do
SQLite e os chunks correspondentes no Chroma.

**Limitação conhecida:** os chunks indexados no Chroma para busca semântica
(`data/chroma_db/`) continuam em texto plano — criptografá-los quebraria a
busca por similaridade, que precisa comparar embeddings calculados sobre o
texto real. A exclusão remove os chunks do documento excluído, mas enquanto
um documento existe, seu conteúdo é pesquisável em texto plano nesse índice
vetorial. Isso é documentado aqui em vez de omitido.

---

## Como usar o sistema

### Tela 1 — Visão geral
Dashboard executivo com:
- cards de métricas (total de documentos, ativos, vencendo em 90 dias, vencidos)
- gráfico de distribuição por tipo documental
- tabela de documentos vencendo nos próximos 90 dias, ordenada por data

NDAs e políticas internas sem data de fim explícita no documento são classificados como "sem vigência aplicável", não como "vencido".

### Tela 2 — Processar documento
Nesta tela, o usuário pode:

1. enviar um documento PDF ou TXT
2. visualizar o texto extraído
3. clicar em **Processar documento**
4. visualizar:
   - tipo do documento
   - resumo executivo
   - alertas
   - análise estruturada completa

### Tela 3 — Consultar histórico
Nesta tela, o usuário pode:

1. selecionar um documento já processado
2. visualizar:
   - resumo
   - alertas
   - análise estruturada
   - texto completo
3. fazer perguntas sobre o documento, caso ele esteja dentro do escopo do MVP

---

## Campos estruturados extraídos

A análise estruturada pode incluir campos como:

- `document_type`
- `summary`
- `parties`
- `object`
- `start_date`
- `end_date`
- `term_duration`
- `renewal_clause`
- `termination_clause`
- `penalty_clause`
- `confidentiality_clause`
- `personal_data_mentions`
- `personal_data_details`
- `key_obligations`
- `risk_alerts`
- `source_snippets`

Além do que o LLM extrai, `full_analysis` também carrega metadados
adicionados pelo próprio sistema (não pelo modelo): `field_confidence` (ver
"Confiança por campo extraído") e `prompt_version` / `model` (ver
"Engenharia de prompt e uso da API", a seguir).

---

## Engenharia de prompt e uso da API (`services/llm_service.py`)

Três decisões deliberadas na forma como o sistema conversa com o modelo:

**1. Structured outputs, não parsing de string.** A chamada de análise usa
`client.responses.parse(text_format=LLMAnalysisResult, ...)`, passando
diretamente o modelo Pydantic de `services/schemas.py` como o schema
esperado. A API garante que a saída bate com o schema (inclusive
`document_type` como enum das categorias suportadas) antes mesmo de chegar
no código — eliminou o parsing manual de markdown/JSON que existia antes
(`_safe_json_loads`, removido) e a classe de falhas que vinha com ele.

**2. `temperature=0`.** Classificar e extrair campos de um documento é uma
tarefa que deveria ser determinística — o mesmo documento não deveria virar
uma análise diferente a cada execução. As duas chamadas ao modelo (análise e
perguntas e respostas) fixam `temperature=0` em vez de usar o padrão.

**3. Delimitação explícita entre dado e instrução.** O texto do documento
(e, na consulta, o contexto recuperado pelo RAG) é conteúdo de terceiros —
um usuário poderia enviar um arquivo contendo texto que tenta se passar por
uma instrução para o modelo ("ignore as regras anteriores e..."). O prompt
agora delimita esse conteúdo explicitamente com tags (`<documento>...
</documento>`, `<contexto_recuperado>...</contexto_recuperado>`), com uma
regra clara de que tudo dentro da tag é dado a ser lido, nunca comando a ser
seguido — e qualquer ocorrência literal da própria tag dentro do texto do
usuário é neutralizada antes de entrar no prompt, para que um documento
malicioso não consiga "fechar" a delimitação antes da hora
(`services/llm_service.py`, `_wrap_as_data`). Testado manualmente com um
documento contendo uma tentativa explícita de injeção de prompt — o modelo
manteve o comportamento esperado nos dois fluxos (análise e perguntas e
respostas) em vez de obedecer à instrução injetada.

**4. Versionamento do prompt.** `ANALYSIS_PROMPT_VERSION` (hoje `"v1"`) é
salvo junto de cada análise, dentro do próprio `full_analysis` (campos
`prompt_version` e `model`) — visível na tela de detalhes do documento, no
relatório em PDF e no cabeçalho de cada relatório gerado por
`eval/run_eval.py`. Sem isso, uma análise salva no banco ou um relatório de
avaliação antigo eram "mudos": não davam para saber, meses depois, se uma
mudança de resultado veio de um ajuste no prompt, de uma atualização
silenciosa do modelo do lado da OpenAI, ou de uma regressão real — os três
ficavam indistinguíveis. O número deve subir (`"v2"`, `"v3"`...) sempre que
o conteúdo do `system_prompt` de `analyze_document_with_llm` mudar de forma
que possa afetar o resultado.

---

## Relatório executivo em PDF

Tanto na tela de Processar documento (logo após a análise) quanto em
Consultar histórico (detalhes de um documento salvo) há um botão **Baixar
relatório em PDF**. O relatório (`services/report_service.py`, via
`reportlab`) traz tipo documental, resumo executivo, alertas e a análise
estruturada em um documento de uma página, pronto para anexar a um e-mail ou
apresentação — o tipo de entregável que um jurídico/administrativo leva para
uma reunião, em vez de só uma tela do sistema.

## Tratamento de erros

Erros da API da OpenAI (limite de requisições, timeout, falha de conexão,
indisponibilidade do serviço, chave inválida) são traduzidos em mensagens
amigáveis em português (`services/error_messages.py`) em vez de expor a
exceção técnica crua na tela — tanto no processamento de documentos quanto
nas perguntas e respostas.

---

## Perguntas e respostas

A funcionalidade de consulta utiliza uma abordagem híbrida com:

- recuperação semântica por Chroma
- geração de resposta por LLM
- apoio do `full_analysis` para perguntas mais objetivas

Exemplos de perguntas suportadas:

- Existe multa?
- Qual é a vigência?
- Quem são as partes envolvidas?
- O documento menciona dados pessoais?
- Há cláusula de confidencialidade?
- Qual é o principal objetivo deste documento?

---

## Documentos fora do escopo

Se o documento enviado não se enquadrar claramente em:
- contrato de prestação de serviços
- política interna
- NDA
- aditivo contratual

o sistema o classifica como:

- `fora_escopo`

Nesses casos:
- o documento é salvo no histórico
- o sistema exibe um aviso de fora do escopo
- a funcionalidade de perguntas e respostas é bloqueada

Esse comportamento foi adotado para reforçar o uso responsável da IA e evitar interpretações incorretas em tipos documentais não calibrados.

---

## Documentos de teste

Recomenda-se manter uma pasta `sample_docs/` com documentos usados para:

- calibração inicial do MVP
- avaliação expandida
- testes de robustez fora do escopo
- avaliação em documentos reais e inéditos (base pública ampliada)

Organização atual:

```text
sample_docs/
├── calibracao/              # documentos fictícios usados para ajustar o prompt
├── avaliacao_expandida/     # documentos fictícios inéditos (checagem pós-calibração)
├── fora_escopo/             # documentos fictícios fora do escopo do MVP
└── base_publica_ampliada/   # 24 documentos REAIS de portais de transparência
                             # (nunca vistos durante o ajuste do sistema — ver
                             # eval/gabarito.json, campo "basis": "real_publico",
                             # com a fonte de cada um em "source")
```

---

## Avaliação da solução

A solução foi validada em três frentes:

### 1. Base de calibração
Dois documentos iniciais usados para:
- depuração
- refinamento de prompt
- ajuste de UX
- melhoria de resposta e evidência

### 2. Base de avaliação expandida
Seis documentos inéditos usados para verificar:
- generalização da classificação
- consistência da extração
- comportamento das perguntas e respostas

### 3. Base de robustez fora do escopo
Dois documentos fora do escopo utilizados para validar:
- classificação correta como `fora_escopo`
- aviso na interface
- bloqueio da funcionalidade de perguntas

### 4. Base pública ampliada (held-out real)
24 documentos reais de portais de transparência do governo brasileiro,
nunca vistos durante o desenvolvimento do prompt — ver detalhes na seção
"Avaliação automatizada fim a fim" abaixo. É a base que sustenta a alegação
de generalização, em vez de apenas regressão sobre casos já conhecidos.

---

## Testes automatizados

O projeto conta com uma suíte de testes unitários em `tests/`, cobrindo os
módulos determinísticos (não dependem de chamada à API):

- validação/normalização da saída do LLM (`services/schemas.py`)
- classificação por palavras-chave (`services/document_classifier.py`)
- validação de grounding das evidências (`services/grounding.py`)
- chunking do RAG por seção/cláusula (`rag/vector_store.py`)
- construção determinística de `risk_alerts` (`services/llm_analysis_service.py`)
- helpers de resposta e inferência de intenção (`services/query_service.py`)
- autenticação e hashing de senha (`services/auth_service.py`)
- categorização de vigência para a Visão geral (`services/portfolio_service.py`)
- filtro de propriedade por usuário no storage (`services/storage_service.py`)
- geração do relatório em PDF (`services/report_service.py`)
- tradução de erros técnicos em mensagens amigáveis (`services/error_messages.py`)

Para rodar:

```bash
python -m unittest discover -s tests -v
```

ou, com pytest instalado:

```bash
pytest tests/ -v
```

A suíte também roda automaticamente em todo push/PR via GitHub Actions (`.github/workflows/tests.yml`), sem depender de `OPENAI_API_KEY`.

## Avaliação automatizada fim a fim (`eval/`)

A avaliação da solução deixou de ser feita manualmente em planilha. O
gabarito estruturado está em `eval/gabarito.json`, com **34 casos** em duas
bases distintas (campo `basis` de cada caso):

- **`sintetico_novalex`** (10 casos): os documentos fictícios da NovaLex
  usados desde o início do projeto. Gabarito completo — `document_type`,
  `personal_data_mentions`, presença de cláusula de multa e de
  confidencialidade.
- **`real_publico`** (24 casos): documentos **reais**, baixados de portais
  de transparência do governo brasileiro (Polícia Federal, MEC, prefeituras
  de Niterói/Ribeirão Preto/Francisco Beltrão, CIASC, CODERP, Suape, BNB,
  ITI, Biblioteca Nacional, entre outros — a fonte de cada um está no campo
  `source` do gabarito). Gabarito apenas de `document_type`, porque validar
  os demais campos exigiria ler cláusula por cláusula de cada um.

### Por que separar as duas bases (calibração vs. held-out)

Um ponto levantado na avaliação do case: medir a acurácia de um sistema nos
**mesmos documentos** usados para ajustar o prompt tende a inflar o
resultado — é uma forma de overfitting do prompt ao conjunto de teste, não
uma prova de generalização. Os documentos `sintetico_novalex` foram, em
parte, usados durante a calibração original do prompt; os 24 documentos
`real_publico` nunca foram vistos durante nenhum ajuste do sistema, servindo
como um conjunto genuinamente *held-out*. É essa segunda base que sustenta a
alegação de generalização — a primeira serve principalmente como regressão
(o sistema continua se comportando como esperado nos casos que já conhece).

Observação importante: a base `real_publico` **não inclui NDA**. Por
definição, um acordo de confidencialidade é um documento privado — não
existe um acervo público de NDAs reais para amostrar. Esse tipo continua
validado apenas pelos exemplos sintéticos.

### Resultado mais recente (34 casos, `eval/results/report_20260927_115513.json`)

- **29/34 casos aprovados (85,3%)**
- `document_type`: **97,1%** (33/34)
- `has_penalty_clause`: **100%**
- `has_confidentiality_clause`: **80%**
- `personal_data_mentions`: **80%**

Ao montar o lote de documentos reais, o próprio processo de avaliação expôs
**dois erros no gabarito** (não no classificador): dois arquivos da Polícia
Federal foram rotulados por mim como "contrato" com base no nome do arquivo,
mas na leitura completa um era na verdade um extrato de aditivo publicado no
Diário Oficial e o outro um termo aditivo (o próprio título do documento
dizia isso). Corrigido o gabarito, a acurácia de classificação subiu de
94,1% para 97,1% e se manteve nesse patamar mesmo após a migração para
structured outputs (ver seção seguinte). O único caso que continua como
"falha" é intencional: um edital de licitação real que traz embutida, como
anexo, uma minuta de contrato completa — o LLM classificou como contrato
(defensável, já que boa parte do conteúdo é mesmo uma minuta contratual),
mantido como divergência documentada em vez de forçado a "passar".

`has_confidentiality_clause` e `personal_data_mentions` continuam sendo os
campos mais instáveis entre execuções — já eram apontados como os mais
interpretativos/ambíguos desde a primeira rodada (ver "Avaliação da
solução" acima), e migrar para `temperature=0` não eliminou essa variação:
são casos genuinamente de fronteira (ex.: uma política de segurança que
fala em "credenciais" e "acesso restrito" pode ou não ser lida como uma
cláusula de confidencialidade, dependendo de quão literal for a leitura),
não um bug de parsing ou de prompt. Os relatórios anteriores
(`eval/results/report_20260926_153128.json`, com 10 casos, e
`report_20260927_101914.json`, com 34 casos antes da migração para
structured outputs) ficam versionados para comparação histórica.

O harness `eval/run_eval.py` roda a pipeline real (incluindo chamadas à API
da OpenAI) sobre cada documento do gabarito, compara o resultado obtido com
o esperado e grava um relatório versionável em `eval/results/`.

Para rodar (requer `OPENAI_API_KEY` configurada, pois faz chamadas reais):

```bash
python -m eval.run_eval
```

Campos em texto livre (resumo, datas, obrigações) continuam exigindo leitura
humana do relatório gerado — o harness automatiza a checagem dos campos
objetivos, não substitui totalmente a revisão qualitativa.

## Confiança por campo extraído

Além dos alertas determinísticos, cada campo de texto extraído (objeto,
vigência, renovação, rescisão, multa, confidencialidade, detalhes de dados
pessoais) recebe um selo de confiança na tela de detalhes do documento:
"Confiança alta/média/baixa", calculado verificando se o valor citado pelo
LLM realmente aparece no texto original (`services/grounding.py`,
`compute_field_confidence`). Isso torna visível, campo a campo, quando a
extração pode ter se apoiado em inferência em vez de conteúdo explícito do
documento.

Esse sinal não fica só decorativo: quando um ou mais campos ficam com
confiança baixa, o documento é sinalizado com **"⚠️ revisão pendente"** — no
banner de detalhes, na lista de "Consultar histórico" e num alerta
específico citando quais campos ficaram abaixo do limiar de confiança
(`services/llm_analysis_service.py`, `low_confidence_fields`). Antes, esse
sinal só existia como badge visual isolado; agora ele participa do mesmo
`needs_review` que já reagia a classificação divergente e evidências não
localizadas, e o resultado fica persistido no banco (não só na tela
imediatamente após o processamento).

---

## Revisão de código e correções de robustez

Depois de todo o desenvolvimento acima, o projeto passou por uma revisão de
código dedicada (múltiplos agentes analisando o diff completo por ângulos
diferentes — correção, comportamento removido, rastreamento entre arquivos,
reuso, simplificação, eficiência, altitude — cada achado confirmado por um
segundo agente antes de virar correção). Encontrado e corrigido:

- **XSS armazenado**: campos extraídos pelo LLM (`object`, `termination_clause`
  etc.) eram renderizados via `st.markdown(..., unsafe_allow_html=True)` sem
  escapar o texto — um documento com HTML/JS embutido na cláusula executaria
  na tela de quem visualizasse a análise. Corrigido com `escape()` em
  `render_text` (`app/streamlit_app.py`).
- **Relatório em PDF quebrando ou perdendo texto**: `reportlab.Paragraph`
  exige escapar `&`/`<`/`>` manualmente; texto do LLM contendo esses
  caracteres causava exceção não tratada ou descarte silencioso de trecho do
  relatório. Corrigido escapando todo texto antes de virar `Paragraph`
  (`services/report_service.py`).
- **Análise quebrando em recusa/truncamento do modelo**: `response.output_parsed`
  pode vir `None` (recusa ou resposta incompleta); o código assumia que
  nunca seria `None` e derrubava com `AttributeError` cru. Corrigido com uma
  checagem explícita que vira uma mensagem amigável (`services/llm_service.py`).
- **Exclusão de documento sem tratamento de erro**: o retorno de
  `delete_document` era ignorado e os chunks do Chroma eram sempre apagados,
  mesmo se a exclusão no SQLite falhasse — risco de exclusão parcial que
  minava o próprio recurso de "direito de eliminação". Corrigido com
  checagem do retorno e tratamento de exceção em cada etapa.
- **Sessão não revalidada em abas já abertas**: TTL e revogação só eram
  checados no primeiro carregamento da página, não a cada interação numa aba
  que ficasse aberta. Corrigido com revalidação periódica (ver "Sessão
  persistente" acima).
- **Reindexação sem checagem de perfil na camada de serviço** e
  **chunks órfãos no Chroma ao reindexar** (quando o novo chunking gera menos
  pedaços que uma indexação anterior): corrigidos em
  `services/storage_service.py` e `rag/vector_store.py`.
- **Mensagem de erro genérica vazando exceção crua**: o fallback de
  `describe_error` interpolava a exceção técnica direto na tela, contrariando
  o propósito do próprio módulo. Agora o detalhe vai para o log do servidor,
  e a tela mostra uma mensagem genérica seria.
- **Rótulos de tipo documental divergentes**: a UI mostrava "NDA" e o PDF
  mostrava "NDA (acordo de confidencialidade)" para o mesmo documento, porque
  os dois mapas eram mantidos independentemente. Unificados em
  `services/document_types.py`.
- **`init_db()` reexecutando a cada interação**: Streamlit reexecuta o script
  inteiro a cada clique; a inicialização do banco agora roda uma única vez
  por processo via `st.cache_resource`.

---

## Limitações do MVP

Esta versão do projeto não contempla:

- OCR avançado para documentos escaneados
- integração com sistemas corporativos externos
- comparação automática entre versões documentais
- monitoramento enterprise em produção
- cobertura ampla de outros tipos documentais
- governança completa de acesso e auditoria
- criptografia dos chunks indexados no Chroma (o texto salvo no SQLite é cifrado, mas o índice de busca semântica continua em texto plano — ver "Proteção de dados pessoais")

O projeto foi intencionalmente delimitado para manter foco, clareza e profundidade no problema escolhido.

---

## Próximos passos

Possíveis evoluções futuras incluem:

- ampliar a cobertura para novos tipos documentais
- melhorar a avaliação automática
- evoluir a autenticação (recuperação de senha, expiração de sessão, múltiplos admins com auditoria)
- comparar versões de documentos
- incorporar OCR
- expandir mecanismos de governança e auditoria
- evoluir a infraestrutura para ambiente mais próximo de produção

---

## Observações sobre custo

O projeto utiliza a OpenAI API. Isso significa que:

- chamadas de processamento consomem API
- perguntas e respostas também consomem API
- é necessário ter billing/crédito ativo
- recomenda-se testar com volume controlado

---

## Deploy no Streamlit Community Cloud

Para publicar o app:

1. suba o projeto para um repositório no GitHub
2. conecte o repositório ao Streamlit Community Cloud
3. configure o arquivo de entrada:
   - `app/streamlit_app.py`
4. adicione a variável `OPENAI_API_KEY` nos **Secrets**
5. faça o deploy

---

## Troubleshooting

### `ModuleNotFoundError`
Verifique se:
- o ambiente virtual está ativado
- as dependências foram instaladas com `pip install -r requirements.txt`

### `streamlit not recognized`
Use:

```bash
python -m streamlit run app/streamlit_app.py
```

### erro de API / autenticação
Verifique se:
- o arquivo `.env` existe
- a variável `OPENAI_API_KEY` está correta
- o billing da OpenAI API está ativo

### respostas inconsistentes em documentos antigos
Utilize o botão:

- **Reindexar documentos salvos**

---

## Contexto do case

Este projeto foi desenvolvido como case prático de **Engenharia de IA**, com foco em:

- IA Generativa
- triagem documental
- extração estruturada
- RAG
- validação de MVP
- controle de escopo e uso responsável da IA
