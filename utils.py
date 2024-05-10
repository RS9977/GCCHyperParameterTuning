import pickle
import numpy as np


def compute_mean_and_filter(data_list):
    # Convert the input list to a NumPy array for efficient operations
    data_array = np.array(data_list)

    # Calculate the mean and standard deviation of the data
    mean = np.mean(data_array)
    std_dev = np.std(data_array)

    # Define the range for values to keep
    lower_bound = mean - std_dev
    upper_bound = mean + std_dev

    # Filter the values that are within the specified range
    filtered_data = data_array[(data_array >= lower_bound) & (data_array <= upper_bound)]

    # Calculate the new mean of the filtered data
    new_mean = np.mean(filtered_data)

    return new_mean

def are_lists_identical(list1, list2):
    for list2e in list2:
        if len(list1) != len(list2e):
            continue
        for i in range(len(list1)):
            if list1[i] != list2e[i]:
                continue
            if i == len(list1)-1:
                return True 
    return False


def save_dictionary_to_file(dictionary, filename):
    with open(filename, 'wb') as file:
        pickle.dump(dictionary, file)

def load_dictionary_from_file(filename):
    with open(filename, 'rb') as file:
        dictionary = pickle.load(file)
    return dictionary

def are_files_equal(binaries, curFile):
    try:
        with open(curFile, 'rb') as curF:
            curContent = curF.read()
            for preContent in binaries:
                if preContent == curContent:
                    return curContent, True          
            return curContent, False
    except FileNotFoundError:
        return curContent, False
