import json
from collections import defaultdict
from pathlib import Path
import streamlit as st
import pandas as pd


tables_dir = Path(__file__).parent.parent.parent  / "cmip6-cmor-tables/Tables"
tbls = defaultdict(list)
ignored_tables = []
var_to_tbl = defaultdict(list)
frequencies = set()
tids={}

def process_table(tbl):
    add_to_ignore = False
    with open(tbl) as fid:
        t = json.load(fid)
    tid = t.get("Header", {}).get("table_id", "").replace("Table ", "")
    tids[tid] = tbl
    if var_entry := t.get("variable_entry"):
        for name, attrs in var_entry.items():
            if freq := attrs.get("frequency"):
                var_to_tbl[name].append((tid, freq))
                tbls[tid].append((name, freq))
                frequencies.add(freq)
            else:
                add_to_ignore = True
    else:
        add_to_ignore = True
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
        r.append(dict(table=t, frequency=f, timemethod=kind))#, select=False))
    r = sorted(r, key=lambda x: x['table'])
    df = pd.DataFrame(r)
    event = st.dataframe(
        df,
        on_select="rerun",
        selection_mode=["multi-row"],
        use_container_width=True)
    if event.selection:
        indices = event.selection['rows']
        _tids = list(df.loc[indices].table)
        attrs = []
        for t in _tids:
            tbl = tids[t]
            info = {}
            with open(tbl) as fid:
                d = json.load(fid)
            info.update(d['Header'])
            info.update(d['variable_entry'][varname])
            attrs.append(info)
        if attrs:
            df_info = pd.DataFrame(attrs, index=indices).T
            def styler(row):
                ncols = len(row)
                if len(row.unique()) > 1:
                    return ['background-color: #e8ebcf' for i in range(ncols)]
                return ['background-color: white' for i in range(ncols)]
            if len(df_info.columns) > 1:
                st.dataframe(df_info.style.apply(styler, axis=1), use_container_width=True)
            else:
                st.dataframe(df_info, use_container_width=True)

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
