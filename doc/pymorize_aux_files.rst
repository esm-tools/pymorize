==================================
``pymorize`` Using auxiliary files
==================================

You can add additional files to your ``Rule`` objects by specifying them in the
``aux`` element of the rule. These files are loaded when the ``Rule`` object is
initialized, and can be accessed in your steps.

For example, consider the following YAML configuration::


  rules:
    - name: My First Rule
      aux:
        - name: My Aux Data
          path: /path/to/aux/data.csv


You can then access this in a step like so::

  def my_step(data, rule):
    aux_data = rule.aux["My Aux Data"]
    print(aux_data)
    return data

By default, the program assumes you just have a text file which you can
read in. However, you may also want to use something else. Here is how
you can include a FESOM mesh object representation in ``pyfesom2``::


  rules:
    - name: My Other Rule
      aux:
        - name: mesh
          path: /some/path/to/a/mesh
          loader: pyfesom2.read_mesh_data.load_mesh

In Python, you get back the already loaded mesh object.
