# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

FROM registry.fedoraproject.org/fedora:latest

# Install native compilation toolchain, GNOME/GTK4/Libadwaita headers, Blueprint compiler, and utilities
RUN dnf update -y && \
    dnf install -y \
        gcc \
        gcc-c++ \
        meson \
        ninja-build \
        pkg-config \
        git \
        make \
        gettext \
        gtk4-devel \
        libadwaita-devel \
        libadwaita-doc \
        gobject-introspection-devel \
        blueprint-compiler \
        appstream \
        appstream-devel \
        desktop-file-utils \
        python3 \
        python3-devel \
        python3-pip \
        sudo \
        which && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Install uv package manager
COPY --from=uv_bin /uv /uvx /usr/local/bin/

# Create non-root developer user with passwordless sudo
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
ENV PATH="/home/$USERNAME/.local/bin:${PATH}"
WORKDIR /workspaces/cartridges
