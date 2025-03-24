====================================
Upward ocean mass transport
====================================

The vertical velocity component 𝑤 (saved as ``wo`` in fesom) is scaled by the
cell area as well as a reference density 𝜌0 = 1035 kg m−3.

``Pymorize`` tool does not have in-built function that can handle such a
computation but it is simple and straightforward to define a custom function and
include it in the pipeline.



.. code-block:: python
   :linenos:

      def weight_by_cellarea_and_density(data, rule):
          gridfile = rule.get("grid_file")
          grid = xr.open_dataset(gridfile)
          cellarea = grid["cell_area"]
          density = ureg("1035 kg m-3")
          data = data.pint.quantify() * density
          return (data * cellarea.pint.quantify()).pint.dequantify()

Notice in the above function, ``density`` is defined as a unit aware quantity so
that the correct dimensionality reduction happens automatically.  Before using
this function, some additional steps are required to represent the 3D variable
``wo`` in a 2D space (i.e., (nodes_3d) -> (levels, nodes_2d)) since
``cell_area`` from griddes file is in 2D space. ``Pymorize`` tool has a built-in
function (for fesom 1.4 grids) to do this transformation.


.. code-block:: python
   :linenos:
      def nodes_to_levels(data, rule):
          mesh_path = rule.get("mesh_path")
          if mesh_path is None:
              raise ValueError(
                  "Set `mesh_path` path in yaml config."
                  "Required for converting nodes to levels"
              )
          return pymorize.fesom_1p4.nodes_to_levels(data, rule)


Note: It is possible to use ``pymorize.fesom_1p4.nodes_to_levels`` directly in
the pipeline instead of this wrapped function.


Check out ``wo_cellarea.yaml`` for details on how these functions are inserted
in the pipeline, ``pymorize_wo_cellarea.slurm`` for the job submission
script. The ``wo_cellarea.py`` has these custom functions defined.



