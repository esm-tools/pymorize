==========================================
Usage: The ``pymorize`` Configuration File
==========================================

The configuration file used for ``pymorize`` is a simple YAML file. A breakdown of each section is provided below.

+----------------+----------+--------------+-------------------------------------------------------------+
| Parameter      | Required | Type         | Description                                                 |
+================+==========+==============+=============================================================+
| cmor_table_dir | REQUIRED | Path         | The directory where the CMOR tables are stored. This is     |
|                |          |              | used to find the CMOR tables when reading in data.          |
+----------------+----------+--------------+-------------------------------------------------------------+
| output_dir     | REQUIRED | Path         | The main directory where model output is stored.            |
+----------------+----------+--------------+-------------------------------------------------------------+
| rules          | REQUIRED | List of      | A list of rules that define how to process the data.        |
|                |          | Dictionaries | Each rule is a dictionary with the following keys:          |
|                |          |              |                                                             |
|                |          |              | - model_variable: The name of the variable as it is in the  |
|                |          |              |   model output.                                             |
|                |          |              | - cmor_variable: The name of the variable as it is in the   |
|                |          |              |   CMOR tables.                                              |
|                |          |              | - cmor_table: The name of the CMOR table to use.            |
|                |          |              | - input_patterns: list of patterns to apply this rule to    |
|                |          |              | - output_pattern: list of files to create. See note about   |
|                |          |              |   placeholder replacements                                  |
|                |          |              | - actions: list of actions. See below for more information. |
|                |          |              |                                                             |
+----------------+----------+--------------+-------------------------------------------------------------+

Example
-------
To better illustrate, here is a full example with a single rule:

.. code-block:: yaml

  cmor_table_dir: /path/to/table/dir
  output_dir: /path/to/output/dir
  rules:
    - model_variable: salt
      model_units: PSU
      cmor_variable: so
      cmor_table: CMIP6_Omon.json
      input_patterns:
        - /path/to/fesom/output/files/*_salt.nc
      output_pattern: salt.nc
      actions:
        - invert_z_axis: True
        - linear_transform:
            slope: 1.0
            intercept: 0.0

Input and Output Pattern Placeholders
-------------------------------------

.. note:: The key names are ``input_patterns`` (PLURAL) and ``output_pattern`` (SINGULAR)

The input and output patterns can contain placeholders that are replaced with the appropriate values. The following placeholders are available:

* ``{model_variable}``: The name of the variable as it is in the model output.
* ``{cmor_variable}``: The name of the variable as it is in the CMOR tables.
* ``{cmor_table}``: The name of the CMOR table to use.
* ``{date}``: The date of the model output.

Dates can further be formatted using the Python ``strftime`` format. For example, to format the date as ``YYYYMMDD``, use ``{date:%Y%m%d}``. More information on the ``strftime`` format can be found in the Python documentation. https://docs.python.org/3/library/datetime.html#format-codes

Actions
-------

The actions are a list of dictionaries that define how to process the data. The main dictionary key is a fully qualifed Python callable. You then can assign arguments as a list, and key-word arguments as a dictionary.

For example, the following action:

.. code-block:: yaml

    actions:
      - invert_z_axis:
          args:
            - True
          kwargs: {}
      - linear_transform:
          args: []
          kwargs:
            slope: 1.0
            intercept: 0.0

Would call the following Python code:

.. code-block:: python

    data = invert_z_axis(data, True)
    data = linear_transform(data, slope=1.0, intercept=0.0)

The actions are applied in the order they are listed in the configuration file. The data argument is the variable in the file that matches the `model_variable` key in the rule for each file described by the `input_patterns` key.
