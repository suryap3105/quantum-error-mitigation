import numpy as np
import gym
from gym import spaces
from vqe_qem.strategies import Strategy
from vqe_qem.sampling_eval import evaluate_point
from vqe_qem.h2_system import build_h2_hamiltonian

class QEMEnv(gym.Env):
    """
    RL Environment for Quantum Error Mitigation.
    State: [gamma, R, step_idx] (simplified)
    Action: Strategy (0: Baseline, 1: DD, 2: Sym, 3: Hybrid)
    Reward: -Error - alpha*Discard - beta*Cost
    """
    def __init__(self):
        super().__init__()
        
        self.strategies = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
        self.action_space = spaces.Discrete(len(self.strategies))
        
        # Observation: [gamma, R]
        # gamma in [0, 0.2], R in [0.5, 2.5]
        self.observation_space = spaces.Box(low=0.0, high=3.0, shape=(2,), dtype=np.float32)
        
        self.gammas = [0.025, 0.08, 0.135]
        self.bond_lengths = [0.5, 0.74, 1.0, 1.5, 2.0, 2.5]
        
        self.current_gamma = 0.0
        self.current_R = 0.0
        self.steps = 0
        self.max_steps = 10 # Episodes per reset
        
    def reset(self):
        self.steps = 0
        self.current_gamma = np.random.choice(self.gammas)
        self.current_R = np.random.choice(self.bond_lengths)
        return np.array([self.current_gamma, self.current_R], dtype=np.float32)
        
    def step(self, action):
        strategy = self.strategies[action]
        
        # Get Ground Truth
        _, _, fci_energy = build_h2_hamiltonian(self.current_R)
        
        # Evaluate
        stats = evaluate_point(self.current_R, self.current_gamma, strategy, fci_energy)
        
        error_mHa = abs(stats["mean_energy"] - fci_energy) * 1000.0
        discard = stats["discard_rate"]
        
        # Cost function
        # Baseline: 0, DD: 1, Sym: 0, Hybrid: 1 (Active cost)
        cost = 0.0
        if strategy in [Strategy.DD, Strategy.HYBRID]:
            cost = 1.0
            
        # Reward
        # We want to minimize error and discard
        # r = - error - 100 * discard - 10 * cost
        reward = -error_mHa - 50.0 * discard - 5.0 * cost
        
        self.steps += 1
        done = self.steps >= self.max_steps
        
        # Next state (random walk for now, or fixed sequence)
        self.current_R = np.random.choice(self.bond_lengths)
        
        return np.array([self.current_gamma, self.current_R], dtype=np.float32), reward, done, {}
