Developer Guide
===============

Thanks for helping develop ``pymorize``!. This document will guide you through
the code structure and layout, and provide a few tips on how to contribute.

Code Layout
-----------

We use a `src` layout, with all files living under `./src/pymorize`. The code is
generally divided into several building blocks:

There are a few main modules and classes you should be aware of:

* ``Rule`` is the main class that defines a rule for processing a CMOR variable. It is
  defined in ``rule.py``. ``Rule`` objects have several attributes which are useful:

  1. ``input_patterns``: A list of regular expressions that are used to match the
     input file name. Note that this is **regex**, not globbing!
  2. ``cmor_variable``: The ``CMOR`` name of the variable.
  3. ``actions``: A list of actions to be performed on the input file. An ``action`` is
       a partially-applied function, where the only remaining argument is the input file.

      **Design Note**: The reason for this design is that it allows us to define a
      list of actions that can be applied to a file, and then apply them all at once
      when we find a match via a loop. It *has not* yet been determined if what we will
      return here. It is probably easiest to return a list of `xarray` objects, corresponding
      to each action. This allows us to grab out the data we need at any step in the chain.

* ``Pipeline``: (**NOT YET IMPLEMENTED**) A ``Pipeline`` is a collection of rules that can
  be applied to a file. It is (will be) defined in ``pipeline.py``.

* ``CMORizer``: This is the main class, if anything can be called that. It is defined in
  ``cmorizer.py``. It is responsible for reading in the rules, and managing the various
  objects. **NOTE**: A ``CMORIZER`` object should **not** have any knowledge about files,
  just about rules and actions. This is because we want to be able to test the rules
  without having to worry about files (separation of concerns). This design is of course
  subject to change. The ``CMORIZER`` object should have a method ``apply_rules`` that
  takes a list of files, and applies the rules to them. (Alternatively, it should be a callable,
  Paul hasn't decided yet)
       
``rule.py`` contains the main ``Rule`` class. It should be used to define a matching
between an output file and a CMOR name. d rules. This list is used to match the
