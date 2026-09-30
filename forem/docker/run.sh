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
      gpu_args=()
      if [[ "${FOREM_GPU:-0}" == 1 ]]; then
        gpu_args=(--runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all)
      fi
      docker run -d --name "$container" --init --network bridge --shm-size=2g \
        "${gpu_args[@]}" -w /root/mm_husky_ws \
        --entrypoint /usr/local/bin/forem-entrypoint \
        --mount "type=bind,src=$root,dst=/root/mm_husky_ws" \
        --mount "type=bind,src=$root/docker/forem-entrypoint.sh,dst=/usr/local/bin/forem-entrypoint,readonly" \
        "$image" sleep infinity
    fi
    # exec runs as the host uid (build files stay owned by the host user); it must traverse /root.
    docker exec -u 0 "$container" chmod 711 /root
    ;;
  shell) docker exec -it -u "$(id -u):$(id -g)" -e HOME=/tmp/forem-home -w /root/mm_husky_ws "$container" /usr/local/bin/forem-entrypoint bash --norc ;;
  exec) docker exec -u "$(id -u):$(id -g)" -e HOME=/tmp/forem-home -w /root/mm_husky_ws "$container" /usr/local/bin/forem-entrypoint "$@" ;;
  bg) docker exec -d -u "$(id -u):$(id -g)" -e HOME=/tmp/forem-home -w /root/mm_husky_ws "$container" /usr/local/bin/forem-entrypoint "$@" ;;
  *) echo "Usage: $0 {image-build|up|shell|exec COMMAND...|bg COMMAND...}" ;;
esac
