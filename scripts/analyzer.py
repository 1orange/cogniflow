import numpy as np


def read_npy_file(file_path):
    """
    Reads and prints the contents of a .npy file.

    Parameters:
        file_path (str): Path to the .npy file.

    Returns:
        data (numpy.ndarray): The data stored in the .npy file.
    """
    try:
        # Load data from .npy file
        data = np.load(file_path, allow_pickle=True)
        print("File loaded successfully!\n")

        # Display basic information
        print(f"Type of data: {type(data)}")
        print(f"Data shape: {getattr(data, 'shape', 'N/A')}\n")
        print("Data preview:")
        print(data)

        return data

    except Exception as e:
        print(f"Error reading the file: {e}")
        return None


if __name__ == "__main__":
    # Example usage: change this path to your .npy file
    file_path = "data/recorded_data_forward_20251005_223350.npy"
    read_npy_file(file_path)
