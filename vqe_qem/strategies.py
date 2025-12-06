from enum import Enum

class Strategy(str, Enum):
    BASELINE = "baseline"
    DD = "dd"
    SYM = "sym"
    HYBRID = "hybrid"
    RL = "rl"

class NoiseType(str, Enum):
    AMPLITUDE_DAMPING = "amplitude_damping" # T1
    PHASE_DAMPING = "phase_damping"         # T2
    DEPOLARIZING = "depolarizing"           # Depol
    COMPOSITE = "composite"                 # Real Hardware
