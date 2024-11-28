#!/bin/bash -l
#SBATCH --job-name=pymorize-controller  # <<< This is the main job, it will launch subjobs if you have Dask enabled.
#SBATCH --account=ab0246                # <<< Adapt this to your computing account!
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --time=00:30:00                 # <<< You may need more time, adapt as needed!
export PREFECT_SERVER_ALLOW_EPHEMERAL_MODE=True
export PREFECT_SERVER_API_HOST=0.0.0.0
conda activate pymorize
prefect server start &
time pymorize process sample.yaml
