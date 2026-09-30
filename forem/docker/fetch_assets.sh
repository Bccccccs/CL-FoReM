#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fetch() {
  local name=$1 url=$2 revision=$3
  local dest="$root/assets/gazebo/$name"
  if [[ ! -d "$dest/.git" ]]; then
    mkdir -p "$dest"
    git -C "$dest" init -q
    git -C "$dest" remote add origin "$url"
  fi
  [[ -z $(git -C "$dest" status --porcelain) ]] || { echo "Dirty assets: $dest" >&2; return 1; }
  if [[ $(git -C "$dest" rev-parse HEAD 2>/dev/null || true) != "$revision" ]]; then
    [[ -z $(git -C "$dest" status --porcelain) ]] || { echo "Dirty assets: $dest" >&2; return 1; }
    git -C "$dest" fetch --depth 1 origin "$revision"
    git -C "$dest" checkout --detach FETCH_HEAD
  fi
  test "$(git -C "$dest" rev-parse HEAD)" = "$revision"
}
fetch pal_gazebo_worlds https://github.com/pal-robotics/pal_gazebo_worlds.git 0029fabc9aef3330de422c9dda0a09dd6592a0fb
fetch aws-bookstore https://github.com/aws-robotics/aws-robomaker-bookstore-world.git ed542eb41809d5c5f1c67f32d4ba24e0e90886b3
