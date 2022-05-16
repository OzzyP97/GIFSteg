
def read_file(filename):
    data = b'';

    # Read file as binary
    try:
        with open(filename, 'rb') as file:
            data = file.read()
    except IOError:
        print("\nInvalid file!\n")

    return data;


def write_file(filename, data):
    # Write file as binary
    try:
        with open(filename, 'wb') as file:
            data = file.write(data)
    except IOError:
        print("Error opening file")
