# Environments

This directory contains everything you need to reproduce the fmri-tutorial
software environment on your own machine, a cloud VM, an HPC cluster, or
inside a container.

---

## Contents

| File / directory | Purpose |
|---|---|
| `environment_full.yml` | Conda env with the complete toolchain |
| `environment_minimal.yml` | Lightweight Conda env for notebook browsing |
| `environment_nipype.yml` | Conda env focused on Nipype pipeline building |
| `setup_environment.sh` | Interactive helper script (conda) |
| `Dockerfile` | Multi-stage Docker image (full environment) |
| `docker-compose.yml` | Docker Compose services (Jupyter, MRIQC, fMRIPrep) |
| `singularity/fmriprep.def` | Singularity definition for fMRIPrep |
| `singularity/mriqc.def` | Singularity definition for MRIQC |

---

## Which environment should I use?

| Situation | Recommended option |
|---|---|
| Just want to run the notebooks | `environment_minimal.yml` |
| Full tutorial including QC and statistics | `environment_full.yml` |
| Building/running Nipype workflows (FSL, ANTs) | `environment_nipype.yml` |
| Reproducible container on a laptop | Docker (`Dockerfile` / `docker-compose.yml`) |
| HPC cluster (no Docker allowed) | Singularity (`.def` files) |

---

## Conda setup

### Prerequisites

Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
or [Anaconda](https://www.anaconda.com/products/individual).

### Quick start (interactive helper)

```bash
cd environments/
bash setup_environment.sh
```

The script will:
1. Check that conda is available.
2. Ask which environment you want (full / minimal / nipype).
3. Create the environment.
4. Register it as a Jupyter kernel.
5. Print next-steps instructions.

### Manual setup

```bash
# full environment
conda env create -f environments/environment_full.yml

# minimal environment
conda env create -f environments/environment_minimal.yml

# nipype environment
conda env create -f environments/environment_nipype.yml

# activate (replace with the env name you chose)
conda activate fmri-tutorial-full

# register as a Jupyter kernel
python -m ipykernel install --user \
    --name fmri-tutorial-full \
    --display-name "Python (fmri-tutorial-full)"

# launch JupyterLab
jupyter lab
```

### Updating an existing environment

```bash
conda env update --name fmri-tutorial-full \
    --file environments/environment_full.yml --prune
```

---

## Docker setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS / Windows)
  or Docker Engine (Linux).
- [Docker Compose](https://docs.docker.com/compose/install/) v2+.

### Build and run JupyterLab

```bash
cd environments/

# Build the image and start JupyterLab
docker compose up jupyter

# Open the printed URL (http://127.0.0.1:8888/lab?token=…) in your browser.
```

Your repository root is mounted at `/home/fmriuser/tutorials` inside the
container, so changes are reflected immediately.

### Run MRIQC via Docker

```bash
# Create output directories first
mkdir -p data/mriqc_output data/mriqc_work

docker compose run --rm mriqc \
    /data /out participant \
    --participant-label sub-01
```

### Run fMRIPrep via Docker

```bash
mkdir -p data/fmriprep_output data/fmriprep_work

docker compose run --rm fmriprep \
    /data /out participant \
    --participant-label sub-01 \
    --fs-license-file /opt/freesurfer/license.txt
```

> **FreeSurfer license** – place your `license.txt` at
> `data/freesurfer_license` before running fMRIPrep.

### Useful Docker commands

```bash
# Stop all services
docker compose down

# Rebuild after changing environment_full.yml
docker compose build --no-cache jupyter

# Open a shell inside the running container
docker exec -it fmri-jupyter bash
```

---

## Singularity setup

Singularity (or [Apptainer](https://apptainer.org)) is the preferred
container runtime on most HPC clusters.

### Build images

```bash
cd environments/singularity/

# fMRIPrep
sudo singularity build fmriprep.sif fmriprep.def

# MRIQC
sudo singularity build mriqc.sif mriqc.def
```

On clusters where you do not have root access use `--fakeroot` (if enabled)
or build locally and copy the `.sif` file.

### Run fMRIPrep

```bash
singularity run --cleanenv fmriprep.sif \
    /path/to/bids /path/to/output participant \
    --participant-label sub-01 \
    --fs-license-file /path/to/license.txt \
    --work-dir /path/to/work
```

### Run MRIQC

```bash
singularity run --cleanenv mriqc.sif \
    /path/to/bids /path/to/output participant \
    --participant-label sub-01 \
    --work-dir /path/to/work
```

### SLURM example

```bash
#!/bin/bash
#SBATCH --job-name=fmriprep
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00

module load singularity

singularity run --cleanenv /path/to/fmriprep.sif \
    /data/bids /data/output participant \
    --participant-label sub-01 \
    --fs-license-file /data/license.txt \
    --nthreads 8 --mem-mb 30000 \
    --work-dir /scratch/fmriprep_work
```

---

## Troubleshooting

### Conda: `PackagesNotFoundError`

Make sure `conda-forge` is in your channel list and try:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
conda env create -f environments/environment_full.yml
```

### Conda: environment solve takes too long

Use [mamba](https://mamba.readthedocs.io) as a drop-in replacement:

```bash
conda install -n base -c conda-forge mamba
mamba env create -f environments/environment_full.yml
```

### Jupyter: kernel not found after environment creation

Re-register the kernel:

```bash
conda activate fmri-tutorial-full
python -m ipykernel install --user \
    --name fmri-tutorial-full \
    --display-name "Python (fmri-tutorial-full)"
```

### Docker: port 8888 already in use

Either stop the process using port 8888 or change the host port:

```bash
# ad-hoc override
docker compose run --rm -p 8889:8888 jupyter
```

### Docker: permission errors on Linux

The `docker-compose.yml` passes your current UID/GID to MRIQC and fMRIPrep.
Export them explicitly if needed:

```bash
export UID=$(id -u) GID=$(id -g)
docker compose run --rm mriqc ...
```

### Singularity: `FATAL: container creation failed`

Ensure the `.sif` was built with a matching Singularity/Apptainer version.
Try pulling directly:

```bash
singularity pull docker://nipreps/fmriprep:latest
```

### Nipype: FSL / ANTs not found

Add the tool binaries to `PATH` before starting Python:

```bash
# FSL (adjust path to your installation)
export FSLDIR=/usr/local/fsl
source "${FSLDIR}/etc/fslconf/fsl.sh"
export PATH="${FSLDIR}/bin:${PATH}"

# ANTs
export PATH=/usr/local/ANTs/bin:${PATH}
```
