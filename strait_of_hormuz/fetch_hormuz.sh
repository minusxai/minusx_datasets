#!/bin/bash
# Fetch daily Strait of Hormuz ship transit data for specified years

SKIP_FETCH="${SKIP_FETCH:-}"
SKIP_UPLOAD="${SKIP_UPLOAD:-}"

YEARS=(2019 2020 2021 2022 2023 2024 2025 2026)
OUT="hormuz_daily.csv"
BASE="https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

if [ -z "$SKIP_FETCH" ]; then
  HEADER_WRITTEN=false
  > "$OUT"

  for YEAR in "${YEARS[@]}"; do
    echo "Fetching $YEAR..."
    DATA=$(curl -s "${BASE}?where=portname%3D%27Strait%20of%20Hormuz%27%20AND%20year%3D${YEAR}&outFields=*&f=json&resultRecordCount=1000")

    COUNT=$(echo "$DATA" | uv run python -c "import json,sys;d=json.load(sys.stdin);print(len(d.get('features',[])))")
    echo "  $YEAR: $COUNT rows"

    if [ "$COUNT" -gt 0 ]; then
      if [ "$HEADER_WRITTEN" = false ]; then
        echo "$DATA" | uv run python -c "import json,csv,sys;data=json.load(sys.stdin);rows=[f['attributes'] for f in data['features']];w=csv.DictWriter(sys.stdout,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)" >> "$OUT"
        HEADER_WRITTEN=true
      else
        echo "$DATA" | uv run python -c "import json,csv,sys;data=json.load(sys.stdin);rows=[f['attributes'] for f in data['features']];w=csv.DictWriter(sys.stdout,fieldnames=rows[0].keys());w.writerows(rows)" >> "$OUT"
      fi
    fi
  done

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
