import random
import subprocess
from Beysian_opt import optimize_compiler_parameters
from benchmarks import *
from utils import generate_periodic_function


compile_args = '-I polybench-c-3.2/utilities -I polybench-c-3.2/linear-algebra/kernels/atax polybench-c-3.2/utilities/polybench.c polybench-c-3.2/linear-algebra/kernels/atax/atax.c -DPOLYBENCH_TIME'



def compile_and_evaluate(parameters, output_binary="tuned", numTest=20, compile_args='', optTarget=0, optPass='', param_tune=False):
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
        #print('##########################################################################################')
        #print("1")
        GCUPS = run_hyperfine_and_extract_time(output_binary+'.out')
        if GCUPS <= 1:
            return 10000.0
        GCUPS /= 1000.0 
    elif optTarget==1:
        #print('##########################################################################################')
        #print("2")
        GCUPS = get_gcups_from_command(f"./{output_binary+'.out'}", numTest)/1000.0
    elif optTarget==2:
        #print('##########################################################################################')
        #print("3")
        GCUPS = sum(count_instructions_in_directory('./')[0].values())/1000.0
    elif optTarget==3:
        #print('##########################################################################################')
        #print("4")
        GCUPS = sum(get_asm_info('./'))/1000.0
    else:
        #print('##########################################################################################')
        #print("5")
        GCUPS = get_size_info(output_binary+'.out')/1000.0
    
    
    return GCUPS#{"size": (size, 0.0)}#, "GCUPS": (GCUPS, 2)}

def reward_cal(action, compile_args, param_tune=False):
    #print(action)
    for key, value in action.items():
        if value:
            compile_args += ' '
            compile_args += key
    #print(compile_args)
    return compile_and_evaluate({}, output_binary="tuned", numTest=40, compile_args=compile_args, optTarget=0, optPass='', param_tune=param_tune)


class EpsilonGreedyBinaryActions:
    def __init__(self, action_set, epsilon=0.1):
        self.action_set = action_set
        self.epsilon = epsilon
        self.counts = {action: [0, 0] for action in action_set}  # Counts for [not taken, taken]
        self.values = {action: [0.0, 0.0] for action in action_set}  # Values for [not taken, taken]
    
    def choose_actions(self, por_episode, eps=0.1):
        chosen_actions = {}
        for action in self.action_set:
            if random.random() < eps:
                chosen_actions[action] = random.choice([True, False])
            elif por_episode<0.5:
                chosen_actions[action] = False
            else:
                chosen_actions[action] = True
            #else:
            #    chosen_actions[action] = self.values[action][1] >= self.values[action][0]
        return chosen_actions
    
    def update(self, chosen_actions, rewards):
        for action, taken in chosen_actions.items():
            index = 1 if taken else 0
            self.counts[action][index] += 1
            n = self.counts[action][index]
            self.values[action][index] += (rewards[action] - self.values[action][index]) / n



# Simulate the environment with fixed rewards
def simulate_environment(actions, compile_args, param_tune=False):
    reward = reward_cal(actions, compile_args, param_tune=param_tune)
    rewards = {}
    for action, taken in actions.items():
        if taken:
            rewards[action] = -reward/200  # Random reward if action is taken
        else:
            rewards[action] = 0  # No reward if action is not taken
    return rewards, -reward


import matplotlib.pyplot as plt

def normalize_and_plot(dictionary):
    # Normalize the dictionary values
    values = np.array(list(agent.values.values()))[:,1]
    min_val = min(values)
    max_val = max(values)
    normalized_values = [(val - min_val) / (max_val - min_val) for val in values]
    
    # Sort the normalized values from highest to lowest
    sorted_values = sorted(normalized_values, reverse=True)
    threshold_dict = {key: normalized_value > 0.5 for key, normalized_value in zip(dictionary.keys(), normalized_values)}
    # Plot the sorted values
    plt.figure(figsize=(40, 5))
    plt.plot(sorted_values, marker='o', linestyle='-')
    plt.title('Normalized and Sorted Values')
    plt.xlabel('Index')
    plt.ylabel('Normalized Value')
    plt.grid(True)
    plt.savefig('out.png')
    return threshold_dict, zip(dictionary.keys(), normalized_values)

def best_seen(seen):
    if len(seen)==0:
        return 1000000
    else:
        return min([x*(-1000.0) for x in seen])

def cnt_false(dictionaty):
    cnt = 0
    for key, val in dictionaty.items():
        if val == False:
            cnt+=1
    return cnt

# Example usage
action_set = get_gcc_optimization_passes()
agent = EpsilonGreedyBinaryActions(action_set, epsilon=0.5)


inti_reward = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args, optTarget=0, optPass='-O3')
print(inti_reward*1000.0)
with open('out.txt', 'w+') as file:
    file.write(f"initial size: {inti_reward*(1000.0)}\n")
num_actions = len(action_set)
occurrences_list = [0 for i in range(len(action_set))]
num_states = len(action_set)
with open('out.txt', 'a+') as file:
    file.write(f"Num of possible actions: {len(action_set)}\n")



seen = []
min_val = 100000
num_eposides = 2000
epsilons = generate_periodic_function(num_eposides)
# Run for 100 iterations
for episode in range(num_eposides):
    chosen_actions = agent.choose_actions(episode/num_eposides, epsilons[episode])
    #print('---------------------------------------------------------\n',cnt_false(chosen_actions),'---------------------------------------------------------\n')
    #print('---------------------------------------------------------\n',chosen_actions)
    rewards, reward = simulate_environment(chosen_actions, compile_args, param_tune=False)
    if (-reward) >= 1000.0:
        continue
    agent.update(chosen_actions, rewards)
    if (-reward) < min_val:
        min_val = -reward
        best_action = chosen_actions
    if reward not in seen:
        seen.append(reward)
    if episode%10==0:
        with open('out.txt', 'a+') as file:
            file.write(f"episode: {episode}|\t Explored Space: {len(seen)}|\t Best: {best_seen(seen)}|\tSeen: {[x*(-1000.0) for x in seen]}\n")
    if episode%100==99:
        th_actions, norm_actions = normalize_and_plot(agent.values)
        rewards, reward = simulate_environment(th_actions, compile_args, param_tune=False)
        with open('out_temp.txt', 'w+') as file:
            file.write(f"Episode: {episode}\n")
            file.write(f"Final best reward: {reward*(-1000.0)}\n")
            file.write(f"The dict val:\n")
            for key, val in norm_actions:
                file.write(f"{key}\t{val}\n")
    print(f"episode: {episode}|\t Explored Space: {len(seen)}",  end='\r')
# Print learned values
print(agent.values)
th_actions, norm_actions = normalize_and_plot(agent.values)
rewards, reward = simulate_environment(th_actions, compile_args, param_tune=False)
with open('out.txt', 'a+') as file:
    file.write(f"Final best reward: {reward*(-1000.0)}\n")
    file.write(f"The dict val:\n")
    for key, val in norm_actions:
        file.write(f"{key}\t{val}\n")


init_reward = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args, optTarget=0, optPass='-O3')
rewards, reward = simulate_environment(th_actions, compile_args, param_tune=False)
print(f"Init: {init_reward}\nFinal: {-reward}")
