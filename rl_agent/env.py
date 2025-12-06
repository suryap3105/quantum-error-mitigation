import numpy as np
import gym
from gym import spaces
from vqe_qem.strategies import Strategy, NoiseType
from vqe_qem.sampling_eval import evaluate_point
from vqe_qem.system_factory import build_molecular_hamiltonian

class QEMEnv(gym.Env):
    """
    RL Environment for Quantum Error Mitigation.
    State: [gamma, R, noise_type_idx, last_error, last_discard, depth]
    Action: Strategy (0: Baseline, 1: DD, 2: Sym, 3: Hybrid)
    Reward: -Error - alpha*Discard - beta*Cost
    """
    def __init__(self, molecule_name="H2"):
        super().__init__()
        
        self.molecule_name = molecule_name
        self.strategies = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
        self.action_space = spaces.Discrete(len(self.strategies))
        
        # Observation: [gamma, R, noise_type_idx, last_error, last_discard, depth]
        # gamma: [0, 0.2]
        # R: [0.5, 3.0]
        # noise_idx: [0, 3]
        # last_error: [0, 1000] (mHa)
        # last_discard: [0, 1]
        # depth: [0, 100]
        self.observation_space = spaces.Box(low=0.0, high=1000.0, shape=(6,), dtype=np.float32)
        
        self.gammas = [0.025, 0.08, 0.135]
        # Bond lengths depend on molecule
        if molecule_name == "H2":
            self.bond_lengths = [0.5, 0.74, 1.0, 1.5, 2.0, 2.5]
        elif molecule_name == "LiH":
            self.bond_lengths = [1.0, 1.2, 1.4, 1.6, 2.0, 2.5]
        elif molecule_name == "BeH2":
            self.bond_lengths = [1.0, 1.3, 1.6, 2.0, 2.5, 3.0]
        else:
            self.bond_lengths = [0.5, 1.0, 1.5, 2.0]

        self.noise_types = [NoiseType.AMPLITUDE_DAMPING, NoiseType.PHASE_DAMPING, NoiseType.DEPOLARIZING, NoiseType.COMPOSITE]
        
        self.current_gamma = 0.0
        self.current_R = 0.0
        self.current_noise_type = NoiseType.AMPLITUDE_DAMPING
        self.last_error = 0.0
        self.last_discard = 0.0
        self.depth = 9.0 
        
        self.steps = 0
        self.max_steps = 20 
        
    def reset(self):
        self.steps = 0
        self.current_gamma = np.random.choice(self.gammas)
        self.current_R = np.random.choice(self.bond_lengths)
        
        noise_idx = np.random.randint(0, len(self.noise_types))
        self.current_noise_type = self.noise_types[noise_idx]
        
        self.last_error = 0.0
        self.last_discard = 0.0
        
        return np.array([self.current_gamma, self.current_R, float(noise_idx), self.last_error, self.last_discard, self.depth], dtype=np.float32)
        
    def step(self, action):
        strategy = self.strategies[action]
        
        # Get Ground Truth
        _, _, fci_energy = build_molecular_hamiltonian(self.molecule_name, self.current_R)
        
        # Evaluate
        stats = evaluate_point(self.current_R, self.current_gamma, strategy, fci_energy, self.current_noise_type)
        
        error_mHa = abs(stats["mean_energy"] - fci_energy) * 1000.0
        discard = stats["discard_rate"]
        
        # Update history
        self.last_error = error_mHa
        self.last_discard = discard
        
        # Cost function
        cost = 0.0
        if strategy in [Strategy.DD, Strategy.HYBRID]:
            cost = 1.0
            
        # Reward
        reward = -error_mHa - 50.0 * discard - 5.0 * cost
        
        self.steps += 1
        done = self.steps >= self.max_steps
        
        # Next state
        self.current_R = np.random.choice(self.bond_lengths)
        self.current_gamma = np.random.choice(self.gammas)
        
        noise_idx = np.random.randint(0, len(self.noise_types))
        self.current_noise_type = self.noise_types[noise_idx]
        
        state = np.array([self.current_gamma, self.current_R, float(noise_idx), self.last_error, self.last_discard, self.depth], dtype=np.float32)
        
        return state, reward, done, {}
