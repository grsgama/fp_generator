# Gerador de Folha de Processo (MVP)

## O que este MVP faz
- Cadastro de equipamentos (SQLite)
- Cadastro de receitas/parâmetros (SQLite)
- Geração automática de planilha `.xlsx` a partir de um template formatado
- Preserva a formatação porque só escreve o conteúdo das células mapeadas
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
streamlit run app.py
```

## Template
Por padrão, o app usa:
`../FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`

Você pode apontar para outro template no campo `Template XLSX` da aba `Gerar planilha`.

## Observação
Se quiser acrescentar novos campos/células, edite o dicionário `CELL_MAP` em `xlsx_writer.py`.
