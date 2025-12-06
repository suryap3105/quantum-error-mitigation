from enum import Enum

class Strategy(str, Enum):
    BASELINE = "baseline"
    DD = "dd"
    SYM = "sym"
    HYBRID = "hybrid"
    RL = "rl"
