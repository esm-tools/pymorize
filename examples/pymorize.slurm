#!/bin/bash -l
#SBATCH --account=ab0246
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=00:30:00
# export PREFECT_SERVER_ALLOW_EPHEMERAL_MODE=False
export PREFECT_SERVER_API_HOST=0.0.0.0
conda activate pymorize
prefect server start &
time pymorize process sample.yaml
