#!/bin/bash
cd "$(dirname "$0")"
./release.sh "$@"
echo
read -p "Нажми Enter, чтобы закрыть окно."
