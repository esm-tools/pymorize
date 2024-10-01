##############
Usage Examples
##############

The directory ``./examples`` shows how you can use ``pymorize``
in batch mode. You can run the example via::

  sbatch -A <YOUR ACCOUNT> pymorize.slurm

The ``sample.yaml`` file shows a configuration for an ``AWI-CM 1`` 
simulation, and processes one set of files, ``fgco2``, which was
called ``CO2f`` in ``FESOM 1``. The default pipeline is used, and
nothing special is done.

If you want to cleanup after your run::

  python cleanup.py

or::

  ./cleanup.py

Monitoring the Dask Progress
============================

``pymorize`` makes heavy use of ``dask``, and ``dask`` provides a dashboard to view the progress, however, you 
need to set up SSH tunnels to properly see it. As a convenient shortcut, ``pymorize`` has tunneling built into 
it's command line interface::

  pymorize ssh-tunnel --gateway=<LOGIN_NODE> --username=<USER> --compute-node=<JOB_NODE>

Note that ``JOB_NODE`` is where your main ``pymorize`` job starts, and **not** one of the dask worker
jobs.

You can also generate the required SSH tunnels by hand. On your local workstation::
  
  ssh -L 8080:localhost:8080 -L 8080:<COMPUTE_NODE>:8787 <USER>@<SPECIFIC_LOGIN_NODE>

On the login node::

  ssh -L 8080:localhost:8787 <COMPUTE_NODE>
