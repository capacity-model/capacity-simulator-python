# :truck: Stochastic Capacity Simulator

An interactive Monte-Carlo simulator for capacity modeling under stochastic demand, reliability, quality, and efficiency. Developed for **ISyE 6202 & 6335 — Supply Chain Facilities** at the Georgia Institute of Technology (Instructor: Prof. Benoit Montreuil). This is the Python (Streamlit) version; an interactive web version is also available.

- **Live Python app:** https://capacity-model.streamlit.app/
- **Web (HTML) app:** https://capacity-model.github.io/

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/capacity-model/capacity-simulator-python.git
   cd capacity-simulator-python
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Launch the app locally:

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501). Set the parameters in the sidebar and roll new simulated instances.

### Model

Each day, production runs on `N` resources with process time `t` and availability `a` minutes/day, over `k` working days per week. Demand is drawn from a chosen distribution (Normal / Triangular / PERT / Beta); reliability, quality, and efficiency are each Beta-distributed on [0, 1].

```
Net capacity = work × ⌊ a·N·(R·Q·E) ÷ t ⌋
Production   = min( Net capacity, Demand + max(0, Target − Init) )
Sales        = max( 0, min( Demand, Production + Init ) )
Lost sales   = max( 0, Demand − Sales )
Final stock  = max( 0, Init + Production − Sales )
```

### Source Code

- `app.py` — the full application (sampling, simulation, and UI).
- `requirements.txt` — Python dependencies.
- `.streamlit/config.toml` — Georgia Tech theme colors.

## Contact

For questions or suggestions, please [raise an issue](https://github.com/capacity-model/capacity-simulator-python/issues) or [contact us](mailto:yquan9@gatech.edu).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
