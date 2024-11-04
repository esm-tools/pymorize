import pymorize
import pymorize.fesom


def test_regridding(fesom_pi_mesh_config, fesom_pi_sst_ds):
    config = fesom_pi_mesh_config
    rule = pymorize.rule.Rule.from_dict(config["rules"][0])
    rule.mesh_file = config["inherit"]["mesh_file"]
    da = fesom_pi_sst_ds.sst
    pymorize.fesom.regrid_to_regular(da, rule)
