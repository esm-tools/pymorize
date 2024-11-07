import pymorize
import pymorize.fesom


def test_regridding(fesom_pi_mesh_config, fesom_pi_sst_ds):
    config = fesom_pi_mesh_config
    rule = pymorize.rule.Rule.from_dict(config["rules"][0])
    rule.mesh_file = config["inherit"]["mesh_file"]
    da = fesom_pi_sst_ds.sst
    da = pymorize.fesom.regrid_to_regular(da, rule)
    assert da.shape == (180, 360)


def test_attach_mesh_to_rule(fesom_pi_mesh_config):
    config = fesom_pi_mesh_config
    rule = pymorize.rule.Rule.from_dict(config["rules"][0])
    rule.mesh_file = config["inherit"]["mesh_file"]
    data = None  # Not important for this test
    assert not hasattr(rule, "mesh")
    # _ symbolizes just any return value, which we never use
    _ = pymorize.fesom.attach_mesh_to_rule(data, rule)
    assert hasattr(rule, "mesh")
