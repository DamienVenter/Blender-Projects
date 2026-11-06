"""Physical parameters for the whip demo.

Every value carries its source. "PHOTO" means measured on the Honda studio
left profile (reference/crf250r-2026/studio_left-profile_..., 1292 px/m,
scale from the wheelbase). "EST" means an engineering estimate, to be replaced
by measurement or research. Units: SI (m, kg, s, N, rad unless named _deg).

Coordinate conventions
- World: X along the jump (forward), Y to the rider's left, Z up. Lip edge at X=0.
- Bike frame (2D sagittal): u forward, w up, origin on the ground under the rear
  axle with the bike at full suspension extension. Lateral v to the left.
"""
import math

# --- Site: Montecasino, Fourways, Johannesburg (KOTW 2025), research/kotw-2025.md
SITE_ELEVATION = 1480.0          # m, Fourways (EST from regional elevation)
LATITUDE_DEG = -26.02            # research/kotw-2025.md
AIR_TEMP_C = 22.0                # late-November late afternoon (EST)


def gravity(lat_deg=LATITUDE_DEG, h=SITE_ELEVATION):
    """WGS84 normal gravity with free-air correction."""
    s = math.sin(math.radians(lat_deg))
    s2 = math.sin(math.radians(2 * lat_deg))
    return 9.780327 * (1 + 0.0053024 * s * s - 0.0000058 * s2 * s2) - 3.086e-6 * h


def air_density(h=SITE_ELEVATION, t_c=AIR_TEMP_C):
    """ISA pressure at altitude, ideal gas density at the given temperature."""
    p = 101325.0 * (1 - 2.25577e-5 * h) ** 5.25588
    return p / (287.05 * (t_c + 273.15))


G = gravity()                    # about 9.786 m/s^2
RHO = air_density()              # about 1.00 kg/m^3
CDA = 0.80                       # m^2, upright MX rider + bike (EST, 0.7 to 0.9 typical)

# --- Jump geometry: research/fmx-ramp-physics-whip.md sections 1.5 and 2.3
GAP = 23.0                       # m lip edge to knuckle: KOTW's "twenty-three-metre competition ramp"
                                 # (Damien: follow KOTW measurements; the brief's 75 ft is 22.86 m)
LIP_HEIGHT = 2.51                # m, Destruction Ramps 8'3" comp ramp for 75 ft gaps; FIM 2.50 to 3.20
RAMP_RADIUS = 9.1                # m, constant radius tangent to the ground ("Aussie/EU consistent radius")
LIP_ANGLE_DEG = math.degrees(math.acos(1 - LIP_HEIGHT / RAMP_RADIUS))   # 43.6 deg, pure arc to the lip
RAMP_WIDTH = 1.5                 # m deck width, scaled from KOTW photo 07 using the 827 mm overall bike width
                                 # (research listing said 1.07 m, low confidence; FIM minimum 0.80)
KNUCKLE_HEIGHT = 4.00            # m, FIM 4.00 to 4.50 (crest 1.49 m above the lip; touchdown about lip height)
DECK_LENGTH = 1.5                # m, FIM table in front of the knuckle
BACK_FACE_ANGLE_DEG = 50.0       # deg, sculpted face toward the ramp (EST, KOTW "flat trimmed faces")
KNUCKLE_RADIUS = 0.75            # m, small natural rounding of the knuckle edge (0.5 to 1.0 recommended)
LANDING_ANGLE_DEG = 42.0         # deg, upper downslope (physics-derived)
LANDING_BOTTOM_RADIUS = 10.36    # m, concave run-out to flat (physics-derived, about 4 g at the bottom)
LANDING_WIDTH = 5.0              # m at the crest (recommended about 5 m, FIM table at least 2.5 m)
TOUCHDOWN_PAST_KNUCKLE = 1.5     # m horizontal, rear tyre contact (research: about 1.5 m past the knuckle)

# --- Bike: 2026 Honda CRF250R, South African (ED-type) spec, research/crf250r-2026.md
WHEELBASE = 1.483                # m, Honda official (all markets)
R_FRONT = 0.350                  # m, Pirelli MX32 80/100-21: nominal 0.693 OD, PHOTO 0.706
R_REAR = 0.3325                  # m, Pirelli MX32 100/90-19 (EST from nominal 0.663 OD + knobs)
RAKE_DEG = 28.4                  # deg, 28 deg 24 min, Honda South Africa 2026 spec sheet (ZA26)
FORK_TRAVEL = 0.310              # m, Honda official
REAR_TRAVEL = 0.308              # m rear axle travel, Honda official
BIKE_MASS_TOTAL = 107.0          # kg wet, Honda South Africa (102 kg kerb, 107 kg wet)
BIKE_MASS_PARTS = [              # (name, kg, u, w): EST breakdown, scaled to BIKE_MASS_TOTAL below
    ("front_wheel", 8.0, WHEELBASE, R_FRONT),
    ("rear_wheel", 9.0, 0.0, R_REAR),
    ("fork_clamps_bars", 12.0, 1.25, 0.75),
    ("engine", 28.0, 0.78, 0.50),
    ("frame", 9.0, 0.75, 0.75),
    ("swingarm_linkage_shock", 8.0, 0.35, 0.47),
    ("fuel_and_tank", 6.2, 0.80, 0.95),
    ("radiators_coolant", 4.0, 1.00, 0.85),
    ("exhaust", 4.0, 0.25, 0.80),
    ("seat_plastics_subframe_airbox", 8.0, 0.40, 0.90),
    ("electrics_misc", 4.0, 0.65, 0.75),
    ("chain_sprockets_brakes", 4.0, 0.40, 0.45),
]
_scale = BIKE_MASS_TOTAL / sum(p[1] for p in BIKE_MASS_PARTS)
BIKE_MASS_PARTS = [(n, m * _scale, u, w) for n, m, u, w in BIKE_MASS_PARTS]
WHEEL_SPIN_INERTIA_FRONT = 0.60  # kg m^2 about the axle (EST: tyre+tube 5 kg at 0.31 m, rim, hub)
WHEEL_SPIN_INERTIA_REAR = 0.71   # kg m^2 (EST: tyre+tube 6.5 kg at 0.30 m, rim, sprocket)

# Frame points (PHOTO), bike frame, full extension
REAR_AXLE = (0.0, R_REAR)
FRONT_AXLE = (WHEELBASE, R_FRONT)
SWINGARM_PIVOT = (0.567, 0.479)
FOOTPEG = (0.544, 0.410)         # ball-of-foot contact on the peg top. u: PHOTO. w: owner's manual
                                 # peg height 422 mm (static), less about 12 mm to the contact line
FOOTPEG_HALF_SPAN = 0.20         # m, lateral offset of each foot contact
GRIP = (0.943, 1.240)
GRIP_HALF_SPAN = 0.35            # m, grip centre lateral offset (bar ~0.80 m wide)

# Suspension (EST, tuned for sag in sim): spring along fork axis / at the rear wheel
FORK_K = 9000.0                  # N/m, both legs (about 0.46 kg/mm per leg)
FORK_AIR_GAIN = 0.8              # fork air-volume progression: extra k*T*GAIN*(s/T)^3 (EST)
FORK_C_COMP, FORK_C_REB = 1100.0, 1500.0   # N s/m (EST, zeta about 0.6)
REAR_K = 6000.0                  # N/m wheel rate at top of stroke
REAR_RISING = 0.6                # Pro-Link rising rate: wheel rate x (1 + RISING (s/T)^2) (EST)
REAR_C_COMP, REAR_C_REB = 1200.0, 1700.0   # N s/m at the wheel (EST, zeta about 0.6)
TARGET_SAG_FRONT = 0.075         # m with rider standing (EST typical)
TARGET_SAG_REAR = 0.105          # m race sag (typical 100 to 110 mm)
BUMP_START = 0.75                # fraction of travel where the hydraulic bottoming cone starts (EST)
BUMP_GAIN = 12.0                 # cone strength: extra force at full travel = GAIN * k * (1-START) * travel (EST)

# Drive
ENGINE_POWER = 28000.0           # W at the wheel, usable (EST, about 40 hp crank)
TYRE_MU = 0.9                    # traction coefficient, steel deck / prepared dirt (EST)

# Rider legs/arms as a spring-damper in the bike frame (EST). A skilled rider absorbs the ramp
# face and landing with muscles working eccentrically: heavily damped, no spring-back (zeta about 1.8).
# A passive, springy rider (zeta 0.5) pushes the rear into the ramp at the lip and over-rotates the
# bike nose-down (-86 deg/s measured in this model), which real riders do not do.
LEG_KW, LEG_CW = 13900.0, 4000.0   # N/m, N s/m along the bike's vertical (about 2 Hz)
LEG_KU, LEG_CU = 31000.0, 3000.0   # fore-aft
CROUCH_MAX, EXTEND_MAX = -0.30, 0.15  # m from the neutral attack pose

# --- Rider: Damien
RIDER_HEIGHT = 1.85              # m (Damien)
RIDER_MASS = 80.0                # kg body (EST, ask Damien)
GEAR_MASS = 8.0                  # kg helmet, boots, armour, kit (EST)
