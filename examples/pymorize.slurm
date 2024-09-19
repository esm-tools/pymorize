#!/bin/bash -l
#SBATCH --account=ab0246
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=00:10:00
# export PREFECT_SERVER_ALLOW_EPHEMERAL_MODE=False
conda activate pymorize
prefect server start &
pymorize process sample.yaml
