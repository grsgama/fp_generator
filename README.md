# Gerador de Folha de Processo (MVP)

## O que este MVP faz
- Cadastro de equipamentos (SQLite)
- Montagem de folhas de processo a partir de blocos reutilizáveis
- Blocos simples, como `Substrato`, `Limpeza química`, `Deposição` e `Lift-off`
- Blocos compostos, como `Litografia óptica`, que expande para promotor, resiste, exposição, revelação e inspeção
- Cadastro de composições salvas como receitas reutilizáveis (SQLite)
- Geração automática de planilha `.xlsx` a partir de um template formatado
- Numeração simples ou hierárquica dos blocos na folha gerada
- Preserva a formatação porque só escreve o conteúdo nas células/linhas mapeadas
- Histórico de arquivos gerados

## Estrutura
- `app.py`: interface Streamlit
- `db.py`: banco SQLite e CRUD básico
- `xlsx_writer.py`: escrita de dados no template
- `fp_data.db`: banco criado automaticamente
- `outputs/`: planilhas geradas

## Requisitos
- Python 3.10+
- Dependências em `requirements.txt`

## Instalação
No diretório deste projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar
```bash
./start_fp_app.sh
```

O app abre em `http://localhost:8511`.

## Template
Por padrão, o app usa:
`../FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`

Você pode apontar para outro template no campo `Template XLSX` da aba `Gerar planilha`.

## Fluxo de uso
1. Abra a aba `Gerar planilha`.
2. Escolha um `Processo base`, como `Lift-off`, ou comece em branco.
3. Adicione blocos da biblioteca quando precisar.
4. Edite a sequência de linhas da FP.
5. Salve a composição se quiser reutilizá-la.
6. Gere a planilha `.xlsx`.

O processo base `Lift-off` monta automaticamente:
- `1` Substrato
- `2` Limpeza química
- `3.1` Litografia óptica / Promotor de adesão
- `3.2` Litografia óptica / Aplicação de resiste
- `3.3` Litografia óptica / Exposição
- `3.4` Litografia óptica / Revelação
- `3.5` Litografia óptica / Inspeção pós-litografia
- `4` Deposição
- `5` Lift-off

## Estrutura dos blocos
Cada linha/bloco tem:
- `ordem`
- `numero`
- `titulo`
- `visao_geral`
- `detalhes`
- `notas`

Na geração da planilha, o software escreve a sequência nas colunas:
- `Nº`
- `Passo do processo`
- `Visão geral do processo`
- `Detalhes do processo`
- `Notas/Comentários`

## Observação
Se quiser ajustar as células do cabeçalho ou as colunas usadas pelos blocos, edite os mapeamentos em `xlsx_writer.py`.

## Atalhos
Iniciar app:
```bash
./start_fp_app.sh
```

Parar app:
```bash
./stop_fp_app.sh
```
