import os
import json
from collections import defaultdict, Counter
from pathlib import Path
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import socket
import pandas as pd


github_url = "https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/main/Tables/"

table_files = {
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

ignored_table_files = {
    "CMIP6_coordinate.json",
    "CMIP6_grids.json",
    "CMIP6_input_example.json",
    "CMIP6_formula_terms.json",
    "CMIP6_fx.json",
    "CMIP6_CV.json",
}

tbls = defaultdict(list)
tbl_raw_data = {}
var_to_tbl = defaultdict(list)
frequencies = set()
tids = {}


def process_table(tbl_name: str, data: dict):
    add_to_ignore = False
    t = data
    tid = t.get("Header", {}).get("table_id", "").replace("Table ", "")
    tids[tid] = tbl_name
    if tid == "fx":
        add_to_ignore = True
    elif var_entry := t.get("variable_entry"):
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
        ignored_table_files.add(tbl_name)
    return


def show_selected_variable(varname):
    res = var_to_tbl[varname]
    kind = ""
    r = []
    for t, f in res:
        if f.endswith("Pt"):
            kind = "Instantaneous"
        elif f.endswith("C") or f.endswith("CM"):
            kind = "Climatology"
        else:
            kind = "Mean"
        r.append(dict(table=t, frequency=f, timemethod=kind))  # , select=False))
    r = sorted(r, key=lambda x: x["table"])
    df = pd.DataFrame(r)
    event = st.dataframe(
        df, on_select="rerun", selection_mode=["multi-row"], use_container_width=True
    )
    if event.selection:
        indices = event.selection["rows"]
        _tids = list(df.loc[indices].table)
        attrs = []
        for t in _tids:
            tbl = tids[t]
            info = {}
            d = tbl_raw_data[tbl]
            info.update(d["Header"])
            info.update(d["variable_entry"][varname])
            attrs.append(info)
        if attrs:
            df_info = pd.DataFrame(attrs, index=indices).T

            def styler(row):
                ncols = len(row)
                if len(row.unique()) > 1:
                    return ["background-color: #eeecf4" for i in range(ncols)]
                return ["background-color: white" for i in range(ncols)]

            if len(df_info.columns) > 1:
                st.dataframe(
                    df_info.style.apply(styler, axis=1), use_container_width=True
                )
            else:
                st.dataframe(df_info, use_container_width=True)
    return


st.set_page_config(layout="wide")

col1, col2 = st.columns([1, 3])
captions = ["raw githubusercontent", f"{socket.gethostname()}", ""]

with col1:
    table_source = st.radio(
        "Select table source",
        ["github", "Local", "Laptop"],
        index=None,
        captions=captions,
    )

if table_source == "Laptop":
    with col2:
        tbl_files = st.file_uploader(
            "Tables, select one or more tables:",
            type="json",
            accept_multiple_files=True,
        )
    for f in tbl_files:
        tbl_name = f.name
        if tbl_name in ignored_table_files:
            continue
        data = json.loads(f.read())
        tbl_raw_data[tbl_name] = data
        process_table(tbl_name, data)

if table_source == "github":
    with col2:
        url = st.text_input("Using the following url:", github_url)
        st.write(
            "For a different data_spec_version (say 01.00.32), replace 'main' with the version '01.00.32' (without quotes) in the above url"
        )
        if url.endswith("json"):
            tbl_files = [url]
        else:
            tbl_files = [
                (url.rstrip("/") + "/" + f)
                for f in table_files
                if f not in ignored_table_files
            ]

    def load_data_from_github(f, ctx):
        st.runtime.scriptrunner.add_script_run_ctx(threading.current_thread(), ctx)
        tbl_name = os.path.basename(f)
        if tbl_name in ignored_table_files:
            return
        r = requests.get(f)
        r.raise_for_status()
        data = json.loads(r.text)
        tbl_raw_data[tbl_name] = data
        process_table(tbl_name, data)

    with ThreadPoolExecutor(8) as tpool:
        # tpool.map(load_data_from_github, tbl_files)
        ctx = st.runtime.scriptrunner.get_script_run_ctx()
        futures = [tpool.submit(load_data_from_github, f, ctx) for f in tbl_files]
        for future in as_completed(futures):
            future.result()

if table_source == "Local":
    with col2:
        srcdir = st.text_input("Table directory:")
    if srcdir:
        srcdir = Path(srcdir).expanduser()
        with col2:
            st.write(srcdir)
        if srcdir.name.endswith("json"):
            st.write("Loading single file")
            try:
                data = json.loads(srcdir.read_text())
                tbl_raw_data[srcdir.name] = data
                process_table(srcdir.name, data)
            except json.decode.JSONDecodeError:
                st.toast(f"{srcdir.name} can not be read.")
        else:
            files = list(srcdir.glob("*.json"))
            filenames = {f.name for f in files}
            is_valid_path = filenames & table_files
            if not is_valid_path:
                with col2:
                    st.error("No known tables found at this path")
            for f in files:
                tbl_name = f.name
                if tbl_name in ignored_table_files:
                    continue
                try:
                    data = json.loads(f.read_text())
                    tbl_raw_data[tbl_name] = data
                    process_table(tbl_name, data)
                except json.decoder.JSONDecodeError:
                    st.toast(f"{tbl_name} can not be read.")


if table_source:
    st.markdown("""
    # Tables - Frequencies - Variables

    ## Metrics
    """)

    cols = st.columns(3)

    with cols[0]:
        st.metric("Tables", len(tbls))
    with cols[1]:
        st.metric("Frequencies", len(frequencies))
    with cols[2]:
        st.metric("Variables", len(var_to_tbl))

    with st.expander("Ignored tables"):
        st.table(sorted(ignored_table_files))

    st.divider()

    variables = sorted(var_to_tbl)

    var_references = defaultdict(set)
    for vname, items in var_to_tbl.items():
        var_references[len(items)].add(vname)
    var_references = {
        counts: sorted(vnames) for counts, vnames in var_references.items()
    }

if var_to_tbl:
    st.markdown("## Variables")
    if var_references and len(var_references) > 1:
        filtered_variables = st.checkbox(
            "Filter variable list by number of references to tables"
        )
        if filtered_variables:
            counts = st.select_slider(
                "Number of references", options=sorted(var_references)
            )
            variables = var_references[counts]

    varname = st.selectbox(
        f"Select Variable (count: {len(variables)})", variables, index=None
    )
    if varname:
        show_selected_variable(varname)
