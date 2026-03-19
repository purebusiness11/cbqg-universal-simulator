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

# ====================== SESSION STATE & CAMERA MATRICES ======================
if "chi_global" not in st.session_state:
    st.session_state.chi_global = 0.50
if "wh_active" not in st.session_state:
    st.session_state.wh_active = False
if "cam_t1_gw" not in st.session_state:
    st.session_state.cam_t1_gw = dict(eye=dict(x=1.5, y=1.5, z=1.5))
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
chi_global = st.sidebar.slider("Global Saturation χ", 0.001, 1.000, st.session_state.get("chi_global", 0.50), 0.01)
st.session_state.chi_global = chi_global

if chi_global <= 0.05:
    st.sidebar.success("χ ≈ 0 — Maximum Expansion: Universe at lowest curvature. Dark energy dominant. Geometry approaches flat baseline.")
elif chi_global >= 0.95:
    st.sidebar.error("χ ≈ 1 — GEOMETRIC SATURATION: C_max reached. Big Bounce imminent. Singularities forbidden by constraint.")
else:
    st.sidebar.success("Engine Engaged: All kinetics bonded interactively to Global χ.")

univ_R = st.sidebar.number_input("Universal 4D Radius (R, meters)", 1e10, 1e30, 1e22, step=1e20)
st.sidebar.caption("Determines baseline universal scale. Exponentially drives Minimum Standoff (D_msd) and exactly dictates the 4D Highway Traversable Core Volume (V_core).")

# ====================== CBQG THEORETICAL CORE ======================
EPS = 1e-9

def clamp_chi(chi):
    return np.clip(chi, 0.0, 1.0)

def m_eff(m0, chi):
    c = clamp_chi(chi)
    return m0 * np.sqrt(max(0.0, 1.0 - c**2))

def f_drag(f0, chi):
    c = clamp_chi(chi)
    return f0 * np.sqrt(max(0.0, 1.0 - c**2))

def d_msd(r, chi):
    c = clamp_chi(chi)
    return r * (c / (1.0 - c + EPS))**(1.0/3.0)

def v_core(R, chi):
    c = clamp_chi(chi)
    return 0.5 * np.pi**2 * R**4 * (1.0 - np.sqrt(max(0.0, 1.0 - c**2)))

def chi_decay(chi_init, k, t):
    return chi_init * np.exp(-k * t)

def v_eff(v0, chi):
    c = clamp_chi(chi)
    return v0 * (1.0 - c)

def lambda_cbqg(L0, t):
    return L0 / (1.0 + L0**3 * t / np.pi)**(1.0/3.0)

def format_distance(m):
    ly = 9.461e15
    if m >= ly:       return f"{m / ly:,.2f} Light Years"
    elif m >= 1e15:   return f"{m / 1e15:,.2f} Trillion km"
    elif m >= 1e12:   return f"{m / 1e12:,.2f} Billion km"
    elif m >= 1e9:    return f"{m / 1e9:,.2f} Million km"
    elif m >= 1000:   return f"{m / 1000:,.2f} km"
    else:             return f"{m:,.2f} m"

U_RES, V_RES = 30j, 30j
u, v = np.mgrid[0:2*np.pi:U_RES, 0:np.pi:V_RES]

def rippled_sphere(rad, chi_val, u_grid, v_grid):
    ripple_amp = chi_val * 0.12 * rad
    ripple = ripple_amp * (np.sin(6*u_grid)*np.sin(4*v_grid) + 0.5*np.sin(10*u_grid)*np.sin(8*v_grid))
    r = rad + ripple
    return r*np.cos(u_grid)*np.sin(v_grid), r*np.sin(u_grid)*np.sin(v_grid), r*np.cos(v_grid)

# ====================== DYNAMIC FIG 1 BUILDER ======================
def build_fig1(chi_val):
    rho = np.linspace(0, 1.0, 500)
    C_max_display = 1.0

    # GR: diverges near rho=1
    gr_curve_rho = rho[rho < 0.92]
    gr_curve_C   = gr_curve_rho / (1.0 - gr_curve_rho + 0.02)
    gr_curve_C   = np.clip(gr_curve_C, 0, 1.55)

    # CBQG: saturates at C_max via tanh
    cbqg_C = C_max_display * np.tanh(rho * 3.5)

    # Current chi marker on CBQG curve
    chi_clamped = float(np.clip(chi_val, 0.001, 0.999))
    rho_marker  = float(np.arctanh(chi_clamped) / 3.5)
    C_marker    = float(C_max_display * np.tanh(rho_marker * 3.5))

    fig = go.Figure()

    # Forbidden zone
    fig.add_hrect(
        y0=C_max_display, y1=1.62,
        fillcolor="rgba(220,80,80,0.18)", line_width=0,
        annotation_text="  Forbidden (χ > 1)",
        annotation_position="top left",
        annotation_font=dict(color="rgba(220,100,100,1)", size=13)
    )

    # C_max dashed line
    fig.add_hline(
        y=C_max_display,
        line_dash="dash", line_color="rgba(200,200,200,0.7)", line_width=2,
    )
    fig.add_annotation(
        x=1.01, y=C_max_display,
        text="C_max (χ = 1)<br><i>Quantum requirement:<br>finite state density</i>",
        showarrow=False, xref="paper", yref="y",
        xanchor="left",
        font=dict(color="rgba(200,200,200,0.9)", size=10)
    )

    # GR curve (blue)
    fig.add_trace(go.Scatter(
        x=gr_curve_rho, y=gr_curve_C,
        mode='lines', name='General Relativity',
        line=dict(color='rgba(110,170,255,1)', width=3)
    ))
    # GR spike to infinity
    rho_spike = np.linspace(0.905, 0.915, 30)
    C_spike   = np.clip(rho_spike / (1.0 - rho_spike + 0.001), 0, 1.58)
    fig.add_trace(go.Scatter(
        x=rho_spike, y=C_spike,
        mode='lines', showlegend=False,
        line=dict(color='rgba(110,170,255,1)', width=3)
    ))
    fig.add_annotation(
        x=0.915, y=1.54,
        ax=0, ay=-30,
        xref="x", yref="y", axref="pixel", ayref="pixel",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor='rgba(110,170,255,1)', arrowwidth=3,
        text="<b>∞</b>", font=dict(size=18, color='rgba(110,170,255,1)')
    )
    fig.add_annotation(
        x=0.955, y=1.44,
        text="GR–QM<br>Incompatibility",
        showarrow=False, xref="x", yref="y",
        font=dict(size=11, color='rgba(110,170,255,0.85)')
    )

    # CBQG saturation curve (gold)
    fig.add_trace(go.Scatter(
        x=rho, y=cbqg_C,
        mode='lines', name='CBQG',
        line=dict(color='rgba(215,175,30,1)', width=3.5)
    ))

    # Saturation label
    fig.add_annotation(
        x=0.68, y=C_max_display - 0.035,
        text="← Saturation", showarrow=False,
        font=dict(size=11, color='rgba(215,175,30,0.85)'), xref="x", yref="y"
    )
    fig.add_annotation(
        x=0.80, y=C_max_display - 0.11,
        text="Geometric<br>Saturation",
        showarrow=False, font=dict(size=12, color='rgba(215,175,30,0.75)'),
        xref="x", yref="y"
    )

    # Dynamic chi marker (white dot)
    fig.add_trace(go.Scatter(
        x=[rho_marker], y=[C_marker],
        mode='markers+text',
        name=f'Current χ = {chi_val:.3f}',
        marker=dict(size=14, color='white', symbol='circle',
                    line=dict(color='rgba(215,175,30,1)', width=2.5)),
        text=[f"  χ = {chi_val:.3f}"],
        textposition="middle right",
        textfont=dict(color='white', size=12)
    ))

    # Vertical dashed line from marker to C_max ceiling
    fig.add_shape(
        type="line",
        x0=rho_marker, x1=rho_marker,
        y0=C_marker,   y1=C_max_display,
        line=dict(color="rgba(255,255,255,0.25)", dash="dot", width=1.5),
        xref="x", yref="y"
    )

    fig.update_layout(
        title=dict(
            text=f"CBQG Fig. 1 — Curvature Saturation vs GR Divergence  (χ = {chi_val:.3f})",
            font=dict(size=14, color='white')
        ),
        xaxis=dict(
            title="Energy Density (ρ) →",
            range=[0, 1.05],
            showgrid=False,
            zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
            tickvals=[], color='white'
        ),
        yaxis=dict(
            title="Spacetime Curvature (C) →",
            range=[0, 1.62],
            showgrid=False,
            zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
            tickvals=[0, C_max_display],
            ticktext=["0", "C_max"],
            color='white'
        ),
        plot_bgcolor='rgba(12,12,22,1)',
        paper_bgcolor='rgba(12,12,22,1)',
        font=dict(color='white'),
        legend=dict(
            x=0.02, y=0.97,
            bgcolor='rgba(0,0,0,0.45)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(color='white')
        ),
        height=430,
        margin=dict(l=65, r=130, b=55, t=55)
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

Alongside the invariant speed of light (c) and the quantum of action (ℏ), formalized by the Geometric Saturation Invariant **χ = C/C_max**, where **C = √(R_abcd R^abcd)** is the invariant curvature magnitude, the square root of the Kretschmann scalar. C is defined this way deliberately: it carries the same physical dimensions as curvature, making C_max a direct geometric ceiling, with χ defined on [0,1] for all physical spacetimes.
""")
    st.info("⚠️ **Structural Engine Disclaimer:** True CBQG incorporates the covariant evolution of the R_abcd tensor field. In this simulator, χ compresses the 4D saturation magnitude into a master 1D scalar to visually drive macroscopic reactions.")
    st.markdown("<h3 style='color:red;'>🚨 χ=1 IS ABSOLUTE GEOMETRIC SATURATION (C_max) 🚨</h3>", unsafe_allow_html=True)

    # --- DYNAMIC FIG 1 ---
    st.markdown("---")
    st.markdown("### 📈 CBQG Fig. 1 — Curvature Saturation vs GR Divergence (Live)")
    st.markdown("""
The **white dot** tracks your current **χ** on the CBQG saturation curve in real time. As χ → 1, CBQG saturates at C_max while GR diverges to infinity. The red zone above C_max is **geometrically forbidden** by C ≤ C_max. At low curvature both theories are identical — CBQG recovers GR exactly in the weak-field limit (χ ≈ 0).
""")
    st.plotly_chart(build_fig1(chi_global), use_container_width=True, key="fig1_dynamic")
    st.caption("Fig. 1 is intentionally schematic. The linear scale communicates the qualitative contrast between unbounded GR curvature growth and CBQG geometric saturation. A fully quantitative plot is future work (CBQG v10.5, p. 244).")

    # --- LIFE CYCLE ---
    st.markdown("---")
    st.markdown("### 🔄 CBQG Universe Life Cycle (v10.2 Derivation)")
    st.markdown("""
The CBQG framework derives a complete **nonsingular** cosmic history governed by constraint closure:

**Bounce → Expansion → Dark Energy Dissipation → Turnaround* → Contraction → Bounce**

This cycle emerges directly from C ≤ C_max with no new axioms. The dark energy cosmological constant decays dynamically (CBQG v10, Planck-normalized form):

**Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)**, implying dΛ/dt < 0.

*Turnaround requires at least one of: (1) closed FRW geometry k>0, (2) CBQG global constraint enforcing compact spatial slices, (3) Λ(t)→0 combined with a sign-reversal mechanism, or (4) a boundary condition forbidding asymptotic Minkowski escape.*
""")

    with st.expander("📅 Cosmic Life Cycle Timing (CBQG v10, pages 164–165)"):
        st.markdown("""
| Milestone | Timescale | Source |
|---|---|---|
| Dark energy crossover (Λ dissipation ends acceleration) | ~10^315 years | CBQG v10, pp. 164–165 (derived) |
| Turnaround begins (H → 0, contraction onset) | > 10^315 years | Derived constraint |
| Curvature-bounded Bounce (heuristic extrapolation) | ~10^400 – 10^500 years | CBQG v10 heuristic extension |

The bounce itself is fully nonsingular: the entire observable universe compresses to ~2.3 proton widths at total energy ≈ 1.35 × 10^70 J, reversing within one Planck time. The bounce range 10^400–10^500 years is a heuristic extrapolation, not a derived result.
""")

    st.markdown("### Λ(t) Dissipation — CBQG v10 (Planck-Normalized Units)")
    L0_val = st.slider("Initial Λ₀ (Planck-normalized)", 0.01, 2.0, 0.5, 0.01)
    t_plot = np.linspace(0, 20, 300)
    L_plot = lambda_cbqg(L0_val, t_plot)
    fig_L = go.Figure()
    fig_L.add_trace(go.Scatter(x=t_plot, y=L_plot, line=dict(color='gold', width=3), name="Λ(t) — CBQG"))
    fig_L.add_hline(y=0, line_dash="dot", line_color="red", annotation_text="Λ → 0 (crossover threshold)")
    fig_L.update_layout(
        title="Λ(t) = Λ₀ / (1 + Λ₀³t/π)^(1/3)",
        xaxis_title="t (Planck-normalized)", yaxis_title="Λ(t)",
        height=300, margin=dict(l=0, r=0, b=0, t=40),
        plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)', font=dict(color='white')
    )
    st.plotly_chart(fig_L, use_container_width=True, key="lambda_plot")

    st.markdown("---")
    view_mode = st.radio("Select 3D Reality Representation:", ["3D Spacetime (Gravity Well)", "4D Hypersphere (Life Cycle Animation)"], horizontal=True)

    if view_mode == "3D Spacetime (Gravity Well)":
        st.write("Visualizing a 3D gravitational well where the depth is strictly bounded by C_max (χ=1).")
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="gw_t"): st.session_state.cam_t1_gw = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="gw_s"): st.session_state.cam_t1_gw = dict(eye=dict(x=2.5, y=0, z=0))
        if c3.button("Isometric View", key="gw_i"): st.session_state.cam_t1_gw = dict(eye=dict(x=1.5, y=1.5, z=1.5))

        x = np.linspace(-5, 5, 40); y = np.linspace(-5, 5, 40)
        xx, yy = np.meshgrid(x, y)
        r_grid = np.sqrt(xx**2 + yy**2)
        zz = np.maximum(-1.0/(r_grid+0.1), -3.0*chi_global)

        fig3d = go.Figure(data=[go.Surface(z=zz, x=xx, y=yy, colorscale='Viridis', opacity=0.9, showscale=False)])
        fig3d.add_trace(go.Surface(z=np.full_like(zz,-3.0), x=xx, y=yy, showscale=False, opacity=0.3, colorscale='Reds', name='C_max floor'))
        fig3d.update_layout(
            title="3D Spacetime: Curvature bounded by χ=1 (C_max)",
            margin=dict(l=0,r=0,b=0,t=40), scene_camera=st.session_state.cam_t1_gw,
            scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (Curvature Depth)',
                       zaxis=dict(range=[-4,0]),
                       annotations=[dict(showarrow=False, x=0, y=0, z=-3.0,
                                         text="GEOMETRIC FLOOR (C_max)", xanchor="center",
                                         font=dict(color="red", size=14))])
        )
        st.plotly_chart(fig3d, use_container_width=True, key="gravity_well_plot")
        st.caption("Visualization only: not a direct solution of the CBQG curvature invariant.")

    else:
        st.markdown("""
**χ = 0** → Maximum expansion, perfectly smooth sphere.
**χ → 1** → Contraction, curvature ripples amplify.
**χ = 1** → Big Bounce. Singularity forbidden. Animation cycles χ: 0 → 1 → 0 continuously.
""")
        scale_mode = st.radio("Viewport Scaling", ["Visual (Linear Drop)", "Physical (Nonlinear Metric Compression)"], horizontal=True)
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="sph_t"): st.session_state.cam_t1_sph = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="sph_s"): st.session_state.cam_t1_sph = dict(eye=dict(x=2.5, y=0, z=0))
        if c3.button("Isometric View", key="sph_i"): st.session_state.cam_t1_sph = dict(eye=dict(x=1.5, y=1.5, z=1.5))

        if chi_global > 0.95:
            st.error("BIG BOUNCE — r_min floor engaged (χ limits reach C_max)")

        max_bound = univ_R * 1.1
        chi_cycle = np.concatenate([np.linspace(0.01,0.999,25), np.linspace(0.999,0.01,25)])

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
            else:              phase = f"χ = {c_val:.3f} | ⚡ BIG BOUNCE — C_max saturation"
            anim_frames.append(go.Frame(
                data=[go.Surface(x=sx, y=sy, z=sz, opacity=0.85, colorscale="Plasma", showscale=False)],
                name=f"frame_{i}",
                layout=go.Layout(title_text=f"4D Hypersphere Life Cycle — {phase}")
            ))
        fig_life.frames = anim_frames

        fig_life.update_layout(
            title=f"4D Hypersphere Life Cycle — χ = {chi_global:.3f}",
            height=560, margin=dict(l=0,r=0,b=0,t=50),
            scene_camera=st.session_state.cam_t1_sph,
            scene=dict(
                xaxis=dict(range=[-max_bound,max_bound], title='X (m)'),
                yaxis=dict(range=[-max_bound,max_bound], title='Y (m)'),
                zaxis=dict(range=[-max_bound,max_bound], title='Z (m)'),
                aspectmode='cube'
            ),
            updatemenus=[dict(
                type="buttons", showactive=False,
                y=1.08, x=0.0, xanchor="left", yanchor="bottom",
                buttons=[
                    dict(label="▶ PLAY LIFE CYCLE (χ: 0 → 1 → 0, repeating)", method="animate",
                         args=[None, dict(frame=dict(duration=120, redraw=True),
                                          transition=dict(duration=0), fromcurrent=False,
                                          mode="immediate", loop=True)]),
                    dict(label="⏹ STOP", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ]
            )],
            sliders=[dict(
                steps=[dict(args=[[f"frame_{i}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                            label=f"χ={chi_cycle[i]:.2f}", method="animate") for i in range(len(chi_cycle))],
                transition=dict(duration=0), x=0, y=0,
                currentvalue=dict(prefix="Life Cycle Frame: ", visible=True, xanchor="center"), len=1.0
            )]
        )
        st.plotly_chart(fig_life, use_container_width=True, key="native_plotly_lifecycle")
        st.caption("χ=0: perfectly smooth sphere (maximum expansion). χ→1: curvature ripples amplify. χ=1: Big Bounce. STOP freezes at current frame.")

    st.markdown("""
---
**The CBQG framework yields five near-term falsifiable predictions:**
I. **UV Spectral Discriminant:** δCBQG ≡ n_t + r/8 ≥ 2 (forbidden by all standard single-field inflationary models).
II. **Tensor Step Feature:** r(k) exhibits step-function suppression at the saturation scale.
III. **CMB Alignment:** n_s = 0.964 and r ≈ 0.003, derived from three degrees of freedom, zero fine-tuning.
IV. **Schwarzschild Resolution:** r_min ∝ M^(1/3) ρ_max^(-1/3), from the Kretschmann scalar.
V. **Dark Energy Dissipation:** Λ(t) = Λ_0 / (1 + Λ_0³t/π)^(1/3), with dΛ/dt < 0 structurally required.
""")

# ==================== TAB 2 ====================
with t2:
    st.subheader("4D Highway Transit — Wormhole Siphoning & Bridging")
    st.markdown("As localized saturation χ approaches 1, the reality manifold is **siphoned radially inward** through the 4th dimensional abstract axis — creating internal transit chords. **All values and the 3D graph respond to the Master Global χ slider.**")

    colA, colB = st.columns([1, 2])
    with colA:
        pt_a_theta = st.slider("Point A Theta (Latitude 0 to π)", 0.0, float(np.pi), float(np.pi/4))
        pt_a_phi   = st.slider("Point A Phi (Longitude 0 to 2π)", 0.0, float(2*np.pi), 0.0)
        pt_a_chi   = st.slider("Point A Saturation χ", 0.000, 1.000, float(chi_global), 0.001, format="%.3f")
        st.markdown("---")
        pt_b_theta = st.slider("Point B Theta (Latitude 0 to π)", 0.0, float(np.pi), float(3*np.pi/4))
        pt_b_phi   = st.slider("Point B Phi (Longitude 0 to 2π)", 0.0, float(2*np.pi), float(np.pi))
        pt_b_chi   = st.slider("Point B Saturation χ", 0.000, 1.000, float(chi_global), 0.001, format="%.3f")

        st.markdown("### 🎚️ Transit Position")
        transit_pct = st.slider("Transit Timeline Scrubber (%)", 0, 100, 50)

        ON_THRESH = 0.96
        st.session_state.wh_active = (pt_a_chi > ON_THRESH and pt_b_chi > ON_THRESH)
        is_wormhole = st.session_state.wh_active
        if is_wormhole:
            st.success("Heuristic visualization threshold for deep saturation (χ → 1) achieved.")
        else:
            st.info("Shallow Sub-manifold Chord: standard geometric descent mapping active.")

        sin_a_th, cos_a_th = np.sin(pt_a_theta), np.cos(pt_a_theta)
        sin_b_th, cos_b_th = np.sin(pt_b_theta), np.cos(pt_b_theta)

        dot_product = np.clip(sin_a_th*sin_b_th*np.cos(pt_a_phi-pt_b_phi)+cos_a_th*cos_b_th, -1.0, 1.0)
        surface_dist = univ_R * np.arccos(dot_product)

        depth_a = 1.0 - pt_a_chi; depth_b = 1.0 - pt_b_chi
        wa = univ_R * pt_a_chi;   wb = univ_R * pt_b_chi

        xa = univ_R*sin_a_th*np.cos(pt_a_phi)*depth_a; ya = univ_R*sin_a_th*np.sin(pt_a_phi)*depth_a; za = univ_R*cos_a_th*depth_a
        xb = univ_R*sin_b_th*np.cos(pt_b_phi)*depth_b; yb = univ_R*sin_b_th*np.sin(pt_b_phi)*depth_b; zb = univ_R*cos_b_th*depth_b

        chord_dist = np.sqrt((xa-xb)**2+(ya-yb)**2+(za-zb)**2+(wa-wb)**2)
        dist_saved = surface_dist - chord_dist

        st.metric("Surface Distance (S)", f"{format_distance(surface_dist)}")
        st.metric("Internal Chord Distance (L)", f"{format_distance(chord_dist)}")
        st.caption("L uses the Appendix-B chord form (includes Δw). Visualization only, not a covariant geodesic solver.")
        st.metric("🚀 Distance Savings (S - L)", f"{format_distance(dist_saved)}", delta="Saved via Metric Depth")
        st.markdown("---")
        st.markdown(f"**Global χ = {chi_global:.3f}** | m_eff = {m_eff(1000,chi_global):,.1f} kg (per 1000 kg) | D_msd = {d_msd(10,chi_global):,.2f} m (per 10m craft)")

    with colB:
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="hw_top"):  st.session_state.cam_t2_hw = dict(eye=dict(x=0,y=0,z=2.5))
        if c2.button("Side Cross-Section", key="hw_side"): st.session_state.cam_t2_hw = dict(eye=dict(x=2.5,y=0,z=0))
        if c3.button("Isometric View", key="hw_iso"): st.session_state.cam_t2_hw = dict(eye=dict(x=1.5,y=1.5,z=1.5))

        sphere_r = univ_R*(1.0-chi_global*0.5)
        fig2 = go.Figure()
        fig2.add_trace(go.Surface(x=sphere_r*np.cos(u)*np.sin(v), y=sphere_r*np.sin(u)*np.sin(v),
                                   z=sphere_r*np.cos(v), opacity=0.10, colorscale="Blues", showscale=False))

        xa_surf=univ_R*sin_a_th*np.cos(pt_a_phi); ya_surf=univ_R*sin_a_th*np.sin(pt_a_phi); za_surf=univ_R*cos_a_th
        xb_surf=univ_R*sin_b_th*np.cos(pt_b_phi); yb_surf=univ_R*sin_b_th*np.sin(pt_b_phi); zb_surf=univ_R*cos_b_th

        ca = "red" if pt_a_chi>0.95 else "orange"; cb = "red" if pt_b_chi>0.95 else "orange"
        fig2.add_trace(go.Scatter3d(x=[xa_surf],y=[ya_surf],z=[za_surf], mode='markers+text',
                                    marker=dict(size=12,color=ca), text=["Edge A"], textposition="top center", name="Surface A"))
        fig2.add_trace(go.Scatter3d(x=[xa_surf,xa],y=[ya_surf,ya],z=[za_surf,za],
                                    mode='lines', line=dict(color=ca,dash='dot'), showlegend=False))
        fig2.add_trace(go.Scatter3d(x=[xb_surf],y=[yb_surf],z=[zb_surf], mode='markers+text',
                                    marker=dict(size=12,color=cb), text=["Edge B"], textposition="top center", name="Surface B"))
        fig2.add_trace(go.Scatter3d(x=[xb_surf,xb],y=[yb_surf,yb],z=[zb_surf,zb],
                                    mode='lines', line=dict(color=cb,dash='dot'), showlegend=False))

        num_steps=40; tx=np.linspace(xa,xb,num_steps); ty=np.linspace(ya,yb,num_steps); tz=np.linspace(za,zb,num_steps)
        fig2.add_trace(go.Scatter3d(x=tx,y=ty,z=tz, mode='lines',
                                    line=dict(width=6,color='lime' if is_wormhole else 'yellow'),
                                    name="Core Wormhole" if is_wormhole else "Shallow Chord"))
        pos_idx=int((transit_pct/100.0)*(num_steps-1))
        fig2.add_trace(go.Scatter3d(x=[tx[pos_idx]],y=[ty[pos_idx]],z=[tz[pos_idx]], mode='markers',
                                    marker=dict(size=10,color='white',symbol='diamond'), name="Transit Craft"))
        fig2.update_layout(title=f"4D Saturation Bridge (Global χ = {chi_global:.3f})", height=600, showlegend=True,
                           margin=dict(l=0,r=0,b=0,t=40), scene_camera=st.session_state.cam_t2_hw,
                           scene=dict(xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False),zaxis=dict(showticklabels=False)))
        st.plotly_chart(fig2, use_container_width=True, key="highway_transit_plot")

    st.markdown("---")
    st.markdown("### 🗺️ Navigational Mission Planner")
    colM1, colM2 = st.columns(2)
    with colM1:
        target_sf_route = st.number_input("Target Surface Distance (S, meters):", 1e3, float(univ_R*np.pi), 1e15, format="%.2e")
        target_ch_route = st.number_input("Desired Max Transit Span (L, meters):", 1e3, float(univ_R), 1e11, format="%.2e")
    with colM2:
        st.info("Heuristic routing: computes a visualization-only χ proxy to reduce surface span S toward target chord span L.")
        if target_ch_route >= target_sf_route:
            st.warning("Desired transit span ≥ surface span. No saturation required.")
        else:
            req_chi = float(clamp_chi(1.0-(target_ch_route/target_sf_route)))
            st.metric("Minimum Required Engine Saturation (χ)", f"{req_chi:.4f}")
            st.progress(min(1.0, req_chi))
            st.caption(f"Relative geometric strain density factor: {100.0*(1.0/(1.0-req_chi+EPS)-1.0):,.1f}")

# ==================== TAB 3 ====================
with t3:
    st.subheader("Addendum B: Military UAP Sensor Correlation")
    st.warning("⚠️ SPECULATIVE ENGINEERING: The following applies CBQG heuristic physics to reverse-engineer reported UAP kinematics. Math core stays Appendix-B. Attribution is strictly speculative.")
    st.markdown("When radar systems track anomalous craft, they report kinematics irreconcilable with General Relativity. Under CBQG, if a craft accumulates localized spacetime tight to its hull limit (χ → 1), **acceleration increases without bound under finite force (via m_eff → 0)**.")

    st.markdown("### 📡 Scenario Modeler")
    scenario = st.selectbox("Load Physical Sensor Profile:", ["Manual Entry", "Nimitz 'Tic Tac' Encounter (2004)", "Malmstrom AFB Shutdown (1967)"])
    if scenario == "Nimitz 'Tic Tac' Encounter (2004)":
        scn_chi, scn_m0, scn_v = 0.999, 15000.0, 120.0
    elif scenario == "Malmstrom AFB Shutdown (1967)":
        scn_chi, scn_m0, scn_v = 0.950, 8000.0, 28.0
    else:
        scn_chi, scn_m0, scn_v = chi_global, 5000.0, 120.0

    colS1, colS2, colS3 = st.columns(3)
    with colS1: m0 = st.slider("Craft Baseline Mass (kg)", 1.0, 1000000.0, float(scn_m0))
    with colS2: active_chi = st.slider("Active Saturation (χ)", 0.001, 1.000, float(scn_chi), 0.001, format="%.3f")
    with colS3: V_electronics = st.slider("Control Voltage (V)", 1.0, 1000.0, float(scn_v))

    base_accel=10000.0/(m0+EPS); m_e=m_eff(m0,active_chi); a_test=10000.0/(m_e+EPS)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. Instantaneous Acceleration — USS Princeton 2004")
        st.markdown(f"**m_eff = {m0:,.0f} × √(1 - {active_chi:.3f}²) = <span style='color:lime'>{m_e:,.1f} kg</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-m_e/(m0+EPS))))
        st.info(f"Apparent radial acceleration proxy: {a_test:,.0f} m/s² under 10kN thrust (illustrative).")
        st.markdown("### 3. Minimum Standoff — Nimitz & Roosevelt")
        d_m=d_msd(10.0,active_chi)
        st.markdown(f"**D_msd = 10 × [{active_chi:.3f} / (1-{active_chi:.3f}+ε)]^(1/3) = <span style='color:lime'>{d_m:,.1f} m</span>**", unsafe_allow_html=True)
    with col2:
        st.markdown("### 2. No Sonic Boom — Nimitz 2004")
        f_d=f_drag(1000.0,active_chi)
        st.markdown(f"**F_drag = 1000 × √(1-{active_chi:.3f}²) = <span style='color:lime'>{f_d:,.1f} N</span>**", unsafe_allow_html=True)
        st.progress(max(0.0,min(1.0,1.0-f_d/1000.0)))
        st.markdown("### 4. EM Damping — Malmstrom 1967")
        v_e=v_eff(V_electronics,active_chi)
        st.markdown(f"**V_eff = {V_electronics} × (1-{active_chi:.3f}) = <span style='color:red'>{v_e:,.2f} V</span>**", unsafe_allow_html=True)
        if active_chi > 0.90:
            st.error("Critical voltage collapse. Avionics/Warhead logic circuits failing (heuristic narrative).")

    st.markdown("---")
    st.markdown("### 🛸 UAP Sensor Trajectory Analysis")
    fig3=go.Figure()
    time_arr=np.linspace(0,10,100)
    traj=[base_accel]*10+[a_test]*80+[base_accel]*10
    fig3.add_trace(go.Scatter(x=time_arr,y=[base_accel]*100, name=f"Conventional ({base_accel:,.1f} m/s²)", line=dict(color='white',dash='dot')))
    fig3.add_trace(go.Scatter(x=time_arr,y=traj, name=f"CBQG (χ={active_chi:.3f})", line=dict(color='lime',width=4)))
    fig3.update_layout(title="Apparent Radar Acceleration (Log Scale)", height=300, margin=dict(l=0,r=0,b=0,t=40),
                       xaxis_title="Seconds", yaxis_title="m/s²", yaxis_type="log",
                       plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)', font=dict(color='white'))
    st.plotly_chart(fig3, use_container_width=True, key="dynamic_uap_transit_plot")

    st.markdown("---")
    st.markdown("### ☄️ Re-entry Protocol Simulator")
    colR1, colR2 = st.columns(2)
    with colR1:
        sim_k=st.slider("Re-entry Damping Factor (k)", 0.1, 15.0, 3.0, 0.1, key="k_slider")
        st.info("High k: fast inertial reconnection, high G-force risk. Low k: slow decay, survivable re-entry (heuristic).")
    with colR2:
        peak_g=50.0*sim_k*active_chi
        st.metric("Peak Inertial Whiplash", f"{peak_g:.1f} Gs")
        st.caption("Heuristic order-of-magnitude estimate only.")
        if peak_g>50: st.error("🚨 STRUCTURAL FAILURE: >50G limit exceeded.")
        elif active_chi<=0.05: st.success("✅ CRAFT AT NORMAL INERTIA.")
        else: st.success("✅ RE-ENTRY SURVIVABLE.")
        t_arr_re=np.linspace(0,5,50)
        chi_t=chi_decay(active_chi,sim_k,t_arr_re)
        fig_re=go.Figure(go.Scatter(x=t_arr_re,y=chi_t,fill='tozeroy',line=dict(color='orange')))
        fig_re.update_layout(title="Phase Decay Profile", height=200, margin=dict(l=0,r=0,b=0,t=30),
                             yaxis_title="χ(t)", xaxis_title="Seconds",
                             plot_bgcolor='rgba(12,12,22,1)', paper_bgcolor='rgba(12,12,22,1)', font=dict(color='white'))
        st.plotly_chart(fig_re, use_container_width=True, key="reentry_chart")

# ==================== TAB 4 ====================
with t4:
    st.subheader("Theory & Axioms")

    st.markdown("### 0. The Unified Scalar Simplification (Engine Constraint)")
    st.markdown("**Explanation:** True CBQG is a covariant tensor formulation driven by the invariant curvature limits of R_abcd R^abcd. For this simulator, the tensor field is simplified into a single master scalar (χ), acting pedagogically across multiple dependent axes as curvature magnitude, spatial depth coordinate, and mass modifier simultaneously.")

    st.markdown("### 1. Metric Saturation Invariant (χ)")
    st.code("χ = C / C_max ≤ 1")
    st.markdown("**Explanation:** Spacetime curvature (C) cannot exceed C_max. χ tracks what fraction of that capacity is exhausted. χ=0 is flat, maximum expansion. χ=1 is geometric saturation — the Big Bounce.")

    st.markdown("### 2. Effective Mass Negation (m_eff)")
    st.code("m_eff = m_0 √(1 - χ²)")
    st.markdown("**Explanation:** As χ → 1, the craft's inertial connection to the universe evaporates toward zero, permitting arbitrarily large velocity vectors under finite applied force. Same mathematical structure as the Lorentz factor, driven by geometric saturation rather than velocity.")

    st.markdown("### 3. Aerodynamic Drag Suppression (F_drag)")
    st.code("F_drag = F_0 √(1 - χ²)")
    st.markdown("**Explanation:** As the local metric saturates, fluid interaction collapses with the same scaling as m_eff. The atmosphere slides around the saturated metric boundary rather than compressing, eliminating sonic booms and aerodynamic heating.")

    st.markdown("### 4. Minimum Standoff Distance (D_msd)")
    st.code("D_msd = R [χ / (1 - χ + ε)]^(1/3)")
    st.markdown("**Explanation:** A saturating craft projects a curvature gradient that repels unsaturated external mass. ε=10⁻⁹ prevents singular divergence at χ=1. At high χ this buffer zone grows rapidly, producing the 'mirroring' behavior reported in UAP encounters (heuristic application).")

    st.markdown("### 5. Electromagnetic Damping (V_eff)")
    st.code("V_eff = V_0 (1 - χ)")
    st.markdown("**Explanation:** Vacuum impedance scales linearly with saturation. As χ → 1, the geometric dielectric barrier bleeds voltage from surrounding electronics, driving active systems toward shutdown. Strictly linear per Appendix B.")

    st.markdown("### 6. 4D Highway Volume (V_core)")
    st.code("V_core = 0.5 π² R⁴ (1 - √(1 - χ²))")
    st.markdown("**Explanation:** Usable interior volume of the 4D hypersphere traversable by saturated craft. Derived from the 4-ball shell volume compressed by the saturation invariant. Zero at χ=0, maximum at χ=1.")

    st.markdown("### 7. Harmonic Re-entry Decay (χ_t)")
    st.code("χ(t) = χ_init e^(-kt)")
    st.markdown("**Explanation:** Instantaneous saturation collapse would reconnect full inertial mass instantly, causing catastrophic G-force whiplash. Exponential decay with factor k distributes the inertial reconnection over a survivable timescale.")

    st.markdown("### 8. Metric Radial Depth Coordinate (w)")
    st.code("w = R * χ")
    st.markdown("**Explanation:** The 4th-dimensional interior penetration depth. At χ=0, w=0 (surface only). At χ=1, w=R (full interior). This coordinate anchors the wormhole chord calculation geometrically.")

    st.markdown("### 9. Wormhole Chord Distance (L)")
    st.code("L = √(Σ(Δxi)² + (Δw)²)")
    st.markdown("**Explanation:** Euclidean chord through the 4D interior connecting two saturated surface points. Requires the explicit w coordinate (Eq. 8). This is a visualization embedding approximation — true CBQG geodesic paths use the full covariant tensor formulation. Shortcut effect is real; magnitude shown is an order-of-magnitude heuristic.")

    st.markdown("### 10. Dark Energy Dissipation (Λ(t))")
    st.code("Λ(t) = Λ₀ / (1 + Λ₀³ t / π)^(1/3)")
    st.markdown("**Explanation:** Derived in CBQG v10 (pages 146–173) as a necessary consequence of total constraint preservation under quantum information bounds. Variables are Planck-normalized (Λ̄ ≡ Λℓ²_P, t̄ ≡ t/t_P). Excludes eternal de Sitter expansion. Dark energy crossover time ~10^315 years (CBQG v10, pp. 164–165).")

st.caption("CBQG v10.5.1 © Dr. Anthony Omar Peña, D.O. — All rights reserved.")

