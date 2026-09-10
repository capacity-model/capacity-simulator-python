# Stochastic Capacity Simulator — Python (Streamlit)

An interactive Monte-Carlo capacity-modeling simulator for
**ISyE 6202 / 6335 — Supply Chain Facilities**, Georgia Institute of Technology.

- **Course:** ISyE 6202 & 6335 — Supply Chain Facilities
- **Instructor:** Prof. Benoit Montreuil
- **Institution:** Georgia Institute of Technology, H. Milton Stewart School of Industrial & Systems Engineering (ISyE)

This is the **Python version** of the simulator, so students can read and modify
the model directly. It shares the same model as the web (HTML) version.

- **Web (HTML) app:** https://capacity-model.github.io/
- **Live Python app:** https://capacity-model.streamlit.app/
- **This repository:** the [Streamlit](https://streamlit.io) source (`app.py`).

## What it models

Each day, production runs on `N` resources with process time `t` and availability
`a` minutes/day, `k` working days per week. Demand is random (Normal / Triangular /
PERT / Beta). Reliability, Quality and Efficiency are each Beta-distributed on
[0, 1] with a student-set mean and σ.

```
Net capacity = work × ⌊ a·N·(R·Q·E) ÷ t ⌋
Production   = min( Net capacity, Demand + max(0, Target − Init) )
Sales        = max( 0, min( Demand, Production + Init ) )
Lost sales   = max( 0, Demand − Sales )
Final stock  = max( 0, Init + Production − Sales )
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Files

- `app.py` — the whole app (model + UI).
- `requirements.txt` — Python dependencies.
- `.streamlit/config.toml` — Georgia Tech theme colors.
