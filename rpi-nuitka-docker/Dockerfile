# Base: lightweight Ubuntu with qemu-user-static
FROM ubuntu:22.04

# Enable ARM emulation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        qemu-user-static \
        binfmt-support \
        python3 \
        python3-pip \
        python3-dev \
        build-essential \
        git \
        rsync \
        ca-certificates \
        sudo && \
    rm -rf /var/lib/apt/lists/*

# Create user to match Pi UID/GID
RUN useradd -m -u 1000 pi
WORKDIR /home/pi

# Copy Pi rootfs into container
COPY rootfs/ /rpi-rootfs/

# Add qemu static binary
RUN cp /usr/bin/qemu-arm-static /rpi-rootfs/usr/bin/

# Set up chroot entrypoint
COPY build-nuitka.sh /usr/local/bin/build-nuitka.sh
RUN chmod +x /usr/local/bin/build-nuitka.sh

ENTRYPOINT ["/usr/local/bin/build-nuitka.sh"]
