#!/usr/bin/env bash
set -euo pipefail

DEVICE=${DEVICE:-"auto"}

# CLI flags
DRY_RUN=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|-n)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run]"
            echo "  --dry-run, -n   Preview uploads without touching the device"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Correct mpremote prefix
if [ "$DEVICE" = "auto" ]; then
    PORT_CMD="mpremote connect auto"
else
    PORT_CMD="mpremote connect $DEVICE"
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "🔍 Dry-run mode: skipping device check and remote actions"
else
    echo "🔍 Checking device..."
    $PORT_CMD exec "print('connected')" || {
        echo "❌ mpremote cannot talk to the device"
        exit 1
    }
fi

echo "🚀 Starting deployment..."
echo "Local src directory: $SRC_DIR"

if [ ! -d "$SRC_DIR" ]; then
    echo "❌ ERROR: src/ directory missing"
    exit 1
fi

echo "📁 Ensuring directories exist on device..."
# Use process substitution to avoid subshell so variables persist
while IFS= read -r DIR; do
    REL="${DIR#$SRC_DIR}"
    REL="${REL#/}"

    # Skip root src dir (REL empty)
    if [ -z "$REL" ]; then
        continue
    fi

    echo "  - mkdir $REL"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    DRY RUN: $PORT_CMD fs mkdir :$REL"
    else
        $PORT_CMD fs mkdir ":$REL" 2>/dev/null || true
    fi
done < <(find "$SRC_DIR" -type d)


printf "\n📤 Uploading changed files...\n"
CHANGED_COUNT=0

while IFS= read -r FILE; do
    REL="${FILE#$SRC_DIR}"
    REL="${REL#/}"

    echo "cp \"$FILE\" \"$REL\""

    # Upload file (show mpremote errors for diagnosis)
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    DRY RUN: $PORT_CMD fs cp \"$FILE\" :$REL"
    else
        if ! $PORT_CMD fs cp "$FILE" ":$REL"; then
            echo "❌ Failed to upload $REL"
            exit 1
        fi
    fi

    CHANGED_COUNT=$((CHANGED_COUNT + 1))
done < <(find "$SRC_DIR" -type f)


echo ""
echo "🔁 Soft reset..."
$PORT_CMD reset

echo ""
echo "🎉 Deployment complete!"
echo "Files updated: $CHANGED_COUNT"
