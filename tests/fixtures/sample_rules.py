import pytest

from pymorize.aux_files import AuxiliaryFile
from pymorize.config import PymorizeConfigManager
from pymorize.controlled_vocabularies import ControlledVocabularies
from pymorize.data_request.collection import CMIP6DataRequest
from pymorize.data_request.table import CMIP6DataRequestTable
from pymorize.data_request.variable import CMIP6DataRequestVariable
from pymorize.factory import create_factory
from pymorize.rule import Rule


@pytest.fixture
def fesom_2p6_esmtools_temp_rule(fesom_2p6_pimesh_esm_tools_data):
    pymorize_config = PymorizeConfigManager.from_pymorize_cfg({})
    return Rule.from_dict(
        {
            "name": "temp",
            "experiment_id": "piControl",
            "output_directory": "./output",
            "source_id": "AWI-CM-1-1-HR",
            "grid_label": "gn",
            "model_component": "ocean",
            "variant_label": "r1i1p1f1",
            "inputs": [
                {
                    "path": fesom_2p6_pimesh_esm_tools_data / "outdata/fesom",
                    "pattern": "temp.fesom..*.nc",
                },
            ],
            "cmor_variable": "thetao",
            "model_variable": "temp",
            "_pymorize_cfg": pymorize_config,
        }
    )


@pytest.fixture
def fesom_2p6_esmtools_temp_rule_without_data():
    pymorize_config = PymorizeConfigManager.from_pymorize_cfg({})
    return Rule.from_dict(
        {
            "name": "temp",
            "experiment_id": "piControl",
            "output_directory": "./output",
            "source_id": "FESOM",
            "variant_label": "r1i1p1f1",
            "inputs": [
                {
                    "path": "REPLACE_ME/outdata/fesom",
                    "pattern": "temp.fesom..*.nc",
                },
            ],
            "cmor_variable": "thetao",
            "model_variable": "temp",
            "_pymorize_cfg": pymorize_config,
        }
    )


@pytest.fixture
def pi_uxarray_temp_rule(pi_uxarray_data):
    pymorize_config = PymorizeConfigManager.from_pymorize_cfg({})
    return Rule.from_dict(
        {
            "name": "temp",
            "experiment_id": "piControl",
            "output_directory": "./output",
            "source_id": "AWI-CM-1-1-HR",
            "grid_label": "gn",
            "model_component": "ocean",
            "variant_label": "r1i1p1f1",
            "inputs": [
                {
                    "path": pi_uxarray_data,
                    "pattern": "temp.fesom..*.nc",
                },
            ],
            "cmor_variable": "thetao",
            "model_variable": "temp",
            "_pymorize_cfg": pymorize_config,
        }
    )


@pytest.fixture
def simple_rule():
    r = Rule(
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
    )
    r._pymorize_cfg = PymorizeConfigManager.from_pymorize_cfg({})
    return r


@pytest.fixture
def rule_with_mass_units():
    r = Rule(
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
        data_request_variables=[
            CMIP6DataRequestVariable.from_dict(
                dict(
                    # unit="kg",
                    cell_measures="area: areacella",
                    cell_methods="time: mean",
                    comment="Some comment",
                    description="Some description",
                    dimensions="lon lat",
                    frequency="mon",
                    long_name="Some long name",
                    modeling_realm="atmos",
                    ok_max_mean_abs=999,
                    ok_min_mean_abs=-999,
                    out_name="var1",
                    positive="up",
                    realms=["atmos"],
                    standard_name="something",
                    table="Some Table",
                    time_method="instant",
                    type="real",
                    units="kg",
                    valid_max=1,
                    valid_min=0,
                )
            )
        ],
    )
    r.data_request_variable = r.data_request_variables[0]
    return r


@pytest.fixture
def rule_with_data_request():
    r = Rule(
        name="temp",
        source_id="AWI-CM-1-1-HR",
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
        data_request_variables=[
            CMIP6DataRequestVariable.from_dict(
                dict(
                    # unit="kg",
                    cell_measures="area: areacella",
                    cell_methods="time: mean",
                    comment="Some comment",
                    description="Some description",
                    dimensions="lon lat",
                    frequency="mon",
                    long_name="Some long name",
                    modeling_realm="atmos",
                    ok_max_mean_abs=999,
                    ok_min_mean_abs=-999,
                    out_name="var1",
                    positive="up",
                    realms=["atmos"],
                    standard_name="something",
                    table="Some Table",
                    time_method="instant",
                    type="real",
                    units="kg",
                    valid_max=1,
                    valid_min=0,
                )
            )
        ],
    )
    r.data_request_variable = r.data_request_variables[0]
    return r


@pytest.fixture
def rule_sos():
    from tests.utils.constants import TEST_ROOT

    sos_path = TEST_ROOT / "data" / "dummy_data"
    return Rule(
        cmor_variable="sos",
        inputs=[{"path": sos_path, "pattern": "sos.*.nc"}],
    )


@pytest.fixture
def rule_after_cmip6_cmorizer_init(tmp_path, CMIP_Tables_Dir, CV_dir):
    # Slimmed down version of what the CMORizer does.
    # This is somewhat of an integration test by itself.
    #
    # `inputs` requires:
    #  - concrete `path` to exist
    #  - a file to exist matching the `pattern`

    # Set the temporary directory and nc file
    d = tmp_path / "inputs"
    d.mkdir(exist_ok=True)
    nc = d / "var1.blah.blah.nc"
    nc.touch()

    # Initialize the rule
    rule = Rule(
        name="temp",
        experiment_id="piControl",
        output_directory="./output",
        source_id="AWI-CM-1-1-HR",
        variant_label="r1i1p1f1",
        grid_label="gn",
        model_component="ocean",
        inputs=[{"path": d, "pattern": "var1.*.nc"}],
        cmor_variable="tos",
        model_variable="temp",
    )

    # Set the tables and data request
    tables = CMIP6DataRequestTable.table_dict_from_directory(CMIP_Tables_Dir)
    data_request = CMIP6DataRequest.from_directory(CMIP_Tables_Dir)
    for tbl in tables.values():
        if rule.cmor_variable in tbl.variables:
            rule.add_table(tbl.table_id)

    # Set other attributes
    rule.dimensionless_unit_mappings = {}
    rule.aux = AuxiliaryFile(name="mesh", path="/some/mesh/file.nc")
    rule.data_request_variable = data_request.variables.get(
        f"Oday.{rule.cmor_variable}"
    )

    # Set the controlled vocabularies
    controlled_vocabularies_factory = create_factory(ControlledVocabularies)
    ControlledVocabulariesClass = controlled_vocabularies_factory.get("CMIP6")
    rule.controlled_vocabularies = ControlledVocabulariesClass.load(CV_dir)

    return rule
