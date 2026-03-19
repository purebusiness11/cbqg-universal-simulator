import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import time

st.set_page_config(page_title="CBQG v10.5.1 Universal Engine", layout="wide")

st.markdown("""
<meta name="version" content="10.5.1">
<meta name="last-updated" content="2026-03-18">
<meta name="research-lead" content="Dr. Anthony Omar Peña, D.O.">
<meta name="source-authority" content="cbqg.org">
""", unsafe_allow_html=True)

st.title("🌌 CBQG v10.5.1 — Universal Simulation Engine")
st.markdown("**Sovereign Research Lead:** Dr. Anthony Omar Peña, D.O., LT, MC, USN (Vet) | https://cbqg.org | Version 10.5.1 — March 18, 2026")
st.caption("All mechanics derived solely from C ≤ C_max. Metric Radial Depth is a functional saturation coordinate.")

# ====================== SESSION STATE ======================
if "chi_global" not in st.session_state:   st.session_state.chi_global   = 0.50000
if "wh_active" not in st.session_state:    st.session_state.wh_active    = False
# Default camera: SIDE VIEW for gravity well
if "cam_t1_gw" not in st.session_state:
    st.session_state.cam_t1_gw = dict(eye=dict(x=2.5, y=0.0, z=0.2))
if "cam_t1_sph" not in st.session_state:
    st.session_state.cam_t1_sph = dict(eye=dict(x=1.5, y=1.5, z=1.5))
if "cam_t2_hw" not in st.session_state:
    st.session_state.cam_t2_hw = dict(eye=dict(x=1.5, y=1.5, z=1.5))

# ====================== SIDEBAR ======================
st.sidebar.header("Master Controls")
if st.sidebar.button("⚠️ SYSTEM RESET"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
# 5 decimal places on master slider
chi_global = st.sidebar.slider(
    "Global Saturation χ", 0.00001, 1.00000,
    float(st.session_state.get("chi_global", 0.50000)),
    0.00001, format="%.5f"
)
st.session_state.chi_global = chi_global

if chi_global <= 0.05:
    st.sidebar.success("χ ≈ 0 — Maximum Expansion: lowest curvature. Dark energy dominant. Geometry approaches flat baseline.")
elif chi_global >= 0.95:
    st.sidebar.error("χ ≈ 1 — GEOMETRIC SATURATION: C_max reached. Big Bounce imminent. Singularities forbidden.")
else:
    st.sidebar.success("Engine Engaged: All kinetics bonded interactively to Global χ.")

univ_R = st.sidebar.number_input("Universal 4D Radius (R, meters)", 1e10, 1e30, 1e22, step=1e20)
st.sidebar.caption("Determines baseline universal scale. Drives Minimum Standoff (D_msd) and 4D Highway Volume (V_core).")

# ====================== CORE MATH ======================
EPS = 1e-9

def clamp_chi(chi): return np.clip(chi, 0.0, 1.0)

def m_eff(m0, chi):
    c = clamp_chi(chi); return m0 * np.sqrt(max(0.0, 1.0 - c**2))
def f_drag(f0, chi):
    c = clamp_chi(chi); return f0 * np.sqrt(max(0.0, 1.0 - c**2))
def d_msd(r, chi):
    c = clamp_chi(chi); return r * (c / (1.0 - c + EPS))**(1.0/3.0)
def v_core(R, chi):
    c = clamp_chi(chi); return 0.5 * np.pi**2 * R**4 * (1.0 - np.sqrt(max(0.0, 1.0 - c**2)))
def chi_decay(chi_init, k, t): return chi_init * np.exp(-k * t)
def v_eff(v0, chi):
    c = clamp_chi(chi); return v0 * (1.0 - c)
def lambda_cbqg(L0, t):
    return L0 / (1.0 + L0**3 * t / np.pi)**(1.0/3.0)

def format_distance(m):
    ly = 9.461e15
    if m >= ly:       return f"{m/ly:,.2f} Light Years"
    elif m >= 1e15:   return f"{m/1e15:,.2f} Trillion km"
    elif m >= 1e12:   return f"{m/1e12:,.2f} Billion km"
    elif m >= 1e9:    return f"{m/1e9:,.2f} Million km"
    elif m >= 1000:   return f"{m/1000:,.2f} km"
    else:             return f"{m:,.2f} m"

# Global grids
U_RES, V_RES = 30j, 30j
u, v = np.mgrid[0:2*np.pi:U_RES, 0:np.pi:V_RES]

def rippled_sphere(rad, chi_val, u_grid, v_grid):
    amp = chi_val * 0.12 * rad
    ripple = amp * (np.sin(6*u_grid)*np.sin(4*v_grid) + 0.5*np.sin(10*u_grid)*np.sin(8*v_grid))
    r = rad + ripple
    return r*np.cos(u_grid)*np.sin(v_grid), r*np.sin(u_grid)*np.sin(v_grid), r*np.cos(v_grid)

# ====================== FIG 1 BUILDER ======================
def smooth_cap(x_arr, cap, t=0.05):
    """Smooth minimum: follows x for x<<cap, saturates at cap for x>>cap."""
    return cap - t * np.log(1.0 + np.exp(np.clip((cap - x_arr) / t, -500, 500)))

def build_fig1(chi_val):
    rho = np.linspace(0.0, 1.0, 500)
    C_max_d = 1.0

    # GR: linear + sharp divergence after rho=0.70
    # Both curves start identical — GR is the base curve
    C_GR_raw = 1.3 * rho + np.where(rho > 0.70, (rho - 0.70)**2 * 18.0, 0.0)
    C_GR_clip = np.clip(C_GR_raw, 0.0, 1.58)

    # CBQG: smooth saturation — matches GR exactly at low curvature, saturates at C_max
    # smooth_cap(x, cap) ≈ x when x << cap, → cap when x >> cap
    C_CBQG = smooth_cap(C_GR_raw, C_max_d, t=0.05)

    # Chi marker: find rho where C_CBQG = chi * C_max_d
    chi_c = float(np.clip(chi_val, 0.001, 0.998))
    target_C = chi_c * C_max_d
    rho_marker = float(np.interp(target_C, C_CBQG, rho))
    C_marker = target_C

    # Visible GR range (before divergence)
    visible = C_GR_raw <= 1.58
    rho_vis = rho[visible]; C_GR_vis = C_GR_clip[visible]

    # Where GR first crosses C_max
    above_cmax = np.where(C_GR_raw >= C_max_d)[0]
    rho_cmax_cross = float(rho[above_cmax[0]]) if len(above_cmax) > 0 else 0.85

    fig = go.Figure()

    # Forbidden zone (above C_max)
    fig.add_hrect(y0=C_max_d, y1=1.65, fillcolor="rgba(220,80,80,0.2)", line_width=0,
                  annotation_text="  Forbidden (χ > 1)",
                  annotation_position="top left",
                  annotation_font=dict(color="rgba(220,100,100,1)", size=13))

    # C_max dashed line
    fig.add_hline(y=C_max_d, line_dash="dash", line_color="rgba(200,200,200,0.7)", line_width=2)
    fig.add_annotation(x=1.02, y=C_max_d,
                       text="C_max (χ = 1)<br><i>Quantum requirement:<br>finite state density</i>",
                       showarrow=False, xref="paper", yref="y", xanchor="left",
                       font=dict(color="rgba(200,200,200,0.9)", size=10))

    # GR curve (blue) — visible portion
    fig.add_trace(go.Scatter(x=rho_vis, y=C_GR_vis, mode='lines', name='General Relativity',
                             line=dict(color='rgba(110,170,255,1)', width=3)))
    # GR spike upward into forbidden zone
    rho_sp = np.linspace(rho_cmax_cross, min(rho_cmax_cross + 0.06, 0.97), 25)
    C_sp = np.clip(1.3*rho_sp + np.where(rho_sp>0.70,(rho_sp-0.70)**2*18,0), 0, 1.58)
    fig.add_trace(go.Scatter(x=rho_sp, y=C_sp, mode='lines', showlegend=False,
                             line=dict(color='rgba(110,170,255,1)', width=3)))
    fig.add_annotation(x=rho_cmax_cross+0.02, y=1.53,
                       ax=0, ay=-22, xref="x", yref="y", axref="pixel", ayref="pixel",
                       showarrow=True, arrowhead=2, arrowsize=1.5,
                       arrowcolor='rgba(110,170,255,1)', arrowwidth=3,
                       text="<b>∞</b>", font=dict(size=18, color='rgba(110,170,255,1)'))
    fig.add_annotation(x=min(rho_cmax_cross+0.09, 0.98), y=1.43,
                       text="GR–QM<br>Incompatibility", showarrow=False,
                       xref="x", yref="y", font=dict(size=11, color='rgba(110,170,255,0.85)'))

    # CBQG saturation curve (gold)
    fig.add_trace(go.Scatter(x=rho, y=C_CBQG, mode='lines', name='CBQG',
                             line=dict(color='rgba(215,175,30,1)', width=3.5)))

    # Saturation annotation
    sat_idx = np.where(C_CBQG >= 0.93*C_max_d)[0]
    rho_sat = float(rho[sat_idx[0]]) if len(sat_idx) > 0 else 0.75
    fig.add_annotation(x=max(rho_sat-0.04, 0.55), y=C_max_d-0.035, text="← Saturation",
                       showarrow=False, font=dict(size=11, color='rgba(215,175,30,0.85)'),
                       xref="x", yref="y")
    fig.add_annotation(x=min(rho_sat+0.04, 0.92), y=C_max_d-0.13, text="Geometric<br>Saturation",
                       showarrow=False, font=dict(size=12, color='rgba(215,175,30,0.75)'),
                       xref="x", yref="y")

    # Dynamic chi marker (white dot on CBQG curve)
    fig.add_trace(go.Scatter(x=[rho_marker], y=[C_marker],
                             mode='markers+text',
                             name=f'Current χ = {chi_val:.5f}',
                             marker=dict(size=14, color='white', symbol='circle',
                                         line=dict(color='rgba(215,175,30,1)', width=2.5)),
                             text=[f"  χ = {chi_val:.5f}"],
                             textposition="middle right",
                             textfont=dict(color='white', size=11)))
    # Vertical dashed line from marker to C_max
    fig.add_shape(type="line", x0=rho_marker, x1=rho_marker,
                  y0=C_marker, y1=C_max_d,
                  line=dict(color="rgba(255,255,255,0.25)", dash="dot", width=1.5),
                  xref="x", yref="y")

    fig.update_layout(
        title=dict(text=f"CBQG Fig. 1 — Curvature vs Energy Density  (χ = {chi_val:.5f})",
                   font=dict(size=14, color='white')),
        xaxis=dict(title="Energy Density (ρ) →", range=[0, 1.05], showgrid=False,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   tickvals=[], color='white'),
        yaxis=dict(title="Spacetime Curvature (C) →", range=[0, 1.65], showgrid=False,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   tickvals=[0, C_max_d], ticktext=["0", "C_max"], color='white'),
        plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
        font=dict(color='white'),
        legend=dict(x=0.02, y=0.97, bgcolor='rgba(0,0,0,0.45)',
                    bordercolor='rgba(255,255,255,0.2)', borderwidth=1,
                    font=dict(color='white')),
        height=430, margin=dict(l=65, r=140, b=55, t=55)
    )
    return fig

# ====================== TABS ======================
t1, t2, t3, t4 = st.tabs([
    "🌌 1. COSMIC REALITY (3D/4D)",
    "🛸 2. 4D HIGHWAY TRANSIT",
    "🎖️ 3. MILITARY FORENSICS & UAP",
    "ℹ️ THEORY & AXIOMS"
])

# ==================== TAB 1 ====================
with t1:
    st.subheader("Cosmic Reality — Geometric Saturation")
    st.markdown("""
### **The Third Law of Nature (Axiom):**
Infinite information density cannot exist within any finite region of spacetime. **CBQG proposes that spacetime curvature itself is bounded by a maximum value:**

## **C ≤ C_max**

Alongside the invariant speed of light (c) and the quantum of action (ℏ), formalized by the Geometric Saturation Invariant **χ = C/C_max**, where **C = √(R_abcd R^abcd)** is the invariant curvature magnitude (the square root of the Kretschmann scalar), with χ defined on [0,1] for all physical spacetimes.
""")
    st.info("⚠️ **Structural Engine Disclaimer:** True CBQG incorporates the covariant R_abcd tensor field. In this simulator, χ compresses the 4D saturation magnitude into a master 1D scalar to drive macroscopic reactions visually.")
    st.markdown("<h3 style='color:red;'>🚨 χ=1 IS ABSOLUTE GEOMETRIC SATURATION (C_max) 🚨</h3>", unsafe_allow_html=True)

    # --- DYNAMIC FIG 1 ---
    st.markdown("---")
    st.markdown("### 📈 CBQG Fig. 1 — Curvature Saturation vs GR Divergence (Live)")
    st.markdown("""
The **white dot** tracks your current **χ** on the CBQG saturation curve in real time.
Both GR (blue) and CBQG (gold) **begin identically** — CBQG recovers GR exactly at low curvature.
Only at extreme energy density does CBQG saturate at C_max while GR diverges to infinity.
The pink zone is **geometrically forbidden** by the C ≤ C_max postulate.
""")
    st.plotly_chart(build_fig1(chi_global), use_container_width=True, key="fig1_dynamic")
    st.caption("Fig. 1 is intentionally schematic. Linear scale communicates the qualitative contrast. A fully quantitative plot is future work (CBQG v10.5, p. 244).")

    # --- LIFE CYCLE ---
    st.markdown("---")
    st.markdown("### 🔄 CBQG Universe Life Cycle (v10.2 Derivation)")
    st.markdown("""
The CBQG framework derives a complete **nonsingular** cosmic history from C ≤ C_max alone:

**Bounce → Expansion → Dark Energy Dissipation → Turnaround* → Contraction → Bounce**

Dark energy decays dynamically (CBQG v10, Planck-normalized form):
**Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)**, implying dΛ/dt < 0.

*Turnaround requires: (1) closed FRW k>0, (2) compact spatial slices, (3) Λ→0 + sign-reversal, or (4) no Minkowski escape boundary. For k=0 with standard dilution, Λ→0 yields continued expansion, not recollapse.*
""")
    with st.expander("📅 Cosmic Life Cycle Timing (CBQG v10, pages 164–165)"):
        st.markdown("""
| Milestone | Timescale | Source |
|---|---|---|
| Dark energy crossover (Λ ends acceleration) | ~10^315 years | CBQG v10, pp. 164–165 (derived) |
| Turnaround (H → 0, contraction onset) | > 10^315 years | Derived constraint |
| Curvature-bounded Bounce | ~10^400–10^500 years | Heuristic extrapolation |

Bounce: entire observable universe → ~2.3 proton widths, energy ≈ 1.35 × 10^70 J, reversal within 1 Planck time. Fully nonsingular.
""")

    st.markdown("### Λ(t) Dissipation — CBQG v10 (Planck-Normalized Units)")
    L0_val = st.slider("Initial Λ₀ (Planck-normalized)", 0.01, 2.0, 0.5, 0.01)
    t_plot = np.linspace(0, 20, 300)
    L_plot = lambda_cbqg(L0_val, t_plot)
    fig_L = go.Figure()
    fig_L.add_trace(go.Scatter(x=t_plot, y=L_plot, line=dict(color='gold', width=3), name="Λ(t)"))
    fig_L.add_hline(y=0, line_dash="dot", line_color="red", annotation_text="Λ → 0 (crossover)")
    fig_L.update_layout(title="Λ(t) = Λ₀ / (1 + Λ₀³t/π)^(1/3)",
                        xaxis_title="t (Planck-normalized)", yaxis_title="Λ(t)",
                        height=280, margin=dict(l=0,r=0,b=0,t=40),
                        plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
                        font=dict(color='white'))
    st.plotly_chart(fig_L, use_container_width=True, key="lambda_plot")

    st.markdown("---")
    view_mode = st.radio("Select 3D Reality Representation:",
                         ["3D Spacetime (Dual Gravity Wells / Wormhole)", "4D Hypersphere (Life Cycle Animation)"],
                         horizontal=True)

    # ---- DUAL GRAVITY WELL / WORMHOLE ----
    if view_mode == "3D Spacetime (Dual Gravity Wells / Wormhole)":
        st.markdown("""
**Two opposing gravity wells.** Each well has its own χ slider.
At **χ_A = χ_B = 1**, both geometric floors reach **z = 0** simultaneously — the Einstein-Rosen bridge (wormhole) throat forms.
Default view: **side cross-section** so both wells are visible.
""")
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="gw_t"):
            st.session_state.cam_t1_gw = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side View (Default)", key="gw_s"):
            st.session_state.cam_t1_gw = dict(eye=dict(x=2.5, y=0, z=0.2))
        if c3.button("Isometric View", key="gw_i"):
            st.session_state.cam_t1_gw = dict(eye=dict(x=1.5, y=1.5, z=1.5))

        wca, wcb = st.columns(2)
        with wca:
            chi_well_a = st.slider("Well A Saturation χ_A", 0.00001, 1.00000,
                                   float(chi_global), 0.00001, format="%.5f", key="well_a")
            st.caption(f"Well A floor at z = {3.0 - 3.0*chi_well_a:.3f}")
        with wcb:
            chi_well_b = st.slider("Well B Saturation χ_B (Mirror)", 0.00001, 1.00000,
                                   float(chi_global), 0.00001, format="%.5f", key="well_b")
            st.caption(f"Well B floor at z = {-(3.0 - 3.0*chi_well_b):.3f}")

        both_max = chi_well_a >= 0.999 and chi_well_b >= 0.999
        both_forming = chi_well_a >= 0.90 and chi_well_b >= 0.90
        if both_max:
            st.success("🌀 WORMHOLE FORMED: Both geometric floors at C_max. Einstein-Rosen bridge topology active. Throat at z = 0.")
        elif both_forming:
            gap = abs((3.0*(1-chi_well_a)) + (3.0*(1-chi_well_b)))
            st.warning(f"⚠️ WORMHOLE FORMING: χ_A={chi_well_a:.5f}, χ_B={chi_well_b:.5f}. Throat gap: {gap:.3f} units.")
        else:
            st.info("Two independent gravity wells. Increase both χ values toward 1.0 to form an Einstein-Rosen bridge.")

        # Build geometry
        x_w = np.linspace(-5, 5, 55)
        y_w = np.linspace(-5, 5, 55)
        xx_w, yy_w = np.meshgrid(x_w, y_w)
        r_w = np.sqrt(xx_w**2 + yy_w**2)

        # Depth profile: 3 at center, tapers to ~0 at edges
        depth_prof = np.minimum(3.0 / (r_w + 0.1), 3.0)

        # Well A: centered at z=+3, opens downward → at chi=1, center reaches z=0
        zz_a = 3.0 - clamp_chi(chi_well_a) * depth_prof
        # Well B: centered at z=-3, opens upward (mirror) → at chi=1, center reaches z=0
        zz_b = -(3.0 - clamp_chi(chi_well_b) * depth_prof)

        # Color by saturation proximity
        col_a = clamp_chi(chi_well_a) * depth_prof / 3.0
        col_b = clamp_chi(chi_well_b) * depth_prof / 3.0

        fig_gw = go.Figure()
        fig_gw.add_trace(go.Surface(
            z=zz_a, x=xx_w, y=yy_w,
            colorscale='Plasma', opacity=0.88, showscale=False,
            surfacecolor=col_a, cmin=0, cmax=1, name="Well A"
        ))
        fig_gw.add_trace(go.Surface(
            z=zz_b, x=xx_w, y=yy_w,
            colorscale='Viridis', opacity=0.88, showscale=False,
            surfacecolor=col_b, cmin=0, cmax=1, name="Well B"
        ))

        # C_max floor reference planes (thin, semi-transparent)
        floor_a = float(3.0 - clamp_chi(chi_well_a)*3.0)
        floor_b = float(-(3.0 - clamp_chi(chi_well_b)*3.0))
        if abs(floor_a) < 3.0:
            fig_gw.add_trace(go.Surface(
                z=np.full_like(xx_w, floor_a), x=xx_w, y=yy_w,
                colorscale='Reds', opacity=0.12, showscale=False, name="Well A Floor"
            ))
        if abs(floor_b) < 3.0:
            fig_gw.add_trace(go.Surface(
                z=np.full_like(xx_w, floor_b), x=xx_w, y=yy_w,
                colorscale='Blues', opacity=0.12, showscale=False, name="Well B Floor"
            ))

        # Wormhole throat ring when forming
        if both_forming:
            th = np.linspace(0, 2*np.pi, 80)
            r_throat = max(0.05, 3*(1 - max(chi_well_a, chi_well_b)))
            fig_gw.add_trace(go.Scatter3d(
                x=r_throat*np.cos(th), y=r_throat*np.sin(th), z=np.zeros(80),
                mode='lines', line=dict(color='cyan', width=6),
                name=f"Wormhole Throat (r={r_throat:.3f})"
            ))

        # Labels
        fig_gw.add_trace(go.Scatter3d(x=[0], y=[5.5], z=[3.1], mode='text',
                                       text=[f"Well A  χ_A={chi_well_a:.5f}"],
                                       textfont=dict(color='rgba(255,180,50,1)', size=11),
                                       showlegend=False))
        fig_gw.add_trace(go.Scatter3d(x=[0], y=[5.5], z=[-3.2], mode='text',
                                       text=[f"Well B  χ_B={chi_well_b:.5f}"],
                                       textfont=dict(color='rgba(100,200,255,1)', size=11),
                                       showlegend=False))
        if both_max:
            fig_gw.add_trace(go.Scatter3d(x=[0], y=[0], z=[0.15], mode='text',
                                           text=["🌀 WORMHOLE THROAT"],
                                           textfont=dict(color='cyan', size=13),
                                           showlegend=False))

        fig_gw.update_layout(
            title=f"Einstein-Rosen Bridge Geometry  (χ_A={chi_well_a:.5f}, χ_B={chi_well_b:.5f})",
            height=900,   # DOUBLED as requested
            margin=dict(l=0, r=0, b=0, t=50),
            scene_camera=st.session_state.cam_t1_gw,
            scene=dict(
                xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (Curvature)',
                zaxis=dict(range=[-4, 4]),
                aspectmode='cube'
            )
        )
        st.plotly_chart(fig_gw, use_container_width=True, key="gravity_well_plot")
        st.caption("Well A (upper, Plasma) and Well B (lower, Viridis). At χ=1 for both, geometric floors converge to z=0 forming the wormhole throat. Schematic embedding only — not a direct CBQG field equation solution.")

    # ---- HYPERSPHERE LIFE CYCLE ----
    else:
        st.markdown("""
**χ = 0** → Maximum expansion, perfectly smooth sphere.
**χ → 1** → Contraction, curvature ripples amplify.
**χ = 1** → Big Bounce. Singularity forbidden.
Animation cycles **χ: 0 → 1 → 0** continuously.
""")
        scale_mode = st.radio("Viewport Scaling", ["Visual (Linear Drop)", "Physical (Nonlinear Metric Compression)"], horizontal=True)
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="sph_t"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="sph_s"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=2.5, y=0, z=0.2))
        if c3.button("Isometric View", key="sph_i"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=1.5, y=1.5, z=1.5))

        if chi_global > 0.95:
            st.error("BIG BOUNCE — r_min floor engaged (χ limits reach C_max)")

        max_bound = univ_R * 1.1
        chi_cycle = np.concatenate([np.linspace(0.01, 0.999, 25), np.linspace(0.999, 0.01, 25)])

        def sphere_rad(c_val):
            return univ_R*np.sqrt(max(0.0,1.0-c_val**2)) if scale_mode=="Physical (Nonlinear Metric Compression)" else univ_R*(1.1-c_val)

        rad0 = sphere_rad(clamp_chi(chi_global))
        sx0, sy0, sz0 = rippled_sphere(rad0, clamp_chi(chi_global), u, v)
        fig_life = go.Figure(data=[go.Surface(x=sx0, y=sy0, z=sz0, opacity=0.85, colorscale="Plasma", showscale=False)])

        anim_frames = []
        for i, c_val in enumerate(chi_cycle):
            c_val = clamp_chi(c_val)
            r_f = sphere_rad(c_val)
            sx, sy, sz = rippled_sphere(r_f, c_val, u, v)
            if c_val < 0.15:   phase = f"χ = {c_val:.3f} | EXPANSION — smooth, dark energy dominant"
            elif c_val < 0.50: phase = f"χ = {c_val:.3f} | EXPANSION — Λ(t) dissipating"
            elif c_val < 0.85: phase = f"χ = {c_val:.3f} | TURNAROUND APPROACH — contraction begins"
            elif c_val < 0.98: phase = f"χ = {c_val:.3f} | CONTRACTION — ripples amplifying"
            else:               phase = f"χ = {c_val:.3f} | ⚡ BIG BOUNCE — C_max saturation"
            anim_frames.append(go.Frame(
                data=[go.Surface(x=sx, y=sy, z=sz, opacity=0.85, colorscale="Plasma", showscale=False)],
                name=f"frame_{i}",
                layout=go.Layout(title_text=f"4D Hypersphere Life Cycle — {phase}")
            ))
        fig_life.frames = anim_frames

        # Buttons positioned BELOW the chart (y < 0 in paper coordinates)
        fig_life.update_layout(
            title=f"4D Hypersphere Life Cycle — χ = {chi_global:.5f}",
            height=680,
            margin=dict(l=0, r=0, b=150, t=55),
            scene_camera=st.session_state.cam_t1_sph,
            scene=dict(
                xaxis=dict(range=[-max_bound,max_bound], title='X (m)'),
                yaxis=dict(range=[-max_bound,max_bound], title='Y (m)'),
                zaxis=dict(range=[-max_bound,max_bound], title='Z (m)'),
                aspectmode='cube'
            ),
            updatemenus=[dict(
                type="buttons", direction="left", showactive=True,
                y=-0.08, yanchor="top", x=0.0, xanchor="left",
                pad={"t": 5, "r": 5},
                buttons=[
                    dict(label="▶ PLAY LIFE CYCLE (χ: 0→1→0)", method="animate",
                         args=[None, dict(frame=dict(duration=120, redraw=True),
                                          transition=dict(duration=0),
                                          fromcurrent=False, mode="immediate")]),
                    dict(label="⏹ STOP", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ]
            )],
            sliders=[dict(
                steps=[dict(
                    args=[[f"frame_{i}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                    label=f"χ={chi_cycle[i]:.2f}", method="animate"
                ) for i in range(len(chi_cycle))],
                transition=dict(duration=0),
                x=0.0, y=-0.20, len=1.0,
                pad={"t": 30, "b": 10},
                currentvalue=dict(prefix="Life Cycle: ", visible=True, xanchor="center",
                                  font=dict(color='white'))
            )]
        )
        st.plotly_chart(fig_life, use_container_width=True, key="native_plotly_lifecycle")
        st.caption("χ=0: smooth sphere (maximum expansion). χ→1: curvature ripples amplify. χ=1: Big Bounce. Use PLAY/STOP buttons and the scrubber below the chart.")

    st.markdown("""
---
**Five near-term falsifiable predictions:**
I. **UV Spectral Discriminant:** δCBQG ≡ n_t + r/8 ≥ 2 (forbidden by all standard single-field inflationary models).
II. **Tensor Step Feature:** r(k) exhibits step-function suppression at the saturation scale.
III. **CMB Alignment:** n_s = 0.964 and r ≈ 0.003 from three degrees of freedom, zero fine-tuning.
IV. **Schwarzschild Resolution:** r_min ∝ M^(1/3) ρ_max^(-1/3) from the Kretschmann scalar.
V. **Dark Energy Dissipation:** Λ(t) = Λ_0 / (1 + Λ_0³t/π)^(1/3), dΛ/dt < 0 structurally required.
""")

# ==================== TAB 2 ====================
with t2:
    st.subheader("4D Highway Transit — Wormhole Siphoning & Bridging")
    st.markdown("As localized saturation χ approaches 1, the reality manifold is **siphoned radially inward** through the 4th dimensional axis — creating internal transit chords. **All values and the 3D graph respond to the Master Global χ slider. Edge A/B always track the current sphere surface.**")

    colA, colB = st.columns([1, 2])
    with colA:
        pt_a_theta = st.slider("Point A Theta (0 to π)", 0.0, float(np.pi), float(np.pi/4))
        pt_a_phi   = st.slider("Point A Phi (0 to 2π)", 0.0, float(2*np.pi), 0.0)
        pt_a_chi   = st.slider("Point A Saturation χ", 0.00001, 1.00000,
                               float(chi_global), 0.00001, format="%.5f", key="t2_chi_a")
        st.markdown("---")
        pt_b_theta = st.slider("Point B Theta (0 to π)", 0.0, float(np.pi), float(3*np.pi/4))
        pt_b_phi   = st.slider("Point B Phi (0 to 2π)", 0.0, float(2*np.pi), float(np.pi))
        pt_b_chi   = st.slider("Point B Saturation χ", 0.00001, 1.00000,
                               float(chi_global), 0.00001, format="%.5f", key="t2_chi_b")

        st.markdown("### 🎚️ Transit Position")
        transit_pct = st.slider("Transit Timeline Scrubber (%)", 0, 100, 50)

        ON_THRESH = 0.96
        st.session_state.wh_active = (pt_a_chi > ON_THRESH and pt_b_chi > ON_THRESH)
        is_wormhole = st.session_state.wh_active
        if is_wormhole:
            st.success("Heuristic visualization threshold for deep saturation (χ → 1) achieved.")
        else:
            st.info("Shallow Sub-manifold Chord: standard geometric descent mapping active.")

        sin_a = np.sin(pt_a_theta); cos_a = np.cos(pt_a_theta)
        sin_b = np.sin(pt_b_theta); cos_b = np.cos(pt_b_theta)

        dot_product = np.clip(
            sin_a*sin_b*np.cos(pt_a_phi-pt_b_phi) + cos_a*cos_b, -1.0, 1.0)
        surface_dist = univ_R * np.arccos(dot_product)

        # Edge A/B TRACK the displayed sphere surface (fixes edge markers not moving)
        sphere_r_t2 = univ_R * (1.0 - chi_global * 0.5)

        xa_surf = sphere_r_t2 * sin_a * np.cos(pt_a_phi)
        ya_surf = sphere_r_t2 * sin_a * np.sin(pt_a_phi)
        za_surf = sphere_r_t2 * cos_a
        xb_surf = sphere_r_t2 * sin_b * np.cos(pt_b_phi)
        yb_surf = sphere_r_t2 * sin_b * np.sin(pt_b_phi)
        zb_surf = sphere_r_t2 * cos_b

        # Interior siphoning depths (scale with sphere)
        depth_a = 1.0 - pt_a_chi; depth_b = 1.0 - pt_b_chi
        xa = xa_surf * depth_a; ya = ya_surf * depth_a; za = za_surf * depth_a
        xb = xb_surf * depth_b; yb = yb_surf * depth_b; zb = zb_surf * depth_b

        # 4D chord distance (w dimension uses full univ_R)
        wa = univ_R * pt_a_chi; wb = univ_R * pt_b_chi
        chord_dist = np.sqrt((xa-xb)**2 + (ya-yb)**2 + (za-zb)**2 + (wa-wb)**2)
        dist_saved = surface_dist - chord_dist

        st.metric("Surface Distance (S)", f"{format_distance(surface_dist)}")
        st.metric("Internal Chord Distance (L)", f"{format_distance(chord_dist)}")
        st.caption("L uses Appendix-B chord form (includes Δw). Visualization only, not a covariant geodesic solver.")
        st.metric("🚀 Distance Savings (S - L)", f"{format_distance(dist_saved)}", delta="Saved via Metric Depth")
        st.markdown("---")
        st.markdown(f"**Global χ = {chi_global:.5f}** | m_eff = {m_eff(1000,chi_global):,.2f} kg / 1000 kg | D_msd = {d_msd(10,chi_global):,.2f} m / 10m craft")

    with colB:
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down", key="hw_top"):  st.session_state.cam_t2_hw = dict(eye=dict(x=0,y=0,z=2.5))
        if c2.button("Side", key="hw_side"):     st.session_state.cam_t2_hw = dict(eye=dict(x=2.5,y=0,z=0.2))
        if c3.button("Isometric", key="hw_iso"): st.session_state.cam_t2_hw = dict(eye=dict(x=1.5,y=1.5,z=1.5))

        fig2 = go.Figure()
        # Sphere surface scales with global chi
        fig2.add_trace(go.Surface(
            x=sphere_r_t2*np.cos(u)*np.sin(v),
            y=sphere_r_t2*np.sin(u)*np.sin(v),
            z=sphere_r_t2*np.cos(v),
            opacity=0.10, colorscale="Blues", showscale=False
        ))

        ca = "red" if pt_a_chi > 0.95 else "orange"
        cb = "red" if pt_b_chi > 0.95 else "orange"
        # Edge A — ON the sphere surface
        fig2.add_trace(go.Scatter3d(x=[xa_surf], y=[ya_surf], z=[za_surf],
                                    mode='markers+text', marker=dict(size=12,color=ca),
                                    text=["Edge A"], textposition="top center", name="Surface A"))
        fig2.add_trace(go.Scatter3d(x=[xa_surf,xa], y=[ya_surf,ya], z=[za_surf,za],
                                    mode='lines', line=dict(color=ca,dash='dot'), showlegend=False))
        # Edge B — ON the sphere surface
        fig2.add_trace(go.Scatter3d(x=[xb_surf], y=[yb_surf], z=[zb_surf],
                                    mode='markers+text', marker=dict(size=12,color=cb),
                                    text=["Edge B"], textposition="top center", name="Surface B"))
        fig2.add_trace(go.Scatter3d(x=[xb_surf,xb], y=[yb_surf,yb], z=[zb_surf,zb],
                                    mode='lines', line=dict(color=cb,dash='dot'), showlegend=False))

        num_steps=40; tx=np.linspace(xa,xb,num_steps); ty=np.linspace(ya,yb,num_steps); tz=np.linspace(za,zb,num_steps)
        fig2.add_trace(go.Scatter3d(x=tx, y=ty, z=tz, mode='lines',
                                    line=dict(width=6, color='lime' if is_wormhole else 'yellow'),
                                    name="Core Wormhole" if is_wormhole else "Shallow Chord"))
        pos_idx = int((transit_pct/100.0)*(num_steps-1))
        fig2.add_trace(go.Scatter3d(x=[tx[pos_idx]], y=[ty[pos_idx]], z=[tz[pos_idx]],
                                    mode='markers',
                                    marker=dict(size=10, color='white', symbol='diamond'),
                                    name="Transit Craft"))

        fig2.update_layout(
            title=f"4D Saturation Bridge (Global χ = {chi_global:.5f})",
            height=600, showlegend=True, margin=dict(l=0,r=0,b=0,t=40),
            scene_camera=st.session_state.cam_t2_hw,
            scene=dict(xaxis=dict(showticklabels=False),
                       yaxis=dict(showticklabels=False),
                       zaxis=dict(showticklabels=False))
        )
        st.plotly_chart(fig2, use_container_width=True, key="highway_transit_plot")

    st.markdown("---")
    st.markdown("### 🗺️ Navigational Mission Planner")
    colM1, colM2 = st.columns(2)
    with colM1:
        target_sf = st.number_input("Target Surface Distance (S, meters):", 1e3, float(univ_R*np.pi), 1e15, format="%.2e")
        target_ch = st.number_input("Desired Max Transit Span (L, meters):", 1e3, float(univ_R), 1e11, format="%.2e")
    with colM2:
        st.info("Heuristic routing: computes visualization-only χ proxy to reduce surface span S toward target chord span L.")
        if target_ch >= target_sf:
            st.warning("Desired transit span ≥ surface span. No saturation required.")
        else:
            req_chi = float(clamp_chi(1.0-(target_ch/target_sf)))
            st.metric("Minimum Required Engine Saturation (χ)", f"{req_chi:.5f}")
            st.progress(min(1.0, req_chi))
            st.caption(f"Relative geometric strain density factor: {100.0*(1.0/(1.0-req_chi+EPS)-1.0):,.1f}")

# ==================== TAB 3 ====================
with t3:
    st.subheader("Addendum B: Military UAP Sensor Correlation")
    st.warning("⚠️ SPECULATIVE ENGINEERING: The following applies CBQG heuristic physics to reverse-engineer reported UAP kinematics. Math core stays Appendix-B. Real-world attribution is strictly speculative.")
    st.markdown("When radar systems track anomalous craft, they report kinematics irreconcilable with GR. Under CBQG, if a craft accumulates localized spacetime tight to its hull limit (χ → 1), **acceleration increases without bound under finite force (via m_eff → 0)**.")

    st.markdown("### 📡 Scenario Modeler")
    scenario = st.selectbox("Load Physical Sensor Profile:",
                            ["Manual Entry", "Nimitz 'Tic Tac' Encounter (2004)", "Malmstrom AFB Shutdown (1967)"])
    if scenario == "Nimitz 'Tic Tac' Encounter (2004)":
        scn_chi, scn_m0, scn_v = 0.99900, 15000.0, 120.0
    elif scenario == "Malmstrom AFB Shutdown (1967)":
        scn_chi, scn_m0, scn_v = 0.95000, 8000.0, 28.0
    else:
        scn_chi, scn_m0, scn_v = chi_global, 5000.0, 120.0

    colS1, colS2, colS3 = st.columns(3)
    with colS1: m0 = st.slider("Craft Baseline Mass (kg)", 1.0, 1000000.0, float(scn_m0))
    with colS2: active_chi = st.slider("Active Saturation (χ)", 0.00001, 1.00000,
                                        float(scn_chi), 0.00001, format="%.5f", key="t3_chi")
    with colS3: V_electronics = st.slider("Control Voltage (V)", 1.0, 1000.0, float(scn_v))

    base_accel = 10000.0/(m0+EPS); m_e = m_eff(m0, active_chi); a_test = 10000.0/(m_e+EPS)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. Instantaneous Acceleration — USS Princeton 2004")
        st.markdown(f"**m_eff = {m0:,.0f} × √(1 - {active_chi:.5f}²) = <span style='color:lime'>{m_e:,.2f} kg</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-m_e/(m0+EPS))))
        st.info(f"Apparent radial acceleration proxy: {a_test:,.0f} m/s² under 10kN thrust (illustrative).")
        st.markdown("### 3. Minimum Standoff — Nimitz & Roosevelt")
        d_m = d_msd(10.0, active_chi)
        st.markdown(f"**D_msd = 10 × [{active_chi:.5f}/(1-{active_chi:.5f}+ε)]^(1/3) = <span style='color:lime'>{d_m:,.2f} m</span>**", unsafe_allow_html=True)
    with col2:
        st.markdown("### 2. No Sonic Boom — Nimitz 2004")
        f_d = f_drag(1000.0, active_chi)
        st.markdown(f"**F_drag = 1000 × √(1-{active_chi:.5f}²) = <span style='color:lime'>{f_d:,.2f} N</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-f_d/1000.0)))
        st.markdown("### 4. EM Damping — Malmstrom 1967")
        v_e = v_eff(V_electronics, active_chi)
        st.markdown(f"**V_eff = {V_electronics} × (1-{active_chi:.5f}) = <span style='color:red'>{v_e:,.2f} V</span>**", unsafe_allow_html=True)
        if active_chi > 0.90:
            st.error("Critical voltage collapse. Avionics/Warhead logic circuits failing (heuristic).")

    st.markdown("---")
    st.markdown("### 🛸 UAP Sensor Trajectory Analysis")
    st.caption("""
**X-axis:** Simulated radar tracking time in arbitrary units (0–10). The craft enters its saturated metric state
(χ-drive engaged) at t=2 and maintains it until t=8, then transitions back to standard kinematics.
This is an **illustrative timeline** to show the acceleration discontinuity signature as it would appear
on radar — not a calibrated real-world measurement. The sudden spike is the moment m_eff → 0 kicks in.
""")

    time_arr  = np.linspace(0, 10, 100)
    traj      = [base_accel]*20 + [a_test]*60 + [base_accel]*20

    # Static figure
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=time_arr, y=[base_accel]*100,
                              name=f"Conventional ({base_accel:,.1f} m/s²)",
                              line=dict(color='white', dash='dot', width=2)))
    fig3.add_trace(go.Scatter(x=time_arr, y=traj,
                              name=f"CBQG (χ={active_chi:.5f})",
                              line=dict(color='lime', width=3)))
    # Engagement zone shading
    fig3.add_vrect(x0=2, x1=8, fillcolor="rgba(0,255,150,0.07)", line_width=0,
                   annotation_text="χ-Drive Engaged", annotation_position="top right",
                   annotation_font=dict(color='rgba(0,255,150,0.8)', size=10))
    fig3.update_layout(
        title="Apparent Radar Acceleration Discontinuity (Log Scale)",
        height=320, margin=dict(l=0,r=0,b=0,t=40),
        xaxis_title="Radar Tracking Time (arbitrary units — see caption)",
        yaxis_title="Apparent Kinematics (m/s²)", yaxis_type="log",
        plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
        font=dict(color='white')
    )
    st.plotly_chart(fig3, use_container_width=True, key="dynamic_uap_transit_plot")

    # FLIGHT DEMO button
    st.markdown("### 🚀 UAP Flight Demo")
    st.caption("Click to watch the UAP craft move along the trajectory in real time, illustrating the radar signature.")
    if st.button("▶ LAUNCH FLIGHT DEMO — Watch UAP Transit", key="flight_demo_btn"):
        demo_fig = go.Figure()
        # Static background
        demo_fig.add_trace(go.Scatter(x=time_arr, y=[base_accel]*100,
                                       name="Conventional", line=dict(color='white', dash='dot', width=2),
                                       mode='lines'))
        demo_fig.add_trace(go.Scatter(x=time_arr, y=traj,
                                       name=f"CBQG (χ={active_chi:.5f})",
                                       line=dict(color='lime', width=3), mode='lines'))
        # Initial trail and craft traces
        demo_fig.add_trace(go.Scatter(x=[], y=[], mode='lines',
                                       line=dict(color='cyan', width=2, dash='dot'),
                                       name="UAP Trail", showlegend=False))
        demo_fig.add_trace(go.Scatter(x=[time_arr[0]], y=[traj[0]],
                                       mode='markers',
                                       marker=dict(size=22, color='cyan', symbol='triangle-right'),
                                       name="UAP Craft"))
        # Build animation frames
        demo_frames = []
        for i in range(0, len(time_arr), 2):
            demo_frames.append(go.Frame(
                data=[
                    go.Scatter(x=time_arr[:i+1], y=traj[:i+1], mode='lines',
                               line=dict(color='cyan', width=1, dash='dot')),
                    go.Scatter(x=[time_arr[i]], y=[traj[i]], mode='markers',
                               marker=dict(size=22, color='cyan', symbol='triangle-right'))
                ],
                traces=[2, 3], name=f"df{i}"
            ))
        demo_fig.frames = demo_frames
        demo_fig.update_layout(
            title=f"UAP Flight Demo — χ={active_chi:.5f} | m_eff={m_e:,.1f} kg | a={a_test:,.0f} m/s²",
            height=380, margin=dict(l=0,r=0,b=90,t=45),
            xaxis_title="Radar Tracking Time (arbitrary units)",
            yaxis_title="Apparent Kinematics (m/s²)", yaxis_type="log",
            plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
            font=dict(color='white'),
            updatemenus=[dict(
                type="buttons", direction="left", showactive=True,
                y=-0.12, yanchor="top", x=0.5, xanchor="center",
                buttons=[
                    dict(label="▶ PLAY FLIGHT", method="animate",
                         args=[None, dict(frame=dict(duration=80, redraw=True),
                                          transition=dict(duration=0),
                                          fromcurrent=False, mode="immediate")]),
                    dict(label="⏹ STOP", method="animate",
                         args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False))])
                ]
            )]
        )
        st.plotly_chart(demo_fig, use_container_width=True, key="flight_demo_chart")

    st.markdown("---")
    st.markdown("### ☄️ Re-entry Protocol Simulator")
    colR1, colR2 = st.columns(2)
    with colR1:
        sim_k = st.slider("Re-entry Damping Factor (k)", 0.1, 15.0, 3.0, 0.1, key="k_slider")
        st.info("High k: fast inertial reconnection, high G-force risk. Low k: slow decay, survivable re-entry (heuristic).")
    with colR2:
        peak_g = 50.0 * sim_k * active_chi
        st.metric("Peak Inertial Whiplash", f"{peak_g:.1f} Gs")
        st.caption("Heuristic order-of-magnitude estimate only.")
        if peak_g > 50:   st.error("🚨 STRUCTURAL FAILURE: >50G limit exceeded.")
        elif active_chi <= 0.05: st.success("✅ CRAFT AT NORMAL INERTIA.")
        else:             st.success("✅ RE-ENTRY SURVIVABLE.")
        t_arr_re = np.linspace(0, 5, 50)
        chi_t = chi_decay(active_chi, sim_k, t_arr_re)
        fig_re = go.Figure(go.Scatter(x=t_arr_re, y=chi_t, fill='tozeroy', line=dict(color='orange')))
        fig_re.update_layout(title="Phase Decay Profile", height=200, margin=dict(l=0,r=0,b=0,t=30),
                             yaxis_title="χ(t)", xaxis_title="Seconds",
                             plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
                             font=dict(color='white'))
        st.plotly_chart(fig_re, use_container_width=True, key="reentry_chart")

# ==================== TAB 4 ====================
with t4:
    st.subheader("Theory & Axioms")

    st.markdown("### 0. Unified Scalar Simplification (Engine Constraint)")
    st.markdown("**Explanation:** True CBQG is a covariant tensor formulation driven by the invariant curvature limits of R_abcd R^abcd. For this browser-based simulator, the tensor field is simplified into a single master scalar UI control (χ). Consequently, χ acts pedagogically across curvature magnitude, spatial depth coordinate, and mass modifier simultaneously. All heuristic engineering equations (Tab 3) are extensions beyond the published v10.5 framework.")

    st.markdown("### 1. Metric Saturation Invariant (χ)")
    st.code("χ = C / C_max ≤ 1")
    st.markdown("**Explanation:** Spacetime curvature C cannot exceed C_max. χ tracks what fraction of that capacity is exhausted across all fields. χ=0: flat, maximum expansion. χ=1: geometric saturation — the Big Bounce.")

    st.markdown("### 2. Effective Mass Negation (m_eff)")
    st.code("m_eff = m_0 √(1 - χ²)")
    st.markdown("**Explanation:** As χ → 1, the craft's inertial connection to the universe evaporates toward zero, permitting arbitrarily large velocity vectors under finite applied force. Same mathematical structure as the Lorentz factor, driven by geometric saturation rather than velocity.")

    st.markdown("### 3. Aerodynamic Drag Suppression (F_drag)")
    st.code("F_drag = F_0 √(1 - χ²)")
    st.markdown("**Explanation:** As the local metric saturates, fluid interaction collapses with the same scaling as m_eff. The atmosphere slides around the saturated metric boundary rather than compressing, eliminating sonic booms and aerodynamic heating simultaneously.")

    st.markdown("### 4. Minimum Standoff Distance (D_msd)")
    st.code("D_msd = R [χ / (1 - χ + ε)]^(1/3)")
    st.markdown("**Explanation:** A saturating craft projects a curvature gradient that repels unsaturated external mass. ε=10⁻⁹ prevents singular divergence at χ=1. At high χ this buffer zone grows rapidly, producing the 'mirroring' behavior reported in UAP encounters (heuristic application).")

    st.markdown("### 5. Electromagnetic Damping (V_eff)")
    st.code("V_eff = V_0 (1 - χ)")
    st.markdown("**Explanation:** Vacuum impedance scales linearly with saturation. As χ → 1, the geometric dielectric barrier bleeds voltage from surrounding electronics, driving active systems toward shutdown. Strictly linear per Appendix B derivation.")

    st.markdown("### 6. 4D Highway Volume (V_core)")
    st.code("V_core = 0.5 π² R⁴ (1 - √(1 - χ²))")
    st.markdown("**Explanation:** Usable interior volume of the 4D hypersphere traversable by saturated craft without phase-lane crossing. Derived from the 4-ball shell volume compressed by the saturation invariant. Zero at χ=0, maximum at χ=1.")

    st.markdown("### 7. Harmonic Re-entry Decay (χ_t)")
    st.code("χ(t) = χ_init e^(-kt)")
    st.markdown("**Explanation:** Instantaneous saturation collapse would reconnect full inertial mass instantly, inducing catastrophic structural G-forces. Exponential decay with factor k distributes the inertial reconnection over a survivable timescale.")

    st.markdown("### 8. Metric Radial Depth Coordinate (w)")
    st.code("w = R * χ")
    st.markdown("**Explanation:** The 4th-dimensional interior penetration depth. At χ=0, w=0 (surface only). At χ=1, w=R (full interior penetration). This coordinate anchors the wormhole chord calculation geometrically.")

    st.markdown("### 9. Wormhole Chord Distance (L)")
    st.code("L = √(Σ(Δxi)² + (Δw)²)")
    st.markdown("**Explanation:** Euclidean chord through the 4D interior connecting two saturated surface points. Requires the explicit w coordinate (Eq. 8). This is a visualization embedding approximation — true CBQG geodesic paths use the full covariant tensor formulation. Shortcut effect is real; magnitude is an order-of-magnitude heuristic.")

    st.markdown("### 10. Dark Energy Dissipation (Λ(t))")
    st.code("Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)")
    st.markdown("**Explanation:** Derived in CBQG v10 (pages 146–173) as a necessary consequence of total constraint preservation under quantum information bounds. Variables are Planck-normalized (Λ̄ ≡ Λℓ²_P, t̄ ≡ t/t_P). Excludes eternal de Sitter expansion and generates the complete cosmic life cycle. Dark energy crossover time ~10^315 years (CBQG v10, pp. 164–165).")

st.caption("CBQG v10.5.1 © Dr. Anthony Omar Peña, D.O. — All rights reserved.")
