"""Builds WCom_Project_Presentation.pptx from the simulation figures and results.json.

Run:  python build_deck.py
Edit the GROUP block below with your names and roll numbers, then rebuild
(or simply edit the title slide in PowerPoint).
"""
import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
R = json.load(open(os.path.join(FIG, "results.json")))

GROUP = ["Shreyas Kumar Rai (23UCC601)"]
COURSE = "Wireless Communication (Theory) | Project Presentation | November 2026"

NAVY = RGBColor(0x14, 0x32, 0x4A)
TEAL = RGBColor(0x0E, 0x8A, 0x8A)
RED = RGBColor(0xC0, 0x39, 0x2B)
INK = RGBColor(0x22, 0x2B, 0x33)
GREY = RGBColor(0x6B, 0x74, 0x7C)
PALE = RGBColor(0xEE, 0xF4, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
state = {"n": 0}

# ---------------- numbers quoted on the slides (all from results.json) ------
e1 = R["exp1_power_vs_distance"]
e2 = R["exp2_power_vs_N"]
e3 = R["exp3_convergence"]["curves"]
e4 = R["exp4_discrete_phase"]
c1 = e1["curves"]
d = e1["d"]
i15, i50 = d.index(15), d.index(50)
ipk = max(range(len(d)), key=lambda i: c1["Alternating optimization"][i])
save50 = c1["Without IRS"][i50] - c1["Alternating optimization"][i50]
gap_user_mrt = c1["AP-user MRT"][i50] - c1["Alternating optimization"][i50]
gap_irs_mrt = c1["AP-IRS MRT"][i15] - c1["Alternating optimization"][i15]
gap_lb = max(a - b for a, b in zip(c1["Alternating optimization"], c1["Lower bound (SDR)"]))
gap_rand = c1["Random phase shift"][i50] - c1["Alternating optimization"][i50]
N2 = e2["N"]
ao50 = e2["curves"]["d=50"]["Alternating optimization"]
ao15 = e2["curves"]["d=15"]["Alternating optimization"]
drop_double = ao50[N2.index(40)] - ao50[N2.index(80)]
drop_double2 = ao50[N2.index(80)] - ao50[N2.index(160)]
drop15 = ao15[0] - ao15[-1]
q = e4["curves"]
loss = {b: q[f"{b}-bit phase shifters"][-1] - q["Alternating optimization"][-1] for b in (1, 2, 3)}
its = {k: v["AO"] for k, v in e3.items()}
gapK = {k: v["AO"][-1] - v["lower_bound"] for k, v in e3.items()}
P = R["params"]


def text(slide, x, y, w, h, paras, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT,
         bullet=False, space=6):
    """paras: list of str or (str, dict) where dict may hold size/color/bold/level."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, p in enumerate(paras):
        opt = {}
        if isinstance(p, tuple):
            p, opt = p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        lvl = opt.get("level", 0)
        mark = ""
        if bullet or opt.get("bullet"):
            mark = "•  " if lvl == 0 else "–  "
        run = para.add_run()
        run.text = mark + p
        run.font.name = FONT
        run.font.size = Pt(opt.get("size", size - 2 * lvl))
        run.font.bold = opt.get("bold", bold)
        run.font.color.rgb = opt.get("color", color)
        para.alignment = align
        para.space_after = Pt(space)
        if lvl:
            para.level = lvl
    return box


def rect(slide, x, y, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
    s.shadow.inherit = False
    return s


def card(slide, x, y, w, h, title, lines, accent=TEAL, size=15):
    rect(slide, x, y, w, h, PALE)
    rect(slide, x, y, 0.07, h, accent)
    text(slide, x + 0.2, y + 0.1, w - 0.3, 0.4, [title], size=size + 1, bold=True, color=NAVY)
    text(slide, x + 0.2, y + 0.55, w - 0.3, h - 0.6, lines, size=size, space=4)


def eq(slide, x, y, w, h, lines, size=18):
    rect(slide, x, y, w, h, PALE)
    text(slide, x + 0.15, y + 0.08, w - 0.3, h - 0.1, lines, size=size, color=NAVY,
         align=PP_ALIGN.CENTER, space=3)


def picture(slide, name, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(os.path.join(FIG, name), Inches(x), Inches(y), **kw)


def new_slide(title, speaker, notes):
    state["n"] += 1
    s = prs.slides.add_slide(BLANK)
    text(s, 0.6, 0.35, 11.2, 0.8, [title], size=30, bold=True, color=NAVY)
    rect(s, 0.6, 1.15, 1.2, 0.05, TEAL)
    text(s, 0.6, 7.0, 9, 0.3, ["IRS-Enhanced Wireless Network via Joint Active and Passive Beamforming"],
         size=10, color=GREY)
    text(s, 10.2, 7.0, 2.55, 0.3, [f"{speaker}   |   {state['n']}"], size=10, color=GREY,
         align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def fmt(x, nd=1):
    return f"{x:.{nd}f}"


M1 = M2 = M3 = "Shreyas Kumar Rai"

# ============================ 1. Title =====================================
state["n"] += 1
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0.8, 3.55, 1.6, 0.06, TEAL)
text(s, 0.8, 1.2, 11.5, 2.3,
     ["Intelligent Reflecting Surface Enhanced Wireless Network via Joint Active and Passive Beamforming"],
     size=38, bold=True, color=WHITE)
text(s, 0.8, 3.8, 11.5, 1.0,
     ["Study and reproduction of: Q. Wu and R. Zhang, IEEE Transactions on Wireless Communications, vol. 18, no. 11, 2019",
      "Category: Reconfigurable Intelligent Surfaces (RIS)  |  5G/6G Communications"],
     size=17, color=RGBColor(0xC9, 0xD8, 0xE3))
text(s, 0.8, 5.3, 11.5, 1.0, ["     ".join(GROUP)], size=18, bold=True, color=WHITE)
text(s, 0.8, 6.5, 11.5, 0.4, [COURSE], size=13, color=RGBColor(0xC9, 0xD8, 0xE3))
s.notes_slide.notes_text_frame.text = (
    "Introduce yourself and the paper. One line: the paper asks how a passive reflecting surface "
    "can be configured together with the base-station beamformer so that a user gets its target SNR "
    "with the least transmit power.")

# ============================ 2. Outline ===================================
s = new_slide("What we will cover", M1,
              "Give the roadmap. Keep this under 30 seconds.")
card(s, 0.6, 1.6, 3.9, 3.0, "1  Overview",
     [("The problem the paper solves", {"bullet": True}),
      ("Why the problem matters", {"bullet": True}),
      ("Why we chose it", {"bullet": True}),
      ("System model", {"bullet": True})], size=16)
card(s, 4.72, 1.6, 3.9, 3.0, "2  Solution",
     [("Problem formulation", {"bullet": True}),
      ("Semidefinite relaxation (SDR)", {"bullet": True}),
      ("Alternating optimization", {"bullet": True}),
      ("The N-squared power scaling law", {"bullet": True})], size=16, accent=NAVY)
card(s, 8.84, 1.6, 3.9, 3.0, "3  Results",
     [("Our Python reproduction", {"bullet": True}),
      ("Four experiments and what they show", {"bullet": True}),
      ("Our results against the paper", {"bullet": True}),
      ("Challenges, limitations, future work", {"bullet": True})], size=16, accent=RED)

# ============================ 3. Problem ===================================
s = new_slide("The problem: coverage costs power", M1,
              "Explain with the course vocabulary: path loss and blockage make the direct link weak. "
              "The classical fixes are more transmit power, more antennas, or active relays. All of these "
              "cost energy and hardware. An IRS is a passive panel: each element only re-radiates the "
              "incoming wave with a phase shift we choose.")
text(s, 0.6, 1.5, 6.3, 4.8, [
    ("A user far from the access point, or behind an obstacle, sees a weak channel.", {"bullet": True}),
    ("Usual remedies all add active hardware or power:", {"bullet": True}),
    ("raise the transmit power", {"level": 1, "bullet": True}),
    ("add antennas and RF chains (massive MIMO)", {"level": 1, "bullet": True}),
    ("deploy relays or more base stations", {"level": 1, "bullet": True}),
    ("An intelligent reflecting surface (IRS, also called RIS) is a panel of N low-cost passive elements. "
     "Each element reflects the incoming signal with an adjustable phase shift.", {"bullet": True}),
    ("No transmit RF chains, no amplifiers, no noise amplification.", {"bullet": True, "bold": True, "color": TEAL}),
], size=19, space=8)
card(s, 7.3, 1.6, 5.4, 4.5, "Key question of the paper", [
    "Given an M-antenna AP, an N-element IRS and a user with an SNR target,",
    "",
    ("how should the AP beamformer (active) and the IRS phase shifts (passive) be chosen together "
     "so that the AP transmit power is minimum?", {"bold": True, "color": NAVY, "size": 19}),
    "",
    "The two are coupled: the best beam depends on the phases, and the best phases depend on the beam.",
], size=16)

# ============================ 4. Motivation ================================
s = new_slide("Motivation and why we chose it", M1,
              "Three reasons for importance: energy efficiency for 6G, low hardware cost, and that this "
              "paper is the foundation of most later RIS optimisation work. Then say why it suited us: "
              "it uses exactly the tools taught in the course (path loss, Rayleigh and Rician fading, "
              "MRC/MRT beamforming) and every result can be reproduced in simulation.")
card(s, 0.6, 1.6, 5.9, 2.25, "Why the problem matters", [
    ("Green 6G: more coverage without more radiated power", {"bullet": True}),
    ("Passive elements are cheap, thin and easy to mount on walls", {"bullet": True}),
    ("Lets the network shape the channel, not only adapt to it", {"bullet": True})], size=15)
card(s, 0.6, 4.05, 5.9, 2.25, "Relevance of this paper", [
    ("One of the first to optimize the AP and the IRS jointly", {"bullet": True}),
    ("Proves the N-squared power gain of an IRS", {"bullet": True}),
    ("Starting point for later work on RIS security, SWIPT, UAV, ISAC", {"bullet": True})],
     size=15, accent=NAVY)
card(s, 6.8, 1.6, 5.9, 4.7, "Why we selected it", [
    ("Builds directly on our course units:", {"bullet": True}),
    ("large-scale fading and path loss (Unit II)", {"level": 1, "bullet": True}),
    ("Rayleigh and Rician fading (Unit II)", {"level": 1, "bullet": True}),
    ("MRC / transmit beamforming and diversity (Unit III)", {"level": 1, "bullet": True}),
    ("MIMO and massive MIMO (Unit IV)", {"level": 1, "bullet": True}),
    ("The solution has a clean physical meaning: make all reflected paths add in phase.", {"bullet": True}),
    ("Every claim can be checked by simulation, so we could verify the paper ourselves.", {"bullet": True}),
], size=15, accent=RED)

# ============================ 5. System model ==============================
s = new_slide("System model", M1,
              "Walk through the figure. Three channels: direct AP-user h_d, AP-IRS G, IRS-user h_r. "
              "The IRS applies a diagonal phase matrix Theta. The user receives the direct signal plus "
              "N reflected copies.")
picture(s, "system_model.png", 0.5, 1.45, w=7.6)
eq(s, 8.4, 1.6, 4.4, 1.25, ["Received signal", "y = (hᵣᴴ Θ G + h_dᴴ) w s + n"], size=18)
text(s, 8.4, 3.05, 4.4, 3.4, [
    ("w : AP transmit beamformer (M x 1), power = ||w||²", {"bullet": True}),
    ("Θ = diag(e^{jθ₁}, ..., e^{jθ_N}) : IRS phase shifts", {"bullet": True}),
    ("G : AP to IRS channel (N x M)", {"bullet": True}),
    ("hᵣ : IRS to user channel, h_d : direct channel", {"bullet": True}),
    ("n : noise of power σ²", {"bullet": True}),
    ("Channel knowledge is assumed perfect at the AP.", {"bullet": True, "color": GREY}),
], size=15, space=6)
text(s, 0.6, 5.3, 7.4, 1.2, [
    "The IRS adds no power. It only decides the phase with which each of the N reflected paths arrives."],
     size=16, bold=True, color=TEAL)

# ============================ 6. Formulation ===============================
s = new_slide("Problem formulation", M2,
              "State (P1). The objective is transmit power, the first constraint is the SNR target, the "
              "second is that every IRS element has unit gain and only a phase. Explain why it is hard: "
              "w and theta multiply each other, and the unit-modulus constraint is non-convex.")
eq(s, 0.6, 1.6, 7.0, 2.3, [
    ("(P1)    minimize over w, θ      ||w||²", {"bold": True}),
    "subject to    |(hᵣᴴ Θ G + h_dᴴ) w|²  ≥  γ σ²",
    "0 ≤ θₙ ≤ 2π,    n = 1, ..., N"], size=20)
card(s, 8.0, 1.6, 4.7, 2.3, "Why it is hard", [
    ("w and Θ are multiplied together: the constraint is not convex", {"bullet": True}),
    ("each reflection coefficient must have modulus exactly 1", {"bullet": True})], size=15, accent=RED)
text(s, 0.6, 4.2, 12.1, 0.5, ["Step 1: the beamformer is easy once the phases are fixed"],
     size=20, bold=True, color=NAVY)
text(s, 0.6, 4.75, 12.1, 0.9, [
    "For any fixed Θ the best w is maximum ratio transmission (MRT) along the combined channel. "
    "This is the transmit-side twin of MRC from our course."], size=16)
eq(s, 0.6, 5.65, 12.1, 0.95, [
    "w* = √P · (hᵣᴴΘG + h_dᴴ)ᴴ / ||hᵣᴴΘG + h_dᴴ||"
    "        ⇒        P = γσ² / ||hᵣᴴΘG + h_dᴴ||²"], size=18)
text(s, 0.6, 6.6, 12.1, 0.4, [
    "So the whole problem becomes: choose the phases that maximize the combined channel gain."],
     size=15, bold=True, color=TEAL)

# ============================ 7. SDR =======================================
s = new_slide("Solution 1: semidefinite relaxation (SDR)", M2,
              "Write the phases as a vector v. The channel gain is a quadratic form in v. Lift to the "
              "matrix V = v v^H, which must be rank one. Drop the rank constraint and the problem is a "
              "convex SDP that a solver handles. Its optimum is an upper bound on the gain, so a lower "
              "bound on power. Then recover a valid phase vector by Gaussian randomization.")
text(s, 0.6, 1.5, 6.2, 5.0, [
    ("Stack the phases: v = [e^(jθ₁), ..., e^(jθ_N)]ᴴ, so vₙ = e^(−jθₙ) (the paper's convention). With Φ = diag(hᵣᴴ) G: hᵣᴴΘG = vᴴΦ.",
     {"bullet": True}),
    ("The channel gain becomes a quadratic form  v̄ᴴ R v̄  with |v̄ₙ| = 1.", {"bullet": True}),
    ("Lift: V = v̄ v̄ᴴ.  The objective tr(RV) is now linear, but V must be rank one.",
     {"bullet": True}),
    ("Relax: drop the rank-one constraint. What remains is a convex semidefinite program.",
     {"bullet": True, "bold": True, "color": NAVY}),
    ("Recover: draw random vectors from the SDP solution, project each onto unit modulus, keep the best "
     "(Gaussian randomization).", {"bullet": True}),
], size=17, space=9)
eq(s, 7.1, 1.6, 5.6, 1.9, [
    ("Relaxed problem (convex SDP)", {"bold": True}),
    "maximize   tr(R V)",
    "subject to   Vₙₙ = 1,   V ⪰ 0"], size=18)
card(s, 7.1, 3.75, 5.6, 1.25, "What it gives", [
    "A lower bound on the transmit power, and a near-optimal solution."], size=15)
card(s, 7.1, 5.2, 5.6, 1.25, "Cost", [
    "The matrix has (N+1)² entries, so it becomes slow for large N."], size=15, accent=RED)

# ============================ 8. AO ========================================
s = new_slide("Solution 2: alternating optimization", M2,
              "The low-complexity algorithm. Fix w, then each phase has a closed form: rotate reflected "
              "path n so it arrives in phase with the direct path. Fix the phases, then w is MRT. Repeat. "
              "Each step can only lower the power, so it converges.")
card(s, 0.6, 1.6, 5.9, 2.15, "Step A: fix w, update the phases", [
    "Rotate every reflected path so that it adds in phase with the direct path:",
    ("θₙ = arg(h_dᴴ w) − arg(hᵣ,ₙᴴ gₙᴴ w)", {"bold": True, "color": NAVY, "size": 17})],
     size=15)
card(s, 0.6, 3.95, 5.9, 1.75, "Step B: fix the phases, update w", [
    "Maximum ratio transmission along the combined channel:",
    ("w = √P (hᵣᴴΘG + h_dᴴ)ᴴ / || · ||", {"bold": True, "color": NAVY, "size": 17})],
     size=15, accent=NAVY)
text(s, 0.6, 5.9, 5.9, 0.9, [
    "Repeat A and B until the power stops decreasing (relative change below 10⁻⁴)."],
     size=15, bold=True, color=TEAL)
text(s, 6.9, 1.55, 5.8, 0.5, ["Why this is attractive"], size=20, bold=True, color=NAVY)
text(s, 6.9, 2.15, 5.8, 4.3, [
    ("Both steps are closed-form: no solver is needed.", {"bullet": True}),
    ("The power never increases from one step to the next, so the algorithm always converges.",
     {"bullet": True}),
    ("Cost grows linearly with N, against a high-order polynomial in N for the SDP.", {"bullet": True}),
    ("Physical meaning: coherent combining over the air. It is MRC performed by the environment.",
     {"bullet": True, "bold": True, "color": NAVY}),
    ("Two simple special cases used as benchmarks: point the AP beam at the user (AP-user MRT) or at "
     "the IRS (AP-IRS MRT).", {"bullet": True}),
], size=16, space=9)

# ============================ 9. N^2 law ===================================
s = new_slide("Key insight: the N-squared power law", M2,
              "This is the headline theory result. When the reflected link dominates, received power grows "
              "with N squared. One factor of N because the surface collects N times more energy, another "
              "factor of N because the N reflections add coherently in amplitude. Compare: massive MIMO "
              "with N antennas gives only a factor N.")
eq(s, 0.6, 1.6, 12.1, 1.3, [
    ("Received power with optimal phases  \u221d  N\u00b2      \u21d2      "
     "required transmit power  \u221d  1/N\u00b2", {"bold": True})], size=20)
card(s, 0.6, 3.2, 3.85, 3.0, "Factor N: aperture gain", [
    "N elements capture N times as much of the energy sent by the AP."], size=16)
card(s, 4.72, 3.2, 3.85, 3.0, "Factor N: beamforming gain", [
    "The N reflected waves are aligned in phase, so their amplitudes add."], size=16, accent=NAVY)
card(s, 8.84, 3.2, 3.85, 3.0, "What it means", [
    "Doubling N saves about 6 dB of transmit power.",
    "",
    "An N-antenna active array gives only a factor N (3 dB per doubling)."], size=16, accent=RED)
text(s, 0.6, 6.35, 12.1, 0.5, [
    "We test this law directly in our second experiment."], size=16, bold=True, color=TEAL)

# ============================ 10. Setup ====================================
s = new_slide("Our reproduction: simulation setup", M3,
              "We wrote the simulator from scratch in Python. NumPy for the channels and the closed-form "
              "algorithm, CVXPY with the SCS solver for the SDP. Each point is an average over many random "
              "channel realizations. Mention the geometry: the user moves along a line from the AP towards "
              "the IRS.")
rows = [("AP antennas, M", str(P["M"])),
        ("AP-IRS distance d₀, offset dᵥ", f"{P['d0']:.0f} m, {P['dv']:.0f} m"),
        ("Path loss at 1 m, C₀", f"{P['C0_dB']:.0f} dB"),
        ("Path-loss exponents (AP-IRS, IRS-user, AP-user)",
         f"{P['alpha_AI']}, {P['alpha_Iu']}, {P['alpha_AU']}"),
        ("Fading", "AP-IRS: LoS;  others: Rayleigh"),
        ("Noise power σ²", f"{P['noise_dBm']:.0f} dBm"),
        ("SNR target γ", f"{P['gamma_dB']:.0f} dB"),
        ("Channel realizations", f"{P['realisations_sdr']} (Exp. 1, 3)  /  {P['realisations']} (Exp. 2, 4)"),
        ("Gaussian randomizations", str(P["randomisations"]))]
tbl = s.shapes.add_table(len(rows) + 1, 2, Inches(0.6), Inches(1.55), Inches(6.9), Inches(4.9)).table
tbl.columns[0].width, tbl.columns[1].width = Inches(4.1), Inches(2.8)
for r, (a, b) in enumerate([("Parameter", "Value")] + rows):
    for c, val in enumerate((a, b)):
        cell = tbl.cell(r, c)
        cell.text = val
        para = cell.text_frame.paragraphs[0]
        para.runs[0].font.size = Pt(14)
        para.runs[0].font.name = FONT
        para.runs[0].font.bold = r == 0
        para.runs[0].font.color.rgb = WHITE if r == 0 else INK
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if r == 0 else (PALE if r % 2 else WHITE)
card(s, 7.9, 1.55, 4.8, 2.35, "Method", [
    ("Draw random channels (Monte Carlo)", {"bullet": True}),
    ("Run every scheme on the same channels", {"bullet": True}),
    ("Average the power, report in dBm", {"bullet": True})], size=15)
card(s, 7.9, 4.1, 4.8, 2.35, "Tools", [
    ("Python, NumPy, Matplotlib", {"bullet": True}),
    ("CVXPY + SCS solver for the SDP", {"bullet": True}),
    ("Fixed random seed, so results are repeatable", {"bullet": True})], size=15, accent=NAVY)

# ============================ 11. Result 1 =================================
s = new_slide("Result 1: transmit power against user position", M3,
              "Three regions. Near the AP the direct link is strong and the IRS hardly matters. Around the "
              "middle the user is far from both and power peaks. Near the IRS the power falls again: the "
              "IRS creates a signal hotspot. Without the IRS, power only keeps rising. Point out that the "
              "alternating optimization sits on top of the SDR lower bound, so it is effectively optimal "
              "here, and that each single-beam heuristic only works in one region.")
picture(s, "fig1_power_vs_distance.png", 0.5, 1.4, h=5.45)
text(s, 8.3, 1.5, 4.5, 5.3, [
    ("Near the AP: the direct link dominates; all schemes except AP-IRS MRT agree.", {"bullet": True}),
    (f"Mid-way (d ≈ {d[ipk]} m): worst case, {fmt(c1['Alternating optimization'][ipk])} dBm.",
     {"bullet": True}),
    (f"Near the IRS (d = 50 m): the IRS saves {fmt(save50)} dB against no IRS.",
     {"bullet": True, "bold": True, "color": TEAL}),
    (f"Joint design is within {max(gap_lb, 0.01):.2f} dB of the SDR lower bound everywhere.",
     {"bullet": True}),
    (f"AP-user MRT loses {fmt(gap_user_mrt)} dB near the IRS; AP-IRS MRT loses {fmt(gap_irs_mrt)} dB "
     "near the AP.", {"bullet": True}),
    (f"Random phases waste the IRS: {fmt(gap_rand)} dB worse at d = 50 m.", {"bullet": True}),
], size=15, space=9)

# ============================ 12. Result 2 =================================
s = new_slide("Result 2: transmit power against IRS size", M3,
              "This tests the N-squared law. For a user next to the IRS the curve is parallel to the dashed "
              "6-dB-per-doubling reference. For a user near the AP the IRS adds almost nothing because the "
              "direct link already dominates. The mid-way user is in between and approaches the law only "
              "as N grows.")
picture(s, "fig2_power_vs_N.png", 0.5, 1.4, h=5.45)
text(s, 8.3, 1.5, 4.5, 5.3, [
    (f"d = 50 m: N from 40 to 80 saves {fmt(drop_double)} dB, 80 to 160 saves {fmt(drop_double2)} dB.",
     {"bullet": True, "bold": True, "color": TEAL}),
    ("Theory predicts 6.0 dB per doubling: the N-squared law is confirmed.", {"bullet": True}),
    (f"d = 15 m: growing N from {N2[0]} to {N2[-1]} changes the power by only {fmt(drop15)} dB.",
     {"bullet": True}),
    ("d = 41 m: the slope steepens as N grows, when the reflected link starts to dominate.",
     {"bullet": True}),
    ("Lesson: an IRS helps most for users that are close to it and far from the AP.", {"bullet": True}),
], size=15, space=9)

# ============================ 13. Results 3 and 4 ==========================
kL, kR, kY = "LoS (K = inf)", "Rician (K = 10 dB)", "Rayleigh (K = 0)"
s = new_slide("Results 3 and 4: convergence and phase resolution", M3,
              "Left: the alternating optimization converges in very few iterations. With a pure line-of-"
              "sight AP-IRS link it is already optimal after one iteration, which we can also prove: the "
              "channel G is rank one, so the phases only enter through one complex number. Right is our "
              "own extension beyond the paper: real IRS elements have only a few phase levels. Two bits "
              "already come close to the ideal.")
picture(s, "fig3_convergence.png", 0.45, 1.4, w=6.1)
picture(s, "fig4_discrete_phase.png", 6.75, 1.4, w=6.1)
text(s, 0.6, 5.75, 5.9, 1.2, [
    (f"LoS link: optimal after 1 iteration. Rayleigh link: within {max(gapK[kY], 0.01):.2f} dB of the "
     "bound after 6.", {"bullet": True}),
    ("Convergence is always monotonic.", {"bullet": True})], size=14, space=4)
text(s, 6.9, 5.75, 5.9, 1.2, [
    (f"Extension: loss against ideal phases is {fmt(loss[1])} dB (1 bit), {fmt(loss[2])} dB (2 bits), "
     f"{fmt(loss[3])} dB (3 bits).", {"bullet": True}),
    ("The N-squared slope is kept even with 1-bit elements.", {"bullet": True})], size=14, space=4)

# ============================ 14. Vs paper =================================
# Paper values extracted from the vector data of its Fig. 3 and Fig. 4(a), d = 50 m
PAPER = {"noirs": 19.19, 20: 4.49, 30: 1.49, 60: -4.06}
s = new_slide("Our results against the paper", M3,
              "All parameters stated in the paper are used unchanged. The paper's values come from the "
              "vector data of its figures, so they are exact, not eyeballed. Trends and the N-squared "
              "scaling match exactly; absolute levels differ, in two separate parts. Direct link: the "
              "paper's no-IRS curve is gamma sigma^2 / L(d) minus 0.29 dB at every distance, with no "
              "fading average, roughly one antenna. Ours averages over 4-antenna Rayleigh fading, which "
              "gives gamma sigma^2 / (3L): that is the 4.4 dB. Reflected link: a further 2.6 to 2.9 dB "
              "we could not trace, constant in N. If asked: the paper's Fig. 3 uses N = 20, inferred "
              "because it matches Fig. 4(a) at N = 20.")
rows = [("d = 50 m", "Paper", "Ours", "Diff."),
        ("Without IRS", f"{PAPER['noirs']:.2f}", fmt(c1['Without IRS'][i50]),
         fmt(PAPER['noirs'] - c1['Without IRS'][i50])),
        ("Joint design, N = 20", f"{PAPER[20]:.2f}", fmt(ao50[N2.index(20)]), fmt(PAPER[20] - ao50[N2.index(20)])),
        ("Joint design, N = 30", f"{PAPER[30]:.2f}", fmt(ao50[N2.index(30)]), fmt(PAPER[30] - ao50[N2.index(30)])),
        ("Joint design, N = 60", f"{PAPER[60]:.2f}", fmt(ao50[N2.index(60)]), fmt(PAPER[60] - ao50[N2.index(60)])),
        ("Saving, N 30\u219260 (dB)", fmt(PAPER[30] - PAPER[60]), fmt(ao50[N2.index(30)] - ao50[N2.index(60)]), "")]
tbl = s.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.55), Inches(7.1), Inches(2.4)).table
for col, w in enumerate((3.5, 1.2, 1.2, 1.2)):
    tbl.columns[col].width = Inches(w)
for r, row in enumerate(rows):
    for col, val in enumerate(row):
        cell = tbl.cell(r, col)
        cell.text = val
        para = cell.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.LEFT if col == 0 else PP_ALIGN.RIGHT
        run = para.runs[0] if para.runs else para.add_run()
        run.font.size, run.font.name = Pt(14), FONT
        run.font.bold = r == 0 or r == len(rows) - 1
        run.font.color.rgb = WHITE if r == 0 else (TEAL if r == len(rows) - 1 else INK)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if r == 0 else (PALE if r % 2 else WHITE)
text(s, 0.6, 4.0, 7.1, 0.35, ["Paper values: exact data extracted from its vector figures (dBm)."],
     size=11, color=GREY)
card(s, 8.0, 1.55, 4.7, 2.75, "What matches", [
    ("Three-region shape against distance", {"bullet": True}),
    ("Joint design on the SDR bound", {"bullet": True}),
    ("Where each MRT scheme fails", {"bullet": True}),
    ("N\u00b2 scaling: same saving per doubling", {"bullet": True, "bold": True, "color": TEAL}),
], size=14)
card(s, 0.6, 4.5, 12.1, 2.3, "Why the absolute levels differ", [
    ("Direct link: the paper's no-IRS curve = \u03b3\u03c3\u00b2/L(d) \u2212 0.29 dB at all 7 distances "
     "(no fading average, about one antenna). Ours averages 4-antenna Rayleigh fading: \u03b3\u03c3\u00b2/(3L). "
     "This explains the 4.4 dB.", {"bullet": True}),
    ("Reflected link: a further 2.6\u20132.9 dB, constant in N, not traceable to the paper's text; "
     "the N\u00b2 comparison is unaffected.", {"bullet": True}),
    ("The paper's Fig. 3 uses N = 20 (it matches Fig. 4(a) at N = 20); our Experiment 1 uses N = 40.",
     {"bullet": True}),
], size=14, accent=RED)

# ============================ 15. Challenges ===============================
s = new_slide("Challenges and how we handled them", M3,
              "Three honest difficulties and what we did about each.")
ch = [("Understanding the mathematics",
       "SDR, lifting and rank relaxation were new to us.",
       "Compared the SDR solution with the closed-form algorithm on the same channels: they agree."),
      ("Slow SDP solves",
       "The first solver took about 10 s per channel for N = 40; thousands of solves were needed.",
       "Switched to a first-order solver (SCS), ran user positions in parallel, and used the closed-form "
       "algorithm wherever the SDP was not needed."),
      ("Checking our own code",
       "A wrong sign or conjugate still gives a plausible-looking curve.",
       "Checks against the SDR bound, the no-IRS closed form and the 6 dB law. The bound check exposed a sampling mismatch (up to 0.3 dB).")]
for i, (t, prob, fix) in enumerate(ch):
    y = 1.6 + i * 1.75
    rect(s, 0.6, y, 12.1, 1.55, PALE)
    rect(s, 0.6, y, 0.07, 1.55, [TEAL, NAVY, RED][i])
    text(s, 0.85, y + 0.1, 3.4, 1.3, [t], size=18, bold=True, color=NAVY)
    text(s, 4.2, y + 0.1, 3.9, 1.4, [("Difficulty", {"bold": True, "color": RED, "size": 13}), prob],
         size=14, space=2)
    text(s, 8.3, y + 0.1, 4.3, 1.4, [("What we did", {"bold": True, "color": TEAL, "size": 13}), fix],
         size=14, space=2)

# ============================ 16. Conclusion ===============================
s = new_slide("Conclusion, limitations and future directions", M3,
              "Summarize in three sentences, then the limitations of the paper's model, then where the "
              "field went next. End and invite questions.")
card(s, 0.6, 1.6, 4.0, 3.9, "Key findings", [
    ("Joint active and passive beamforming cuts transmit power sharply for users near the IRS "
     f"({fmt(save50)} dB at d = 50 m, N = {e1['N']}).", {"bullet": True}),
    ("A closed-form alternating algorithm reaches the SDR bound.", {"bullet": True}),
    ("Near the IRS, power falls as 1/N²: about 6 dB per doubling of the surface.", {"bullet": True}),
], size=15)
card(s, 4.67, 1.6, 4.0, 3.9, "Limitations", [
    ("Perfect channel knowledge is assumed; a passive IRS cannot estimate channels itself.",
     {"bullet": True}),
    ("Ideal, continuous, lossless phase shifters.", {"bullet": True}),
    ("Far-field, narrowband, single-cell model.", {"bullet": True}),
    ("The N² law needs the reflected link to dominate.", {"bullet": True}),
], size=15, accent=RED)
card(s, 8.74, 1.6, 4.0, 3.9, "Future directions", [
    ("Channel estimation with low pilot overhead", {"bullet": True}),
    ("Discrete phases and hardware impairments", {"bullet": True}),
    ("Multiuser, multi-IRS and wideband (OFDM) systems", {"bullet": True}),
    ("Active and STAR-RIS, near-field operation", {"bullet": True}),
    ("Learning-based phase control", {"bullet": True}),
], size=15, accent=NAVY)

# ============================ 17. References ===============================
s = new_slide("References", "All",
              "Thank the audience and take questions.")
text(s, 0.6, 1.5, 12.1, 4.2, [
    "[1] Q. Wu and R. Zhang, “Intelligent reflecting surface enhanced wireless network via joint active "
    "and passive beamforming,” IEEE Trans. Wireless Commun., vol. 18, no. 11, pp. 5394–5409, Nov. 2019.",
    "[2] Q. Wu and R. Zhang, “Towards smart and reconfigurable environment: Intelligent reflecting surface "
    "aided wireless network,” IEEE Commun. Mag., vol. 58, no. 1, pp. 106–112, Jan. 2020.",
    "[3] Q. Wu and R. Zhang, “Beamforming optimization for wireless network aided by intelligent reflecting "
    "surface with discrete phase shifts,” IEEE Trans. Commun., vol. 68, no. 3, pp. 1838–1851, Mar. 2020.",
    "[4] Z.-Q. Luo, W.-K. Ma, A. M.-C. So, Y. Ye, and S. Zhang, “Semidefinite relaxation of quadratic "
    "optimization problems,” IEEE Signal Process. Mag., vol. 27, no. 3, pp. 20–34, May 2010.",
    "[5] A. Goldsmith, Wireless Communications. Cambridge University Press, 2005.",
    "[6] D. Tse and P. Viswanath, Fundamentals of Wireless Communication. Cambridge University Press, 2005.",
], size=14, space=10)
text(s, 0.6, 5.9, 12.1, 0.8, ["Thank you. Questions?"], size=30, bold=True, color=TEAL,
     align=PP_ALIGN.CENTER)

out = os.path.join(HERE, "WCom_Project_Presentation.pptx")
prs.save(out)
print("saved", out, "slides:", len(prs.slides))
