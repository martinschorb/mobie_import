FROM mambaorg/micromamba:focal

MAINTAINER Martin Schorb (martin.schorb@embl.de)

ARG ARCH=linux-64
ARG MAMBA_DOCKERFILE_ACTIVATE=1

ENV IMOD_VER=4.11.24 CUDA_VER=8.0

ENV SHELL=/bin/bash LANG=C.UTF-8 LC_ALL=C.UTF-8

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*


USER $MAMBA_USER

RUN micromamba activate base \
    && \
    IMOD_INSTALLER=imod_"$IMOD_VER"_RHEL7-64_CUDA"$CUDA_VER".sh \
    && \
    wget https://bio3d.colorado.edu/imod/AMD64-RHEL5/$IMOD_INSTALLER --no-check-certificate \
    && \
    bash $IMOD_INSTALLER -yes -dir $HOME/IMOD -skip \
    && \
    export PATH=$PATH:$HOME/IMOD/bin\
    && \
    micromamba install --yes -n base -c conda-forge \
    python=3.10 \
    mobie_utils \
    && \
    micromamba clean --all --yes

ENTRYPOINT bash