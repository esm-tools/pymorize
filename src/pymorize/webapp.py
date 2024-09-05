import json
from collections import defaultdict
from pathlib import Path
import streamlit as st

tables_dir = Path(__file__).parent.parent.parent  / "cmip6-cmor-tables/Tables"
tbls = defaultdict(list)
ignored_tables = []
var_to_tbl = defaultdict(list)
frequencies = set()


def process_table(tbl):
    add_to_ignore = False
    with open(tbl) as fid:
        t = json.load(fid)
    tid = t.get("Header", {}).get("table_id", "").replace("Table ", "")
    if var_entry := t.get("variable_entry"):
        for name, attrs in var_entry.items():
            if freq := attrs.get("frequency"):
                var_to_tbl[name].append((tid, freq))
                tbls[tid].append((name, freq))
                frequencies.add(freq)
            else:
                add_to_ignore = True
    else:
        tid = tbl.stem.replace("CMIP6_", "")
        ignored_tables.append(tid)
    if add_to_ignore:
        tid = tbl.stem.replace("CMIP6_", "")
        ignored_tables.append(tid)
    return


for tbl in tables_dir.glob("*.json"):
    process_table(tbl)


cols = st.columns(3)

with cols[0]:
    st.metric("Tables", len(tbls))
with cols[1]:
    st.metric("Frequencies", len(frequencies))
with cols[2]:
    st.metric("Variables", len(var_to_tbl))


with st.expander("Ignored tables"):
    st.table(sorted(ignored_tables))

st.divider()


def show_selected_variable(varname):
    res = var_to_tbl[varname]
    kind = ""
    r = []
    for t, f in res:
        if f.endswith('Pt'):
            kind = 'Instantanious'
        elif f.endswith('C') or f.endswith('CM'):
            kind = 'Climotology'
        else:
            kind = 'Mean'
        r.append(dict(table=t, frequency=f, timemethod=kind))
    r = sorted(r, key=lambda x: x['table'])
    st.table(r)

variables = sorted(var_to_tbl)

var_references = defaultdict(set)
for vname, items in var_to_tbl.items():
    var_references[len(items)].add(vname)
var_references = {counts: sorted(vnames) for counts, vnames in var_references.items()}

filtered_variables = st.checkbox("Filter variable list by number of references to tables")
if filtered_variables:
    counts = st.select_slider("Number of references", options=sorted(var_references))
    variables = var_references[counts]

varname = st.selectbox(f"Select Variable (count: {len(variables)})", variables, index=None)
if varname:
    show_selected_variable(varname)
