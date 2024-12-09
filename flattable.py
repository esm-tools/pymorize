import json
from collections import UserDict, defaultdict
from pathlib import Path

import requests

ignored_table_files = {
    "CMIP6_coordinate.json",
    "CMIP6_grids.json",
    "CMIP6_input_example.json",
    "CMIP6_formula_terms.json",
    "CMIP6_fx.json",
    "CMIP6_CV.json",
}

all_table_files = {
    "CMIP6_3hr.json",
    "CMIP6_6hrLev.json",
    "CMIP6_6hrPlev.json",
    "CMIP6_6hrPlevPt.json",
    "CMIP6_AERday.json",
    "CMIP6_AERhr.json",
    "CMIP6_AERmon.json",
    "CMIP6_AERmonZ.json",
    "CMIP6_Amon.json",
    "CMIP6_CF3hr.json",
    "CMIP6_CFday.json",
    "CMIP6_CFmon.json",
    "CMIP6_CFsubhr.json",
    "CMIP6_CV.json",
    "CMIP6_E1hr.json",
    "CMIP6_E1hrClimMon.json",
    "CMIP6_E3hr.json",
    "CMIP6_E3hrPt.json",
    "CMIP6_E6hrZ.json",
    "CMIP6_Eday.json",
    "CMIP6_EdayZ.json",
    "CMIP6_Efx.json",
    "CMIP6_Emon.json",
    "CMIP6_EmonZ.json",
    "CMIP6_Esubhr.json",
    "CMIP6_Eyr.json",
    "CMIP6_IfxAnt.json",
    "CMIP6_IfxGre.json",
    "CMIP6_ImonAnt.json",
    "CMIP6_ImonGre.json",
    "CMIP6_IyrAnt.json",
    "CMIP6_IyrGre.json",
    "CMIP6_LImon.json",
    "CMIP6_Lmon.json",
    "CMIP6_Oclim.json",
    "CMIP6_Oday.json",
    "CMIP6_Odec.json",
    "CMIP6_Ofx.json",
    "CMIP6_Omon.json",
    "CMIP6_Oyr.json",
    "CMIP6_SIday.json",
    "CMIP6_SImon.json",
    "CMIP6_coordinate.json",
    "CMIP6_day.json",
    "CMIP6_formula_terms.json",
    "CMIP6_fx.json",
    "CMIP6_grids.json",
    "CMIP6_input_example.json",
}


valid_table_files = all_table_files - ignored_table_files


class FlatTable(UserDict):
    """FlatTable class is a dictionary-like object that stores data
    from tables, where each table has variables and attributes.  The
    keys are in the format "table_id.variable.attribute". The table
    header attributes are stored in the "table_id.header.attribute"
    format.

    Load tables from a directory of JSON files using `from_path`
    method or load table data from the latest version on the
    cmip6-cmor-tables github repository using `from_github` method.

    `get_variable` method returns the data for a specific variable if
    variable name and table name are given.  If table name is not
    given, the data for all tables containing the variable is
    returned.

    Usage:
    >>> # Loading specific tables from github
    >>> table = FlatTable()
    >>> table.from_github("Omon")
    >>> table.from_github("Odec")
    >>> table['Omon.so.units']
    '0.001'
    >>> so = table.get_variable(variable="so", table="Omon")
    >>> so.units
    '0.001'
    >>> so.standard_name
    'sea_water_salinity'
    >>> so.approx_interval
    '30.00000'
    >>> so.table
    'Omon'
    >>> # getting "so" from all tables
    >>> so = table.get_variable(variable="so")
    [<CompoundTable Odec.so>, <CompoundTable Omon.so>]
    """

    def __init__(self, dict=None, /, **kwargs):
        self._tables = defaultdict(set)
        self._variables = defaultdict(set)
        self._compoundkeys = defaultdict(set)
        super().__init__(dict, **kwargs)

    def __setitem__(self, key, value):
        tblname, varname, attr = key.split(".")
        ck = f"{tblname}.{varname}"
        if varname != "header":
            self._tables[tblname].add(varname)
            self._variables[varname].add(tblname)
        self._compoundkeys[ck].add(key)
        super().__setitem__(key, value)

    def _from_dict(self, data):
        tmp = {}
        table_id = data.get("Header", {}).get("table_id", None)
        if table_id is None:
            raise ValueError("table_id not found (Header.table_id)")
        tbl_name = table_id.split()[-1]
        for name, val in data.get("Header", {}).items():
            tmp[f"{tbl_name}.header.{name}"] = val
            if name == "table_id":
                tmp[f"{tbl_name}.header.{name}"] = tbl_name
        for varname, vardata in data.get("variable_entry", {}).items():
            for name, val in vardata.items():
                tmp[f"{tbl_name}.{varname}.{name}"] = val
        self.update(tmp)
        return self

    def load_json(self, fpath):
        fpath = Path(fpath).expanduser()
        if fpath.name in ignored_table_files:
            return self
        data = json.loads(fpath.read_text())
        _, tbl_name = fpath.stem.split("_", 1)
        return self._from_dict(data)

    @classmethod
    def from_path(cls, path):
        """
        Load tables from a directory of JSON files.

        Parameters
        ----------
        path : str or Path
            Path to the directory of JSON files.

        Returns
        -------
        self
        """
        obj = cls()
        path = Path(path).expanduser()
        for fname in path.iterdir():
            obj.load_json(fname)
        return obj

    def from_github(self, table: str = None, version: str = None):
        """
        Load table data from the latest version on the cmip6-cmor-tables
        github repository.

        Parameters
        ----------
        table : str, optional
            Specific table to load. If not given, all tables are loaded.
        version : str, optional
            Specific version to load. If not given, the latest version is
            loaded.

        Returns
        -------
        self
        """
        url = "https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/main/Tables/"
        if table:
            if table not in valid_table_files:
                table_file = f"CMIP6_{table}.json"
                if table_file not in valid_table_files:
                    raise ValueError(f"{table} not in valid_table_files")
                tables = [table_file]
        else:
            tables = list(valid_table_files)
        if version:
            url = url.replace("main", version)
        table_data = []
        for tbl in tables:
            _url = url.rstrip("/") + "/" + tbl
            r = requests.get(_url)
            r.raise_for_status()
            table_data.append(json.loads(r.content))
        for data in table_data:
            self._from_dict(data)
        return self

    def get_variable(self, variable, table=None):
        """
        Get the data for a specific variable.

        Parameters
        ----------
        variable : str
            The variable to retrieve.
        table : str, optional
            The table to retrieve the variable from. If not given, all tables
            containing the variable are returned.

        Returns
        -------
        CompoundTable or list of CompoundTable
            The retrieved variable. If `table` is given, a single
            `CompoundTable` is returned. Otherwise, a list of `CompoundTable`s
            is returned, one for each table containing the variable.
        """
        tables = self._variables.get(variable)
        if tables is None:
            raise ValueError(f"{variable} not found")
        if table is not None:
            if table not in tables:
                raise ValueError(f"{table} not found in {tables}")
            ck = f"{table}.{variable}"
            header = f"{table}.header"
            d = {}
            for key in self._compoundkeys[ck]:
                d[key] = self[key]
            for key in self._compoundkeys[header]:
                d[key] = self[key]
            return CompoundTable.from_dict(d)
        collection = []
        for tbl in tables:
            collection.append(self.get_variable(variable, tbl))
        return collection

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            d = {}
            if key in self._compoundkeys:
                for ck in self._compoundkeys[key]:
                    d[ck] = self[ck]
                tbl, var = key.split(".")
                if var != "header":
                    key = f"{tbl}.header"
                    for ck in self._compoundkeys[key]:
                        d[ck] = self[ck]
                    return CompoundTable.from_dict(d)
                else:
                    d = {k.split(".")[-1]: v for k, v in d.items()}
                    return d
            if key in self._tables:
                collection = []
                for var in self._tables[key]:
                    collection.append(self.get_variable(var, key))
                return collection
            if key in self._variables:
                return self.get_variable(key)
            return {k: self[k] for k in self.keys() if key == k.split(".")[-1]}

    def tables(self):
        """
        Return a list of table names.
        """
        return list(self._tables)

    def variables(self):
        """
        Return a list of variable names.
        """
        return list(self._variables)


class CompoundTable:
    _attrs = ("standard_name", "long_name", "units", "cell_measures", "cell_methods")

    def __init__(self, table, variable, data: dict):
        self.table = self.table_id = table
        self.variable = variable
        self.name = self.compoundkey = f"{table}.{variable}"
        for name, value in data.items():
            setattr(self, name, value)
        self._data = data

    @classmethod
    def from_dict(cls, data: dict):
        d = {}
        _tables = set()
        _variables = set()
        for key, value in data.items():
            tbl, var, name = key.split(".")
            _tables.add(tbl)
            if var != "header":
                _variables.add(var)
            d[name] = value
        if len(_tables) > 1 or len(_variables) > 1:
            raise ValueError(
                f"Single variable from single table expected. Got: Table(s) {_tables} Variable(s) {_variables}"
            )
        table = next(iter(_tables))
        variable = next(iter(_variables))
        return cls(table, variable, d)

    def attrs(self):
        d = {}
        for name in self._attrs:
            d[name] = getattr(self, name)
        return d

    def __repr__(self):
        s = f"<{self.__class__.__name__} {self.name}>"
        return s

    def __iter__(self):
        return iter(self._data.items())

    def is_unitless(self):
        units = getattr(self, "units")
        if not units:
            return True
        try:
            float(self.units)
        except ValueError:
            return False
        return True


if __name__ == "__main__":
    tbl_dir = Path("~/repos/pymorize/cmip6-cmor-tables/Tables").expanduser()
    tables = FlatTable.from_path(tbl_dir)
