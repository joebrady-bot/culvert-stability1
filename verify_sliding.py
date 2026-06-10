import math
import lm3_loading

# ── Geometry (worked example defaults) ──────────────────────────────────────────
B, H, t_w, t_s = 2.5, 2.0, 0.30, 0.30
B_ext = B + 2*t_w      # 3.10
H_ext = H + 2*t_s      # 2.60
LL = 20.6
lane_width = 3.0
H_c = 0.2 + 0.3 + 0.5  # 1.0 m

g_road, t_road = 24.0, 0.20
g_sub,  t_sub  = 20.0, 0.30
g_fill, t_fill = 19.0, 0.50

W_conc = 25.0*(B_ext*H_ext - B*H)
W_road = g_road*t_road*B_ext
W_sub  = g_sub *t_sub *B_ext
W_fill = g_fill*t_fill*B_ext
W_road_max = W_road*1.55
g_Sd = 1.15
P_super = g_Sd*(W_road_max + W_sub + W_fill)   # superimposed dead
P_self  = W_conc                                # concrete self-weight

# Horizontal earth stresses (surcharge constant + backfill triangle)
s_top = W_road_max/B_ext + (W_sub + W_fill)/B_ext   # 22.94 (surcharge, no γSd)
s_bot = s_top + g_fill*H_ext                         # 72.34
rF = (1 - H_c/2)**2                                  # 0.25
phi_fnd_k = math.radians(32)

# LM3 SV196 vertical + braking from the real module (B_ext travel direction)
lm3 = lm3_loading.compute("SV196", B_ext=B_ext, LL=LL, H_c=H_c,
                          lane_width=lane_width, n_lanes=1)
Q_vk    = lm3.max_V_per_m
braking = lm3.braking.Q_brk_per_m

# ── Per-limit-state factors (matching app.py LS dict) ───────────────────────────
LS = {
    'SLS': dict(Ka=0.33, Ka_tr=0.33, Kmax=0.60, gGsup=1.00, gGself=1.00, gQ=1.00, g_phi=1.00),
    'EQU': dict(Ka=0.44, Ka_tr=0.37, Kmax=0.60, gGsup=1.05, gGself=1.05, gQ=1.35, g_phi=1.10),
    'C1' : dict(Ka=0.40, Ka_tr=0.33, Kmax=0.72, gGsup=1.20, gGself=1.35, gQ=1.35, g_phi=1.00),
    'C2' : dict(Ka=0.49, Ka_tr=0.41, Kmax=0.84, gGsup=1.00, gGself=1.00, gQ=1.15, g_phi=1.25),
}

# Worked example (PD6694-1 D. Childs), Table B.4 sliding, LM3/SV196
EXAMPLE = {
    'SLS': dict(active=108.76, passive=74.32, friction=34.44, Rd=193, UR=0.178),
    'EQU': dict(active=156.06, passive=78.04, friction=78.02, Rd=210, UR=0.372),
    'C1' : dict(active=154.96, passive=113.95, friction=41.01, Rd=253, UR=0.162),
    'C2' : dict(active=151.01, passive=104.04, friction=46.97, Rd=166, UR=0.283),
}

def earth(K, gsup, gself):
    F_rect = K * gsup  * s_top * H_ext
    F_tri  = K * gself * 0.5 * (s_bot - s_top) * H_ext
    return F_rect + F_tri

print(f"B.4 Sliding — App (new factor model) vs Worked Example  [LM3 Q_vk={Q_vk:.1f}, brk={braking:.2f}]")
print("=" * 84)
for name, p in LS.items():
    F_Ka   = earth(p['Ka'],   p['gGsup'], p['gGself'])
    F_Kmax = earth(p['Kmax'], p['gGsup'], p['gGself'])

    Q_udl  = 30.0 * p['Ka_tr'] * H_ext
    F_line = 2*330*p['Ka_tr']*rF/lane_width
    F_h_tr = p['gQ']*(Q_udl + F_line + braking)
    F_drv  = max(0.0, F_Ka + F_h_tr - F_Kmax)

    phi_d = math.atan(math.tan(phi_fnd_k) / p['g_phi'])
    V_u   = p['gGsup']*P_super + p['gGself']*P_self + p['gQ']*Q_vk
    Rfric = math.tan(phi_d)*V_u
    UR    = F_drv/Rfric

    ex = EXAMPLE[name]
    print(f"\n--- {name} ---")
    print(f"  active earth   : app {F_Ka:7.2f}      passive {F_Kmax:7.2f}  (ex active {ex['active']-ex['friction']-ex['passive']+ex['passive']+ex['friction']-ex['active']+ex['active']:.2f}/passive {ex['passive']:.2f})")
    print(f"  Friction needed: app {F_drv:7.2f}   ex {ex['friction']:7.2f}   diff {F_drv-ex['friction']:+.2f}")
    print(f"  R_d (friction) : app {Rfric:7.2f}   ex {ex['Rd']:7.0f}   diff {Rfric-ex['Rd']:+.2f}")
    print(f"  UR_B4_sliding  : app {UR:7.3f}   ex {ex['UR']:7.3f}   diff {UR-ex['UR']:+.3f}")
