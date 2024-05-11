import pickle
import numpy as np
import os


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

def delete_files_with_extension(directory, extension):
    # Get a list of all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    # Iterate over the files
    for file_name in files:
        # Check if the file has the specified extension
        if file_name.endswith(extension):
            # Construct the full path of the file
            file_path = os.path.join(directory, file_name)
            # Delete the file
            os.remove(file_path)

def create_or_clear_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        # Clear the directory if it already exists
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(e)


def change_directory(new_directory):
    try:
        os.chdir(new_directory)
        return True
    except FileNotFoundError:
        print("Error: Directory not found.")
        return False
    except PermissionError:
        print("Error: Permission denied.")
        return False