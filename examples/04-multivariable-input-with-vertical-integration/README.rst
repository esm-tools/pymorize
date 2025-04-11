Multivariable Inputs and vertical integration
---------------------------------------------

Here we show how use two input variables and perform a
vertical integration. The motivating example is from the
``CMIP6_Omon.json`` table:

  .. code:: json

      "intpp": {
          "standard_name": "net_primary_mole_productivity_of_biomass_expressed_as_carbon_by_phytoplankton",
          "units": "mol m-2 s-1",
          "long_name": "Primary Organic Carbon Production by All Types of Phytoplankton",
          "comment": "Vertically integrated total primary (organic carbon) production by phytoplankton.  This should equal the sum of intpdiat+intpphymisc, but those individual components may be unavailable in some models.",
   }

In the ``AWI-ESM-1-REcoM`` case two phytoplanktion groups
contribute to primary production:

1. nanophytoplankton (variable ``diags3d01``)
2. diatoms (variable ``diags3d02``)

Hence, the workflow to get implemented would be:

.. math::

    \text{NPP} = \int_{\text{bottom}}^{\text{top}} (\text{NPP}_{\text{nanopythoplankton}} + \text{NPP}_{\text{diatoms}})

In pseudo-code::

  pp = diags3d01 + diags3d03
  pp.sum(dim="depth")
  mmol_mol = 1e-3
  per_day_to_per_sec = 1/86400
  conversion_factor_mmolC_m2_d_to_molC_m2_s = 1/1e3/86400  # About 1.157407e-08

We implement custom steps for the addition and vertical integration.


**Preparing the example**

You should run this example on ``DKRZ Levante``. Start by downloading the sample data::

  $ ./download-example-data.sh

This will extract 10 years of example data for the two variables in question.

Next, we define some custom functions in ``intpp_recom.py``:

.. literalinclude:: ../examples/04-multivariable-input-with-vertical-integration/intpp_recom.py
   :linenos:
   :language: python
