========================================
Develop: Including Custom Pipeline Steps
========================================

To include custom pipeline steps in your pipeline, you can add them to the
pipeline's ``steps`` attribute. For example, to include a custom step that
is defined in ``my_module.py`` and is named ``my_custom_step``, you can
declare it like this:

.. code-block:: yaml

  pipelines:
   - name: custom_pipeline
     steps:
        - custom_package.my_module.my_custom_step

In the file ``my_module.py``, which is somewhere in ``custom_package``,
you can define the custom step like this:

.. code-block:: python

   def my_custom_step(data, rule):
       # Do something with the data
       return data

This works best if you have a full-fledged Python package, with a proper
``setup.py`` file, that you can install in your environment. If you don't
have a package, you can also define the custom step in a separate Python
file and import it in your pipeline configuration file:

.. code-block:: yaml

  pipelines:
   - name: custom_pipeline
     steps:
        - script:///albedo/home/pgierz/Code/playground/my_custom_step.py:my_custom_step

Note that the ``script://`` prefix is required! Thereafter, you should still start your
path with a slash, e.g. use an absolute path all the way. The function inside your file
should be defined like this with a colon ``:`` followed by the function name.
