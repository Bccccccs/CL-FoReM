#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
container=${MM_CONTAINER:-mmhusky-node01}
image=${MM_IMAGE:-mm_husky:node01}
command=${1:-help}
if (($#)); then shift; fi
run() { local runtime_image
  runtime_image=$(docker inspect "$container" --format '{{.Image}}')
  docker exec "$container" /usr/local/bin/mm-entrypoint env P0_IMAGE_ID="$runtime_image" P0_CONTAINER="$container" \
  GAZEBO_MODEL_PATH=/root/mm_husky_ws/src/modulation_rl/gazebo_models:/root/mm_husky_ws/assets/gazebo/pal_gazebo_worlds/models:/root/mm_husky_ws/assets/gazebo/aws-bookstore/models:/usr/share/gazebo-11/models "$@"; }
case "$command" in
  build)
    dockerfile=${MM_DOCKERFILE:-Dockerfile.node01}
    if [[ $dockerfile != Dockerfile ]]; then
      # node01: public Noetic base; direct connection (no proxy build-args), see ENV.md.
      docker build --network host -f "$root/docker/$dockerfile" -t "$image" "$root/docker"
      exit
    fi
    # Legacy source-machine path: incremental build on the audited local mm_husky:deps.
    base=${MM_BASE_IMAGE:-mm_husky:deps}
    expected=sha256:7e08e15e9865c49c7ee903f6e5b9172ac4d1438574c9351c600181a41e75024d
    actual=$(docker image inspect "$base" --format '{{.Id}}')
    if [[ -z ${MM_BASE_IMAGE:-} && "$actual" != "$expected" ]]; then
      echo 'Base image changed; select an audited base with MM_BASE_IMAGE.' >&2; exit 1
    fi
    docker build --network host --build-arg HTTP_PROXY --build-arg HTTPS_PROXY \
      --build-arg http_proxy --build-arg https_proxy --build-arg NO_PROXY \
      --build-arg "BASE_IMAGE=$base" -t "$image" "$root/docker"
    ;;
  up)
    if docker container inspect "$container" >/dev/null 2>&1; then
      echo "$container already exists; checking mounted workspace."
      [[ $(docker inspect "$container" --format '{{.State.Running}}') == true ]] || docker start "$container"
    else
      gui_args=()
      if [[ -n ${DISPLAY:-} && -d /tmp/.X11-unix ]]; then
        gui_args+=(-e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix:ro)
        auth=${XAUTHORITY:-}
        if [[ -n "$auth" && -f "$auth" ]]; then
          gui_args+=(-v "$auth:/tmp/mm.xauthority:ro" -e XAUTHORITY=/tmp/mm.xauthority)
        fi
      fi
      docker run -d --name "$container" --init --network bridge --shm-size=8g \
        --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all \
        --label mm_husky.managed=true \
        --mount "type=bind,src=$root,dst=/root/mm_husky_ws" \
        "${gui_args[@]}" "$image"
    fi
    testfile=$(mktemp "$root/.docker-mount-check.XXXXXX")
    trap 'rm -f "$testfile"' EXIT
    token=$(cat /proc/sys/kernel/random/uuid)
    echo "$token" > "$testfile"
    [[ $(docker exec "$container" cat "/root/mm_husky_ws/$(basename "$testfile")") == "$token" ]]
    ;;
  check) run nvidia-smi -L; run python3 -u /root/mm_husky_ws/docker/check.py ;;
  shell) docker exec -it "$container" /usr/local/bin/mm-entrypoint bash --norc ;;
  exec) run "$@" ;;
  analytical) run roslaunch modulation_rl n2m2_husky_analytical.launch gui:=false "$@" ;;
  env-smoke) run python3 -u /root/mm_husky_ws/docker/env_smoke.py ;;
  train-smoke) run python3 -u /root/mm_husky_ws/docker/train_smoke.py ;;
  gazebo-smoke) run python3 -u /root/mm_husky_ws/docker/gazebo_smoke.py ;;
  gazebo-check) run python3 -u /root/mm_husky_ws/docker/gazebo_smoke.py --startup-only ;;
  gazebo)
    run xvfb-run -a roslaunch modulation_rl n2m2_husky_empty_world.launch \
      world_name:=/usr/share/gazebo-11/worlds/empty.world p0_laser:=true p0_start_pose:=true gui:=false "$@"
    ;;
  gazebo-gui)
    run roslaunch modulation_rl n2m2_husky_empty_world.launch \
      world_name:=/usr/share/gazebo-11/worlds/empty.world p0_laser:=true p0_start_pose:=true gui:=true "$@"
    ;;
  eval) run python3 -u eval.py --task simpleobstacle --world-type sim --seed 11 "$@" ;;
  train) run python3 -u main.py --task simpleobstacle --world-type sim --seed 11 "$@" ;;
  stop-ros) run pkill -INT -f '^/usr/bin/python3 /opt/ros/noetic/bin/roslaunch ' ;;
  *) echo "Usage: $0 {build|up|check|shell|exec COMMAND...|analytical|env-smoke|train-smoke|gazebo|gazebo-gui|gazebo-check|gazebo-smoke|stop-ros|eval|train}" ;;
esac
