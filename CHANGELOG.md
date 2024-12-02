## Unreleased

### BREAKING CHANGE

- Any signature constructing a Rule object will need to
be changed!

### Feat

- warn if set method is used on rules instead of directly failing
- **inheritance**: allow for inheritance of rule attributes from a global section
- include customizable prefect ports in ssh tunnel command
- ssh tunnel shortcuts
- ssh tunnel shortcuts
- hook up @siligam's webapp to table-explorer command
- preliminary prefect support
- rules validator
- hooks up pipeline validator
- validation for pipeline dictionary
- forgot to add step in Pipeline
- new API for inputs in Rule
- adds Python tranlation of Seamore Controlled Vocabularies
- add data request classes as in Ruby
- **units.py**: add CMIP frequencies
- allow for parallel pipelines via dask
- first major working CLI
- **directories**: create CMOR directory structure as part of the pipeline
- check if a rule has specific marked regex available for usage
- allow a list of files to be rendered as a string
- allow files to be sorted by year if a named regex is used
- add functionality to resolve symlinks
- list a directory and output to yaml, for fakefs use in tests
- environment variables from config for matching patterns
- add a basic CRUD DB for pipelines
- calendar features
- generation of calendar ranges
- **calendar**: allow generation of year bounds
- **setup.py**: add development requirements
- adds cmip6 tables
- adds questionary for interaction
- some xarray features
- versioneer

### Fix

- allowed input_source and input_type is handled by cerberus
- **gather_inputs.py**: deprecates the gather_inputs function
- small mistake in gather inputs
- fixed merge table id test
- restructure design for multiple pipelines applied in a single rule
- typo in attribute name
- return values for parallel futures
- changes parallel setting to be defined in the pymorize config, where it belongs, rather than in general
- multiple pipelines can connect end-to-end
- rearrange test helpers into generic for CI testing to work
- forgot loguru import in integration test
- some tests broke during refactoring
- accidently removed pyfakefs from testing dependencies
- the main recipe should return the config
- wrong keyword for extra requires
- delete db test was wrong
- silly mistake in f-string
- **units.py**: log conversion factor separately
- corrects test for undefined weight conversion
- **test_units**: ensure that the test uses the module's unit registry, not pint's one
- minor syntax errors
- import error
- **rule.py**: ensure all input patterns are regex compiled strings when giving a list
- **setup.py**: wrong package name
- pytest should work now

### Refactor

- removes repetation of ignore files, these should only be defined in a single place
- rules can no longer have actions
