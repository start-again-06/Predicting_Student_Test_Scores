path = "/kaggle/working/"

import os
import ast
import copy
import shutil
import numpy as np
import pandas as pd

from bokeh.plotting import figure, gridplot
from bokeh.io import output_file, show, output_notebook

output_notebook()

def bokeh_show(params, df_cross, show_figures1, show_figures2, wps_fig2, color_cross):
    colors = [subm['color'] for subm in params['subm']]

    def dossier(js, subms, cols):
        def quant(i, js, subms, cols):
            return {
                "c": i,
                "q": sum([1 for subm in cols[i] if subm == subms[js]])
            }
        return {
            "name": subms[js],
            "q_in": [quant(i, js, subms, cols) for i in range(len(subms))]
        }

    alls = pd.read_csv("tida_desc.csv")
    matrix = [ast.literal_eval(str(row.alls)) for row in alls.itertuples()]

    subms = sorted(matrix[0])
    cols = [[data[i] for data in matrix] for i in range(len(subms))]
    dossiers = [dossier(js, subms, cols) for js in range(len(subms))]
    subm_names = [d["name"] for d in dossiers]

    figures1, qss = [], []
    height = 174

    for i, d in enumerate(dossiers):
        qs = [one["q"] for one in d["q_in"]]
        x_names = [n.replace("Group", "").replace("subm_", "") for n in subm_names]
        f = figure(x_range=x_names, width=140, height=height, title=f"alls.{i}")
        f.vbar(x=x_names, top=qs, width=0.6, color=colors)
        figures1.append(f)
        qss.append(qs)

    output_file("tida_alls.html")
    if show_figures1:
        show(gridplot([figures1]))

def matrix_vs(path, fs_names):
    dfs = [pd.read_csv(path + f"{n}.csv").rename(columns={"exam_score": n}) for n in fs_names]
    dfm = dfs[0]
    for df in dfs[1:]:
        dfm = pd.merge(dfm, df, on="id")

    pairs = []
    for i in range(len(fs_names) - 1):
        for j in range(i + 1, len(fs_names)):
            pairs.append((fs_names[i], fs_names[j]))

    for a, b in pairs:
        dfm[f"{a}_vs_{b}"] = abs(dfm[a] - dfm[b])

    data = {"subm": fs_names}
    for name in fs_names:
        data[name] = [
            round(dfm.get(f"{name}_vs_{o}", 0).sum(), 2)
            if f"{name}_vs_{o}" in dfm else 0
            for o in fs_names
        ]

    return pd.DataFrame(data)

def arr_colors(color):
    base = ['darkgray', 'silver', 'gainsboro']
    palettes = {
        "R": ['firebrick', 'red', 'crimson', 'tomato'],
        "G": ['darkgreen', 'limegreen', 'green', 'lime'],
        "B": ['midnightblue', 'blue', 'mediumblue', 'deepskyblue'],
        "RGB": ['mediumblue', 'darkgreen', 'crimson'],
        "M": ['mediumvioletred', 'darkorchid', 'darkmagenta', 'magenta']
    }
    return palettes.get(color, ['black', 'dimgray', 'gray']) + base

def h_blend(params, _update={}, cross="silver", details=False):
    params = copy.deepcopy(params)
    params.update(_update)

    def read(i):
        name = params["subm"][i]["name"]
        df = pd.read_csv(params["path"] + name + ".csv")
        return df.rename(columns={params["id_target"][1]: name})

    dfs = [read(i) for i in range(len(params["subm"]))]
    df = dfs[0]
    for d in dfs[1:]:
        df = pd.merge(df, d, on=params["id_target"][0])

    cols = [s["name"] for s in params["subm"]]
    wts = [s["weight"] for s in params["subm"]]
    subwts = params.get("subwts", [0]*len(cols))

    def ensemble(row):
        return sum(row[c] * (wts[i] + subwts[i]) for i, c in enumerate(cols))

    df["ensemble"] = df.apply(ensemble, axis=1)

    out = df[[params["id_target"][0], "ensemble"]]
    out = out.rename(columns={"ensemble": params["id_target"][1]})

    out.to_csv("submission.csv", index=False)
    return out

def trend_T(x, ct1, ct2, k):
    e1, e2, e3 = x["es1"], x["es2"], x["es3"]
    if e1 < e2 < e3:
        return e3 * (ct1 - k * (e3 - e1))
    if e1 > e2 > e3:
        return e3 / (ct2 - k * (e1 - e3))
    return e3

def prepare_trend(df1, df2, df3, ct1, ct2, k):
    df1 = df1.rename(columns={"exam_score": "es1"})
    df2 = df2.rename(columns={"exam_score": "es2"})
    df3 = df3.rename(columns={"exam_score": "es3"})

    df = df1.merge(df2, on="id").merge(df3, on="id")
    df["exam_score"] = df.apply(lambda x: trend_T(x, ct1, ct2, k), axis=1)
    return df[["id", "exam_score"]]

def cleanup(files):
    for f in files:
        if os.path.isfile(path + f):
            os.remove(path + f)

print("Pipeline executed successfully.")
