import atexit
import datetime
import io
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd
import xarray as xr
from imohash import hashfile
from tqdm.contrib.concurrent import process_map

"""
This module contains functions for creating, loading and manipulating a file cache.

The file cache is a CSV file that contains a pandas DataFrame with the following columns:

- ``variable``: The name of the variable in the file.
- ``freq``: The frequency of the variable in the file.
- ``start``: The start time of the variable in the file.
- ``end``: The end time of the variable in the file.
- ``timespan``: The timespan of the variable in the file.
- ``steps``: The number of time steps in the variable in the file.
- ``units``: The units of the variable in the file.
- ``filename``: The filename of the file.
- ``filesize``: The file size of the file in bytes.
- ``mtime``: The last modified time of the file in seconds since the epoch.
- ``checksum``: The imohash checksum of the file.
- ``filepath``: The absolute path to the file.

The file cache can be used to quickly select files from the cache that have a
specific variable, frequency, start date, end date, timespan, number of time
steps, units, filename, file size, last modified time, checksum, or absolute
path.

The file cache is stored in the following location by default:

    $HOME/.config/pymorize_filecache.csv

The file cache can be loaded and saved using the following functions:

.. code-block:: python

    >>> from pymorize.filecache import Filecache
    >>> cache = Filecache.load()
    >>> cache.save()


Collect metadata about the file(s) by adding it to the cache with the following methods:
`cache.add_file` or `cache.add_files`

.. code-block:: python

    >>> filepath = "/pool/data/CO2f_fesom_1850-01-01_1900-01-01.nc"
    >>> cache.add_file(filepath)
    >>> # adding multiple files at once
    >>> cache.add_files(["/path/to/file1.nc", "/path/to/file2.nc"])
    >>> # alternative way of adding file to cache and getting the metadata is by usuig the `get` method
    >>> cache.get("filepath")


For an overview of the cached data, use `summary` method: This method returns a
pandas DataFrame containing the summary each of the variables in the cache.  The
fields include the variable name, frequency, start date, end date, timespan,
number of files in the collection for this variable.

.. code-block:: python

    >>> cache.summary()

To use a subset of the collection for a given variable, use `select_range`
method. This will limit the files in the cache to those that are within the
given range.

.. code-block:: python
    >>> c = cache.select_range(variable="tas", start="1850-01-01", end="1900-01-01")

"""

CACHE_FILE = "~/.cache/pymorize_filecache.csv"


class Filecache:
    _fields = "variable freq start end timespan steps units filename filesize mtime checksum filepath".split()

    def __init__(self, cache: Optional[pd.DataFrame] = None):
        """
        Parameters
        ----------
        cache : pd.DataFrame, optional
            A pandas DataFrame with columns corresponding to the fields of the file cache.
            If not provided, an empty DataFrame is created.

        Attributes
        ----------
        df : pd.DataFrame
            A pandas DataFrame containing the file cache.
        """
        if cache is None:
            cache = pd.DataFrame([], columns=self._fields)
        self.df: pd.DataFrame = cache

    @classmethod
    def load(cls):
        """
        Load the file cache from the default location.

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing the file cache.
        """
        p = Path(CACHE_FILE)
        if not p.exists():
            p.parent.mkdir(exist_ok=True, parents=True)
            p.touch()
        with p.open() as f:
            comment = f.readline()
            comment = comment.strip()
            if comment.startswith("#"):
                meta_string = comment
            else:
                # there no date recorded for the cache.
                # create todays date
                _date = datetime.datetime.now().strftime("%Y-%m-%d")
                _checkfreq = "1ME"
                meta_string = f"#{_date};{_checkfreq}"
            meta_string = meta_string.rstrip() + "\n"
        if p.stat().st_size == 0:
            data = None
        else:
            data = pd.read_csv(str(p.expanduser()), comment="#")
        obj = cls(data)
        setattr(obj, "cache_meta", meta_string)
        return obj

    def save(self) -> None:
        """
        Save the file cache to the default location.
        """
        buf = io.StringIO()
        buf.write(self.cache_meta)
        self.df.to_csv(buf, index=False)
        with open(Path(CACHE_FILE).expanduser(), "w") as f:
            buf.seek(0)
            shutil.copyfileobj(buf, f)
        # self.df.to_csv(CACHE_FILE, index=False)

    def _add_file(self, filename: str) -> None:
        """
        Internal method to add a file to the cache.

        Only adds a file if no file with the same name already exists in the cache.
        """
        name = Path(filename).name
        if name not in self.df.filename.values:
            self.df = self.df._append(self._make_record(filename), ignore_index=True)

    def add_file(self, filename: str) -> None:
        """
        Add a file to the cache.

        Only adds a file if no file with the same name already exists in the cache.

        Parameters
        ----------
        filename : str
            The path to the file to add.
        """
        name = Path(filename).name
        if name not in self.df.filename.values:
            record = self._make_record(filename).to_frame().T
            if self.df.empty:
                self.df = record
            else:
                self.df = pd.concat([self.df, record], ignore_index=True)

    def add_files(self, files: List[str]) -> None:
        """
        Add a list of files to the cache.

        Only adds a file if no file with the same name already exists in the cache.

        Parameters
        ----------
        files : list of str
            List of paths to the files to add.
        """
        _files = np.asarray(files)
        mask = np.isin(_files, self.df.filepath.values)
        files = _files[~mask].tolist()
        records = process_map(
            self._make_record,
            files,
            chunksize=5,
            max_workers=10,
            unit="files",
        )
        if self.df.empty:
            self.df = pd.DataFrame(records)
        else:
            self.df = pd.concat([self.df, pd.DataFrame(records)], ignore_index=True)

    def _make_record(self, filename: str) -> pd.Series:
        """
        Internal method to create a record from a file.

        Parameters
        ----------
        filename : str
            The path to the file to create a record from.

        Returns
        -------
        pd.Series
            A pandas Series containing the metadata of the file.
        """
        record = {}
        record["filepath"] = filename
        record["filename"] = os.path.basename(filename)
        # file checksum
        record["checksum"] = f"imohash:{hashfile(filename, hexdigest=True)}"
        # file stats
        st = os.stat(filename)
        record["filesize"] = st.st_size
        record["mtime"] = st.st_mtime
        # load_dataset
        ds = xr.open_dataset(filename, use_cftime=True)
        t = ds.time.to_pandas()
        record["start"] = str(t.iloc[0])
        record["end"] = str(t.iloc[-1])
        record["timespan"] = str(t.iloc[-1] - t.iloc[0])
        record["freq"] = t.index.freq
        record["steps"] = t.size
        record["variable"] = list(ds.data_vars.keys()).pop()
        record["units"] = [
            val.attrs.get("units") for val in ds.data_vars.values()
        ].pop()
        ds.close()
        return pd.Series(record)

    def summary(self) -> pd.DataFrame:
        """
        Return a summary of the cached files.

        Parameters
        ----------
        None

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing the summary of the cached files.
            The summary includes the following information:
            - `freq`: the frequency of the files (str)
            - `start`: the start date of the files (str)
            - `end`: the end date of the files (str)
            - `timespan`: the timespan of the files (str)
            - `nfiles`: the number of files (int)
            - `steps`: the number of steps in the files (int)
            - `size`: the total size of the files (int)

        The summary is grouped by the variable name of the files.
        """

        def _summary(df: pd.DataFrame) -> pd.Series:
            d = {}
            d["freq"] = df.freq.iloc[0]
            d["start"] = start = df.start.min()
            d["end"] = end = df.end.max()
            d["timespan"] = str(pd.Timestamp(end) - pd.Timestamp(start))
            d["nfiles"] = df.shape[0]
            d["steps"] = df.steps.iloc[0]
            d["size"] = df.filesize.sum()
            return pd.Series(d)

        info = self.df.groupby(["variable"]).apply(_summary, include_groups=False)
        return info.T

    def details(self) -> pd.DataFrame:
        return self.df

    def variables(self) -> List[str]:
        """
        Return a list of unique variable names in the cache.

        Parameters
        ----------
        None

        Returns
        -------
        list
            A list of unique variable names in the cache.
        """
        return self.df.variable.unique().tolist()

    def frequency(
        self, *, filename: Optional[str] = None, variable: Optional[str] = None
    ) -> str:
        """
        Return the frequency of a variable or a file.

        Parameters
        ----------
        filename : str, optional
            The path to the file to get the frequency from.
        variable : str, optional
            The variable to get the frequency from.

        Returns
        -------
        str
            The frequency of the variable or file.
        """
        if filename is None and variable is None:
            return dict(self.df[["variable", "freq"]].drop_duplicates().values.tolist())
        if variable:
            return (
                self.df[self.df.variable == variable]["freq"]
                .drop_duplicates()
                .squeeze()
            )
        if filename:
            name = Path(filename).name
            return (
                (self.df[self.df.filename == name])["freq"].drop_duplicates().squeeze()
            )

    def show_range(self, *, variable: Optional[str] = None) -> pd.DataFrame:
        """
        Return the start and end dates of the cached files.

        Parameters
        ----------
        variable : str, optional
            The variable to filter the results by.

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing the start and end dates of the cached files.
        """
        df = self.df
        if variable:
            df = self.df[self.df.variable == variable]
        return df[["start", "end"]]

    def select_range(
        self,
        *,
        start: Optional[Union[str, pd.Timestamp]] = None,
        end: Optional[Union[str, pd.Timestamp]] = None,
        variable: Optional[str] = None,
    ) -> "Filecache":
        """
        Select the files in the cache that have a time range within the given start and end dates.

        Parameters
        ----------
        start : str or pd.Timestamp, optional
            The start date of the time range. If None, the start date of the first file is used.
        end : str or pd.Timestamp, optional
            The end date of the time range. If None, the end date of the last file is used.
        variable : str, optional
            The variable to filter the results by.

        Returns
        -------
        Filecache
            A new Filecache object containing the selected files.
        """
        df = self.df
        if variable:
            df = self.df[self.df.variable == variable]
        if start is None and end is None:
            return df
        _start = df["start"].apply(pd.Timestamp)
        _end = df["end"].apply(pd.Timestamp)
        start = start and pd.Timestamp(start) or _start.min()
        end = end and pd.Timestamp(end) or _end.max()
        df = df[(_start >= start) & (_end <= end)]
        return Filecache(df)

    def validate_range(
        self,
        *,
        start: Optional[Union[str, pd.Timestamp]] = None,
        end: Optional[Union[str, pd.Timestamp]] = None,
        variable: Optional[str] = None,
    ) -> bool:
        """
        Validate the given time range.

        Parameters
        ----------
        start : str or pd.Timestamp, optional
            The start date of the time range. If None, the start date of the first file is used.
        end : str or pd.Timestamp, optional
            The end date of the time range. If None, the end date of the last file is used.
        variable : str, optional
            The variable to filter the results by.

        Returns
        -------
        bool
            True if the given time range is valid, False otherwise.

        Raises
        ------
        ValueError
            If the given time range is out-of-bounds.
        """
        df = self.df
        if variable:
            known_variables = self.variables()
            assert (
                variable in known_variables
            ), f"{variable} is not in {known_variables}"
            df = self.df[self.df.variable == variable]
        if start:
            start_ts = pd.Timestamp(start)
            _start = df["start"].apply(pd.Timestamp)
            is_valid = start_ts >= _start.min()
            if not is_valid:
                raise ValueError(
                    f"Start date {start} is out-of-bounds. Valid range: {_start.min()} - {_start.max()}"
                )
        if end:
            end_ts = pd.Timestamp(end)
            _end = df["end"].apply(pd.Timestamp)
            is_valid = end_ts <= _end.max()
            if not is_valid:
                raise ValueError(
                    f"End date {end} is out-of-bounds. Valid range: {_end.min()} - {_end.max()}"
                )
        return True

    def files(
        self, *, variable: Optional[str] = None, fullpath: bool = True
    ) -> List[str]:
        """
        Return the list of files in the cache.

        Parameters
        ----------
        variable : str, optional
            The variable to filter the results by.
        fullpath : bool
            If True, return the full path to each file. If False, return the
            filename only.

        Returns
        -------
        list of str
            The list of files in the cache.
        """
        df = self.df
        if variable:
            df = self.df[self.df.variable == variable]
        col = "filepath" if fullpath else "filename"
        return df[col].tolist()

    def get(self, filename):
        """
        Return the record for the given filename from the cache.

        Parameters
        ----------
        filename : str
            The path to the file to get the record for.

        Returns
        -------
        pd.DataFrame
            The record for the given filename from the cache.

        Notes
        -----
        If the filename is not in the cache and the file exists, it is added
        to the cache and the record is returned.
        """
        name = Path(filename).name
        df = self.df[self.df.filename.str.contains(name)]
        if df.empty:
            if Path(filename).exists():
                self.add_file(filename)
                return self.get(filename)
        return df


fc = Filecache.load()


@atexit.register
def _save():
    """
    Perform the save operation on the file cache.

    This function is registered to execute at program exit using `atexit.register`.
    It triggers the `save` method of the `fc` object, which saves the file cache.
    """
    fc.save()


def register_cache(ds):
    """
    Register a dataset in the file cache.

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset to register. The source filename is extracted from the
        dataset's encoding and added to the cache.
    """
    filename = ds.encoding["source"]
    fc.add_file(filename)


datapath = "/work/ba1103/a270073/out/awicm-1.0-recom/awi-esm-1-1-lr_kh800/piControl/outdata/fesom"
# filepat = "CO2f_fesom_*nc"
