import pymorize
import pymorize.fesom_2p1.regridding


def test_regridding(fesom_pi_mesh_config, fesom_pi_sst_ds):
    config = fesom_pi_mesh_config
    rule = pymorize.rule.Rule.from_dict(config["rules"][0])
    rule.mesh_path = config["inherit"]["mesh_path"]
    da = fesom_pi_sst_ds.sst
    da = pymorize.fesom_2p1.regridding.regrid_to_regular(da, rule)
    assert da.shape == (180, 360)


def test_attach_mesh_to_rule(fesom_pi_mesh_config):
    config = fesom_pi_mesh_config
    rule = pymorize.rule.Rule.from_dict(config["rules"][0])
    rule.mesh_path = config["inherit"]["mesh_path"]
    data = None  # Not important for this test
    assert not hasattr(rule, "mesh")
    # _ symbolizes just any return value, which we never use
    _ = pymorize.fesom_2p1.regridding.attach_mesh_to_rule(data, rule)
    assert hasattr(rule, "mesh")
