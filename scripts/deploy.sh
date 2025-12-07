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

# If a .env file exists at project root (or WIFI_SSID/WIFI_PASSWORD are set
# in the environment), generate a temporary `src/local_config.py` so
# credentials are not stored in the main `src/config.py` file. The temp file
# will be removed after deployment.
ENV_FILE="$PROJECT_ROOT/.env"
TMP_LOCAL_CONFIG="$SRC_DIR/local_config.py"
CLEAN_LOCAL_CONFIG=0

escape_single_quote() {
    # Escape single quotes for safe single-quoted here-doc insertion.
    printf "%s" "$1" | sed "s/'/'\\''/g"
}

if [ -f "$ENV_FILE" ]; then
    echo "Found .env — generating temporary src/local_config.py"
    SSID_RAW=$(grep -E '^WIFI_SSID=' "$ENV_FILE" || true)
    PASS_RAW=$(grep -E '^WIFI_PASSWORD=' "$ENV_FILE" || true)
    SSID=${SSID_RAW#WIFI_SSID=}
    PASS=${PASS_RAW#WIFI_PASSWORD=}
    # strip surrounding quotes if present
    # Strip surrounding single or double quotes if present
    SSID=$(printf "%s" "$SSID" | sed -E "s/^\"(.*)\"$/\\1/; s/^'(.*)'$/\\1/")
    PASS=$(printf "%s" "$PASS" | sed -E "s/^\"(.*)\"$/\\1/; s/^'(.*)'$/\\1/")
    SSID_ESC=$(escape_single_quote "$SSID")
    PASS_ESC=$(escape_single_quote "$PASS")
    cat > "$TMP_LOCAL_CONFIG" <<EOF
WIFI_SSID = '$SSID_ESC'
WIFI_PASSWORD = '$PASS_ESC'
EOF
    CLEAN_LOCAL_CONFIG=1
elif [ -n "${WIFI_SSID:-}" ] && [ -n "${WIFI_PASSWORD:-}" ]; then
    echo "Using WIFI_SSID/WIFI_PASSWORD from environment to generate temporary src/local_config.py"
    SSID_ESC=$(escape_single_quote "$WIFI_SSID")
    PASS_ESC=$(escape_single_quote "$WIFI_PASSWORD")
    cat > "$TMP_LOCAL_CONFIG" <<EOF
WIFI_SSID = '$SSID_ESC'
WIFI_PASSWORD = '$PASS_ESC'
EOF
    CLEAN_LOCAL_CONFIG=1
fi

if [ "$DRY_RUN" -eq 1 ]; then
    echo "🔍 Dry-run mode: skipping device check and remote actions"
else
    echo "🔍 Checking device..."
    if ! $PORT_CMD exec "print('connected')" 2>/dev/null; then
        echo "⚠️ Device check failed — attempting soft reset and retry..."
        # Try a soft reset to stop any running user program and free raw-REPL
        if ! $PORT_CMD reset 2>/dev/null; then
            echo "⚠️ Soft reset failed; will continue and try file operations (they may fail)"
        else
            # give device a moment to restart
            sleep 1
            if ! $PORT_CMD exec "print('connected')" 2>/dev/null; then
                echo "⚠️ Still cannot talk to device; file operations may fail"
            fi
        fi
    fi
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

# Upload `local_config.py` first if it exists (generated from .env or env vars)
if [ -f "$SRC_DIR/local_config.py" ]; then
    REL="local_config.py"
    echo "cp \"$SRC_DIR/local_config.py\" \"$REL\""
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    DRY RUN: $PORT_CMD fs cp \"$SRC_DIR/local_config.py\" :$REL"
    else
        if $PORT_CMD fs cp "$SRC_DIR/local_config.py" ":$REL"; then
            CHANGED_COUNT=$((CHANGED_COUNT + 1))
        else
            echo "⚠️ Failed to upload $REL (continuing)"
        fi
    fi
fi

while IFS= read -r FILE; do
    REL="${FILE#$SRC_DIR}"
    REL="${REL#/}"

    echo "cp \"$FILE\" \"$REL\""

    # Upload file (show mpremote errors for diagnosis)
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    DRY RUN: $PORT_CMD fs cp \"$FILE\" :$REL"
    else
        if $PORT_CMD fs cp "$FILE" ":$REL"; then
            CHANGED_COUNT=$((CHANGED_COUNT + 1))
        else
            echo "⚠️ Failed to upload $REL (continuing)"
        fi
    fi
done < <(find "$SRC_DIR" -type f ! -name 'local_config.py')


echo ""
echo "🔁 Soft reset..."
PORT_CMD_reset() {
    # Wrapper to run reset and avoid aborting the whole script on failure.
    if ! $PORT_CMD reset; then
        echo "⚠️ Warning: soft reset failed (could not enter raw REPL); continuing"
        return 1
    fi
    return 0
}

if [ "$DRY_RUN" -eq 1 ]; then
    echo "    DRY RUN: $PORT_CMD reset"
else
    # Attempt reset but don't let it abort the deployment on failure
    PORT_CMD_reset || true
fi

# Clean up any generated local_config.py
if [ "$CLEAN_LOCAL_CONFIG" -eq 1 ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    DRY RUN: would remove $TMP_LOCAL_CONFIG"
    else
        rm -f "$TMP_LOCAL_CONFIG" || true
        echo "🧹 Removed temporary local config: $TMP_LOCAL_CONFIG"
    fi
fi

echo ""
echo "🎉 Deployment complete!"
echo "Files updated: $CHANGED_COUNT"
