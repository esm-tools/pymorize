import os

import pytest

from pymorize.data_request import DataRequest, DataRequestTable


class TestDataRequest:
    @pytest.fixture(autouse=True)
    def setup(self):
        current_location = os.path.dirname(os.path.abspath(__file__)) + "/../"
        self.datarequest_paths = []
        self.datarequest_paths.append(f"{current_location}/fixtures/CMIP6_3hr.json")
        self.datarequest_paths.append(f"{current_location}/fixtures/CMIP6_SIday.json")
        self.datarequest_paths.append(f"{current_location}/fixtures/CMIP6_Oday.json")

    def test_approx_interval_for_table_Omon_is_30(self):
        assert DataRequest.approx_interval_for_table("Omon") == 30.0

    def test_difmxybo_and_difmxybo2d_exist(self):
        dr = DataRequest(["tests/fixtures/difmxybo2d/CMIP6_Oclim.json"])
        assert dr.variable_ids == ["difmxybo", "difmxybo2d"]

    def test_returns_version(self):
        assert DataRequest(self.datarequest_paths).version == "01.00.27"

    def test_returns_merged_table_ids(self):
        assert DataRequest(self.datarequest_paths).table_ids == ["3hr", "Oday", "SIday"]

    def test_returns_merged_variable_ids(self):
        expected_variable_ids = [
            "chlos",
            "clt",
            "hfls",
            "hfss",
            "huss",
            "mrro",
            "mrsos",
            "omldamax",
            "phycos",
            "pr",
            "prc",
            "prsn",
            "ps",
            "rlds",
            "rldscs",
            "rlus",
            "rsds",
            "rsdscs",
            "rsdsdiff",
            "rsus",
            "rsuscs",
            "siconc",
            "siconca",
            "sisnthick",
            "sispeed",
            "sitemptop",
            "sithick",
            "sitimefrac",
            "siu",
            "siv",
            "sos",
            "sossq",
            "tas",
            "tos",
            "tossq",
            "tslsi",
            "uas",
            "vas",
        ]
        assert DataRequest(self.datarequest_paths).variable_ids == expected_variable_ids

    def test_can_be_created_with_multiple_table_paths(self):
        DataRequest(self.datarequest_paths)

    def test_finds_variable_tos(self):
        var = DataRequest(self.datarequest_paths).find("tos", "3hrPt")
        assert var
        assert var.variable_id == "tos"

    def test_sithick_has_realms_seaIce_and_ocean(self):
        var = DataRequest(self.datarequest_paths).find("sithick", "day")
        assert var
        assert var.realms == ["seaIce", "ocean"]


class TestDataRequestTable:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.datarequest_path = "tests/fixtures/CMIP6_Oday.json"
        self.t = DataRequestTable(self.datarequest_path)

    def test_can_create_variable_objects(self):
        assert self.t.variable_entries[0].variable_id == "chlos"

    def test_can_read_frequencies(self):
        assert self.t.frequencies == ["day"]

    def test_can_read_multiple_frequencies(self):
        assert DataRequestTable("tests/fixtures/CMIP6_3hr.json").frequencies == [
            "3hr",
            "3hrPt",
        ]

    def test_can_read_variable_ids(self):
        assert self.t.variable_ids == [
            "chlos",
            "omldamax",
            "phycos",
            "sos",
            "sossq",
            "tos",
            "tossq",
        ]

    def test_can_read_version(self):
        assert self.t.version == "01.00.27"

    def test_can_read_table_id(self):
        assert self.t.table_id == "Oday"
