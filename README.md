# FP Generator

MVP local para cadastrar equipamentos, registrar blocos de receita e montar folhas de processo em uma interface web.

## Arquitetura

- `FastAPI`: API e servidor da interface web
- `SQLite`: banco local em `fp_data.db`
- `HTML/CSS/JS`: frontend simples em `static/`
- `openpyxl`: geração de planilhas `.xlsx` a partir do template existente

## Fluxo do MVP

1. O master cadastra equipamentos.
2. Usuarios cadastram blocos de receita usando equipamentos existentes.
3. Uma folha de processo e montada como uma sequencia desses blocos.
4. O sistema gera um XLSX e salva o historico.

## Categorias iniciais

- Litografia: Optica, Feixe de eletrons
- Deposicao: Sputtering, Evaporacao
- Ataque: Umido, RIE, DRIE, Ion Milling
- Inspecao: MEV, TEM, Microscopio optico, Probe Station
- Preparacao: FIB, Wire Bonder

## Estrutura

- `app.py`: API FastAPI e rotas de download
- `db.py`: schema SQLite e funcoes de persistencia
- `xlsx_writer.py`: escrita no template XLSX
- `static/index.html`: interface visual
- `static/styles.css`: estilos
- `static/app.js`: logica do frontend
- `outputs/`: arquivos XLSX gerados

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar

```bash
./start_fp_app.sh
```

URL local:

```text
http://localhost:8511
```

Para acessar de outro computador na mesma rede, use o IP deste PC:

```text
http://IP_DO_PC:8511
```

## Parar

```bash
./stop_fp_app.sh
```

## Template XLSX

O app procura o template nestes caminhos:

1. `../FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`
2. `/home/grsgama/Nextcloud/LabNano/Folha de Processo/FP_FolhaDeProcesso_Modelo_EmBranco.xlsx`

Se o template nao for encontrado, o cadastro funciona, mas a geracao de XLSX falha ate o arquivo existir.
