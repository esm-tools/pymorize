=====================================
Usage: ``pymorize``'s Building Blocks
=====================================

The ``pymorize`` CLI has a few basic concepts you should be familiar with before you start using it. This guide
will give you a brief overview of these concepts. Suggestions for improvements are always welcome!

Configuration
-------------

The configuration is the central piece of the ``pymorize`` CLI. It is a YAML file that specifies the behavior of
the CLI. The configuration file is divided into four sections:

1. ``pymorize``: This section contains the configuration for the CLI itself. It specifies the program version, log verbosity, the location of the user configuration file, and the location of the log file.
2. ``general``: This section contains information that will be passed to all pipelines. You will specify the location of the data directory (your model output files),
   the output directory (where re-written data should be stored), the location of the CMOR tables, the location of your model's geometry description file (or files), and
   any other information that may be needed by all pipelines.
3. ``pipelines``: This section contains the configuration for the pipelines. Each pipeline is a sequence of operations that will be applied to the data. You can specify the name of the pipeline, the class
   that implements the pipeline, and any parameters that the pipeline needs.
4. ``rules``: This section contains the configuration for the rules. Each rule describes a set of files needed to produce a CMOR output variable. You must specify the CMOR variable of interest, the input
   patterns to use to find the files, and the pipeline(s) to apply to the files.
5. ``inherit``: This section contains key-value pairs that will be added to all rules, unless the rules already have an attribute
   of this name attached to them.

Pipelines
---------

:py:class:`~pymorize.pipeline.Pipeline`'s come in two flavors. The first is a predefined pipeline, which is
attached to the configuration via a ``uses`` directive. In the user configuration file, you would specify it
like this:

  .. code-block:: yaml
  
      # ... other configuration
      pipelines:
        - name: my_pipeline
          uses: pymorize.pipeline.DefaultPipeline
      # ... other configuration

Alternatively you can define your own pipeline by specifying the steps it should take. Here is an example of a
custom pipeline:

  .. code-block:: yaml
  
      # ... other configuration
      pipelines:
        - name: my_pipeline
          steps:
            - pymorize.generic.dummy_load_data
            - pymorize.generic.dummy_process_data
            - pymorize.generic.dummy_save_data
      # ... other configuration

Rules
-----

Rules are the heart of the ``pymorize`` CLI. They specify the files needed to produce a CMOR output variable. Each rule has a name, a CMOR variable, and a list of input patterns. The input patterns are used to find the files needed to produce the CMOR output variable. Here is an example of a rule:

  .. code-block:: yaml
  
      # ... other configuration
      rules:
        - name: my_rule
          cmor_variable: tas
          patterns:
            - 'tas_*.nc'
          pipelines:
            - my_pipeline
      # ... other configuration

  .. note::

       If you do not specify a pipeline, the default pipeline will be run!

Inheritance
-----------

Rules can inherit global values. To do so, you should include them in the ``inherit`` section of the configuration file. Here is an example:

  .. code-block:: yaml
  
      # ... other configuration
      inherit:
        frequency: mon
      # ... other configuration

      rules:
        - name: my_rule
          cmor_variable: tas
          patterns:
            - 'tas_*.nc'
          pipelines:
            - my_pipeline

The rule ``my_rule`` will inherit the frequency ``mon`` from the global configuration, and can be accessed in
Python code as ``rule_spec.frequency``.

