import torch
import numpy as np
from agents.dqn_agent import DQNAgent
from  env.mininet_env  import MininetNetworkEnvironment

def demonstrate_trained_agent(model_path="dqn_model.pth", episodes=3):
    env = MininetNetworkEnvironment()
    state_dim = env.state_space
    action_dim = env.action_space

    # Load trained agent
    agent = DQNAgent(state_dim, action_dim)
    agent.model.load_state_dict(torch.load(model_path))
    agent.model.eval()  # Turn off dropout, etc.
    agent.epsilon = 0.0  # Disable exploration

    for episode in range(episodes):
        print(f"\n==== Episode {episode+1} ====")
        state = env.reset()
        total_reward = 0

        for step in range(env.episode_length):
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            state = next_state
            total_reward += reward

            print(f"Step {step+1}: Action={action}, Reward={reward:.2f}, Perf={info['performance']:.2f}")

            if done:
                break

        print(f"Total Episode Reward: {total_reward:.2f}")

    # Cleanup Mininet
    env.cleanup()

if __name__ == "__main__":
    demonstrate_trained_agent()
