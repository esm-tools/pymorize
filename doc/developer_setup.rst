===============
Developer Setup
===============

We use ``black`` and ``isort`` to format the code. You can make sure
that your editor is set up to use those tools, and the included ``setup.cfg``
file configures them to match the project's style guide.

We have also run ``black`` once on the entire code base. To ensure that you still see changes
in ``git blame`` correctly, you can follow this guide:

https://black.readthedocs.io/en/stable/guides/introducing_black_to_your_project.html

Importantly, the relevante change for your local ``.git/config`` file is stored in the
included ``.gitconfig`` file. You can add this to the project's ``.git/config`` file by running::

  $ git config --local include.path ../.gitconfig
