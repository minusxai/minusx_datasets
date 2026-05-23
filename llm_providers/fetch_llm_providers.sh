#!/bin/bash
# Fetch AI model data from models.dev and upload to Google Sheet

SKIP_FETCH="${SKIP_FETCH:-}"
SKIP_UPLOAD="${SKIP_UPLOAD:-}"

OUT="llm_providers.csv"
API="https://models.dev/api.json"

if [ -z "$SKIP_FETCH" ]; then
  echo "Fetching models from models.dev..."
  DATA=$(curl -s "$API")

  echo "$DATA" | uv run python -c "
import json, csv, sys

data = json.load(sys.stdin)
rows = []

for provider_key, provider in data.items():
    provider_name = provider.get('name', provider_key)
    models = provider.get('models', {})
    for model_key, m in models.items():
        input_modalities = ','.join(m.get('modalities', {}).get('input', []))
        output_modalities = ','.join(m.get('modalities', {}).get('output', []))
        cost = m.get('cost', {})
        limit = m.get('limit', {})
        rows.append({
            'provider': provider_name,
            'model_id': m.get('id', ''),
            'model_name': m.get('name', ''),
            'family': m.get('family', ''),
            'reasoning': m.get('reasoning', False),
            'tool_call': m.get('tool_call', False),
            'open_weights': m.get('open_weights', False),
            'input_modalities': input_modalities,
            'output_modalities': output_modalities,
            'context_limit': limit.get('context', ''),
            'output_limit': limit.get('output', ''),
            'cost_input': cost.get('input', ''),
            'cost_output': cost.get('output', ''),
            'cost_cache_read': cost.get('cache_read', ''),
            'cost_cache_write': cost.get('cache_write', ''),
            'knowledge': m.get('knowledge', ''),
            'release_date': m.get('release_date', ''),
            'last_updated': m.get('last_updated', ''),
        })

print(f'Total models: {len(rows)}', file=sys.stderr)
w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
w.writeheader()
w.writerows(rows)
" > "$OUT"

  echo "Done: $(wc -l < "$OUT") lines in $OUT"
else
  echo "Skipping fetch (SKIP_FETCH is set)"
fi

if [ -z "$SKIP_UPLOAD" ]; then
  # Upload to Google Sheet
  SHEET_ID=$(cat sheet_id.txt) || { echo "Missing sheet_id.txt"; exit 1; }
  KEY_FILE="key.json"

  echo "Uploading to Google Sheet..."
  uv run --with gspread --with google-auth python -c "
import gspread, csv
gc = gspread.service_account(filename='${KEY_FILE}')
sh = gc.open_by_key('${SHEET_ID}')
ws = sh.sheet1
ws.clear()
rows = list(csv.reader(open('${OUT}')))
ws.update(rows, 'A1')
print(f'Uploaded {len(rows)-1} rows to sheet')
print('https://docs.google.com/spreadsheets/d/${SHEET_ID}')
"
else
  echo "Skipping upload (SKIP_UPLOAD is set)"
fi
