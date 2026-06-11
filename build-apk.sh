#!/usr/bin/env bash
# Build l'APK dans Docker (aucun Android Studio requis) et l'extrait ici.
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="formae-deeplink-poc-build"

echo "==> Build de l'image Docker (télécharge le SDK Android au 1er run, soyez patient)..."
# --platform linux/amd64 : indispensable sur Mac Apple Silicon, aapt2 n'existe
# qu'en x86_64 (voir Dockerfile).
docker build --platform linux/amd64 -t "$IMAGE" .

echo "==> Extraction de l'APK..."
CID="$(docker create --platform linux/amd64 "$IMAGE")"
docker cp "$CID:/project/app/build/outputs/apk/debug/app-debug.apk" ./formae-poc.apk
docker rm "$CID" > /dev/null

echo ""
echo "==> APK prêt : $(pwd)/formae-poc.apk"
echo "    Lancez maintenant : uv run receiver-server.py"
echo "    Puis, sur le téléphone Android (dans Chrome), ouvrez l'URL affichée."
echo "    L'app se télécharge depuis la page d'onboarding (autoriser les sources inconnues)."
