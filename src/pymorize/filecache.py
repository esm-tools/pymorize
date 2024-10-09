import json
import os
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict

import pandas as pd
import xarray as xr
from imohash import hashfile
from tqdm.contrib.concurrent import process_map


@contextmanager
def timethis(msg=""):
    "measures execution time for a given operation"
    st = time.time()
    yield
    elapsed = time.time() - st
    if msg:
        print(f"{msg} Elapsed {elapsed:.2f}s")
    else:
        print(f"Elapsed {elapsed:.2f}s")


CACHE_FILE = "~/.config/pymorize_filecache.json"


class Filecache:
    def __init__(self, cachefile=None):
        self.cachefile = os.path.expanduser(cachefile or CACHE_FILE)
        self.cache = {}
        if not os.path.exists(self.cachefile):
            self.reset()
        self.load()

    def reset(self):
        self.cache = {
            "summary": defaultdict(dict),
            "details": defaultdict(list),
            "files": defaultdict(dict),
        }
        self.save()

    def load(self):
        with open(self.cachefile) as fid:
            d = json.load(fid)
        d["summary"] = defaultdict(dict, d["summary"])
        d["details"] = defaultdict(list, d["details"])
        d["files"] = defaultdict(dict, d["files"])
        self.cache = d

    def save(self):
        self.update_summary()
        with open(self.cachefile, "w") as fid:
            json.dump(self.cache, fid)

    def add_file(self, filepath, flush=False):
        cache = self.cache
        varname = cache["files"].get(filepath, None)
        if varname is None:
            rec = self._make_record(filepath)
            varname = rec["variable"]
            cache["files"][filepath] = varname
            cache["details"][varname].append(rec)
            # self.update_summary(varname)
        else:
            filestat = self._stats(filepath)
            index, rec = self._find_record(filepath, index=True)
            if (filestat["filesize"] == rec["filesize"]) and (filestat["mtime"] == rec["mtime"]):
                print(f"File already exists {filepath}")
                return
            print("File changed on disk. updating...")
            self.cache.get("details").get(varname).pop(index)
            self.cache.get("files").pop(filepath)
            self.add_file(filepath, flush, sort)
        if flush:
            self.save()

    def add_files(self, files):
        records = []
        nworkers = int(
            os.environ.get(
                "SLURM_CUPS_PER_TASK", os.environ.get("SLURM_JOB_CPUS_PER_NODE", 10)
            )
        )
        nworkers = min(nworkers, os.cpu_count())
        with timethis("Computing hashes: "):
            futures = process_map(
                self._make_record,
                files,
                chunksize=2,
                max_workers=nworkers,
                unit="files",
            )
            for item in futures:
                records.append(item)
        for record in records:
            self.add_record(record)
        self.save()

    def add_record(self, record):
        filepath = record["path"]
        varname = self.cache["files"].get(filepath, None)
        if varname is None:
            varname = record["variable"]
            self.cache["files"][filepath] = varname
            self.cache["details"][varname].append(record)
        else:
            filestat = self._stats(filepath)
            index, rec = self._find_record(filepath, index=True)
            if (filestat["filesize"] == rec["filesize"]) and (filestat["mtime"] == rec["mtime"]):
                print(f"File already exists {filepath}")
                return
            print("File changed on disk. updating...")
            self.cache.get("details").get(varname).pop(index)
            self.cache["details"][varname].insert(index, record)

    def _find_record(self, filepath, index=False):
        varname = self.cache.get("files").get(filepath)
        records = self.cache.get("details").get(varname)
        for ind, record in enumerate(records):
            if record["path"] == filepath:
                if index:
                    return ind, record
                return record
        else:
            raise ValueError(f"No matching records for file: {filepath}")

    def _sort_records(self, variable):
        records = self.cache.get("details").get(variable)
        records = sorted(records, key=lambda x: x.get("start"))
        self.cache["details"][variable] = records

    def update_summary(self, variable=None):
        if variable:
            records = self.cache.get("details").get(variable)
            records = sorted(records, key=lambda x: x.get("start"))
            d = {}
            d["freq"] = records[0]["freq"]
            d["start"] = start = records[0]["start"]
            d["end"] = end = records[-1]["end"]
            d["timespan"] = str(pd.Timestamp(end) - pd.Timestamp(start))
            d["nfiles"] = len(records)
            d["steps"] = records[0]["steps"]
            d["size"] = size = sum(i["filesize"] for i in records)
            d["size_in_GB"] = f"{size/1e9} GB"
            self.cache["summary"][variable] = d
        else:
            for variable in self.cache.get("details"):
                self.update_summary(variable)

    @staticmethod
    def _stats(filepath: str) -> Dict:
        st = os.stat(filepath)
        return {"filesize": st.st_size, "mtime": st.st_mtime}

    @staticmethod
    def _make_record(filepath: str) -> Dict:
        record = {}
        record["path"] = filepath
        record["filename"] = os.path.basename(filepath)
        # file checksum
        record["checksum"] = f"imohash:{hashfile(filepath, hexdigest=True)}"
        # file stats
        st = os.stat(filepath)
        record["filesize"] = st.st_size
        record["mtime"] = st.st_mtime
        # load_dataset
        ds = xr.open_dataset(filepath, use_cftime=True)
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
        return record

    @property
    def summary(self):
        return self.cache['summary']

    @property
    def files(self):
        return list(self.cache['files'])

    @property
    def variables(self):
        return list(self.cache['details'])


datapath = "/work/ba1103/a270073/out/awicm-1.0-recom/awi-esm-1-1-lr_kh800/piControl/outdata/fesom"
filepat = f"CO2f_fesom_*nc"

