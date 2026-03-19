import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="CBQG v10.5.1 Universal Engine", layout="wide")
st.title("🌌 CBQG v10.5.1 — Universal Simulation Engine")
st.markdown("**Sovereign Research Lead:** Dr. Anthony Omar Peña, D.O., LT, MC, USN (Vet) | cbqg.org | Version 10.5.1 — March 18, 2026")
st.caption("All mechanics derived solely from C ≤ C_max. Metric Radial Depth is a functional saturation coordinate.")

# ====================== SESSION STATE ======================
if "chi_global" not in st.session_state: st.session_state.chi_global = 0.50
if "t_anim" not in st.session_state: st.session_state.t_anim = 0.0
if "playing" not in st.session_state: st.session_state.playing = False

# ====================== SIDEBAR ======================
st.sidebar.header("Master Controls")
chi_global = st.sidebar.slider("Global Saturation χ", 0.001, 1.01, st.session_state.chi_global, 0.01)
st.session_state.chi_global = chi_global
univ_R = st.sidebar.number_input("Universal 4D Radius (R, meters)", 1e20, 1e26, 1e22)

# ====================== CORE MATH ======================
def m_eff(m0, chi): return m0 * np.sqrt(max(0, 1 - chi**2))
def f_drag(f0, chi): return f0 * np.sqrt(max(0, 1 - chi**2))
def d_msd(r, chi): return r * (chi / (1 - chi + 1e-9))**(1/3)
def v_eff(v0, chi): return v0 * (1 - chi)
def v_core(R, chi): return 0.5 * np.pi**2 * R**4 * (1 - np.sqrt(max(0, 1 - chi**2)))
def chi_decay(chi_init, k, t): return chi_init * np.exp(-k * t)

# ====================== TABS ======================
t1, t2, t3, t4 = st.tabs([
    "🌌 1. COSMIC REALITY (3D/4D)",
    "🛸 2. 4D HIGHWAY TRANSIT",
    "🎖️ 3. MILITARY FORENSICS",
    "ℹ️ THEORY & AXIOMS"
])

# ==================== TAB 1: COSMIC REALITY ====================
with t1:
    st.subheader("Cosmic Reality — Geometric Saturation")
    st.markdown("### **Core Postulate:** The curvature invariant C reaches a universal ceiling ($C_{max}$). Therefore, $\chi = C / C_{max} \le 1$.")
    st.markdown("<h3 style='color:red;'>🚨 χ=1 IS ABSOLUTE GEOMETRIC SATURATION (C_max) 🚨</h3>", unsafe_allow_html=True)
    
    view_mode = st.radio("Select Reality Representation:", ["3D Spacetime (Gravity Well)", "4D Hypersphere (Pulsating)"], horizontal=True)
    
    if view_mode == "3D Spacetime (Gravity Well)":
        st.write("Visualizing a 3D gravitational well where the depth (curvature) is strictly bounded by $C_{max}$ ($\chi=1$).")
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        xx, yy = np.meshgrid(x, y)
        r = np.sqrt(xx**2 + yy**2)
        
        # Depth without bounds goes to infinity at r=0
        depth_nominal = -1.0 / (r + 0.1)
        
        # limit max depth based on chi_global. chi=1 -> max depth.
        max_depth = -3.0 * chi_global
        zz = np.maximum(depth_nominal, max_depth)
        
        fig3d = go.Figure(data=[go.Surface(z=zz, x=xx, y=yy, colorscale='Viridis', opacity=0.8)])
        # Highlight saturation plane
        fig3d.add_trace(go.Surface(z=np.full_like(zz, -3.0), x=xx, y=yy, showscale=False, opacity=0.2, colorscale='Reds', name='C_max (χ=1) Limit', hoverinfo='name', showlegend=True))
        
        fig3d.update_layout(title="3D Spacetime: Curvature bounded horizontally by χ=1 (C_max)", 
                            scene=dict(zaxis=dict(range=[-4, 0])))
        st.plotly_chart(fig3d, use_container_width=True)

    else:
        st.write("Visualizing the pulsating 4D Hypersphere geometry.")
        play = st.button("▶ Play Lifecycle" if not st.session_state.playing else "⏸ Pause")
        if play: st.session_state.playing = not st.session_state.playing
        if st.button("Reset"): st.session_state.t_anim = 0.0
        if st.session_state.playing:
            st.session_state.t_anim += 0.08
            st.rerun()
        t = st.session_state.t_anim
        chi_t = np.clip(1 / np.cosh(t % 8 - 4), 0.001, 1.0)
        r_t = univ_R / (chi_t + 0.01)
        st.metric("Pulsation χ", f"{chi_t:.3f}")
        st.metric("Hypersphere Radius", f"{r_t:.2e} m")
        if chi_t > 0.95:
            st.error("BIG BOUNCE — r_min floor engaged (χ limits reach C_max)")
        else:
            st.success("Stable Expansion")
            
        u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
        fig_life = go.Figure(data=go.Surface(
            x=r_t * np.cos(u) * np.sin(v),
            y=r_t * np.sin(u) * np.sin(v),
            z=r_t * np.cos(v),
            opacity=0.8, colorscale="Plasma"))
        fig_life.update_layout(title="Pulsating 4D Hypersphere Lifecycle", height=500)
        st.plotly_chart(fig_life, use_container_width=True)

# ==================== TAB 2: 4D HIGHWAY ====================
with t2:
    st.subheader("4D Highway Transit — Saturation Bridge & Wormhole Creation")
    st.markdown("Set points on the 4D hypersphere surface. When their saturation $\chi$ reaches 1, they form an internal chord—a **Saturation Bridge (Wormhole)** through the bulk, allowing zero-time transit via Metric Radial Depth.")
    
    colA, colB = st.columns([1, 2])
    with colA:
        st.markdown("### Craft Departure (Point A)")
        pt_a_theta = st.slider("Point A Theta", 0.0, np.pi, np.pi/4)
        pt_a_phi = st.slider("Point A Phi", 0.0, 2*np.pi, 0.0)
        pt_a_chi = st.slider("Point A Saturation χ", 0.0, 1.0, 0.5)

        st.markdown("### Craft Arrival (Point B)")
        pt_b_theta = st.slider("Point B Theta", 0.0, np.pi, 3*np.pi/4)
        pt_b_phi = st.slider("Point B Phi", 0.0, 2*np.pi, np.pi)
        pt_b_chi = st.slider("Point B Saturation χ", 0.0, 1.0, 0.5)
        
        is_wormhole = pt_a_chi > 0.95 and pt_b_chi > 0.95
        if is_wormhole:
            st.success("WORMHOLE ACTIVE: Saturation Bridge Formed! (χ ≈ 1)")
        else:
            st.warning("Insufficient Saturation: Both points must reach χ ≈ 1 to open bridge.")
            
        st.markdown("### Re-entry Constraints")
        k = st.slider("Re-entry Elasticity k", 0.1, 2.0, 0.5)
        t_re = st.slider("Re-entry Time (s)", 0, 15, 3)
        safe = chi_decay(max(pt_a_chi, pt_b_chi), k, t_re)
        st.metric("Safe Re-entry χ (Harmonic Decay)", f"{safe:.3f}", "WHIPLASH RISK" if safe > 0.2 else "SAFE")
        
        vcore = v_core(univ_R, max(pt_a_chi, pt_b_chi))
        st.metric("4D Highway V_core Capacity", f"{vcore:.2e} m⁴")
        
    with colB:
        fig2 = go.Figure()
        u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:40j]
        x_sph = univ_R * np.cos(u) * np.sin(v)
        y_sph = univ_R * np.sin(u) * np.sin(v)
        z_sph = univ_R * np.cos(v)
        
        # Transparent hypersphere surface
        fig2.add_trace(go.Surface(x=x_sph, y=y_sph, z=z_sph, opacity=0.15, colorscale="Blues", showscale=False))
        
        # Point A
        xa = univ_R * np.sin(pt_a_theta) * np.cos(pt_a_phi)
        ya = univ_R * np.sin(pt_a_theta) * np.sin(pt_a_phi)
        za = univ_R * np.cos(pt_a_theta)
        color_a = "red" if pt_a_chi > 0.95 else "orange"
        size_a = 5 + 15 * pt_a_chi
        fig2.add_trace(go.Scatter3d(x=[xa], y=[ya], z=[za], mode='markers+text', marker=dict(size=size_a, color=color_a), text=["Dep A"], textposition="top center", name="Point A"))
        
        # Point B
        xb = univ_R * np.sin(pt_b_theta) * np.cos(pt_b_phi)
        yb = univ_R * np.sin(pt_b_theta) * np.sin(pt_b_phi)
        zb = univ_R * np.cos(pt_b_theta)
        color_b = "red" if pt_b_chi > 0.95 else "orange"
        size_b = 5 + 15 * pt_b_chi
        fig2.add_trace(go.Scatter3d(x=[xb], y=[yb], z=[zb], mode='markers+text', marker=dict(size=size_b, color=color_b), text=["Arr B"], textposition="top center", name="Point B"))

        # Bridge
        if is_wormhole:
            # Transit animation: show dots along the chord
            num_steps = 30
            tx = np.linspace(xa, xb, num_steps)
            ty = np.linspace(ya, yb, num_steps)
            tz = np.linspace(za, zb, num_steps)
            fig2.add_trace(go.Scatter3d(x=tx, y=ty, z=tz, mode='lines', line=dict(width=10, color='lime'), name="Saturation Bridge / Chord"))
            
            # Show transit craft traveling through the wormhole
            fig2.add_trace(go.Scatter3d(x=tx, y=ty, z=tz, mode='markers', marker=dict(size=5, color='white'), name="Transit Craft"))

        fig2.update_layout(title="4D Saturation Bridge — Interactive Hypersphere Chords", height=600, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# ==================== TAB 3: MILITARY FORENSICS ====================
with t3:
    st.subheader("Addendum B: Kinematic Sensor Correlation (Military Forensics)")
    st.markdown("All observed anomalous kinematics derived directly from the CBQG limit $\chi = C/C_{max} \le 1$. By controlling Geometric Saturation, all subsequent phenomena are achieved.")
    
    m0 = st.slider("Craft Baseline Mass (kg)", 1000.0, 100000.0, 5000.0)
    drag_base = 1000.0
    R_craft = 10.0
    V_electronics = 120.0 # Volts baseline
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Instantaneous Acceleration")
        st.markdown("**USS Princeton, 2004 - AN/SPY-1**")
        st.markdown("*m_eff = m₀ √(1 - χ²)*")
        m_e = m_eff(m0, chi_global)
        st.info(f"As $\chi \\to 1$, Effective Mass drops to 0. At current Global $\chi={chi_global:.3f}$, **$m_{{eff}} = {m_e:.1f}$ kg**.")
        st.progress(max(0.0, min(1.0, 1.0 - m_e/m0)))

        st.markdown("### 3. Minimum Standoff (Mirroring)")
        st.markdown("**Nimitz & Roosevelt Radar/Visual**")
        st.markdown("*D_msd = R [χ / (1 - χ)]^(1/3)*")
        d_m = d_msd(R_craft, chi_global)
        st.info(f"Saturation gradient repulsion creates a standoff sphere of **{d_m:.1f} meters** around the craft before desaturation instability.")
        
    with col2:
        st.markdown("### 2. No Sonic Boom")
        st.markdown("**Nimitz, 2004 - Pilot Testimony**")
        st.markdown("*F_drag = F₀ √(1 - χ²)*")
        f_d = f_drag(drag_base, chi_global)
        st.info(f"Craft creates a Metric Slipstream. Drag reduces to **{f_d/drag_base*100:.1f}%** of normal. Atmosphere slides through the manifold seamlessly.")
        st.progress(max(0.0, min(1.0, 1.0 - f_d/drag_base)))
        
        st.markdown("### 4. Electromagnetic Damping")
        st.markdown("**Malmstrom AFB, 1967 - Launch Control**")
        st.markdown("*V_eff = V₀ (1 - χ)*")
        v_e = v_eff(V_electronics, chi_global)
        st.info(f"Saturation increases vacuum impedance. Missile electronics available voltage drops to **{v_e:.1f} V** (from {V_electronics} V).")

    # Data Plot summarizing these effects
    chi_range = np.linspace(0, 1, 100)
    df_plot = pd.DataFrame({
        "χ (Saturation)": chi_range,
        "Mass %": np.sqrt(np.maximum(0, 1 - chi_range**2)) * 100,
        "Voltage %": (1 - chi_range) * 100
    })
    
    fig_mil = go.Figure()
    fig_mil.add_trace(go.Scatter(x=df_plot["χ (Saturation)"], y=df_plot["Mass %"], name="Effective Mass & Drag %", line=dict(color='blue', width=3)))
    fig_mil.add_trace(go.Scatter(x=df_plot["χ (Saturation)"], y=df_plot["Voltage %"], name="Available Voltage %", line=dict(color='red', width=3)))
    fig_mil.update_layout(title="Kinematic Decay vs Geometric Saturation (χ)", xaxis_title="Saturation χ", yaxis_title="% of Baseline", height=400)
    st.plotly_chart(fig_mil, use_container_width=True)

# ==================== TAB 4: THEORY ====================
with t4:
    st.subheader("Core Axioms (Plain Text)")
    st.code("""
χ = C / C_max ≤ 1
m_eff = m₀ √(1 - χ²)
F_drag = F₀ √(1 - χ²)
D_msd = R [χ / (1 - χ)]^(1/3)
V_eff = V₀ (1 - χ)
V_core = 0.5 π² R⁴ (1 - √(1 - χ²))
χ(t) = χ_init e^(-kt)
""")
    st.info("Falsifiable via CMB-S4, LiteBIRD, NIST mass-reduction tests.")

st.caption("CBQG v10.5.1 © Dr. Anthony Omar Peña, D.O. — All rights reserved.")
