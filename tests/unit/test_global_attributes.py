from pymorize.global_attributes import GlobalAttributes


# Name, expected pass
required_attributes = {
    ("activity_id", True),
    ("Conventions", True),
    ("creation_date", True),
    ("data_specs_version", True),
    ("experiment", True),
    ("experiment_id", True),
    ("forcing_index", True),
    ("frequency", True),
    ("grid", True),
    ("grid_label", True),
    ("initialization_index", True),
    ("institution", True),
    ("institution_id", True),
    ("license", True),
    ("mip_era", True),
    ("nominal_resolution", True),
    ("physics_index", True),
    ("product", True),
    ("realization_index", True),
    ("realm", True),
    ("source", True),
    ("source_id", True),
    ("source_type", True),
    ("sub_experiment", False),
    ("sub_experiment_id", True),
    ("table_id", True),
    ("tracking_id", False),
    ("variable_id", True),
    ("variant_label", True),
}


def test_global_attributes(rule_after_cmip6_cmorizer_init):
    rule = rule_after_cmip6_cmorizer_init
    # cmor_version = "CMIP6"
    rule_attrs = rule.global_attributes_set_on_rule()
    ga = GlobalAttributes(rule.controlled_vocabularies)
    d = ga.get_global_attributes(rule_attrs)
    for name, is_needed in required_attributes:
        assert name in d
