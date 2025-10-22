# Testes do Robô de Download Neo

Este diretório contém scripts de teste para validar o parsing e envio das planilhas exportadas.

## Estrutura de Testes

### 1. Testes de Parse (Parsing)
Fazem o parse dos arquivos Excel e geram arquivos JSON para inspeção:

- **`test_parse.py`** - Parse de `ExportacaoProducao.xlsx`
- **`test_parse_atividades.py`** - Parse de `ExportacaoAtividade.xlsx`
- **`test_parse_status.py`** - Parse de `ExportacaoStatus.xlsx`

**Uso:**
```bash
# Parse do arquivo padrão em Downloads
python tests/test_parse.py
python tests/test_parse_atividades.py
python tests/test_parse_status.py

# Parse de arquivo específico
python tests/test_parse.py "C:\caminho\para\ExportacaoProducao.xlsx"
python tests/test_parse_atividades.py "C:\caminho\para\ExportacaoAtividade.xlsx"
python tests/test_parse_status.py "C:\caminho\para\ExportacaoStatus.xlsx"
```

**Saída:** 
- Arquivos JSON em `tests/json/` com timestamp
- Mostra primeiros 3 registros no console

### 2. Testes de Envio (POST)
Enviam registros dos arquivos JSON gerados para as APIs do NocoDB:

- **`test_post.py`** - Envia dados de produção
- **`test_post_atividades.py`** - Envia dados de atividades
- **`test_post_status.py`** - Envia dados de status

**Uso:**
```bash
# Envio com arquivo JSON mais recente
python tests/test_post.py
python tests/test_post_atividades.py
python tests/test_post_status.py

# Envio com dry-run (não envia, apenas simula)
python tests/test_post.py --dry-run
python tests/test_post_atividades.py --dry-run --batch-size 10
python tests/test_post_status.py --dry-run

# Envio de arquivo específico
python tests/test_post.py --file tests/json/parsed_20250122_143000.json
python tests/test_post_atividades.py --file tests/json/parsed_atividades_20250122_143000.json

# Customizar parâmetros
python tests/test_post.py --batch-size 50 --post-retries 5 --backoff-base 2.0
```

**Opções:**
- `--file, -f`: Caminho para arquivo JSON específico
- `--dry-run`: Simula envio sem fazer POST real
- `--batch-size`: Tamanho dos lotes (default: 25)
- `--post-retries`: Tentativas por batch (default: 3)
- `--backoff-base`: Base exponencial para retry (default: 1.5)
- `--url`: Override da URL da API
- `--token`: Override do BEARER_TOKEN

### 3. Testes Diretos

- **`test_direct_post.py`** - Teste direto da API com registro de exemplo (sem usar função do app.py)
- **`test_single_record.py`** - Testa envio de um único registro usando a função do app.py

## Fluxo de Teste Completo

1. **Parse:** Gera JSON a partir do Excel
   ```bash
   python tests/test_parse_atividades.py
   ```

2. **Dry-run:** Valida formato sem enviar
   ```bash
   python tests/test_post_atividades.py --dry-run
   ```

3. **Envio real:** Envia para a API
   ```bash
   python tests/test_post_atividades.py
   ```

4. **Verificar logs:**
   - `logs/sent_records_atividades.jsonl` - Log detalhado por registro
   - `robo_download.log` - Log geral da aplicação

## Variáveis de Ambiente Necessárias

Configure no arquivo `.env`:
```env
BEARER_TOKEN=seu_token_aqui
URL_TABELA_PRODUCAO=https://...
URL_TABELA_ATIVIDADES=https://...
URL_TABELA_ATIVIDADES_STATUS=https://...

# Opcionais para testes
DRY_RUN=false
BATCH_SIZE=25
POST_RETRIES=3
BACKOFF_BASE=1.5
```

## Arquivos de Saída

### JSON (tests/json/)
- `parsed_YYYYMMDD_HHMMSS.json` - Produção
- `parsed_atividades_YYYYMMDD_HHMMSS.json` - Atividades
- `parsed_status_YYYYMMDD_HHMMSS.json` - Status

### Logs (logs/)
- `sent_records_producao.jsonl` - Envios de produção
- `sent_records_atividades.jsonl` - Envios de atividades
- `sent_records_atividades_status.jsonl` - Envios de status
- `robo_download.log` - Log geral

## Dicas

- Use `--dry-run` sempre que quiser validar sem enviar
- Os arquivos JSON são úteis para debug e podem ser re-enviados
- Logs em formato JSONL permitem fácil análise com `jq` ou scripts
- Batch size menor = mais lento mas mais confiável
- Aumentar retries ajuda em redes instáveis
