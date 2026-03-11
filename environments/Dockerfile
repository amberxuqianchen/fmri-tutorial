# syntax=docker/dockerfile:1

# ── Stage 1: base image with Miniconda ──────────────────────────────────────
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        bzip2 \
        ca-certificates \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO /tmp/miniconda.sh \
        https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash /tmp/miniconda.sh -b -p ${CONDA_DIR} \
    && rm /tmp/miniconda.sh \
    && conda clean -afy

# ── Stage 2: install full fmri-tutorial environment ─────────────────────────
FROM base AS final

# Create non-root user
RUN useradd -m -s /bin/bash fmriuser

# Copy environment spec and install
COPY environment_full.yml /tmp/environment_full.yml
RUN conda env create -f /tmp/environment_full.yml \
    && conda clean -afy \
    && rm /tmp/environment_full.yml

# Activate environment by default
ENV CONDA_DEFAULT_ENV=fmri-tutorial-full \
    PATH=/opt/conda/envs/fmri-tutorial-full/bin:$PATH

# Register the conda environment as a Jupyter kernel available to all users
RUN /opt/conda/envs/fmri-tutorial-full/bin/python -m ipykernel install \
        --name fmri-tutorial-full \
        --display-name "Python (fmri-tutorial-full)"

WORKDIR /home/fmriuser/tutorials
RUN chown fmriuser:fmriuser /home/fmriuser/tutorials

USER fmriuser

EXPOSE 8888

ENTRYPOINT ["jupyter", "lab", \
    "--ip=0.0.0.0", \
    "--port=8888", \
    "--no-browser", \
    "--notebook-dir=/home/fmriuser/tutorials"]
