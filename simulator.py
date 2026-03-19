import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import time

st.set_page_config(page_title="CBQG v10.5.1 Universal Engine", layout="wide")

# ====================== GLOBAL CSS — prevent Plotly animation buttons turning white ======================
st.markdown("""
<style>
/* Force Plotly updatemenus (animation play/stop buttons) to stay dark even when active */
.updatemenu-item-rect {
    fill: rgba(40, 40, 80, 1) !important;
    stroke: rgba(120, 120, 190, 1) !important;
}
.updatemenu-item-text {
    fill: rgba(210, 210, 255, 1) !important;
}
/* Also target active/hover states */
.updatemenu-item-rect:hover,
.updatemenu-item.active .updatemenu-item-rect {
    fill: rgba(70, 70, 130, 1) !important;
}
</style>
""", unsafe_allow_html=True)

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
defaults = {
    "chi_global": 0.50000, "wh_active": False,
    "cam_t1_gw": dict(eye=dict(x=2.5, y=0.0, z=0.2)),
    "cam_t1_sph": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
    "cam_t2_hw": dict(eye=dict(x=1.5, y=1.5, z=1.5)),
    "uap_demo_active": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ====================== SIDEBAR ======================
st.sidebar.header("Master Controls")
if st.sidebar.button("⚠️ SYSTEM RESET"):
    st.session_state.clear(); st.rerun()

st.sidebar.markdown("---")
chi_global = st.sidebar.slider(
    "Global Saturation χ", 0.00001, 1.00000,
    float(st.session_state.get("chi_global", 0.50000)), 0.00001, format="%.5f"
)
st.session_state.chi_global = chi_global

if chi_global <= 0.05:
    st.sidebar.success("χ ≈ 0 — Maximum Expansion: lowest curvature. Dark energy dominant. Geometry approaches flat baseline.")
elif chi_global >= 0.95:
    st.sidebar.error("χ ≈ 1 — GEOMETRIC SATURATION: C_max reached. Big Bounce imminent. Singularities forbidden.")
else:
    st.sidebar.success("Engine Engaged: All kinetics bonded interactively to Global χ.")

univ_R = st.sidebar.number_input("Universal 4D Radius (R, meters)", 1e10, 1e30, 1e22, step=1e20)
st.sidebar.caption("Drives Minimum Standoff (D_msd) and 4D Highway Volume (V_core).")

# ====================== CORE MATH ======================
EPS = 1e-9
C_LIGHT = 3e8  # m/s

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
    if m >= ly:       return f"{m/ly:,.3f} Light Years"
    elif m >= 1e15:   return f"{m/1e15:,.3f} Trillion km"
    elif m >= 1e12:   return f"{m/1e12:,.3f} Billion km"
    elif m >= 1e9:    return f"{m/1e9:,.3f} Million km"
    elif m >= 1000:   return f"{m/1000:,.3f} km"
    else:             return f"{m:,.3f} m"

def format_time(seconds):
    if seconds < 0.001:       return f"{seconds*1e6:.2f} μs"
    elif seconds < 1:          return f"{seconds*1000:.3f} ms"
    elif seconds < 60:         return f"{seconds:.3f} s"
    elif seconds < 3600:       return f"{seconds/60:.3f} min"
    elif seconds < 86400:      return f"{seconds/3600:.3f} hr"
    elif seconds < 3.156e7:    return f"{seconds/86400:.3f} days"
    elif seconds < 3.156e9:    return f"{seconds/3.156e7:.4f} yr"
    else:                      return f"{seconds/3.156e7:.3e} yr"

def format_energy(joules):
    if joules <= 0:             return "0 J"
    tsar = 2.1e17
    if joules < 1e9:            return f"{joules:.3e} J"
    elif joules < 1e12:         return f"{joules/1e9:.3f} GJ"
    elif joules < 1e15:         return f"{joules/1e12:.3f} TJ"
    elif joules < 1e18:         return f"{joules/1e15:.3f} PJ"
    elif joules < 1e21:         return f"{joules/1e18:.3f} EJ  ({joules/tsar:.2f}× Tsar Bomba)"
    else:                        return f"{joules:.3e} J  ({joules/tsar:.3e}× Tsar Bomba)"

# Global sphere grids
U_RES = 30j
u, v = np.mgrid[0:2*np.pi:U_RES, 0:np.pi:U_RES]

def rippled_sphere(rad, chi_val, u_g, v_g):
    amp = chi_val * 0.12 * rad
    ripple = amp * (np.sin(6*u_g)*np.sin(4*v_g) + 0.5*np.sin(10*u_g)*np.sin(8*v_g))
    r = rad + ripple
    return r*np.cos(u_g)*np.sin(v_g), r*np.sin(u_g)*np.sin(v_g), r*np.cos(v_g)

# ====================== FIG 1 BUILDER ======================
def smooth_cap(x_arr, cap, t=0.05):
    return cap - t * np.log(1.0 + np.exp(np.clip((cap - x_arr) / t, -500, 500)))

def build_fig1(chi_val):
    rho = np.linspace(0.0, 1.0, 500); C_max_d = 1.0
    C_GR_raw = 1.3*rho + np.where(rho > 0.70, (rho - 0.70)**2 * 18.0, 0.0)
    C_GR_clip = np.clip(C_GR_raw, 0.0, 1.58)
    C_CBQG = smooth_cap(C_GR_raw, C_max_d, t=0.05)
    chi_c = float(np.clip(chi_val, 0.001, 0.998))
    target_C = chi_c * C_max_d
    rho_marker = float(np.interp(target_C, C_CBQG, rho)); C_marker = target_C
    visible = C_GR_raw <= 1.58
    above_cmax = np.where(C_GR_raw >= C_max_d)[0]
    rho_cmax_cross = float(rho[above_cmax[0]]) if len(above_cmax) > 0 else 0.85
    sat_idx = np.where(C_CBQG >= 0.93*C_max_d)[0]
    rho_sat = float(rho[sat_idx[0]]) if len(sat_idx) > 0 else 0.75

    fig = go.Figure()
    fig.add_hrect(y0=C_max_d, y1=1.65, fillcolor="rgba(220,80,80,0.2)", line_width=0,
                  annotation_text="  Forbidden (χ > 1)",
                  annotation_position="top left",
                  annotation_font=dict(color="rgba(220,100,100,1)", size=13))
    fig.add_hline(y=C_max_d, line_dash="dash", line_color="rgba(200,200,200,0.7)", line_width=2)
    fig.add_annotation(x=1.02, y=C_max_d,
                       text="C_max (χ = 1)<br><i>Quantum requirement:<br>finite state density</i>",
                       showarrow=False, xref="paper", yref="y", xanchor="left",
                       font=dict(color="rgba(200,200,200,0.9)", size=10))
    fig.add_trace(go.Scatter(x=rho[visible], y=C_GR_clip[visible],
                             mode='lines', name='General Relativity',
                             line=dict(color='rgba(110,170,255,1)', width=3)))
    rho_sp = np.linspace(rho_cmax_cross, min(rho_cmax_cross+0.06, 0.97), 25)
    C_sp = np.clip(1.3*rho_sp + np.where(rho_sp>0.70,(rho_sp-0.70)**2*18,0), 0, 1.58)
    fig.add_trace(go.Scatter(x=rho_sp, y=C_sp, mode='lines', showlegend=False,
                             line=dict(color='rgba(110,170,255,1)', width=3)))
    fig.add_annotation(x=rho_cmax_cross+0.02, y=1.53, ax=0, ay=-22,
                       xref="x", yref="y", axref="pixel", ayref="pixel",
                       showarrow=True, arrowhead=2, arrowsize=1.5,
                       arrowcolor='rgba(110,170,255,1)', arrowwidth=3,
                       text="<b>∞</b>", font=dict(size=18, color='rgba(110,170,255,1)'))
    fig.add_annotation(x=min(rho_cmax_cross+0.09, 0.98), y=1.43,
                       text="GR–QM<br>Incompatibility", showarrow=False,
                       xref="x", yref="y", font=dict(size=11, color='rgba(110,170,255,0.85)'))
    fig.add_trace(go.Scatter(x=rho, y=C_CBQG, mode='lines', name='CBQG',
                             line=dict(color='rgba(215,175,30,1)', width=3.5)))
    fig.add_annotation(x=max(rho_sat-0.04, 0.55), y=C_max_d-0.035,
                       text="← Saturation", showarrow=False,
                       font=dict(size=11, color='rgba(215,175,30,0.85)'), xref="x", yref="y")
    fig.add_annotation(x=min(rho_sat+0.04, 0.92), y=C_max_d-0.13,
                       text="Geometric<br>Saturation", showarrow=False,
                       font=dict(size=12, color='rgba(215,175,30,0.75)'), xref="x", yref="y")
    fig.add_trace(go.Scatter(x=[rho_marker], y=[C_marker],
                             mode='markers+text', name=f'Current χ = {chi_val:.5f}',
                             marker=dict(size=14, color='white', symbol='circle',
                                         line=dict(color='rgba(215,175,30,1)', width=2.5)),
                             text=[f"  χ = {chi_val:.5f}"], textposition="middle right",
                             textfont=dict(color='white', size=11)))
    fig.add_shape(type="line", x0=rho_marker, x1=rho_marker,
                  y0=C_marker, y1=C_max_d,
                  line=dict(color="rgba(255,255,255,0.25)", dash="dot", width=1.5),
                  xref="x", yref="y")
    fig.update_layout(
        title=dict(text=f"CBQG Fig. 1 — Curvature vs Energy Density  (χ = {chi_val:.5f})",
                   font=dict(size=14, color='white')),
        xaxis=dict(title="Energy Density (ρ) →", range=[0,1.05], showgrid=False,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)', tickvals=[], color='white'),
        yaxis=dict(title="Spacetime Curvature (C) →", range=[0,1.65], showgrid=False,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   tickvals=[0, C_max_d], ticktext=["0","C_max"], color='white'),
        plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)',
        font=dict(color='white'),
        legend=dict(x=0.02, y=0.97, bgcolor='rgba(0,0,0,0.45)',
                    bordercolor='rgba(255,255,255,0.2)', borderwidth=1, font=dict(color='white')),
        height=430, margin=dict(l=65, r=140, b=55, t=55)
    )
    return fig

BG = dict(plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)', font=dict(color='white'))

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

    st.markdown("---")
    st.markdown("### 📈 CBQG Fig. 1 — Curvature Saturation vs GR Divergence (Live)")
    st.markdown("""
The **white dot** tracks your current **χ** on the CBQG saturation curve in real time.
Both GR (blue) and CBQG (gold) **begin identically at low energy density** — CBQG recovers GR exactly in the weak-field limit.
Only at extreme energy density does CBQG saturate at C_max while GR diverges to infinity.
The pink zone is **geometrically forbidden** by C ≤ C_max.
""")
    st.plotly_chart(build_fig1(chi_global), use_container_width=True, key="fig1_dynamic")
    st.caption("Fig. 1 is intentionally schematic. Linear scale communicates the qualitative contrast. A fully quantitative plot is future work (CBQG v10.5, p. 244).")

    st.markdown("---")
    st.markdown("### 🔄 CBQG Universe Life Cycle (v10.2 Derivation)")
    st.markdown("""
The CBQG framework derives a complete **nonsingular** cosmic history from C ≤ C_max alone:

**Bounce → Expansion → Dark Energy Dissipation → Turnaround* → Contraction → Bounce**

Dark energy decays dynamically (CBQG v10, Planck-normalized): **Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)**, dΛ/dt < 0.

*Turnaround requires: (1) closed FRW k>0, (2) compact spatial slices, (3) Λ→0 + sign-reversal, or (4) no Minkowski escape boundary.*
""")
    with st.expander("📅 Cosmic Life Cycle Timing (CBQG v10, pages 164–165)"):
        st.markdown("""
| Milestone | Timescale | Source |
|---|---|---|
| Dark energy crossover | ~10^315 years | CBQG v10, pp. 164–165 (derived) |
| Turnaround begins | > 10^315 years | Derived constraint |
| Curvature-bounded Bounce | ~10^400–10^500 years | Heuristic extrapolation |

Bounce: entire observable universe → ~2.3 proton widths, energy ≈ 1.35 × 10^70 J, reversal within 1 Planck time. Fully nonsingular.
""")

    st.markdown("### Λ(t) Dissipation — CBQG v10 (Planck-Normalized Units)")
    L0_val = st.slider("Initial Λ₀ (Planck-normalized)", 0.01, 2.0, 0.5, 0.01, key="lambda_slider")
    t_plot = np.linspace(0, 20, 300); L_plot = lambda_cbqg(L0_val, t_plot)
    fig_L = go.Figure()
    fig_L.add_trace(go.Scatter(x=t_plot, y=L_plot, line=dict(color='gold', width=3), name="Λ(t)"))
    fig_L.add_hline(y=0, line_dash="dot", line_color="red", annotation_text="Λ → 0 (crossover)")
    fig_L.update_layout(title="Λ(t) = Λ₀ / (1 + Λ₀³t/π)^(1/3)",
                        xaxis_title="t (Planck-normalized)", yaxis_title="Λ(t)",
                        height=280, margin=dict(l=0,r=0,b=0,t=40), **BG)
    st.plotly_chart(fig_L, use_container_width=True, key="lambda_plot")

    st.markdown("---")
    view_mode = st.radio("Select 3D Reality Representation:",
                         ["3D Spacetime (Dual Gravity Wells / Wormhole)", "4D Hypersphere (Life Cycle Animation)"],
                         horizontal=True)

    # ---- DUAL GRAVITY WELLS ----
    if view_mode == "3D Spacetime (Dual Gravity Wells / Wormhole)":
        st.markdown("""
**Two opposing gravity wells.** Each well has its own χ slider.
At **χ_A = χ_B = 1**, both geometric floors reach **z = 0** simultaneously — the Einstein-Rosen bridge (wormhole) throat forms.
Default view: **side cross-section** so both wells are visible simultaneously.
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
            st.caption(f"Well A floor: z = {3.0 - 3.0*chi_well_a:.4f}")
        with wcb:
            chi_well_b = st.slider("Well B Saturation χ_B (Mirror)", 0.00001, 1.00000,
                                   float(chi_global), 0.00001, format="%.5f", key="well_b")
            st.caption(f"Well B floor: z = {-(3.0 - 3.0*chi_well_b):.4f}")

        both_max = chi_well_a >= 0.999 and chi_well_b >= 0.999
        both_forming = chi_well_a >= 0.90 and chi_well_b >= 0.90
        if both_max:
            st.success("🌀 WORMHOLE FORMED: Both geometric floors at C_max. Einstein-Rosen bridge topology active. Throat at z = 0.")
        elif both_forming:
            gap = (3.0*(1-chi_well_a)) + (3.0*(1-chi_well_b))
            st.warning(f"⚠️ WORMHOLE FORMING: χ_A={chi_well_a:.5f}, χ_B={chi_well_b:.5f}. Throat gap: {gap:.4f} units.")
        else:
            st.info("Two independent gravity wells. Increase both χ values toward 1.0 to form the Einstein-Rosen bridge.")

        x_w = np.linspace(-5, 5, 55); y_w = np.linspace(-5, 5, 55)
        xx_w, yy_w = np.meshgrid(x_w, y_w)
        r_w = np.sqrt(xx_w**2 + yy_w**2)
        depth_prof = np.minimum(3.0 / (r_w + 0.1), 3.0)
        zz_a = 3.0 - clamp_chi(chi_well_a) * depth_prof
        zz_b = -(3.0 - clamp_chi(chi_well_b) * depth_prof)
        col_a = clamp_chi(chi_well_a) * depth_prof / 3.0
        col_b = clamp_chi(chi_well_b) * depth_prof / 3.0

        fig_gw = go.Figure()
        fig_gw.add_trace(go.Surface(z=zz_a, x=xx_w, y=yy_w, colorscale='Plasma',
                                     opacity=0.88, showscale=False, surfacecolor=col_a,
                                     cmin=0, cmax=1, name="Well A"))
        fig_gw.add_trace(go.Surface(z=zz_b, x=xx_w, y=yy_w, colorscale='Viridis',
                                     opacity=0.88, showscale=False, surfacecolor=col_b,
                                     cmin=0, cmax=1, name="Well B"))
        floor_a = float(3.0 - clamp_chi(chi_well_a)*3.0)
        floor_b = float(-(3.0 - clamp_chi(chi_well_b)*3.0))
        if abs(floor_a) < 3.0:
            fig_gw.add_trace(go.Surface(z=np.full_like(xx_w, floor_a), x=xx_w, y=yy_w,
                                         colorscale='Reds', opacity=0.12, showscale=False))
        if abs(floor_b) < 3.0:
            fig_gw.add_trace(go.Surface(z=np.full_like(xx_w, floor_b), x=xx_w, y=yy_w,
                                         colorscale='Blues', opacity=0.12, showscale=False))
        if both_forming:
            th = np.linspace(0, 2*np.pi, 80)
            r_throat = max(0.05, 3*(1-max(chi_well_a, chi_well_b)))
            fig_gw.add_trace(go.Scatter3d(
                x=r_throat*np.cos(th), y=r_throat*np.sin(th), z=np.zeros(80),
                mode='lines', line=dict(color='cyan', width=6),
                name=f"Wormhole Throat (r={r_throat:.4f})"))
        fig_gw.add_trace(go.Scatter3d(x=[0],y=[5.5],z=[3.1], mode='text',
                                       text=[f"Well A  χ_A={chi_well_a:.5f}"],
                                       textfont=dict(color='rgba(255,180,50,1)',size=11), showlegend=False))
        fig_gw.add_trace(go.Scatter3d(x=[0],y=[5.5],z=[-3.2], mode='text',
                                       text=[f"Well B  χ_B={chi_well_b:.5f}"],
                                       textfont=dict(color='rgba(100,200,255,1)',size=11), showlegend=False))
        if both_max:
            fig_gw.add_trace(go.Scatter3d(x=[0],y=[0],z=[0.15], mode='text',
                                           text=["🌀 WORMHOLE THROAT"],
                                           textfont=dict(color='cyan',size=13), showlegend=False))
        fig_gw.update_layout(
            title=f"Einstein-Rosen Bridge Geometry  (χ_A={chi_well_a:.5f}, χ_B={chi_well_b:.5f})",
            height=900, margin=dict(l=0,r=0,b=0,t=50),
            scene_camera=st.session_state.cam_t1_gw,
            scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (Curvature)',
                       zaxis=dict(range=[-4,4]), aspectmode='cube')
        )
        st.plotly_chart(fig_gw, use_container_width=True, key="gravity_well_plot")
        st.caption("Well A (upper, Plasma) and Well B (lower, Viridis). At χ=1 for both, floors converge at z=0 forming the wormhole throat. Schematic embedding only.")

    # ---- HYPERSPHERE LIFE CYCLE ----
    else:
        st.markdown("""
**One complete CBQG cosmic cycle:**

| χ value | Phase |
|---|---|
| **χ = 1.000** | ⚡ **Big Bounce** — C_max saturation. Singularity forbidden. Geometry at maximum curvature. |
| χ: 1 → 0.5 | **Expansion** — Universe grows rapidly. Dark energy dominant. Sphere smooths out. |
| χ: 0.5 → 0.1 | **Dark Energy Dissipation** — Λ(t) decays. Expansion slows. |
| **χ = 0.000** | 🔵 **Turnaround Point** — Maximum expansion. Perfectly smooth sphere. H → 0. |
| χ: 0 → 0.5 | **Contraction** — Universe collapses inward. Curvature ripples amplify. |
| χ: 0.5 → 1 | **Big Crunch** — Collapse accelerates toward C_max. Ripples at maximum. |
| **χ = 1.000** | ⚡ **Big Bounce** — Cycle repeats. Singularity forbidden. |

Animation plays **one full cycle: χ=1 → χ=0 → χ=1**. Use PLAY/STOP and the scrubber below.
""")
        scale_mode = st.radio("Viewport Scaling", ["Visual (Linear Drop)", "Physical (Nonlinear Metric Compression)"], horizontal=True)
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="sph_t"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=0,y=0,z=2.5))
        if c2.button("Side View", key="sph_s"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=2.5,y=0,z=0.2))
        if c3.button("Isometric View", key="sph_i"):
            st.session_state.cam_t1_sph = dict(eye=dict(x=1.5,y=1.5,z=1.5))

        if chi_global < 0.05:
            st.info("TURNAROUND POINT — χ ≈ 0, maximum expansion. Universe is at its largest and smoothest.")
        elif chi_global > 0.95:
            st.error("BIG BOUNCE / BIG CRUNCH — χ ≈ 1, C_max saturation. Geometry at maximum curvature.")

        max_bound = univ_R * 1.15

        # Cycle starts at chi=1 (Big Bounce), expands to chi=0 (Turnaround), contracts back to chi=1 (Big Bounce)
        # 35 steps each half = 70 total frames, starting and ending at chi=1
        chi_expand   = np.linspace(1.000, 0.000, 36)   # Big Bounce → Turnaround
        chi_contract = np.linspace(0.000, 1.000, 36)   # Turnaround → Big Bounce
        # Drop duplicate endpoints where they join
        chi_cycle = np.concatenate([chi_expand[:-1], chi_contract])

        def sphere_rad(c_val):
            c_v = clamp_chi(c_val)
            if scale_mode == "Physical (Nonlinear Metric Compression)":
                # At chi=1: radius=0 (bounce point). At chi=0: radius=univ_R (max expansion)
                return univ_R * np.sqrt(max(0.0, 1.0 - c_v**2))
            else:
                # Visual linear: at chi=1 sphere is small (0.1*R), at chi=0 sphere is large (1.1*R)
                return univ_R * max(0.001, 1.1 - c_v)

        # Initial frame: start at chi=1 (Big Bounce) — small, highly rippled sphere
        rad0 = sphere_rad(1.000)
        sx0, sy0, sz0 = rippled_sphere(rad0, 1.000, u, v)

        fig_life = go.Figure(data=[go.Surface(
            x=sx0, y=sy0, z=sz0, opacity=0.85,
            colorscale="Plasma", showscale=False,
            cmin=0, cmax=1
        )])

        def phase_label(c_val, frame_idx, total_frames):
            """Generate accurate phase label based on position in cycle."""
            half = total_frames // 2
            in_expansion = frame_idx < half  # first half: chi 1→0 (expansion)

            if c_val >= 0.999:
                if frame_idx == 0:
                    return f"χ = {c_val:.3f} | ⚡ BIG BOUNCE — C_max geometric saturation. Singularity forbidden."
                else:
                    return f"χ = {c_val:.3f} | ⚡ BIG BOUNCE — Cycle complete. C_max reached again."
            elif c_val <= 0.001:
                return f"χ = {c_val:.3f} | 🔵 TURNAROUND POINT — Maximum expansion. Perfectly smooth. H → 0. Contraction begins."
            elif in_expansion:
                if c_val > 0.70:
                    return f"χ = {c_val:.3f} | EXPANSION — Post-bounce rapid growth. Dark energy rising."
                elif c_val > 0.40:
                    return f"χ = {c_val:.3f} | EXPANSION — Λ(t) dissipating. Expansion rate slowing."
                else:
                    return f"χ = {c_val:.3f} | EXPANSION — Dark energy near minimum. Approaching turnaround."
            else:
                if c_val < 0.30:
                    return f"χ = {c_val:.3f} | CONTRACTION — Collapse beginning. Curvature ripples emerging."
                elif c_val < 0.70:
                    return f"χ = {c_val:.3f} | CONTRACTION — Curvature ripples amplifying."
                else:
                    return f"χ = {c_val:.3f} | BIG CRUNCH — Collapse accelerating toward C_max. Geometry saturating."

        anim_frames = []
        total_frames = len(chi_cycle)
        for i, c_val in enumerate(chi_cycle):
            c_val = float(np.clip(c_val, 0.0, 1.0))
            r_f = sphere_rad(c_val)
            sx, sy, sz = rippled_sphere(r_f, c_val, u, v)
            phase = phase_label(c_val, i, total_frames)
            anim_frames.append(go.Frame(
                data=[go.Surface(x=sx, y=sy, z=sz, opacity=0.85,
                                  colorscale="Plasma", showscale=False, cmin=0, cmax=1)],
                name=f"frame_{i}",
                layout=go.Layout(
                    title_text=f"CBQG Universe Life Cycle — {phase}",
                    plot_bgcolor='rgba(12,12,22,1)',
                    paper_bgcolor='rgba(12,12,22,1)'
                )
            ))
        fig_life.frames = anim_frames

        fig_life.update_layout(
            title=f"CBQG Universe Life Cycle — Starting at Big Bounce (χ = 1.000)",
            height=680,
            margin=dict(l=0, r=0, b=160, t=55),
            plot_bgcolor='rgba(12,12,22,1)',
            paper_bgcolor='rgba(12,12,22,1)',
            scene_camera=st.session_state.cam_t1_sph,
            scene=dict(
                xaxis=dict(range=[-max_bound,max_bound], title='X (m)',
                           backgroundcolor='rgba(12,12,22,1)', gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(range=[-max_bound,max_bound], title='Y (m)',
                           backgroundcolor='rgba(12,12,22,1)', gridcolor='rgba(255,255,255,0.1)'),
                zaxis=dict(range=[-max_bound,max_bound], title='Z (m)',
                           backgroundcolor='rgba(12,12,22,1)', gridcolor='rgba(255,255,255,0.1)'),
                aspectmode='cube',
                bgcolor='rgba(12,12,22,1)'
            ),
            updatemenus=[dict(
                type="buttons", direction="left", showactive=False,
                active=-1,
                y=-0.10, yanchor="top", x=0.0, xanchor="left",
                bgcolor='rgba(40,40,80,1)',
                bordercolor='rgba(120,120,190,1)',
                font=dict(color='rgba(210,210,255,1)'),
                pad={"t": 8, "r": 8},
                buttons=[
                    dict(label="▶ PLAY FULL CYCLE (Big Bounce → Turnaround → Big Bounce)",
                         method="animate",
                         args=[None, dict(frame=dict(duration=110, redraw=True),
                                          transition=dict(duration=0),
                                          fromcurrent=False, mode="immediate")]),
                    dict(label="⏹ STOP",
                         method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ]
            )],
            sliders=[dict(
                steps=[dict(
                    args=[[f"frame_{i}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                    label=f"χ={chi_cycle[i]:.2f}", method="animate"
                ) for i in range(len(chi_cycle))],
                transition=dict(duration=0),
                x=0.0, y=-0.22, len=1.0,
                bgcolor='rgba(40,40,80,0.8)',
                bordercolor='rgba(120,120,190,1)',
                font=dict(color='white'),
                tickcolor='white',
                pad={"t": 40, "b": 10},
                currentvalue=dict(
                    prefix="Life Cycle Position: ", visible=True,
                    xanchor="center", font=dict(color='white', size=12)
                )
            )]
        )
        st.plotly_chart(fig_life, use_container_width=True, key="native_plotly_lifecycle")
        st.caption("χ=1.000: Big Bounce (small, highly rippled sphere — C_max saturation). χ→0.000: expansion, sphere grows and smooths. χ=0.000: Turnaround Point (large perfectly smooth sphere). χ→1.000: contraction, ripples amplify toward Big Bounce again. Buttons and scrubber below the chart.")

    st.markdown("""
---
**Five near-term falsifiable predictions:**
I. **UV Spectral Discriminant:** δCBQG ≡ n_t + r/8 ≥ 2.
II. **Tensor Step Feature:** r(k) step-function suppression at saturation scale.
III. **CMB Alignment:** n_s = 0.964, r ≈ 0.003 from three degrees of freedom.
IV. **Schwarzschild Resolution:** r_min ∝ M^(1/3) ρ_max^(-1/3).
V. **Dark Energy Dissipation:** Λ(t) = Λ_0/(1+Λ_0³t/π)^(1/3), dΛ/dt < 0.
""")

# ==================== TAB 2 ====================
with t2:
    st.subheader("4D Highway Transit — Wormhole Siphoning & Bridging")
    st.markdown("""
As localized saturation χ approaches 1, the reality manifold is **siphoned radially inward** through the 4th dimensional axis — creating internal transit chords shorter than surface paths.
**Edge A and Edge B always track the current sphere surface.** The transit scrubber moves the UAP craft from Point A (left) to Point B (right).
""")

    colA, colB = st.columns([1, 2])
    with colA:
        st.markdown("#### Point A (Departure)")
        pt_a_theta = st.slider("A Theta (0 to π)", 0.0, float(np.pi), float(np.pi/4), key="t2_theta_a")
        pt_a_phi   = st.slider("A Phi (0 to 2π)", 0.0, float(2*np.pi), 0.0, key="t2_phi_a")
        pt_a_chi   = st.slider("A Saturation χ", 0.00001, 1.00000,
                               float(chi_global), 0.00001, format="%.5f", key="t2_chi_a")
        st.markdown("#### Point B (Arrival)")
        pt_b_theta = st.slider("B Theta (0 to π)", 0.0, float(np.pi), float(3*np.pi/4), key="t2_theta_b")
        pt_b_phi   = st.slider("B Phi (0 to 2π)", 0.0, float(2*np.pi), float(np.pi), key="t2_phi_b")
        pt_b_chi   = st.slider("B Saturation χ", 0.00001, 1.00000,
                               float(chi_global), 0.00001, format="%.5f", key="t2_chi_b")

        st.markdown("---")
        st.markdown("#### Ship Parameters")
        ship_mass   = st.number_input("Ship Mass (kg)", value=5000.0, min_value=1.0, max_value=1e9, step=100.0, format="%.1f")
        ship_radius = st.number_input("Ship Radius (m)", value=10.0, min_value=0.1, max_value=1000.0, step=0.5, format="%.1f")

        st.markdown("#### Transit Timeline")
        transit_pct = st.slider("Transit Position — A (0%) → B (100%)", 0, 100, 50,
                                help="Slide to move the UAP craft from Point A to Point B along the chord path.")

        ON_THRESH = 0.96
        st.session_state.wh_active = (pt_a_chi > ON_THRESH and pt_b_chi > ON_THRESH)
        is_wormhole = st.session_state.wh_active
        if is_wormhole:
            st.success("Wormhole threshold reached — deep core siphoning active (χ → 1).")
        else:
            st.info("Shallow sub-manifold chord — partial saturation transit.")

        sin_a = np.sin(pt_a_theta); cos_a = np.cos(pt_a_theta)
        sin_b = np.sin(pt_b_theta); cos_b = np.cos(pt_b_theta)
        dot_product = np.clip(sin_a*sin_b*np.cos(pt_a_phi-pt_b_phi)+cos_a*cos_b, -1.0, 1.0)
        surface_dist = univ_R * np.arccos(dot_product)

        # Edge markers track the sphere surface (scales with global chi)
        sphere_r_t2 = univ_R * (1.0 - chi_global * 0.5)
        xa_surf = sphere_r_t2*sin_a*np.cos(pt_a_phi)
        ya_surf = sphere_r_t2*sin_a*np.sin(pt_a_phi)
        za_surf = sphere_r_t2*cos_a
        xb_surf = sphere_r_t2*sin_b*np.cos(pt_b_phi)
        yb_surf = sphere_r_t2*sin_b*np.sin(pt_b_phi)
        zb_surf = sphere_r_t2*cos_b

        # Interior chord endpoints
        depth_a = 1.0 - pt_a_chi; depth_b = 1.0 - pt_b_chi
        xa = xa_surf*depth_a; ya = ya_surf*depth_a; za = za_surf*depth_a
        xb = xb_surf*depth_b; yb = yb_surf*depth_b; zb = zb_surf*depth_b
        wa = univ_R*pt_a_chi;  wb = univ_R*pt_b_chi
        chord_dist = np.sqrt((xa-xb)**2+(ya-yb)**2+(za-zb)**2+(wa-wb)**2)
        dist_saved = surface_dist - chord_dist

        # Transit fraction and craft position along FULL path:
        # surface A → interior A → interior B → surface B
        t_frac = transit_pct / 100.0

        # 3D segment lengths for path weighting
        seg1_len = np.sqrt((xa-xa_surf)**2 + (ya-ya_surf)**2 + (za-za_surf)**2)  # descent into A
        seg2_len = np.sqrt((xb-xa)**2 + (yb-ya)**2 + (zb-za)**2)                 # interior chord
        seg3_len = np.sqrt((xb_surf-xb)**2 + (yb_surf-yb)**2 + (zb_surf-zb)**2) # ascent out of B
        total_path_len = seg1_len + seg2_len + seg3_len + EPS

        # Fractional breakpoints along [0,1]
        f1 = seg1_len / total_path_len   # end of descent
        f2 = (seg1_len + seg2_len) / total_path_len  # end of chord

        if t_frac <= f1:
            # Descending from surface A into interior A
            local = t_frac / (f1 + EPS)
            craft_x = xa_surf + (xa - xa_surf)*local
            craft_y = ya_surf + (ya - ya_surf)*local
            craft_z = za_surf + (za - za_surf)*local
        elif t_frac <= f2:
            # Traveling interior chord A → B
            local = (t_frac - f1) / (f2 - f1 + EPS)
            craft_x = xa + (xb - xa)*local
            craft_y = ya + (yb - ya)*local
            craft_z = za + (zb - za)*local
        else:
            # Ascending from interior B to surface B
            local = (t_frac - f2) / (1.0 - f2 + EPS)
            craft_x = xb + (xb_surf - xb)*local
            craft_y = yb + (yb_surf - yb)*local
            craft_z = zb + (zb_surf - zb)*local

        chi_at_pos = pt_a_chi + (pt_b_chi - pt_a_chi)*t_frac

        # Heuristic transit velocity and time
        v_transit = chi_at_pos * C_LIGHT  # m/s — heuristic: velocity ∝ chi
        dist_traveled = chord_dist * t_frac
        t_elapsed = dist_traveled / (v_transit + EPS)

        # Heuristic energy: field maintenance + kinetic equivalent
        chi_avg = (pt_a_chi + pt_b_chi) / 2.0
        m_eff_craft = m_eff(ship_mass, chi_avg)
        E_field    = ship_mass * C_LIGHT**2 * chi_avg**2       # metric warping energy (heuristic)
        E_kinetic  = 0.5 * m_eff_craft * (chi_avg * C_LIGHT)**2  # kinetic (m_eff based)
        E_total    = E_field + E_kinetic

        st.markdown("---")
        st.markdown("#### Transit Telemetry")
        rows = [
            ("Surface Distance (S)",    format_distance(surface_dist)),
            ("Chord Distance (L)",       format_distance(chord_dist)),
            ("Distance Saved",           format_distance(max(0, dist_saved))),
            ("Distance Traveled",        format_distance(dist_traveled)),
            ("Elapsed Transit Time",     format_time(t_elapsed)),
            ("Total Est. Field Energy",  format_energy(E_total)),
        ]
        html_rows = "".join(
            f"<tr><td style='padding:4px 8px 4px 0; color:#aaa; white-space:nowrap'>{lbl}</td>"
            f"<td style='padding:4px 0 4px 8px; color:#fff; font-weight:bold; word-break:break-word'>{val}</td></tr>"
            for lbl, val in rows
        )
        st.markdown(
            f"<table style='width:100%; border-collapse:collapse; font-size:0.95em'>{html_rows}</table>",
            unsafe_allow_html=True
        )

        st.caption(f"χ at position: {chi_at_pos:.5f} | Heuristic transit velocity: {chi_at_pos*100:.3f}% c | m_eff: {m_eff_craft:,.2f} kg")
        st.caption("Energy heuristic: E_field = m·c²·χ² (metric warping) + E_kinetic (m_eff·v²/2). Order-of-magnitude estimate only — not a derived CBQG result.")

    with colB:
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down", key="hw_top"):  st.session_state.cam_t2_hw = dict(eye=dict(x=0,y=0,z=2.5))
        if c2.button("Side", key="hw_side"):     st.session_state.cam_t2_hw = dict(eye=dict(x=2.5,y=0,z=0.2))
        if c3.button("Isometric", key="hw_iso"): st.session_state.cam_t2_hw = dict(eye=dict(x=1.5,y=1.5,z=1.5))

        fig2 = go.Figure()
        fig2.add_trace(go.Surface(
            x=sphere_r_t2*np.cos(u)*np.sin(v),
            y=sphere_r_t2*np.sin(u)*np.sin(v),
            z=sphere_r_t2*np.cos(v),
            opacity=0.10, colorscale="Blues", showscale=False
        ))
        ca = "red" if pt_a_chi > 0.95 else "orange"
        cb = "red" if pt_b_chi > 0.95 else "orange"
        fig2.add_trace(go.Scatter3d(x=[xa_surf],y=[ya_surf],z=[za_surf], mode='markers+text',
                                    marker=dict(size=14,color=ca),
                                    text=["A (Departure)"], textposition="top center", name="Point A"))
        fig2.add_trace(go.Scatter3d(x=[xa_surf,xa],y=[ya_surf,ya],z=[za_surf,za],
                                    mode='lines', line=dict(color=ca,dash='dot',width=3), showlegend=False))
        fig2.add_trace(go.Scatter3d(x=[xb_surf],y=[yb_surf],z=[zb_surf], mode='markers+text',
                                    marker=dict(size=14,color=cb),
                                    text=["B (Arrival)"], textposition="top center", name="Point B"))
        fig2.add_trace(go.Scatter3d(x=[xb_surf,xb],y=[yb_surf,yb],z=[zb_surf,zb],
                                    mode='lines', line=dict(color=cb,dash='dot',width=3), showlegend=False))

        num_steps = 60
        # Full path: surface A → interior A → interior B → surface B
        # Build by concatenating the three segments
        def seg_pts(p0, p1, n):
            return np.linspace(p0, p1, n)
        n1 = max(2, int(num_steps * seg1_len / (total_path_len + EPS)))
        n2 = max(2, int(num_steps * seg2_len / (total_path_len + EPS)))
        n3 = max(2, num_steps - n1 - n2)
        tx = np.concatenate([seg_pts(xa_surf,xa,n1), seg_pts(xa,xb,n2)[1:], seg_pts(xb,xb_surf,n3)[1:]])
        ty = np.concatenate([seg_pts(ya_surf,ya,n1), seg_pts(ya,yb,n2)[1:], seg_pts(yb,yb_surf,n3)[1:]])
        tz = np.concatenate([seg_pts(za_surf,za,n1), seg_pts(za,zb,n2)[1:], seg_pts(zb,zb_surf,n3)[1:]])
        fig2.add_trace(go.Scatter3d(x=tx,y=ty,z=tz, mode='lines',
                                    line=dict(width=5, color='lime' if is_wormhole else 'yellow'),
                                    name="Core Wormhole" if is_wormhole else "Shallow Chord"))

        # UAP CRAFT — saucer-like appearance using two overlapping markers
        fig2.add_trace(go.Scatter3d(
            x=[craft_x], y=[craft_y], z=[craft_z],
            mode='markers',
            marker=dict(size=22, color='rgba(0,255,255,0.25)', symbol='circle'),
            showlegend=False, name="_ufo_rim"
        ))
        fig2.add_trace(go.Scatter3d(
            x=[craft_x], y=[craft_y], z=[craft_z],
            mode='markers+text',
            marker=dict(size=11, color='cyan', symbol='diamond',
                        line=dict(color='white', width=2)),
            text=[f"UAP  {transit_pct}%\n{format_time(t_elapsed)}"],
            textposition="top center",
            textfont=dict(color='cyan', size=10),
            name="UAP Craft"
        ))

        fig2.update_layout(
            title=f"4D Saturation Bridge | Global χ={chi_global:.5f} | Transit: {transit_pct}% | Time: {format_time(t_elapsed)}",
            height=600, showlegend=True, margin=dict(l=0,r=0,b=0,t=45),
            scene_camera=st.session_state.cam_t2_hw,
            scene=dict(xaxis=dict(showticklabels=False),
                       yaxis=dict(showticklabels=False),
                       zaxis=dict(showticklabels=False))
        )
        st.plotly_chart(fig2, use_container_width=True, key="highway_transit_plot")

    # ---- 2D TRANSIT CROSS-SECTION ----
    st.markdown("---")
    st.markdown("### 📊 Transit Cross-Section — UAP Moving from A → B")
    st.caption("Shows the UAP's path through the 4D manifold interior. Y-axis = metric depth (0 = core, 1 = surface). Slide the Transit Position above to move the UAP craft.")

    transit_x_arr = np.linspace(0, 1, 200)
    # Chi along the chord (linear interpolation)
    chi_path = pt_a_chi + (pt_b_chi - pt_a_chi)*transit_x_arr
    # Metric depth (1 = surface, 0 = at core)
    y_depth_path = 1.0 - chi_path

    craft_depth  = 1.0 - chi_at_pos
    craft_x_norm = t_frac

    # Time along path
    v_path = np.maximum(chi_path, 0.00001) * C_LIGHT
    dx = chord_dist / 200.0
    dt_path = dx / v_path
    t_cumul = np.cumsum(dt_path)

    fig_2d = go.Figure()
    # Universe surface line
    fig_2d.add_hline(y=1.0, line_color='rgba(100,180,255,0.5)', line_dash='dash')
    fig_2d.add_annotation(x=1.02, y=1.0, text="Surface (χ=0)", xref="paper", yref="y",
                           showarrow=False, font=dict(color='rgba(100,180,255,0.9)', size=11))
    # Universe core line
    fig_2d.add_hline(y=0.0, line_color='rgba(255,100,100,0.5)', line_dash='dash')
    fig_2d.add_annotation(x=1.02, y=0.0, text="Core (χ=1)", xref="paper", yref="y",
                           showarrow=False, font=dict(color='rgba(255,100,100,0.9)', size=11))

    # Chord path (filled)
    fig_2d.add_trace(go.Scatter(
        x=transit_x_arr, y=y_depth_path,
        fill='tozeroy', fillcolor='rgba(0,200,100,0.08)',
        line=dict(color='rgba(0,200,100,0.7)', width=2.5),
        name="Transit Chord Path"
    ))

    # Point A marker
    fig_2d.add_trace(go.Scatter(
        x=[0], y=[1.0 - pt_a_chi],
        mode='markers+text',
        marker=dict(size=16, color='orange', symbol='square'),
        text=["A"], textposition="top right",
        textfont=dict(color='orange', size=12),
        name="Point A"
    ))
    # Point B marker
    fig_2d.add_trace(go.Scatter(
        x=[1], y=[1.0 - pt_b_chi],
        mode='markers+text',
        marker=dict(size=16, color='orange', symbol='square'),
        text=["B"], textposition="top left",
        textfont=dict(color='orange', size=12),
        name="Point B"
    ))

    # UAP Craft on 2D chart — saucer using two markers
    fig_2d.add_trace(go.Scatter(
        x=[craft_x_norm], y=[craft_depth],
        mode='markers',
        marker=dict(size=32, color='rgba(0,255,255,0.2)', symbol='circle'),
        showlegend=False
    ))
    fig_2d.add_trace(go.Scatter(
        x=[craft_x_norm], y=[craft_depth],
        mode='markers+text',
        marker=dict(size=15, color='cyan', symbol='diamond',
                    line=dict(color='white', width=2)),
        text=[f"UAP  {transit_pct}%\n{format_time(t_elapsed)}\n{format_energy(E_total)}"],
        textposition="top center",
        textfont=dict(color='cyan', size=10),
        name="UAP Craft"
    ))

    fig_2d.update_layout(
        title=f"UAP Transit: A → B  |  Position: {transit_pct}%  |  Time elapsed: {format_time(t_elapsed)}  |  Energy: {format_energy(E_total)}",
        xaxis=dict(title="Transit Position (0% = Point A, 100% = Point B)", range=[-0.02, 1.12],
                   tickformat=".0%", tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                   ticktext=["A (0%)", "25%", "50%", "75%", "B (100%)"]),
        yaxis=dict(title="Metric Depth (1=Surface, 0=Core)", range=[-0.05, 1.1],
                   tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                   ticktext=["Core (χ=1)", "0.25", "0.50", "0.75", "Surface (χ=0)"]),
        height=350, margin=dict(l=0,r=100,b=40,t=45),
        **BG
    )
    st.plotly_chart(fig_2d, use_container_width=True, key="transit_2d_plot")

    # ---- NAVIGATIONAL MISSION PLANNER ----
    st.markdown("---")
    st.markdown("### 🗺️ Navigational Mission Planner")
    st.markdown("""
**How this works:**
- Enter a **Target Surface Distance (S)**: how far apart two points are measured along the 4D manifold surface (e.g., 1 light-year).
- Enter a **Desired Max Transit Span (L)**: the maximum chord distance you want to travel through the interior (must be less than S to save distance).
- The planner calculates the **minimum χ required** to compress the geodesic from S down to L.
- **Geometric strain** measures how close to C_max the metric must be pushed — higher strain means higher field energy.
- **All values update automatically** when you change the inputs.
""")
    colM1, colM2 = st.columns(2)
    with colM1:
        st.markdown("**Step 1: Set the mission parameters**")
        target_sf = st.number_input(
            "Target Surface Distance S (meters):",
            min_value=1e3, max_value=float(univ_R*np.pi),
            value=9.461e15, step=9.461e15,
            format="%.3e",
            help="The arc-length distance between two points on the manifold surface. 1 light-year = 9.461×10¹⁵ m."
        )
        target_ch = st.number_input(
            "Desired Max Transit Chord L (meters):",
            min_value=1e3, max_value=float(univ_R),
            value=9.461e14, step=9.461e13,
            format="%.3e",
            help="The maximum chord distance you're willing to travel through the 4D interior. Must be < S to achieve a shortcut."
        )
        st.caption("Tip: Use the step arrows to adjust values, or type directly and press Enter.")

    with colM2:
        st.markdown("**Step 2: Read the mission output**")
        if target_ch >= target_sf:
            st.warning("⚠️ Desired chord span ≥ surface distance. No saturation required — travel on the surface.")
            st.info("Set L < S to achieve a geometric shortcut through the manifold interior.")
        else:
            shortcut_ratio = target_ch / target_sf
            req_chi_raw = 1.0 - shortcut_ratio
            req_chi = float(clamp_chi(req_chi_raw))
            dist_save_plan = target_sf - target_ch
            strain_factor = 1.0 / (1.0 - req_chi + EPS) - 1.0
            m_eff_plan = m_eff(ship_mass, req_chi)
            v_plan = req_chi * C_LIGHT
            t_plan = target_ch / (v_plan + EPS)
            E_plan_field   = ship_mass * C_LIGHT**2 * req_chi**2
            E_plan_kinetic = 0.5 * m_eff_plan * v_plan**2
            E_plan_total   = E_plan_field + E_plan_kinetic

            st.metric("Minimum Required Saturation χ", f"{req_chi:.5f}")
            st.progress(min(1.0, req_chi), text=f"χ = {req_chi:.5f} / 1.00000")
            st.metric("Distance Saved", format_distance(dist_save_plan),
                      delta=f"{(1-shortcut_ratio)*100:.2f}% shorter than surface path")
            st.metric("Geometric Strain Factor", f"{strain_factor:,.2f}×",
                      help="How much more intense the metric field is compared to flat space. Diverges as χ→1.")

            with st.expander("📋 Full Mission Report"):
                st.markdown(f"""
| Parameter | Value |
|---|---|
| Surface Distance (S) | {format_distance(target_sf)} |
| Chord Distance (L) | {format_distance(target_ch)} |
| Shortcut Ratio (L/S) | {shortcut_ratio:.5f} |
| Required χ | {req_chi:.5f} |
| Geometric Strain | {strain_factor:,.2f}× |
| Effective Ship Mass (m_eff) | {m_eff_plan:,.2f} kg |
| Transit Velocity (heuristic) | {req_chi*100:.5f}% c |
| Estimated Transit Time | {format_time(t_plan)} |
| Est. Field Energy | {format_energy(E_plan_field)} |
| Est. Kinetic Energy | {format_energy(E_plan_kinetic)} |
| Est. Total Energy | {format_energy(E_plan_total)} |
""")
                st.caption("Heuristic estimates. Transit velocity = χ × c (not a derived CBQG result). Energy scaling = m·c²·χ². Order-of-magnitude guidance only.")

    st.markdown("---")
    st.markdown(f"**Global χ = {chi_global:.5f}** | m_eff = {m_eff(ship_mass, chi_global):,.3f} kg | D_msd = {d_msd(ship_radius, chi_global):,.3f} m")

# ==================== TAB 3 ====================
with t3:
    st.subheader("Addendum B: Military UAP Sensor Correlation")
    st.warning("⚠️ SPECULATIVE ENGINEERING: The following applies CBQG heuristic physics to reverse-engineer reported UAP kinematics. Math core stays Appendix-B. Real-world attribution is strictly speculative.")
    st.markdown("""
When radar systems track anomalous craft, they report kinematics irreconcilable with General Relativity.
Under CBQG, if a craft accumulates localized spacetime tight to its hull limit (χ → 1),
**acceleration increases without bound under finite force (via m_eff → 0)**, severing inertial coupling from classical reality.
""")

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
        st.markdown(f"**m_eff = {m0:,.0f} × √(1 - {active_chi:.5f}²) = <span style='color:lime'>{m_e:,.3f} kg</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-m_e/(m0+EPS))))
        st.info(f"Apparent radial acceleration proxy: {a_test:,.0f} m/s² under 10kN thrust (illustrative).")
        st.markdown("### 3. Minimum Standoff — Nimitz & Roosevelt")
        d_m = d_msd(10.0, active_chi)
        st.markdown(f"**D_msd = 10 × [{active_chi:.5f}/(1-{active_chi:.5f}+ε)]^(1/3) = <span style='color:lime'>{d_m:,.3f} m</span>**", unsafe_allow_html=True)
    with col2:
        st.markdown("### 2. No Sonic Boom — Nimitz 2004")
        f_d = f_drag(1000.0, active_chi)
        st.markdown(f"**F_drag = 1000 × √(1-{active_chi:.5f}²) = <span style='color:lime'>{f_d:,.3f} N</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-f_d/1000.0)))
        st.markdown("### 4. EM Damping — Malmstrom 1967")
        v_e = v_eff(V_electronics, active_chi)
        st.markdown(f"**V_eff = {V_electronics} × (1-{active_chi:.5f}) = <span style='color:red'>{v_e:,.3f} V</span>**", unsafe_allow_html=True)
        if active_chi > 0.90:
            st.error("Critical voltage collapse. Avionics/Warhead logic circuits failing (heuristic).")

    st.markdown("---")
    st.markdown("### UAP Sensor Trajectory Analysis")
    st.caption("""
**Reading this chart:** The X-axis represents a simulated radar tracking window divided into 10 equal time segments.
The UAP operates under standard kinematics at segments 0–2 and 8–10 (baseline, dotted white line).
At segment 2, the χ-Drive engages (green zone): m_eff → 0, causing a sudden apparent acceleration spike visible on the radar return.
At segment 8, the craft decelerates back to conventional kinematics.
This illustrates the **radar signature** of a CBQG-saturation maneuver — not a calibrated real-world timeline.
""")

    time_arr  = np.linspace(0, 10, 100)
    traj_base = [base_accel]*20
    traj_sat  = [a_test]*60
    traj_end  = [base_accel]*20
    traj      = traj_base + traj_sat + traj_end

    # Build fig3 — with or without UAP animation overlay
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=time_arr, y=[base_accel]*100,
                              name=f"Conventional kinematics ({base_accel:,.1f} m/s²)",
                              line=dict(color='white', dash='dot', width=2)))
    fig3.add_trace(go.Scatter(x=time_arr, y=traj,
                              name=f"CBQG χ-Drive engaged (χ={active_chi:.5f})",
                              line=dict(color='lime', width=3)))
    fig3.add_vrect(x0=2, x1=8, fillcolor="rgba(0,255,150,0.06)", line_width=0,
                   annotation_text="χ-Drive Engaged", annotation_position="top right",
                   annotation_font=dict(color='rgba(0,255,150,0.8)', size=10))

    if st.session_state.uap_demo_active:
        # Add UAP craft trace (index 2) and trail trace (index 3)
        fig3.add_trace(go.Scatter(
            x=[time_arr[0]], y=[traj[0]],
            mode='markers',
            marker=dict(size=26, color='rgba(0,255,255,0.25)', symbol='circle'),
            showlegend=False, name="_ufo_rim"
        ))
        fig3.add_trace(go.Scatter(
            x=[time_arr[0]], y=[traj[0]],
            mode='markers+text',
            marker=dict(size=13, color='cyan', symbol='diamond',
                        line=dict(color='white', width=2)),
            text=["UAP"], textposition="top center",
            textfont=dict(color='cyan', size=11),
            name="UAP Craft"
        ))
        fig3.add_trace(go.Scatter(
            x=[time_arr[0]], y=[traj[0]],
            mode='lines', line=dict(color='rgba(0,255,255,0.4)', width=2, dash='dot'),
            showlegend=False, name="_trail"
        ))

        demo_frames = []
        for i in range(0, len(time_arr), 2):
            demo_frames.append(go.Frame(
                data=[
                    go.Scatter(x=[time_arr[i]], y=[traj[i]], mode='markers',
                               marker=dict(size=26, color='rgba(0,255,255,0.25)', symbol='circle')),
                    go.Scatter(x=[time_arr[i]], y=[traj[i]], mode='markers+text',
                               marker=dict(size=13, color='cyan', symbol='diamond',
                                           line=dict(color='white', width=2)),
                               text=["UAP"], textposition="top center",
                               textfont=dict(color='cyan', size=11)),
                    go.Scatter(x=time_arr[:i+1], y=traj[:i+1], mode='lines',
                               line=dict(color='rgba(0,255,255,0.4)', width=2, dash='dot'))
                ],
                traces=[2, 3, 4], name=f"df{i}"
            ))
        fig3.frames = demo_frames
        fig3.update_layout(
            updatemenus=[dict(
                type="buttons", direction="left", showactive=False,
                active=-1,
                y=-0.20, yanchor="top", x=0.5, xanchor="center",
                bgcolor='rgba(40,40,80,1)', bordercolor='rgba(120,120,190,1)',
                font=dict(color='rgba(210,210,255,1)'), pad={"t": 8, "r": 8},
                buttons=[
                    dict(label="▶ PLAY FLIGHT",
                         method="animate",
                         args=[None, dict(frame=dict(duration=80, redraw=True),
                                          transition=dict(duration=0),
                                          fromcurrent=False, mode="immediate")]),
                    dict(label="⏹ STOP",
                         method="animate",
                         args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False))])
                ]
            )],
            margin=dict(l=0, r=0, b=130, t=45)
        )

    fig3.update_layout(
        title=f"Apparent Radar Acceleration (Log Scale) | χ={active_chi:.5f} | a_CBQG={a_test:,.0f} m/s²",
        height=380,
        xaxis_title="Radar Tracking Window (10 segments — see caption)",
        yaxis_title="Apparent Kinematics (m/s²)", yaxis_type="log",
        **BG
    )
    if not st.session_state.uap_demo_active:
        fig3.update_layout(margin=dict(l=0, r=0, b=0, t=45))

    st.plotly_chart(fig3, use_container_width=True, key="dynamic_uap_transit_plot")

    # Demo toggle buttons
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        if st.button("🛸 ENGAGE UAP FLIGHT DEMO", key="demo_on",
                     help="Animates a UAP craft flying along the radar trajectory on the chart above."):
            st.session_state.uap_demo_active = True; st.rerun()
    with c_d2:
        if st.button("⏹ END FLIGHT DEMO", key="demo_off"):
            st.session_state.uap_demo_active = False; st.rerun()

    # ---- TRANS-MEDIUM TRAVEL ----
    st.markdown("---")
    st.markdown("### 💧 Trans-Medium Travel — How UAPs Enter Water Without a Splash")
    st.markdown("""
One of the most documented and inexplicable behaviors of UAPs is seamless **trans-medium transit** —
entering and exiting water at high speed without generating a wake, cavitation, or surface disturbance.
Under CBQG, this is a direct consequence of the curvature ceiling:

**As χ → 1, the craft's effective cross-section → 0.**

The effective interaction radius with any medium (air, water, solid material) scales as:
> **σ_eff = σ_0 × √(1 - χ²)**

At χ = 0: standard cross-section — normal physics applies.
At χ → 1: σ_eff → 0 — the craft geometrically decouples from the medium. Water molecules have no geometry to interact with.
No displacement. No surface break. No wake. No cavitation. The craft does not *push through* the water — it passes *through the geometry* of the water.
""")

    chi_arr_tm = np.linspace(0.0, 0.9999, 200)
    sigma_eff   = np.sqrt(np.maximum(0.0, 1.0 - chi_arr_tm**2))

    fig_tm = go.Figure()
    fig_tm.add_trace(go.Scatter(x=chi_arr_tm, y=sigma_eff, fill='tozeroy',
                                fillcolor='rgba(0,150,255,0.12)',
                                line=dict(color='rgba(0,180,255,1)', width=3),
                                name="Effective Cross-Section (σ_eff)"))
    fig_tm.add_vline(x=float(active_chi), line_dash="dash", line_color="cyan",
                     annotation_text=f"  Current χ = {active_chi:.5f}\n  σ_eff = {np.sqrt(max(0,1-active_chi**2)):.5f}",
                     annotation_font=dict(color="cyan", size=11))
    fig_tm.add_hrect(y0=0.0, y1=0.05, fillcolor="rgba(0,255,100,0.08)", line_width=0,
                     annotation_text="Trans-Medium Zone (σ_eff ≈ 0)", annotation_position="bottom right",
                     annotation_font=dict(color="rgba(0,255,100,0.8)", size=10))
    fig_tm.update_layout(
        title="Trans-Medium Effective Cross-Section vs Saturation χ",
        xaxis=dict(title="Saturation χ", range=[0, 1.0]),
        yaxis=dict(title="σ_eff / σ_0  (normalized cross-section)", range=[-0.02, 1.05]),
        height=280, margin=dict(l=0,r=0,b=0,t=40), **BG
    )
    st.plotly_chart(fig_tm, use_container_width=True, key="transmedium_plot")
    st.caption("σ_eff = σ_0 × √(1-χ²) — same Lorentz-like structure as m_eff. At χ≈1, the craft's effective interaction cross-section with any medium collapses to zero. Heuristic application of CBQG Appendix-B scaling.")

    st.markdown("---")
    st.markdown("### ☄️ Re-entry Protocol Simulator")
    colR1, colR2 = st.columns(2)
    with colR1:
        sim_k = st.slider("Re-entry Damping Factor (k)", 0.1, 15.0, 3.0, 0.1, key="k_slider")
        st.info("High k: fast inertial reconnection, high G-force risk. Low k: slow decay, survivable re-entry (heuristic).")
    with colR2:
        peak_g = 50.0 * sim_k * active_chi
        st.metric("Peak Inertial Whiplash", f"{peak_g:.2f} Gs")
        st.caption("Heuristic order-of-magnitude estimate only.")
        if peak_g > 50:        st.error("STRUCTURAL FAILURE: >50G limit exceeded.")
        elif active_chi <= 0.05: st.success("CRAFT AT NORMAL INERTIA.")
        else:                    st.success("RE-ENTRY SURVIVABLE.")
        t_arr_re = np.linspace(0, 5, 50)
        chi_t = chi_decay(active_chi, sim_k, t_arr_re)
        fig_re = go.Figure(go.Scatter(x=t_arr_re, y=chi_t, fill='tozeroy', line=dict(color='orange')))
        fig_re.update_layout(title="Phase Decay Profile", height=200,
                             margin=dict(l=0,r=0,b=0,t=30),
                             yaxis_title="χ(t)", xaxis_title="Seconds", **BG)
        st.plotly_chart(fig_re, use_container_width=True, key="reentry_chart")

# ==================== TAB 4 ====================
with t4:
    st.subheader("Theory & Axioms")

    st.markdown("### 0. Unified Scalar Simplification (Engine Constraint)")
    st.markdown("**Explanation:** True CBQG is a covariant tensor formulation driven by the invariant curvature limits of R_abcd R^abcd. For this simulator, the tensor field is simplified into a single master scalar (χ) acting pedagogically across curvature magnitude, spatial depth coordinate, and mass modifier simultaneously. All heuristic engineering equations in Tab 3 are extensions beyond the published v10.5 framework.")

    st.markdown("### 1. Metric Saturation Invariant (χ)")
    st.code("χ = C / C_max ≤ 1")
    st.markdown("**Explanation:** Spacetime curvature C cannot exceed C_max. χ tracks what fraction of that capacity is exhausted. χ=0: flat, maximum expansion. χ=1: geometric saturation — the Big Bounce.")

    st.markdown("### 2. Effective Mass Negation (m_eff)")
    st.code("m_eff = m_0 √(1 - χ²)")
    st.markdown("**Explanation:** As χ → 1, the craft's inertial connection to the universe evaporates toward zero, permitting arbitrarily large velocity vectors under finite applied force. Same mathematical structure as the Lorentz factor, driven by geometric saturation rather than velocity.")

    st.markdown("### 3. Aerodynamic Drag Suppression (F_drag)")
    st.code("F_drag = F_0 √(1 - χ²)")
    st.markdown("**Explanation:** As the local metric saturates, fluid interaction collapses with the same scaling as m_eff. The atmosphere slides around the saturated metric boundary rather than compressing, eliminating sonic booms and aerodynamic heating simultaneously.")

    st.markdown("### 4. Minimum Standoff Distance (D_msd)")
    st.code("D_msd = R [χ / (1 - χ + ε)]^(1/3)")
    st.markdown("**Explanation:** A saturating craft projects a curvature gradient that repels unsaturated external mass. ε=10⁻⁹ prevents singular divergence at χ=1. At high χ this buffer grows rapidly, producing the 'mirroring' behavior reported in UAP encounters (heuristic application).")

    st.markdown("### 5. Electromagnetic Damping (V_eff)")
    st.code("V_eff = V_0 (1 - χ)")
    st.markdown("**Explanation:** Vacuum impedance scales linearly with saturation. As χ → 1, the geometric dielectric barrier bleeds voltage from surrounding electronics, driving active systems toward shutdown. Strictly linear per Appendix B.")

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
    st.markdown("**Explanation:** Euclidean chord through the 4D interior connecting two saturated surface points. Requires the explicit w coordinate (Eq. 8). Visualization embedding approximation — true CBQG geodesic paths use the full covariant tensor formulation. Shortcut effect is real; magnitude is an order-of-magnitude heuristic.")

    st.markdown("### 10. Dark Energy Dissipation (Λ(t))")
    st.code("Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)")
    st.markdown("**Explanation:** Derived in CBQG v10 (pages 146–173) as a necessary consequence of total constraint preservation under quantum information bounds. Variables are Planck-normalized (Λ̄ ≡ Λℓ²_P, t̄ ≡ t/t_P). Excludes eternal de Sitter expansion and generates the complete cosmic life cycle. Dark energy crossover time ~10^315 years (CBQG v10, pp. 164–165).")

    st.markdown("### 11. Trans-Medium Effective Cross-Section (σ_eff)")
    st.code("σ_eff = σ_0 × √(1 - χ²)")
    st.markdown("**Explanation:** The effective interaction cross-section of a saturated craft with any medium (air, water, solid). Follows the same Lorentz-like scaling as m_eff. As χ → 1, σ_eff → 0: the craft geometrically decouples from the medium, enabling trans-medium transit (air→water→air) without displacing material or generating a wake (heuristic application).")

st.caption("CBQG v10.5.1 © Dr. Anthony Omar Peña, D.O. — All rights reserved.")
