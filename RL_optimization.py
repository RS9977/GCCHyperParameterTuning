import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from utils import get_gcc_optimization_passes
from benchmarks import *

from Beysian_opt import optimize_compiler_parameters

# Define the list of possible actions (integers from 0 to 10)
possible_actions = get_gcc_optimization_passes()
compile_args = '-I polybench-c-3.2/utilities -I polybench-c-3.2/linear-algebra/kernels/atax polybench-c-3.2/utilities/polybench.c polybench-c-3.2/linear-algebra/kernels/atax/atax.c -DPOLYBENCH_TIME'
class QNetwork(nn.Module):
    def __init__(self, num_states, num_actions):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(num_states, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, num_actions)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class DQNAgent:
    def __init__(self, num_actions, num_states, learning_rate=0.001, discount_factor=0.9, exploration_rate=1.0,
                 exploration_decay=0.995, min_exploration_rate=0.01, batch_size=32):
        self.num_actions = num_actions
        self.num_states = num_states
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.min_exploration_rate = min_exploration_rate
        self.batch_size = batch_size

        # Initialize Q-network and target Q-network
        self.q_network = QNetwork(num_states, num_actions)
        self.target_q_network = QNetwork(num_states, num_actions)
        self.update_target_network()

        # Initialize optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        # Initialize replay memory
        self.replay_memory = []
        self.replay_memory_capacity = 10000

    def update_target_network(self):
        self.target_q_network.load_state_dict(self.q_network.state_dict())

    def choose_action(self, state):
        if np.random.uniform(0, 1) < self.exploration_rate:
            # Explore: choose a random action
            return random.sample(possible_actions, random.randint(1, len(possible_actions)))
        else:
            # Exploit: choose the action with the highest Q-value
            with torch.no_grad():
                q_values = self.q_network(torch.tensor(state, dtype=torch.float32))
                action_indices = torch.argsort(q_values, descending=True)
                for i in range(len(action_indices)):
                    action = [possible_actions[idx] for idx in action_indices[:i+1].tolist()]
                    if action not in self.replay_memory:
                        return action

    def remember(self, state, action, reward, next_state, done):
        self.replay_memory.append((state, action, reward, next_state, done))
        if len(self.replay_memory) > self.replay_memory_capacity:
            self.replay_memory.pop(0)

    def experience_replay(self):
        if len(self.replay_memory) < self.batch_size:
            return

        minibatch = random.sample(self.replay_memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*minibatch)

        #print(states)

        states = torch.tensor(states, dtype=torch.float32)
        #actions = torch.tensor(actions)  # no need to convert to tensor
        rewards = torch.tensor(rewards, dtype=torch.float32)
        next_states = torch.tensor(next_states, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)

        # Compute Q-values
        q_values = self.q_network(states)
        selected_actions = torch.tensor([[action in a for action in possible_actions] for a in actions], dtype=torch.float32)
        q_values = (q_values * selected_actions).sum(dim=1)

        # Compute target Q-values using target Q-network
        with torch.no_grad():
            next_q_values = self.target_q_network(next_states)
            max_next_q_values = next_q_values.max(1)[0]
            target_q_values = rewards + (1 - dones) * self.discount_factor * max_next_q_values

        # Compute loss
        loss = nn.functional.mse_loss(q_values, target_q_values)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

def compile_and_evaluate(parameters, output_binary="tuned", numTest=20, compile_args='', optTarget=1, optPass='-O3', param_tune=False):
    #included_params = [param for param, include in parameters if include]
    
    # Build the compiler command with the selected parameters
    if param_tune:
        parameters = optimize_compiler_parameters(numIter=200, output_binary=output_binary,  numTest=numTest*5, compile_args=compile_args, optTarget=optTarget, optPass=optPass)

    compiler_command = "gcc -Werror -w "  + optPass + ' ' + compile_args

    i = 0
    for param_name, param_value in parameters.items():
        if i>255:
            break
        compiler_command += f" --param={param_name}={param_value}"
        i += 1
    
    # Compile the code and measure runtime
    try:
        subprocess.check_call((compiler_command+ ' -S').split())
        subprocess.check_call((compiler_command+' -o '  + output_binary+'.out').split())
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {i}")
        print(e.output)
        return 1e7#, "GCUPS": (-1e7, 1e7)}  # Return negative infinity in case of compilation failure
    
    # Measure runtime using your method
    if optTarget == 0:
        GCUPS = run_hyperfine_and_extract_time(output_binary+'.out')/100
    if optTarget==1:
        GCUPS = get_gcups_from_command(f"./{output_binary+'.out'}", numTest)
    elif optTarget==2:
        GCUPS = sum(count_instructions_in_directory('./')[0].values())
    elif optTarget==3:
        GCUPS = sum(get_asm_info('./'))/27279.0
    else:
        GCUPS = get_size_info(output_binary+'.out')/(17200*2)
    
    
    return GCUPS#{"size": (size, 0.0)}#, "GCUPS": (GCUPS, 2)}

def environment(action, compile_args, param_tune=False):
    #print(action)
    for a in action:
        compile_args += ' '
        compile_args += a
    #print(compile_args)
    return compile_and_evaluate({}, output_binary="tuned", numTest=40, compile_args=compile_args, optTarget=5, optPass='-O3', param_tune=param_tune)

def update_state(original_list, subset, occurrences_list):
    for string in subset:
        if string in original_list:
            index = original_list.index(string)
            occurrences_list[index] += 1
    return np.array(occurrences_list)

def best_seen(seen):
    if len(seen)==0:
        return 1000000
    else:
        return min([x*(-100*2) for x in seen])

def main():
    # Define the environment parameters
    inti_reward = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args, optTarget=5, optPass='-O3')
    print(inti_reward)
    with open('out.txt', 'w+') as file:
        file.write(f"initial size: {inti_reward*(100*2)}\n")
    num_actions = len(possible_actions)
    occurrences_list = [0 for i in range(len(possible_actions))]
    num_states = len(possible_actions)
    with open('out.txt', 'a+') as file:
        file.write(f"Num of possible actions: {len(possible_actions)}\n")
    # Create DQN agent  
    agent = DQNAgent(num_actions, num_states)

    # Training loop
    seen = []
    num_episodes = 50

    min = 1e10
    best_action = []
    for episode in range(num_episodes):
        state = np.zeros([num_states])
        inti_reward = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args, optTarget=0, optPass='-O3')
          # Initial state
        done = False
        while not done:
            # Choose action
            action = agent.choose_action(state)
            

            next_state = update_state(possible_actions, action, occurrences_list)
            #print(next_state)
            # Perform action
            #next_state = np.random.rand(num_states)  # Example: transition to a random state
            reward = -environment(action, compile_args, param_tune=False)  # Example: get a random reward
            if (-reward) < min:
                min = -reward
                best_action = action
            if reward not in seen:
                seen.append(reward)
            done = np.random.rand() < 0.1  # Example: random termination

            #print(reward)
            # Remember experience
            agent.remember(state, action, reward, next_state, done)

            # Update state
            state = next_state

            # Experience replay
            agent.experience_replay()
        with open('out.txt', 'a+') as file:
            file.write(f"episode: {episode}|\t Explored Space: {len(seen)}|\t Best: {best_seen(seen)}|\tSeen: {[x*(-100*2) for x in seen]}\n")
        print(f"episode: {episode}|\t Explored Space: {len(seen)}",  end='\r')

    best1 = environment(best_action, compile_args, param_tune=False)*(100*2)
    best2 = environment(best_action, compile_args, param_tune=True)*(100*2)
    with open('out.txt', 'a+') as file:
        file.write(f"Best w/o param: {best1}|\t Best w/ param: {best2}")
    

if __name__ == "__main__":
    main()
