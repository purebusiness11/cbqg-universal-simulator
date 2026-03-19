import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import time

st.set_page_config(page_title="CBQG v10.5.1 Universal Engine", layout="wide")
st.title("🌌 CBQG v10.5.1 — Universal Simulation Engine")
st.markdown("**Sovereign Research Lead:** Dr. Anthony Omar Peña, D.O., LT, MC, USN (Vet) | [cbqg.org](https://cbqg.org) | Version 10.5.1 — March 18, 2026")
st.caption("All mechanics derived solely from C ≤ C_max. Metric Radial Depth is a functional saturation coordinate.")

# ====================== SESSION STATE & CAMERA MATRICES ======================
if "chi_global" not in st.session_state: st.session_state.chi_global = 0.50
if "wh_active" not in st.session_state: st.session_state.wh_active = False

# Camera Memory Storage
if "cam_t1_gw" not in st.session_state: st.session_state.cam_t1_gw = dict(eye=dict(x=1.5, y=1.5, z=1.5))
if "cam_t1_sph" not in st.session_state: st.session_state.cam_t1_sph = dict(eye=dict(x=1.5, y=1.5, z=1.5))
if "cam_t2_hw" not in st.session_state: st.session_state.cam_t2_hw = dict(eye=dict(x=1.5, y=1.5, z=1.5))

# ====================== SIDEBAR ======================
st.sidebar.header("Master Controls")
if st.sidebar.button("⚠️ SYSTEM RESET"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
chi_global = st.sidebar.slider("Global Saturation χ", 0.001, 1.000, st.session_state.get("chi_global", 0.50), 0.01)
st.session_state.chi_global = chi_global

univ_R = st.sidebar.number_input("Universal 4D Radius (R, meters)", 1e10, 1e30, 1e22, step=1e20)
st.sidebar.caption("Determines baseline universal scale. Exponentially drives Minimum Standoff (D_msd) and exactly dictates the 4D Highway Traversable Core Volume (V_core).")

st.sidebar.markdown("---")
st.sidebar.success("Engine Engaged: All kinetics bonded interactively to Global χ.")

# ====================== CORE MATH ======================
def clamp_chi(chi, eps=1e-9): return np.clip(chi, eps, 1.0 - eps)

def m_eff(m0, chi): return m0 * np.sqrt(1 - clamp_chi(chi)**2)
def f_drag(f0, chi): return f0 * np.sqrt(1 - clamp_chi(chi)**2)
def d_msd(r, chi): 
    c = clamp_chi(chi)
    return r * (c / (1 - c))**(1/3)
def v_core(R, chi): return 0.5 * np.pi**2 * R**4 * (1 - np.sqrt(1 - clamp_chi(chi)**2))
def chi_decay(chi_init, k, t): return chi_init * np.exp(-k * t)

def v_eff(v0, chi): 
    c = clamp_chi(chi)
    base_v = v0 * (1 - c)
    return base_v * np.exp(-40 * (c - 0.90)) if c > 0.90 else base_v

def format_distance(m):
    ly = 9.461e15
    if m >= ly:            return f"{m / ly:,.2f} Light Years"
    elif m >= 1e15:        return f"{m / 1e15:,.2f} Trillion km"
    elif m >= 1e12:        return f"{m / 1e12:,.2f} Billion km"
    elif m >= 1e9:         return f"{m / 1e9:,.2f} Million km"
    elif m >= 1000:        return f"{m / 1000:,.2f} km"
    else:                  return f"{m:,.2f} m"

# GLOBAL PARAMETRIC GRIDS
U_RES, V_RES = 30j, 30j
u, v = np.mgrid[0:2*np.pi:U_RES, 0:np.pi:V_RES]

U_ANIM, V_ANIM = 20j, 20j
u_anim, v_anim = np.mgrid[0:2*np.pi:U_ANIM, 0:np.pi:V_ANIM]


# ====================== TABS ======================
t1, t2, t3, t4 = st.tabs([
    "🌌 1. COSMIC REALITY (3D/4D)",
    "🛸 2. 4D HIGHWAY TRANSIT",
    "🎖️ 3. MILITARY FORENSICS & UAP",
    "ℹ️ THEORY & AXIOMS"
])

# ==================== TAB 1: COSMIC REALITY ====================
with t1:
    st.subheader("Cosmic Reality — Geometric Saturation")
    st.markdown("""
    ### **The Third Law of Nature (Axiom):** 
    Infinite information density cannot exist within any finite region of spacetime. The open question is therefore not whether a constraint exists, but which physical mechanism enforces it. **CBQG proposes that spacetime curvature itself is bounded by a maximum value:**
    
    ## **C ≤ C_max**
    
    Alongside the invariant speed of light (c) and the quantum of action (h-bar), formalized by the Geometric Saturation Invariant **χ = C/C_max**, where **C = √(R_abcd R^abcd)** is the invariant curvature magnitude, the square root of the Kretschmann scalar. C is defined this way deliberately: it carries the same physical dimensions as curvature, making C_max a direct geometric ceiling rather than a bound on a squared quantity, with χ defined on [0,1] for all physical spacetimes.
    """)
    st.markdown("<h3 style='color:red;'>🚨 χ=1 IS ABSOLUTE GEOMETRIC SATURATION (C_max) 🚨</h3>", unsafe_allow_html=True)
    
    view_mode = st.radio("Select Reality Representation:", ["3D Spacetime (Gravity Well)", "4D Hypersphere (Dynamic Edge)"], horizontal=True)
    
    if view_mode == "3D Spacetime (Gravity Well)":
        st.write("Visualizing a 3D gravitational well where the depth (curvature) is strictly bounded by C_max (χ=1).")
        
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="gw_t"): st.session_state.cam_t1_gw = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="gw_s"): st.session_state.cam_t1_gw = dict(eye=dict(x=2.5, y=0, z=0))
        if c3.button("Isometric View (Default)", key="gw_i"): st.session_state.cam_t1_gw = dict(eye=dict(x=1.5, y=1.5, z=1.5))
        
        x = np.linspace(-5, 5, 40) 
        y = np.linspace(-5, 5, 40)
        xx, yy = np.meshgrid(x, y)
        r = np.sqrt(xx**2 + yy**2)
        
        depth_nominal = -1.0 / (r + 0.1)
        max_depth = -3.0 * chi_global
        zz = np.maximum(depth_nominal, max_depth)
        
        fig3d = go.Figure(data=[go.Surface(z=zz, x=xx, y=yy, colorscale='Viridis', opacity=0.9, showscale=False)])
        fig3d.add_trace(go.Surface(z=np.full_like(zz, -3.0), x=xx, y=yy, showscale=False, opacity=0.3, colorscale='Reds', name='Absolute Limit (χ=1)', hoverinfo='name', showlegend=True))
        
        fig3d.update_layout(
            title="3D Spacetime: Curvature bounded horizontally by χ=1 (C_max)", margin=dict(l=0, r=0, b=0, t=40),
            scene_camera=st.session_state.cam_t1_gw, 
            scene=dict(
                xaxis_title='X Space (m)', yaxis_title='Y Space (m)', zaxis_title='Z (Curvature Depth χ)',
                zaxis=dict(range=[-4, 0]),
                annotations=[dict(showarrow=False, x=0, y=0, z=-3.0, text="GEOMETRIC FLOOR (C_max)", xanchor="center", font=dict(color="red", size=14))]
            )
        )
        st.plotly_chart(fig3d, use_container_width=True, key="gravity_well_plot")

    else:
        st.write("### The 4D Hypersphere Map")
        st.markdown("**Why are there only 3 axes?** This is a 3D surface projection of a 4D shape. The 4th geometric dimension extends radially inward toward the core, physically experienced as metric density.")
        
        scale_mode = st.radio("Viewport Scaling Matrix", ["Visual (Linear Drop)", "Physical (Nonlinear Metric Compression)"], horizontal=True)

        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="sph_t"): st.session_state.cam_t1_sph = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="sph_s"): st.session_state.cam_t1_sph = dict(eye=dict(x=2.5, y=0, z=0))
        if c3.button("Isometric View", key="sph_i"): st.session_state.cam_t1_sph = dict(eye=dict(x=1.5, y=1.5, z=1.5))

        r_t = univ_R / (chi_global + 0.01)
        st.metric("Hypersphere True Radius", f"{r_t:.2e} m")
        
        if chi_global > 0.95:
             st.error("BIG BOUNCE — r_min floor engaged (χ limits reach C_max)")
        
        max_bound = univ_R * 1.1 
        sphere_container = st.empty()
        
        def draw_sphere(chi_target, is_anim=False):
             c_targ = clamp_chi(chi_target)
             if scale_mode == "Physical (Nonlinear Metric Compression)":
                 rad = univ_R / (c_targ + 0.01)
             else:
                 rad = univ_R * (1.1 - c_targ)
             
             mesh_u, mesh_v = (u_anim, v_anim) if is_anim else (u, v)
             
             fig_life = go.Figure(data=go.Surface(
                 x=rad * np.cos(mesh_u) * np.sin(mesh_v), y=rad * np.sin(mesh_u) * np.sin(mesh_v), z=rad * np.cos(mesh_v),
                 opacity=0.8, colorscale="Plasma", showscale=False))
            
             fig_life.update_layout(
                 title="4D Hypersphere Envelope", height=500, margin=dict(l=0, r=0, b=0, t=40),
                 scene_camera=st.session_state.cam_t1_sph, 
                 scene=dict(xaxis=dict(range=[-max_bound, max_bound], title='X (m)'),
                            yaxis=dict(range=[-max_bound, max_bound], title='Y (m)'),
                            zaxis=dict(range=[-max_bound, max_bound], title='Z (m)'),
                            aspectmode='cube')
             )
             k = f"sph_anim_{time.time_ns()}" if is_anim else "sph_static_main"
             sphere_container.plotly_chart(fig_life, use_container_width=True, key=k)

        if st.button("▶ Simulate Universal Life Cycle", key="btn_life"):
             st.info("Running geometric expansion/contraction sequence...")
             for chi_step in np.linspace(chi_global, 0.01, 20):
                 draw_sphere(chi_step, is_anim=True)
                 time.sleep(0.04)
             draw_sphere(chi_global, is_anim=False)
             st.session_state.chi_global = chi_global 
        else:
             draw_sphere(chi_global, is_anim=False)

    st.markdown("""
    ---
    **The CBQG framework yields five near-term falsifiable predictions:**
    I. **UV Spectral Discriminant:** δCBQG ≡ n_t + r/8 ≥ 2 (forbidden by all standard single-field inflationary models).
    II. **Tensor Step Feature:** r(k) exhibits step-function suppression at the saturation scale.
    III. **CMB Alignment:** n_s = 0.964 and r ≈ 0.003, derived from three degrees of freedom, zero fine-tuning.
    IV. **Schwarzschild Resolution:** r_min ∝ M^(1/3) ρ_max^(-1/3), from the Kretschmann scalar.
    V. **Dark Energy Dissipation:** Λ(t) = Λ_0 / (1 + Λ_0³t/π)^(1/3), with dΛ/dt < 0 structurally required.
    """)

# ==================== TAB 2: 4D HIGHWAY ====================
with t2:
    st.subheader("4D Highway Transit — Wormhole Siphoning & Bridging")
    st.markdown("Set points on the 4D hypersphere surface. As localized saturation χ approaches 1, the reality manifold is **siphoned radially inward** through the 4th dimensional 'w' axis—creating abstract chords, or true geometrically anchored Wormholes.")
    st.code("8. Wormhole Chord Distance: L = √(Σ(Δxi)² + (Δw)²)")
    
    colA, colB = st.columns([1, 2])
    with colA:
        pt_a_theta = st.slider("Point A Theta (Latitude 0 to π)", 0.0, np.pi, np.pi/4)
        pt_a_phi = st.slider("Point A Phi (Longitude 0 to 2π)", 0.0, 2*np.pi, 0.0)
        pt_a_chi = st.slider("Point A Saturation χ", 0.0, 1.0, 0.8)

        st.markdown("---")
        pt_b_theta = st.slider("Point B Theta (Latitude 0 to π)", 0.0, np.pi, 3*np.pi/4)
        pt_b_phi = st.slider("Point B Phi (Longitude 0 to 2π)", 0.0, 2*np.pi, np.pi)
        pt_b_chi = st.slider("Point B Saturation χ", 0.0, 1.0, 0.8)
        
        st.markdown("### 🎚️ Transit Position")
        transit_pct = st.slider("Transit Timeline Scrubber (%)", 0, 100, 50)
        
        ON_THRESH, OFF_THRESH = 0.96, 0.94
        if pt_a_chi > ON_THRESH and pt_b_chi > ON_THRESH: st.session_state.wh_active = True
        elif pt_a_chi < OFF_THRESH or pt_b_chi < OFF_THRESH: st.session_state.wh_active = False
        is_wormhole = st.session_state.wh_active

        if is_wormhole:
            st.success("WORMHOLE ACTIVE: Deep Core Siphoning Achieved. (χ ≈ 1)")
        else:
            st.info("Shallow Sub-manifold Chord: Partial saturation permits transit through the upper metric layers.")

        sin_a_th, cos_a_th = np.sin(pt_a_theta), np.cos(pt_a_theta)
        sin_b_th, cos_b_th = np.sin(pt_b_theta), np.cos(pt_b_theta)
        sin_a_ph, cos_a_ph = np.sin(pt_a_phi), np.cos(pt_a_phi)
        sin_b_ph, cos_b_ph = np.sin(pt_b_phi), np.cos(pt_b_phi)

        dot_product = np.clip(sin_a_th * sin_b_th * np.cos(pt_a_phi - pt_b_phi) + cos_a_th * cos_b_th, -1.0, 1.0)
        surface_dist = univ_R * np.arccos(dot_product)
        
        depth_a = clamp_chi(1.0 - pt_a_chi)
        depth_b = clamp_chi(1.0 - pt_b_chi)
        wa = univ_R * pt_a_chi
        wb = univ_R * pt_b_chi
        
        xa = univ_R * sin_a_th * cos_a_ph * depth_a
        ya = univ_R * sin_a_th * sin_a_ph * depth_a
        za = univ_R * cos_a_th * depth_a
        
        xb = univ_R * sin_b_th * cos_b_ph * depth_b
        yb = univ_R * sin_b_th * sin_b_ph * depth_b
        zb = univ_R * cos_b_th * depth_b
        
        chord_dist = np.sqrt((xa - xb)**2 + (ya - yb)**2 + (za - zb)**2 + (wa - wb)**2)
        dist_saved = surface_dist - chord_dist

        st.metric("Surface Distance (S)", f"{format_distance(surface_dist)}")
        st.metric("Internal Chord Distance (L)", f"{format_distance(chord_dist)}")
        st.metric("🚀 Distance Savings (S - L)", f"{format_distance(dist_saved)}", delta="Saved via Metric Depth")
        
    with colB:
        st.write("### 🎥 Explicit Camera Controls")
        c1, c2, c3 = st.columns(3)
        if c1.button("Top-Down View", key="hw_top"): st.session_state.cam_t2_hw = dict(eye=dict(x=0, y=0, z=2.5))
        if c2.button("Side Cross-Section", key="hw_side"): st.session_state.cam_t2_hw = dict(eye=dict(x=2.5, y=0, z=0))
        if c3.button("Isometric View", key="hw_iso"): st.session_state.cam_t2_hw = dict(eye=dict(x=1.5, y=1.5, z=1.5))
        
        fig2 = go.Figure()
        x_sph = univ_R * np.cos(u) * np.sin(v)
        y_sph = univ_R * np.sin(u) * np.sin(v)
        z_sph = univ_R * np.cos(v)
        
        fig2.add_trace(go.Surface(x=x_sph, y=y_sph, z=z_sph, opacity=0.10, colorscale="Blues", showscale=False))
        
        xa_surf = univ_R * sin_a_th * cos_a_ph
        ya_surf = univ_R * sin_a_th * sin_a_ph
        za_surf = univ_R * cos_a_th

        xb_surf = univ_R * sin_b_th * cos_b_ph
        yb_surf = univ_R * sin_b_th * sin_b_ph
        zb_surf = univ_R * cos_b_th

        color_a = "red" if pt_a_chi > 0.95 else "orange"
        fig2.add_trace(go.Scatter3d(x=[xa_surf], y=[ya_surf], z=[za_surf], mode='markers+text', marker=dict(size=12, color=color_a), text=["Edge A"], textposition="top center", name="Surface A"))
        fig2.add_trace(go.Scatter3d(x=[xa_surf, xa], y=[ya_surf, ya], z=[za_surf, za], mode='lines', line=dict(color=color_a, dash='dot'), name="Siphoning Depth A", showlegend=False))

        color_b = "red" if pt_b_chi > 0.95 else "orange"
        fig2.add_trace(go.Scatter3d(x=[xb_surf], y=[yb_surf], z=[zb_surf], mode='markers+text', marker=dict(size=12, color=color_b), text=["Edge B"], textposition="top center", name="Surface B"))
        fig2.add_trace(go.Scatter3d(x=[xb_surf, xb], y=[yb_surf, yb], z=[zb_surf, zb], mode='lines', line=dict(color=color_b, dash='dot'), name="Siphoning Depth B", showlegend=False))

        num_steps = 40
        tx = np.linspace(xa, xb, num_steps)
        ty = np.linspace(ya, yb, num_steps)
        tz = np.linspace(za, zb, num_steps)
        
        line_color = 'lime' if is_wormhole else 'yellow'
        bridge_name = "Core Wormhole" if is_wormhole else "Shallow Chord"
            
        fig2.add_trace(go.Scatter3d(x=tx, y=ty, z=tz, mode='lines', line=dict(width=6, color=line_color), name=bridge_name))
        
        pos_idx = int((transit_pct / 100.0) * (num_steps - 1))
        fig2.add_trace(go.Scatter3d(x=[tx[pos_idx]], y=[ty[pos_idx]], z=[tz[pos_idx]], mode='markers', marker=dict(size=10, color='white', symbol='diamond'), name="Transit Craft"))

        fig2.update_layout(
            title="4D Saturation Bridge", height=600, showlegend=True, margin=dict(l=0, r=0, b=0, t=40),
            scene_camera=st.session_state.cam_t2_hw, 
            scene=dict(xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False), zaxis=dict(showticklabels=False)),
        )
        st.plotly_chart(fig2, use_container_width=True, key="highway_transit_plot")

# ==================== TAB 3: MILITARY FORENSICS ====================
with t3:
    st.subheader("Addendum B: Military UAP Sensor Correlation")
    st.warning("⚠️ SPECULATIVE ENGINEERING: The following applies CBQG heuristics to reported UAP kinematics. This is not a verified claim.")
    st.info("**DISCLAIMER:** The application of CBQG kinematics back-engineered onto military UFO/UAP anomalies is strictly speculative engineering. However, the exact mathematical framework demonstrates a stark, unavoidable consilience with DoD sensor data (e.g. Nimitz 2004) regarding macroscopic inertia negation.")
    
    st.markdown("""
    When radar systems track anomalous craft, they display impossible kinematics: jumping vast distances instantaneously and accelerating without creating sonic booms. Under CBQG, if a craft accumulates local spacetime tightly to its hull limit (χ → 1), it severs its inertial coupling from reality, allowing the UAP to safely execute a **4D interior chord transit** completely uninhibited by normal mass barriers.
    """)
    
    m0 = st.slider("Craft Baseline Mass (kg)", 1.0, 1000000.0, 5000.0)
    drag_base = 1000.0
    R_craft = 10.0
    V_electronics = 120.0 
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. Instantaneous Acceleration")
        st.markdown("**USS Princeton, 2004 - AN/SPY-1**")
        m_e = m_eff(m0, chi_global)
        st.markdown(f"**m_eff = {m0:,.0f} × √(1 - {chi_global}²) = <span style='color:lime'>{m_e:,.1f} kg</span>**", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, 1.0 - m_e/m0)))

        st.markdown("### 3. Minimum Standoff (Mirroring)")
        st.markdown("**Nimitz & Roosevelt**")
        d_m = d_msd(R_craft, chi_global)
        st.markdown(f"**D_msd = {R_craft} × [{chi_global} / (1 - {chi_global})]^(1/3) = <span style='color:lime'>{d_m:,.1f} m</span>**", unsafe_allow_html=True)
        
    with col2:
        st.markdown("### 2. No Sonic Boom")
        st.markdown("**Nimitz, 2004 - Commander Fravor**")
        f_d = f_drag(drag_base, chi_global)
        st.markdown(f"**F_drag = {drag_base} × √(1 - {chi_global}²) = <span style='color:lime'>{f_d:,.1f} N</span>**", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, 1.0 - f_d/drag_base)))
        
        st.markdown("### 4. Electromagnetic Damping")
        st.markdown("**Malmstrom AFB, 1967**")
        v_e = v_eff(V_electronics, chi_global)
        
        if chi_global <= 0.90:
            st.markdown(f"**V_eff = {V_electronics} × (1 - {chi_global}) = <span style='color:red'>{v_e:,.2f} V</span>**", unsafe_allow_html=True)
        else:
            st.markdown(f"**V_eff = {V_electronics} × (1 - {chi_global}) × exp(-k) = <span style='color:red'>{v_e:,.4f} V</span>**", unsafe_allow_html=True)
            st.warning("⚡ SEVERE VACUUM IMPEDANCE CUTOFF: Electronics strictly suppressed.")

    st.markdown("---")
    
    st.markdown("### 5. Harmonic Re-entry Decay (Whiplash Mitigation)")
    k_factor = st.slider("Re-entry Damping Factor (k)", 0.1, 10.0, 2.0, 0.1)
    chi_safe = 0.05
    if chi_global > chi_safe:
        t_safe = -np.log(chi_safe / chi_global) / k_factor
        st.markdown(f"**χ(t) = χ_init e^(-kt) | Safe standard-spacetime inertia (χ < {chi_safe}) reached in: <span style='color:orange'>{t_safe:.2f} seconds</span>**", unsafe_allow_html=True)
        st.info("A rapid saturation drop (high k) violently reconnects the mass to the 3D manifold, inducing catastrophic G-force 'whiplash'. Slower decay buffers the inertial wave.")
    else:
        st.markdown(f"**Craft is natively operating at safe inertia (χ = {chi_global}). No re-entry buffering required.**")

    st.markdown("---")
    vc = v_core(univ_R, chi_global)
    st.info(f"**Core Highway Traversable Volume (V_core): {vc:.3e} m³** — Unlocked via the master 4D Radius scaler.")
    
    st.markdown("### 🚀 Sub-Manifold Sync Simulator")
    
    uap_container = st.empty()
    
    def draw_uap(target_phase, is_anim=False):
        y_craft = -np.sin(target_phase) * chi_global  
        df_wh = pd.DataFrame({"Spacetime X": np.linspace(0, np.pi, 50)})
        df_wh["Curvature Y"] = -np.sin(df_wh["Spacetime X"]) * chi_global
        
        fig_wh = go.Figure()
        fig_wh.add_trace(go.Scatter(x=df_wh["Spacetime X"], y=df_wh["Curvature Y"], fill='tozeroy', name="Wormhole Throat Limit"))
        fig_wh.add_trace(go.Scatter(x=[target_phase], y=[y_craft], mode='markers', marker=dict(size=25, color='lime', symbol='triangle-down'), name="UAP Trajectory"))
        fig_wh.update_layout(
            title="Active UAP Dive Trajectory (Arc Preserved)", xaxis_title="Dimensional Spacing", yaxis_title="Curvature Droop", 
            height=300, margin=dict(l=0, r=0, b=0, t=40), yaxis=dict(range=[-1.1, 0.1]), xaxis=dict(range=[0, np.pi])
        )
        
        k = f"uap_anim_{time.time_ns()}" if is_anim else "uap_static_main"
        uap_container.plotly_chart(fig_wh, use_container_width=True, key=k)

    if st.button("▶ Deploy UAP Dive Sequence", key="launch_uap"):
        for phase in np.linspace(0, np.pi, 20):
            draw_uap(phase, is_anim=True)
            time.sleep(0.04)
        draw_uap(np.pi / 2, is_anim=False) 
    else:
        draw_uap(np.pi / 2, is_anim=False)

# ==================== TAB 4: THEORY ====================
with t4:
    st.subheader("Theory & Axioms")
    
    st.markdown("### 1. Metric Saturation Invariant (χ)")
    st.code("χ = C / C_max ≤ 1")
    st.markdown("**Explanation:** Spacetime curvature (C) cannot exceed a maximum capacity (C_max).")
    
    st.markdown("### 2. Effective Mass Negation (m_eff)")
    st.code("m_eff = m_0 √(1 - χ²)")
    st.markdown("**Explanation:** Saturated vacuum evaporates the inertial connection to the universe.")

    st.markdown("### 3. Aerodynamic Drag Suppression (F_drag)")
    st.code("F_drag = F_0 √(1 - χ²)")
    st.markdown("**Explanation:** Standard fluid interactions cease, extinguishing friction and sonic booms.")

    st.markdown("### 4. Minimum Standoff Distance (D_msd)")
    st.code("D_msd = R [χ / (1 - χ)]^(1/3)")
    st.markdown("**Explanation:** Saturation boundaries form massive kinetic repulsion spheres.")

    st.markdown("### 5. Electromagnetic Damping (V_eff)")
    st.code("V_eff = V_0 (1 - χ)")
    st.markdown("**Explanation:** Vacuum impedance destroys standard voltage conductivity.")

    st.markdown("### 6. 4D Highway Volume (V_core)")
    st.code("V_core = 0.5 π² R⁴ (1 - √(1 - χ²))")
    st.markdown("**Explanation:** Quantifies usable 4D interior space for sub-manifold fleets.")

    st.markdown("### 7. Harmonic Re-entry Decay (χ_t)")
    st.code("χ(t) = χ_init e^(-kt)")
    st.markdown("**Explanation:** Buffers structural whiplash upon exiting deep saturation chords.")
    
    st.markdown("### 8. Wormhole Chord Distance (L)")
    st.code("L = √(Σ(Δxi)² + (Δw)²)")
    st.markdown("**Explanation:** Pythonic proof of purely geometric, traversable 4D shortcuts.")

st.caption("CBQG v10.5.1 © Dr. Anthony Omar Peña, D.O. — All rights reserved.")
