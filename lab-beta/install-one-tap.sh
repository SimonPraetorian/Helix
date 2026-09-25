#!/data/data/com.termux/files/usr/bin/bash
set -eu
source_dir="$(cd "$(dirname "$0")" && pwd)"
project_dir="$HOME/helix-floor"
mkdir -p "$project_dir" "$HOME/.shortcuts"
cp -R "$source_dir/." "$project_dir/"
cat > "$HOME/.shortcuts/Helix Floor" <<'LAUNCH'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/helix-floor" || exit 1
if python - <<'PY'
import urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:8765/api/state', timeout=1)
except Exception:
    raise SystemExit(1)
PY
then
    termux-open-url 'http://127.0.0.1:8765'
    exit 0
fi
(
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if python - <<'PY'
import urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:8765/api/state', timeout=1)
except Exception:
    raise SystemExit(1)
PY
    then
      termux-open-url 'http://127.0.0.1:8765'
      exit 0
    fi
    sleep 1
  done
  echo 'Dashboard did not start; check the Termux window.'
) &
exec python -m helix.floor
LAUNCH
chmod 700 "$HOME/.shortcuts/Helix Floor"
chmod 700 "$HOME/.shortcuts"
printf 'Helix Floor installed. Add a Termux:Widget launcher shortcut or widget to your home screen.\n'
