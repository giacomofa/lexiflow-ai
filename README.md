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
- **reportlab**

---

## Estrutura do projeto

A estrutura principal esperada do projeto é semelhante a esta:

```text
lexiflow-ai/
├── app/
│   └── streamlit_app.py
├── services/
├── rag/
├── data/
├── sample_docs/
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

## Como usar o sistema

### Tela 1 — Processar documento
Nesta tela, o usuário pode:

1. enviar um documento PDF ou TXT
2. visualizar o texto extraído
3. clicar em **Processar documento**
4. visualizar:
   - tipo do documento
   - resumo executivo
   - alertas
   - análise estruturada completa

### Tela 2 — Consultar histórico
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

Uma organização possível é:

```text
sample_docs/
├── calibracao/
├── avaliacao_expandida/
└── fora_escopo/
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

---

## Limitações do MVP

Esta versão do projeto não contempla:

- OCR avançado para documentos escaneados
- autenticação por usuário/perfil
- integração com sistemas corporativos externos
- comparação automática entre versões documentais
- monitoramento enterprise em produção
- cobertura ampla de outros tipos documentais
- governança completa de acesso e auditoria

O projeto foi intencionalmente delimitado para manter foco, clareza e profundidade no problema escolhido.

---

## Próximos passos

Possíveis evoluções futuras incluem:

- ampliar a cobertura para novos tipos documentais
- melhorar a avaliação automática
- adicionar autenticação e controle de acesso
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
