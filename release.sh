#!/bin/bash
# Cuts a release. Bumps the version, tags it, pushes, and CI builds all
# four platforms and attaches them to the release.
#
#   ./release.sh              patch bump   (1.0.0 -> 1.0.1)
#   ./release.sh minor        minor bump   (1.0.1 -> 1.1.0)
#   ./release.sh major        major bump   (1.1.0 -> 2.0.0)
#   ./release.sh 1.4.2        that exact version
#   ./release.sh minor -n     примерка: показать и ничего не делать

set -e
cd "$(dirname "$0")"

DRY=0
ARG=""
for a in "$@"; do
  case "$a" in
    --dry-run|-n) DRY=1 ;;
    *) ARG="$a" ;;
  esac
done
ARG="${ARG:-patch}"

# --- где мы вообще
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Здесь нет git-репозитория."; exit 1
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
  echo "Ты на ветке '$BRANCH', а релизы делаются с main."; exit 1
fi

# --- незакоммиченное (при примерке не мешаем)
if [ "$DRY" = "0" ] && [ -n "$(git status --porcelain)" ]; then
  echo "Есть незакоммиченные изменения:"
  git status --short | sed 's/^/   /'
  echo
  if [ -t 0 ]; then
    read -p "Закоммитить их перед релизом? [y/N] " ok
  else
    ok=""   # запускали не из терминала — ничего не спрашиваем
  fi
  case "$ok" in
    [yY]*) git add -A; git commit -q -m "Changes for the next release" ;;
    *) echo "Останавливаюсь. Сначала закоммить изменения."; exit 1 ;;
  esac
fi

# --- какая версия следующая
git fetch --tags --quiet 2>/dev/null || true
LAST=$(git tag -l 'v*' | sort -V | tail -1)
LAST=${LAST:-v0.0.0}
CUR=${LAST#v}
IFS=. read -r MA MI PA <<< "$CUR"

case "$ARG" in
  patch) NEW="$MA.$MI.$((PA + 1))" ;;
  minor) NEW="$MA.$((MI + 1)).0" ;;
  major) NEW="$((MA + 1)).0.0" ;;
  [0-9]*.[0-9]*.[0-9]*) NEW="$ARG" ;;
  *) echo "Не понял «$ARG». Можно: patch, minor, major или 1.2.3"; exit 1 ;;
esac

if git rev-parse "v$NEW" >/dev/null 2>&1; then
  echo "Тег v$NEW уже существует."; exit 1
fi

echo "  было:  $LAST"
echo "  будет: v$NEW"
echo

if [ "$DRY" = "1" ]; then
  echo "Это была примерка, ничего не сделано."
  exit 0
fi

# --- версия внутри приложения должна совпадать с тегом
sed -i '' "s/\"CFBundleShortVersionString\": \"[^\"]*\"/\"CFBundleShortVersionString\": \"$NEW\"/" hush.spec
if [ -n "$(git status --porcelain hush.spec)" ]; then
  git add hush.spec
  git commit -q -m "Bump version to $NEW"
fi

git push -q origin main
git tag -a "v$NEW" -m "Hush $NEW"
git push -q origin "v$NEW"

REPO=$(git remote get-url origin | sed -E 's#.*github.com[:/]([^/]+/[^/.]+).*#\1#')
echo "Тег v$NEW отправлен. Сборка пошла."
echo
echo "  прогресс:  https://github.com/$REPO/actions"
echo "  релиз:     https://github.com/$REPO/releases/tag/v$NEW"
echo
echo "Через 5-10 минут в релизе появятся сборки под все четыре системы."
