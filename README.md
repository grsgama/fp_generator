# FP Generator

Sistema local para cadastrar equipamentos, registrar blocos de receita e montar folhas de processo a partir de uma interface web.

O software roda neste computador como um site local. Ele usa FastAPI no backend, SQLite como banco de dados e uma interface simples em HTML/CSS/JavaScript. A saida principal e uma planilha `.xlsx` gerada a partir do template de Folha de Processo.

## Estado Atual

Esta versao ja permite:

- Cadastrar, editar, inativar ou remover equipamentos.
- Classificar equipamentos por categoria e subtipo de processo.
- Cadastrar blocos de receita vinculados a equipamentos existentes.
- Adicionar parametros tecnicos em cada bloco de receita.
- Duplicar blocos de receita para criar uma variacao com o sufixo `- 1`.
- Criar folhas de processo a partir de uma sequencia de blocos cadastrados.
- Reordenar blocos da folha arrastando com o mouse.
- Gerar arquivos `.xlsx` usando o template existente.
- Baixar arquivos gerados.
- Consultar historico de geracao.

Ainda nao ha login, permissao por usuario ou aprovacao formal de receita. Por enquanto, o papel de "master" e operacional: quem tem acesso ao app consegue cadastrar equipamentos e editar dados.

## Arquitetura

```text
Navegador
   |
   | HTTP
   v
FastAPI - app.py
   |
   v
SQLite - fp_data.db
   |
   +--> outputs/*.xlsx
   |
   +--> Template XLSX externo
```

Componentes principais:

- `app.py`: define a API FastAPI, serve o frontend e expoe as rotas de download.
- `db.py`: cria o schema SQLite, executa migracoes simples e contem as funcoes CRUD.
- `xlsx_writer.py`: abre o template XLSX e escreve cabecalho/blocos preservando a formatacao.
- `static/index.html`: estrutura da interface web.
- `static/styles.css`: layout e aparencia da interface.
- `static/app.js`: chamadas HTTP para a API e comportamento da interface.
- `fp_data.db`: banco SQLite local.
- `outputs/`: pasta onde as folhas geradas sao salvas.
- `start_fp_app.sh`: inicia o servidor.
- `stop_fp_app.sh`: para o servidor.

## Modelo de Dados

O banco principal e `fp_data.db`. As tabelas relevantes da versao atual sao:

### `equipment`

Guarda os equipamentos disponiveis para uso nos blocos de receita.

Campos principais:

- `name`: nome do equipamento.
- `category`: categoria do processo.
- `subtype`: subtipo do processo.
- `model`: modelo.
- `manufacturer`: fabricante.
- `location`: localizacao.
- `status`: `active` ou `inactive`.
- `notes`: observacoes.

Quando um equipamento ja esta sendo usado por uma receita, a remocao nao apaga o registro fisicamente; o equipamento e marcado como `inactive`.

### `recipe_block`

Guarda blocos reutilizaveis de receita/processo.

Campos principais:

- `name`: nome do bloco.
- `category`: categoria do processo.
- `subtype`: subtipo do processo.
- `equipment_id`: equipamento usado.
- `author`: responsavel que cadastrou.
- `confidence_level`: nivel de confianca, como `experimental`, `provisoria`, `validada` ou `rotina`.
- `description`: descricao geral do bloco.
- `notes`: observacoes.

### `recipe_parameter`

Guarda os parametros tecnicos de cada bloco.

Cada parametro tem:

- `name`: nome do parametro.
- `value`: valor.
- `unit`: unidade.
- `seq`: ordem de exibicao.

Exemplo:

```text
Rotacao | 4000 | RPM
Temperatura | 100 | Celsius
Tempo | 60 | segundos
```

### `process_sheet`

Guarda uma folha de processo salva.

Campos principais:

- `title`: titulo da folha.
- `author`: responsavel.
- `project_name`: projeto.
- `supervisor`: supervisor/orientador.
- `description`: descricao curta.
- `status`: status interno, atualmente usado como rascunho.

### `process_sheet_block`

Guarda a sequencia de blocos dentro de uma folha.

Campos principais:

- `process_sheet_id`: folha.
- `recipe_block_id`: bloco de receita usado.
- `seq`: ordem do bloco na folha.
- `title_override`: titulo opcional especifico daquela folha.
- `notes_override`: nota opcional especifica daquela folha.

### `generated_sheet`

Guarda historico dos arquivos gerados.

Campos principais:

- `process_sheet_id`: folha que originou o arquivo.
- `output_path`: caminho local do arquivo `.xlsx`.
- `created_at`: data/hora de geracao.

## Categorias e Subtipos

As categorias iniciais estao definidas em `db.py`.

```text
Litografia
  - Optica
  - Feixe de eletrons

Deposicao
  - Sputtering
  - Evaporacao

Ataque
  - Umido
  - RIE
  - DRIE
  - Ion Milling

Inspecao
  - MEV
  - TEM
  - Microscopio optico
  - Probe Station

Preparacao
  - FIB
  - Wire Bonder
```

## Como Usar

Abra o app no navegador:

```text
http://localhost:8511
```

Se estiver acessando de outro computador na mesma rede, use o IP do computador que esta hospedando o app:

```text
http://IP_DO_PC:8511
```

### 1. Cadastrar Equipamentos

Use a aba **Equipamentos**.

Preencha:

- Nome.
- Categoria.
- Subtipo.
- Modelo.
- Fabricante.
- Local.
- Status.
- Observacoes.

Depois clique em **Salvar**.

Os equipamentos cadastrados aparecem na lista ao lado. A partir dela e possivel editar ou remover. Se o equipamento ja estiver vinculado a uma receita, ele sera inativado em vez de apagado.

### 2. Cadastrar Blocos de Receita

Use a aba **Blocos de receita**.

Um bloco de receita representa uma etapa reutilizavel de processo, por exemplo:

- Primer AR 300-80.
- Spin coating de AR-P 3120.
- Exposicao optica.
- Revelacao.
- Deposicao de Au.
- Ataque por Ion Milling.
- Inspecao optica.

Para cadastrar:

1. Informe o nome do bloco.
2. Escolha categoria e subtipo.
3. Escolha um equipamento existente.
4. Informe autor e nivel de confianca.
5. Escreva uma descricao e notas, se necessario.
6. Adicione parametros tecnicos em **Parametros**.
7. Clique em **Salvar bloco**.

Cada bloco salvo aparece na lista lateral. A lista permite:

- **Editar**: carrega o bloco no formulario.
- **Duplicar**: cria uma copia com o sufixo `- 1`.
- **Remover**: remove o bloco, desde que ele nao esteja sendo usado em uma folha.

### 3. Montar uma Folha de Processo

Use a aba **Folhas de processo**.

Preencha:

- Titulo.
- Autor.
- Projeto.
- Supervisor.
- Descricao.

Depois monte a **Sequencia de blocos**:

1. Clique em **Adicionar bloco**.
2. Escolha o bloco de receita no seletor.
3. Opcionalmente preencha `Titulo opcional`.
4. Opcionalmente preencha `Nota opcional`.
5. Repita para adicionar mais etapas.

A ordem e preenchida automaticamente. Para trocar a ordem, arraste as linhas pelo controle lateral. A numeracao sera recalculada automaticamente.

Depois clique em **Salvar folha**.

As folhas salvas aparecem na lista ao lado. Cada folha pode ser:

- Editada.
- Removida.
- Usada para gerar XLSX.

### 4. Gerar XLSX

Na aba **Folhas de processo**, encontre uma folha salva e clique em **Gerar XLSX**.

O sistema:

1. Busca a folha no banco.
2. Carrega os blocos e parametros associados.
3. Converte a folha em um payload para o template.
4. Abre o template XLSX.
5. Escreve cabecalho e blocos.
6. Salva o arquivo em `outputs/`.
7. Registra a geracao no historico.
8. Inicia o download no navegador.

### 5. Historico

Use a aba **Historico**.

Ela mostra os arquivos gerados e permite baixar novamente cada `.xlsx`, desde que o arquivo ainda exista em `outputs/`.

## Como o XLSX e Montado

O arquivo `xlsx_writer.py` usa `openpyxl`.

O cabecalho e escrito nestas celulas:

```text
E2: titulo da folha
E3: supervisor
E4: projeto
E5: autor/responsavel
E6: descricao
E7: data ou marcador
```

Os blocos sao escritos a partir da linha 10:

```text
Coluna B: numero
Coluna C: titulo
Coluna D: visao geral
Coluna E: detalhes
Coluna F: notas
```

Se houver mais blocos do que linhas existentes no template, o sistema insere novas linhas e copia a formatacao das linhas do template.

## Template XLSX

O app procura o template nestes caminhos:

1. `../FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`
2. `/home/grsgama/Nextcloud/LabNano/Folha de Processo/FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`

Se o template nao for encontrado:

- O cadastro de equipamentos, blocos e folhas continua funcionando.
- A geracao de XLSX falha ate que o template exista em um dos caminhos acima.

O status do template aparece no canto superior direito da interface.

## Instalar em um Ambiente Novo

No diretorio do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias principais:

- `fastapi`
- `uvicorn`
- `openpyxl`

## Executar

Para iniciar:

```bash
./start_fp_app.sh
```

Por padrao, o app sobe em:

```text
http://localhost:8511
```

O script usa:

```bash
.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8511
```

Se houver suporte a `systemd --user`, ele inicia como unidade transiente:

```text
fp_generator.service
```

Caso contrario, usa `nohup` e grava:

```text
fp_generator.pid
fp_generator.log
```

Para usar outra porta:

```bash
./start_fp_app.sh 8520
```

## Parar

```bash
./stop_fp_app.sh
```

O script tenta parar primeiro a unidade `fp_generator.service`. Se ela nao existir, usa o PID salvo em `fp_generator.pid`.

## API Principal

A interface web usa estas rotas:

```text
GET    /api/meta
GET    /api/equipment
POST   /api/equipment
PUT    /api/equipment/{id}
DELETE /api/equipment/{id}

GET    /api/recipe-blocks
POST   /api/recipe-blocks
PUT    /api/recipe-blocks/{id}
DELETE /api/recipe-blocks/{id}
POST   /api/recipe-blocks/{id}/duplicate

GET    /api/process-sheets
POST   /api/process-sheets
PUT    /api/process-sheets/{id}
DELETE /api/process-sheets/{id}
POST   /api/process-sheets/{id}/generate

GET    /api/generated
GET    /download/{generated_id}
```

A documentacao interativa do FastAPI tambem fica disponivel em:

```text
http://localhost:8511/docs
```

## Backup

Para preservar os dados cadastrados, faca backup destes itens:

```text
fp_data.db
outputs/
```

O codigo esta versionado no Git, mas o banco e os XLSX gerados sao dados locais de operacao.

## Limitacoes Atuais

- Nao ha login ou controle real de permissao.
- Qualquer pessoa com acesso ao app pode editar cadastros.
- Nao ha aprovacao formal de receitas.
- Nao ha versionamento interno de receita.
- Nao ha validacao profunda de compatibilidade entre materiais, equipamentos e etapas.
- A geracao depende do template XLSX existir em caminho conhecido.
- O banco e SQLite local, adequado para uso interno simples.

## Proximas Melhorias Naturais

- Criar usuarios e permissoes, separando master/admin de usuario comum.
- Adicionar estado de aprovacao para blocos: rascunho, em revisao, validado, obsoleto.
- Adicionar historico de alteracoes por receita.
- Melhorar os formularios por categoria, com campos especificos para litografia, deposicao, ataque, inspecao e preparacao.
- Criar templates de fluxo, como `Lift-off`, `Etching`, `Deposicao simples`.
- Exportar tambem PDF.
- Criar busca e filtros por categoria, equipamento e nivel de confianca.
