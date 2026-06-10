import math

# Geometry (worked example defaults)
B, H, t_w, t_s = 2.5, 2.0, 0.30, 0.30
B_ext = B + 2*t_w      # 3.10
H_ext = H + 2*t_s      # 2.60
LL = 20.6
lane_width = 3.0
H_c = 0.2 + 0.3 + 0.5  # 1.0 m

g_road, t_road = 24.0, 0.20
g_sub,  t_sub  = 20.0, 0.30
g_fill, t_fill = 19.0, 0.50

W_road = g_road*t_road*B_ext
W_sub  = g_sub *t_sub *B_ext
W_fill = g_fill*t_fill*B_ext
W_road_max = W_road*1.55
W_road_min = W_road*0.60
g_Sd = 1.15
W_conc = 25.0*(B_ext*H_ext - B*H)
N_Gkmax = W_conc + g_Sd*(W_road_max + W_sub + W_fill)
N_Gkmin = W_conc + (W_road_min + W_sub + W_fill)
s_top = W_road_max/B_ext + (W_sub + W_fill)/B_ext   # 22.94
s_bot = s_top + g_fill*H_ext                         # 72.34
rF = (1 - H_c/2)**2                                  # 0.25
Q_vk = 151.0   # worked example LM3 vertical
phi_fnd_k = math.radians(32)

LS = {
    'SLS': dict(Ka=0.33, Ka_tr=0.33, Kmax=0.60, gGu=1.00, gQ=1.00, g_phi=1.00),
    'EQU': dict(Ka=0.44, Ka_tr=0.37, Kmax=0.60, gGu=1.10, gQ=1.35, g_phi=1.25),
    'C1' : dict(Ka=0.40, Ka_tr=0.33, Kmax=0.72, gGu=1.35, gQ=1.35, g_phi=1.00),
    'C2' : dict(Ka=0.49, Ka_tr=0.41, Kmax=0.84, gGu=1.00, gQ=1.35, g_phi=1.25),
}

EXAMPLE = {
    'SLS': dict(F_active=108.76, F_passive=74.32, friction=34.44, Rd=193,  UR=34.44/193),
    'EQU': dict(F_active=156.06, F_passive=78.04, friction=78.02, Rd=210,  UR=78.02/210),
    'C1' : dict(F_active=154.96, F_passive=113.95, friction=41.01, Rd=253, UR=41.01/253),
    'C2' : dict(F_active=151.01, F_passive=104.04, friction=46.97, Rd=166, UR=46.97/166),
}

def trapz_F(K, st, sb, h):
    return 0.5*K*(st+sb)*h

print("B.4 Sliding check — App vs Worked Example (LM3/SV196)")
print("="*80)

for name, p in LS.items():
    F_Ka   = trapz_F(p['Ka'],   s_top, s_bot, H_ext)
    F_Kmax = trapz_F(p['Kmax'], s_top, s_bot, H_ext)

    Q_udl   = 30.0 * p['Ka_tr'] * H_ext
    F_line  = 2*330*p['Ka_tr']*rF/lane_width
    braking = 0.25*1945/LL
    F_h_tr  = p['gQ']*(Q_udl + F_line + braking)
    F_drv   = max(0.0, F_Ka + F_h_tr - F_Kmax)

    phi_d = math.atan(math.tan(phi_fnd_k) / p['g_phi'])
    V_u   = p['gGu']*N_Gkmax + p['gQ']*Q_vk
    Rfric = math.tan(phi_d)*V_u
    UR    = F_drv/Rfric if Rfric > 0 else 999

    ex = EXAMPLE[name]

    print(f"\n--- {name} ---")
    print(f"  Earth active  : app {F_Ka:.2f}  ex {ex['F_active'] - (ex['F_active'] - ex['F_passive'] + ex['friction']):.2f}  (Ka*sig*H, no traffic)")
    print(f"  Earth passive : app {F_Kmax:.2f}  ex {ex['F_passive']:.2f}")
    print(f"  F_h_tr (traffic): app {F_h_tr:.2f} kN  (udl {Q_udl:.2f} + F_line {F_line:.2f} + brk {p['gQ']*braking:.2f})")
    print(f"  Friction needed : app {F_drv:.2f} kN   ex {ex['friction']:.2f} kN   diff {F_drv - ex['friction']:+.2f} kN")
    print(f"  phi_fnd_d       : {math.degrees(phi_d):.2f} deg  (g_phi={p['g_phi']:.2f})")
    print(f"  V_u             : app {V_u:.1f} kN  (gGu={p['gGu']:.2f}*{N_Gkmax:.1f} + {p['gQ']:.2f}*{Q_vk:.0f})")
    print(f"  R_fric_B4       : app {Rfric:.1f} kN   ex {ex['Rd']:.0f} kN   diff {Rfric - ex['Rd']:+.1f} kN")
    print(f"  UR_B4_sl        : app {UR:.3f}   ex {ex['UR']:.3f}   diff {UR - ex['UR']:+.3f}")
