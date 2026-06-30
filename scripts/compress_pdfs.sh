#!/usr/bin/env bash
# Compression adaptative des PDFs > 50 MB dans cours/
# Strategie : /prepress (meilleure qualite) -> /printer si trop gros -> /ebook en dernier recours

set -uo pipefail

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

PROJECT_ROOT="/mnt/c/Users/aabed/Desktop/Platform"
TARGET_DIR="$PROJECT_ROOT/cours"
THRESHOLD_MB=50
MAX_OUTPUT_MB=95

# Niveaux de qualite (meilleur d'abord)
QUALITY_LEVELS=("prepress" "printer" "ebook")

compress_at_preset() {
  local input="$1"
  local output="$2"
  local preset="$3"
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
     -dPDFSETTINGS=/${preset} \
     -dNOPAUSE -dQUIET -dBATCH \
     -sOutputFile="$output" "$input" 2>/dev/null
}

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERROR: $TARGET_DIR n'existe pas"
  exit 1
fi

echo "=== Recherche des PDFs > ${THRESHOLD_MB} MB ==="
mapfile -d '' -t FILES < <(find "$TARGET_DIR" -type f -name "*.pdf" -size +${THRESHOLD_MB}M -print0)

TOTAL=${#FILES[@]}
echo "Trouve : $TOTAL fichier(s)"
echo "Strategie : /prepress -> /printer -> /ebook (jusqu'a < ${MAX_OUTPUT_MB} MB)"
echo ""

if [ "$TOTAL" -eq 0 ]; then
  echo "Rien a faire."
  exit 0
fi

COUNTER=0
TOTAL_BEFORE=0
TOTAL_AFTER=0

for FILE in "${FILES[@]}"; do
  COUNTER=$((COUNTER + 1))
  SIZE_BEFORE=$(stat -c%s "$FILE")
  SIZE_BEFORE_MB=$((SIZE_BEFORE / 1024 / 1024))
  TOTAL_BEFORE=$((TOTAL_BEFORE + SIZE_BEFORE))

  BASENAME=$(basename "$FILE")
  echo "[$COUNTER/$TOTAL] $BASENAME (${SIZE_BEFORE_MB} MB)"

  CHOSEN_PRESET=""

  for PRESET in "${QUALITY_LEVELS[@]}"; do
    TEMP_FILE="${FILE}.tmp_${PRESET}.pdf"

    if compress_at_preset "$FILE" "$TEMP_FILE" "$PRESET"; then
      OUTPUT_SIZE=$(stat -c%s "$TEMP_FILE")
      OUTPUT_MB=$((OUTPUT_SIZE / 1024 / 1024))

      echo "    Test /$PRESET -> ${OUTPUT_MB} MB"

      if [ "$OUTPUT_MB" -lt "$MAX_OUTPUT_MB" ]; then
        mv "$TEMP_FILE" "$FILE"
        CHOSEN_PRESET="$PRESET"
        TOTAL_AFTER=$((TOTAL_AFTER + OUTPUT_SIZE))
        RATIO=$((100 - (OUTPUT_SIZE * 100 / SIZE_BEFORE)))
        echo "    -> CHOISI : /$PRESET, ${OUTPUT_MB} MB (-${RATIO}%)"
        break
      else
        rm -f "$TEMP_FILE"
      fi
    else
      echo "    Test /$PRESET echec"
      rm -f "$TEMP_FILE"
    fi
  done

  if [ -z "$CHOSEN_PRESET" ]; then
    echo "    -> ECHEC : aucun preset ne passe (fichier inchange)"
    TOTAL_AFTER=$((TOTAL_AFTER + SIZE_BEFORE))
  fi

  echo ""
done

echo "=== Resume ==="
echo "Total avant : $((TOTAL_BEFORE / 1024 / 1024)) MB"
echo "Total apres : $((TOTAL_AFTER / 1024 / 1024)) MB"
echo "Economie : $(((TOTAL_BEFORE - TOTAL_AFTER) / 1024 / 1024)) MB"
echo ""
echo "Taille totale cours/ :"
du -sh "$TARGET_DIR"
