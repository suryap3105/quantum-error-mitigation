import torch
import torch.optim as optim
import numpy as np
from .env import QEMEnv
from .policy import PolicyNet

def train_ppo():
    env = QEMEnv()
    policy = PolicyNet(input_dim=2, output_dim=4)
    optimizer = optim.Adam(policy.parameters(), lr=1e-3)
    
    num_episodes = 500
    
    print("Starting RL Training...")
    
    for episode in range(num_episodes):
        state = env.reset()
        log_probs = []
        rewards = []
        
        done = False
        while not done:
            state_tensor = torch.FloatTensor(state)
            dist = policy(state_tensor)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            next_state, reward, done, _ = env.step(action.item())
            
            log_probs.append(log_prob)
            rewards.append(reward)
            state = next_state
            
        # Compute returns
        returns = []
        G = 0
        for r in reversed(rewards):
            G = r + 0.99 * G
            returns.insert(0, G)
            
        returns = torch.tensor(returns)
        returns = (returns - returns.mean()) / (returns.std() + 1e-9)
        
        # Update policy
        policy_loss = []
        for log_prob, G in zip(log_probs, returns):
            policy_loss.append(-log_prob * G)
            
        optimizer.zero_grad()
        policy_loss = torch.stack(policy_loss).sum()
        policy_loss.backward()
        optimizer.step()
        
        if (episode+1) % 50 == 0:
            print(f"Episode {episode+1}, Total Reward: {sum(rewards):.2f}")
            
    print("Training Complete.")
    torch.save(policy.state_dict(), "rl_agent/policy.pth")

if __name__ == "__main__":
    train_ppo()
