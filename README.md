# WCom Theory project: IRS joint active and passive beamforming

Paper: Q. Wu and R. Zhang, "Intelligent Reflecting Surface Enhanced Wireless Network via Joint
Active and Passive Beamforming," IEEE Trans. Wireless Commun., vol. 18, no. 11, 2019.

## Contents

| Folder | What it is |
| --- | --- |
| `simulation/ris_sim.py` | The simulator. Produces the four result figures and `figures/results.json`. |
| `simulation/make_diagram.py` | Draws the system-model figure. |
| `simulation/make_numbers.py` | Writes `report/numbers.tex` and copies figures into `report/`. |
| `figures/` | Figures (PNG and PDF) and the raw numbers. |
| `report/` | LaTeX report. Upload `report_overleaf.zip` to Overleaf (New Project > Upload Project), compile with pdfLaTeX. |
| `presentation/` | `WCom_Project_Presentation.pptx` and the script that builds it. |

## Re-running everything

```
pip install numpy matplotlib cvxpy python-pptx
cd simulation
python ris_sim.py          # about 15 minutes on 8 cores; add --quick for a 1-minute test
python make_diagram.py
python make_numbers.py
python ../presentation/build_deck.py
```

## Notes

- Phase convention: `v = [e^{j theta_1}, ..., e^{j theta_N}]^H`, so `v_n = e^{-j theta_n}` (as in the paper).
  The code computes the reflected channel as `v.conj() @ Phi` and the physical phases as `-angle(v)`.
- Experiments 1 and 3 (compared with the SDR lower bound) evaluate every scheme on the same 200
  channel realisations per point; Experiments 2 and 4 use 1000.
- The software versions of the last run are stored in `figures/results.json` and listed in the report.
