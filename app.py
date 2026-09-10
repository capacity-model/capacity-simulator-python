"""
Stochastic Capacity Simulator — Streamlit (Python) version
ISyE 6202 & 6335 Supply Chain Facilities · Georgia Tech

A Monte-Carlo model of daily production under stochastic demand, reliability,
quality and efficiency. Same model as the web (HTML) version:
https://capacity-model.github.io/

Run locally:   pip install -r requirements.txt   then   streamlit run app.py
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Stochastic Capacity Simulator", page_icon="🚚", layout="wide")

# Georgia Tech look-and-feel
st.markdown(
    """
<style>
  .block-container {padding-top: 2.2rem; max-width: 1300px;}
  h1 {color: #003057; letter-spacing: -.01em;}
  h2, h3 {color: #003057;}
  [data-testid="stMetricValue"] {color: #003057; font-variant-numeric: tabular-nums;}
  [data-testid="stMetricLabel"] {color: #5c6a78;}
  [data-testid="stVerticalBlockBorderWrapper"] {
      background: #ffffff; border: 1px solid #e3e7ea; border-radius: 12px;
      box-shadow: 0 1px 3px rgba(16, 35, 58, 0.07); padding: 4px 6px;}
  [data-testid="stSidebar"] {border-right: 1px solid #d8dde2;}
  [data-testid="stSidebar"] h1 {font-size: 1.1rem; color: #5c6a78;
      text-transform: uppercase; letter-spacing: .08em;}
  .stButton>button {background: #b3a369; color: #241f07; font-weight: 700;
      border: none;}
  .stButton>button:hover {filter: brightness(1.05); color: #241f07;}
</style>
""",
    unsafe_allow_html=True,
)

# Georgia Tech palette
GOLD, NAVY = "#b3a369", "#003057"
SERIES1_COLORS = ["#3b82c4", "#d24b57", "#e0982a", "#157a8a", "#9c4f2f", "#4f9d54", "#7a5cc0"]


# ----------------------------------------------------------------------------
# Random sampling (mirrors the JS engine)
# ----------------------------------------------------------------------------
def beta_from_moments(mean, sigma):
    """Beta(a, b) on [0, 1] matching a target mean and std dev."""
    mean = min(0.999, max(0.001, mean))
    sigma = max(1e-3, sigma)
    nu = mean * (1 - mean) / (sigma * sigma) - 1
    a = max(1e-4, mean * nu)
    b = max(1e-4, (1 - mean) * nu)
    return a, b


def sample_beta_scaled(rng, lo, hi, mean, sigma):
    m = (mean - lo) / (hi - lo)
    s = sigma / (hi - lo)
    a, b = beta_from_moments(m, s)
    return lo + (hi - lo) * rng.beta(a, b)


def draw_demand(rng, p):
    d = p["dMean"] + rng.standard_normal() * p["dStd"] if p["dem"] == "Normal" else 0.0
    if p["dem"] == "Triangular":
        d = rng.triangular(p["tMin"], p["tMode"], p["tMax"])
    elif p["dem"] == "PERT":
        a = 1 + p["pLam"] * (p["pMode"] - p["pMin"]) / (p["pMax"] - p["pMin"])
        b = 1 + p["pLam"] * (p["pMax"] - p["pMode"]) / (p["pMax"] - p["pMin"])
        d = p["pMin"] + (p["pMax"] - p["pMin"]) * rng.beta(a, b)
    elif p["dem"] == "Beta":
        d = sample_beta_scaled(rng, p["bMin"], p["bMax"], p["bMean"], p["bStd"])
    return max(0.0, d)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------
def simulate(p, rng):
    gross = p["N"] * p["a"] / p["t"]  # gross capacity = N*a/t (units/day)
    init = p["target"]  # day 1 opens at the target inventory
    rows = []
    for day in range(1, p["days"] + 1):
        work = 1 if (day - 1) % 7 < p["k"] else 0  # work-day flag: 1 if working day, else 0
        demand = draw_demand(rng, p)  # demand
        R = sample_beta_scaled(rng, 0, 1, p["rMean"], p["sAvail"])  # reliability (0-1)
        Q = sample_beta_scaled(rng, 0, 1, p["qMean"], p["sQual"])  # quality (0-1)
        E = sample_beta_scaled(rng, 0, 1, p["eMean"], p["sEff"])  # efficiency (0-1)
        netcap = work * np.floor(p["a"] * p["N"] * R * Q * E / p["t"])  # net capacity
        prod = min(netcap, demand + max(0.0, p["target"] - init))  # production
        sales = max(0.0, min(demand, prod + init))  # sales
        lost = max(0.0, demand - sales)  # lost sales
        final = max(0.0, init + prod - sales)  # final stock
        svc = sales / demand if demand > 0 else 1.0  # service level
        gu = prod / gross  # gross utilization
        nu = prod / netcap if (work == 1 and netcap > 0) else 0.0  # net utilization
        rows.append(
            dict(
                day=day,
                work=work,
                init=init,
                demand=demand,
                R=R,
                Q=Q,
                E=E,
                netcap=netcap,
                prod=prod,
                sales=sales,
                lost=lost,
                final=final,
                svc=svc,
                gu=gu,
                nu=nu,
            )
        )
        init = final  # carry today's closing stock to tomorrow's opening stock
    return pd.DataFrame(rows), gross


# ----------------------------------------------------------------------------
# Sidebar — parameters
# ----------------------------------------------------------------------------
st.sidebar.title("Parameters")
if st.sidebar.button("🎲  Run new simulation", use_container_width=True):
    st.session_state["seed"] = np.random.randint(0, 2**31 - 1)
seed = st.session_state.get("seed", 42)

st.sidebar.subheader("Resources & process")
N = st.sidebar.number_input("Number of production resources", 1, 60, 12, 1)
t = st.sidebar.number_input("Process time (min/part)", 0.1, value=5.0, step=0.1)
a = st.sidebar.number_input("Availability (min/day)", 1.0, value=480.0, step=10.0)
k = st.sidebar.number_input("Days per week (first k work)", 1, 7, 5, 1)

st.sidebar.subheader("Inventory & horizon")
target = st.sidebar.number_input("Target inventory (units)", 0.0, value=400.0, step=10.0)
days = st.sidebar.number_input("Simulation days", 7, 2000, 300, 1)

st.sidebar.subheader("Demand distribution")
dem = st.sidebar.selectbox("Distribution", ["Normal", "Triangular", "PERT", "Beta"])
p = dict(
    N=N,
    t=t,
    a=a,
    k=int(k),
    target=target,
    days=int(days),
    dem=dem,
    dMean=429.0,
    dStd=38.0,
    tMin=300.0,
    tMode=429.0,
    tMax=560.0,
    pMin=300.0,
    pMode=429.0,
    pMax=560.0,
    pLam=4.0,
    bMin=300.0,
    bMax=560.0,
    bMean=429.0,
    bStd=40.0,
)
if dem == "Normal":
    p["dMean"] = st.sidebar.number_input("Mean (units/day)", value=429.0)
    p["dStd"] = st.sidebar.number_input("Std dev (units/day)", 0.0, value=38.0)
elif dem == "Triangular":
    p["tMin"] = st.sidebar.number_input("Min", value=300.0)
    p["tMode"] = st.sidebar.number_input("Most likely", value=429.0)
    p["tMax"] = st.sidebar.number_input("Max", value=560.0)
elif dem == "PERT":
    p["pMin"] = st.sidebar.number_input("Min", value=300.0)
    p["pMode"] = st.sidebar.number_input("Most likely", value=429.0)
    p["pMax"] = st.sidebar.number_input("Max", value=560.0)
    p["pLam"] = st.sidebar.number_input("λ shape", 0.1, value=4.0)
else:
    p["bMin"] = st.sidebar.number_input("Min", value=300.0)
    p["bMax"] = st.sidebar.number_input("Max", value=560.0)
    p["bMean"] = st.sidebar.number_input("Mean", value=429.0)
    p["bStd"] = st.sidebar.number_input("Std dev", 0.1, value=40.0)

st.sidebar.subheader("Daily factors — Beta on [0, 1]")
st.sidebar.caption("Each factor is Beta-distributed on [0, 1]. Set its mean and σ.")
c1, c2 = st.sidebar.columns(2)
p["rMean"] = c1.number_input("Reliability mean", 0.01, 0.99, 0.90, 0.01)
p["sAvail"] = c2.number_input("Reliability σ", 0.01, 0.30, 0.05, 0.01)
p["qMean"] = c1.number_input("Quality mean", 0.01, 0.99, 0.90, 0.01)
p["sQual"] = c2.number_input("Quality σ", 0.01, 0.30, 0.05, 0.01)
p["eMean"] = c1.number_input("Efficiency mean", 0.01, 0.99, 0.90, 0.01)
p["sEff"] = c2.number_input("Efficiency σ", 0.01, 0.30, 0.05, 0.01)

# ----------------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------------
rng = np.random.default_rng(seed)
df, gross = simulate(p, rng)
eqr = p["rMean"] * p["qMean"] * p["eMean"]

st.markdown("#### ISyE 6202 · 6335 Supply Chain Facilities · Capacity Modeling")
st.title("🚚 Stochastic Capacity Simulator")
st.caption(
    "A Monte-Carlo model of daily production under stochastic demand, "
    "reliability, quality and efficiency. Adjust the parameters in the sidebar, "
    "then roll a new simulated instance."
)

# KPIs
k1, k2, k3, k4 = st.columns(4, border=True)
k1.metric("Mean service level", f"{df['svc'].mean()*100:.1f}%")
k2.metric("Total demand", f"{df['demand'].sum():,.0f}", help="units over horizon")
k3.metric("Stockout days", f"{int((df['lost'] > 0.5).sum())}", help=f"of {len(df)} days")
k4.metric("Total lost sales", f"{df['lost'].sum():,.0f}", help="units over horizon")

d1, d2, d3 = st.columns(3, border=True)
d1.metric("Gross capacity", f"{gross:,.0f}", help="units/day")
d2.metric("r·q·e", f"{eqr*100:.0f}%", help="mean factor")
d3.metric("Est. net capacity", f"{eqr*gross:,.0f}", help="units/day")


# Charts. A "Show lines" picker above each chart controls which series are drawn —
# remove any lines you don't want (you can remove several); re-add them from the dropdown.
def line_chart(data, key_names, colors, height, shown, pct=False):
    names = list(key_names.values())
    shown_keys = [k for k in key_names if key_names[k] in shown]
    shown_ordered = [key_names[k] for k in shown_keys]  # display names, in a stable order

    # long format for the coloured lines
    long = data.melt(id_vars="day", value_vars=shown_keys, var_name="k", value_name="value")
    long["Series"] = long["k"].map(key_names)
    if pct:
        long["value"] = long["value"] * 100

    # wide format for a single hover tooltip listing every shown line's value that day
    wide = data[["day"] + shown_keys].copy()
    if pct:
        for kk in shown_keys:
            wide[kk] = wide[kk] * 100
    wide = wide.rename(columns={k: key_names[k] for k in shown_keys})

    color = alt.Color(
        "Series:N",
        title=None,
        sort=names,
        scale=alt.Scale(domain=names, range=colors),
        legend=alt.Legend(symbolSize=70, symbolType="circle"),
    )
    nearest = alt.selection_point(nearest=True, on="pointerover", fields=["day"], empty=False)

    lines = (
        alt.Chart(long)
        .mark_line()
        .encode(
            x=alt.X("day:Q", title="Day"),
            y=alt.Y("value:Q", title="%" if pct else None),
            color=color,
        )
    )
    dots = lines.mark_point(size=45, filled=True).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )
    rule = (
        alt.Chart(wide)
        .mark_rule(color="#9aa5b1")
        .encode(
            x="day:Q",
            opacity=alt.condition(nearest, alt.value(0.5), alt.value(0)),
            tooltip=[alt.Tooltip("day:Q", title="Day")]
            + [
                alt.Tooltip(field=v, type="quantitative", title=v, format=".0f")
                for v in shown_ordered
            ],
        )
        .add_params(nearest)
    )
    return alt.layer(lines, dots, rule).properties(height=height).interactive()


names1 = {
    "init": "Initial stock",
    "demand": "Demand",
    "netcap": "Net capacity",
    "prod": "Production",
    "sales": "Sales",
    "lost": "Lost sales",
    "final": "Final stock",
}
st.subheader("Daily quantities under current scenario instance")
opts1 = list(names1.values())
shown1 = st.multiselect("Show lines", opts1, default=opts1, key="show1")
st.altair_chart(line_chart(df, names1, SERIES1_COLORS, 360, shown1), use_container_width=True)

names2 = {"svc": "Service level", "gu": "Gross cap utilization", "nu": "Net cap utilization"}
c2_colors = [SERIES1_COLORS[0], SERIES1_COLORS[1], SERIES1_COLORS[5]]
st.subheader("Dynamic service & capacity utilization performance")
opts2 = list(names2.values())
shown2 = st.multiselect("Show lines", opts2, default=opts2, key="show2")
st.altair_chart(line_chart(df, names2, c2_colors, 320, shown2, pct=True), use_container_width=True)

# Summary statistics
st.subheader("Summary statistics")
disp = df.copy()
disp["netcapPct"] = disp["netcap"] / gross
cols = [
    ("Initial Stock", "init"),
    ("Demand", "demand"),
    ("Reliability", "R"),
    ("Quality", "Q"),
    ("Efficiency", "E"),
    ("Net Capacity (% of gross)", "netcapPct"),
    ("Production", "prod"),
    ("Sales", "sales"),
    ("Lost Sales", "lost"),
    ("Final Stock", "final"),
    ("Service Level", "svc"),
    ("Gross Capacity Utilization", "gu"),
    ("Net Capacity Utilization", "nu"),
]
pct_keys = {"R", "Q", "E", "netcapPct", "svc", "gu", "nu"}
stats = {}
for label, key in cols:
    s = disp[key]
    if key in pct_keys:
        stats[label] = [f"{s.min()*100:.0f}%", f"{s.mean()*100:.0f}%", f"{s.max()*100:.0f}%"]
    else:
        stats[label] = [f"{s.min():,.0f}", f"{s.mean():,.0f}", f"{s.max():,.0f}"]
st.dataframe(pd.DataFrame(stats, index=["Min", "Mean", "Max"]), use_container_width=True)

# Daily ledger
st.subheader("Daily ledger")
led = pd.DataFrame(
    {
        "Day": df["day"],
        "Off": np.where(df["work"] == 0, "off", ""),
        "Initial Stock": df["init"].round(0).astype(int),
        "Demand": df["demand"].round(0).astype(int),
        "Reliability": (df["R"] * 100).round(0).astype(int).astype(str) + "%",
        "Quality": (df["Q"] * 100).round(0).astype(int).astype(str) + "%",
        "Efficiency": (df["E"] * 100).round(0).astype(int).astype(str) + "%",
        "Net Capacity": df["netcap"].round(0).astype(int),
        "Production": df["prod"].round(0).astype(int),
        "Sales": df["sales"].round(0).astype(int),
        "Lost Sales": df["lost"].round(0).astype(int),
        "Final Stock": df["final"].round(0).astype(int),
        "Service Level": (df["svc"] * 100).round(0).astype(int).astype(str) + "%",
        "Gross Capacity Utilization": (df["gu"] * 100).round(0).astype(int).astype(str) + "%",
        "Net Capacity Utilization": (df["nu"] * 100).round(0).astype(int).astype(str) + "%",
    }
)
st.dataframe(led, use_container_width=True, height=440, hide_index=True)

st.caption("Capacity Modeling · ISyE 6202 & 6335 Supply Chain Facilities · Georgia Tech ISyE")
st.caption(
    "Simulator developed by PhD student Yinzhu Quan and Prof. Benoit Montreuil "
    "· Version 1.0, 2026-09-10"
)
