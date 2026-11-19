#!/bin/sh
set -eu

level=${1:-patch}

latest_tag=$(git tag --list 'v*.*.*' --sort=-v:refname | head -n 1)
latest_version=${latest_tag#v}
latest_version=${latest_version:-0.0.0}
IFS=. read -r major minor patch <<EOF
$latest_version
EOF

case "$level" in
  major)
    version=$((major + 1)).0.0
    ;;
  minor)
    version=${major}.$((minor + 1)).0
    ;;
  patch)
    version=${major}.${minor}.$((patch + 1))
    ;;
  *)
    echo 'Use patch, minor, or major.' >&2
    exit 1
    ;;
esac

tag="v${version}"

test "$(git branch --show-current)" = main || {
  echo 'Run the release from main.' >&2
  exit 1
}

git add --all
git diff --cached --check
if ! git diff --cached --quiet; then
  git commit -m "Release $tag"
fi
git push origin main
git tag "$tag"
git push origin "$tag"
