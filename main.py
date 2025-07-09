from agents.dqn_agent import DQNAgent
from utils.replay_buffer import ReplayBuffer
from env.mininet_env import MininetNetworkEnvironment
import numpy as np
import torch
import os
from datetime import datetime

def train_dqn_agent():
    env = MininetNetworkEnvironment()
    state_dim = env.state_space
    action_dim = env.action_space

    agent = DQNAgent(state_dim, action_dim)
    replay_buffer = ReplayBuffer()

    episodes = 10
    batch_size = 64
    target_update_freq = 10

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0

        for t in range(env.episode_length):
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)

            replay_buffer.add(state, action, reward, next_state, float(done))
            agent.train(replay_buffer, batch_size)

            state = next_state
            total_reward += reward

            if done:
                break

        if episode % target_update_freq == 0:
            agent.update_target()

        print(f"Episode {episode+1}, Total Reward: {total_reward:.2f}, Epsilon: {agent.epsilon:.2f}")

    # Save model
    torch.save(agent.model.state_dict(), "dqn_model.pth")

    # Cleanup
    env.cleanup()

if __name__ == "__main__":
    train_dqn_agent()
