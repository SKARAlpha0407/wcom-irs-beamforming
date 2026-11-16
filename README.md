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

## Before you submit

1. Put your names and roll numbers on the report title page (`report/main.tex`) and the first slide.
2. Replace "Member 1/2/3" in the slide footers and outline with your names.
3. Check Table I of the report against Section V of the paper, and edit any value that differs
   (the constants are at the top of `ris_sim.py`), then re-run.
