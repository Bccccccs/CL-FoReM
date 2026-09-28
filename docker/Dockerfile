ARG BASE_IMAGE=mm_husky:deps
FROM ${BASE_IMAGE}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Bootstrap pip past the inherited apt OpenSSL / pip cryptography conflict.
RUN if [ -d /usr/lib/python3/dist-packages/OpenSSL ]; then mv /usr/lib/python3/dist-packages/OpenSSL /usr/lib/python3/dist-packages/OpenSSL.disabled; fi \
    && python3 -m pip install --no-cache-dir --no-deps pettingzoo==1.23.1 pyOpenSSL==24.3.0 cryptography==44.0.3 \
    && python3 -c 'import OpenSSL, pettingzoo; print(OpenSSL.__version__)'
RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/local/bin/python

COPY requirements-p0.txt /opt/mm-husky/requirements-p0.txt
RUN python3 -m pip install --no-cache-dir --no-deps --only-binary=:all: -r /opt/mm-husky/requirements-p0.txt \
    && python3 -m pip check

COPY entrypoint.sh /usr/local/bin/mm-entrypoint
RUN chmod +x /usr/local/bin/mm-entrypoint
ENV PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
    WANDB_MODE=offline QT_X11_NO_MITSHM=1 \
    ROS_MASTER_URI=http://127.0.0.1:11311 ROS_IP=127.0.0.1 \
    GAZEBO_MASTER_URI=http://127.0.0.1:11345
WORKDIR /root/mm_husky_ws/src/modulation_rl/scripts
ENTRYPOINT ["/usr/local/bin/mm-entrypoint"]
CMD ["sleep", "infinity"]
