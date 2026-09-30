#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
container=${FOREM_CONTAINER:-forem-dev}
image=${FOREM_IMAGE:-mm_husky:node01}
command=${1:-help}
if (($#)); then shift; fi
case "$command" in
  image-build)
    docker build --network host -f "$root/docker/Dockerfile.node01" -t "$image" "$root/docker"
    ;;
  up)
    if docker container inspect "$container" >/dev/null 2>&1; then
      mounted=$(docker inspect "$container" --format '{{range .Mounts}}{{if eq .Destination "/root/mm_husky_ws"}}{{.Source}}{{end}}{{end}}')
      [[ "$mounted" == "$root" ]] || { echo "Refusing container with another workspace: $mounted" >&2; exit 1; }
      [[ $(docker inspect "$container" --format '{{.State.Running}}') == true ]] || docker start "$container"
    else
      docker run -d --name "$container" --init --network bridge --shm-size=8g \
        --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all \
        --mount "type=bind,src=$root,dst=/root/mm_husky_ws" "$image"
    fi
    ;;
  shell) docker exec -it "$container" /usr/local/bin/mm-entrypoint bash --norc ;;
  exec) docker exec "$container" /usr/local/bin/mm-entrypoint "$@" ;;
  *) echo "Usage: $0 {image-build|up|shell|exec COMMAND...}" ;;
esac
