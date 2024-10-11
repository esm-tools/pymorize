====================================
Usage: Running ``pymorize`` on Slurm
====================================

See the ``examples`` directory for a sample configuration file, ``sample.yaml``. This contains
three rules, each of which runs the ``default`` pipeline on a different dataset. To run this, you
can use the provided ``pymorize.slurm`` script, which looks like this:

.. literalinclude:: ../examples/pymorize.slurm
   :linenos:
   :language: bash

After analysing the configuration file, the script will submit several ``Dask`` worker jobs to
Slurm, and then feed the pipeline jobs to those workers. The script waits for all the jobs to finish
before completing, so if one of the pipelines fails, the rest will still keep going. You can monitor the
progress of the jobs by running ``squeue -u <username>``, and follow in more detail on the Prefect dashboard.


