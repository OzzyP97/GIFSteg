import numpy as np
from blend_gif import encode, decode
from encrypt_data import encrypt, decrypt, keygen
from file_handler import read_file, write_file
from access_manager import find_user, add_user, validate_user
'''
PUBLIC KEY STEGANOGRAPHY TOOL
'''

'''
This is the UI and control loop.

Security considerations:
Most security checks are in the other modules, but we do check that inputs to
functions are not empty where necessary. Inputs from the user are handled as
strings only, and all cases should be accounted for.
'''


def create_user(user, passphrase):
    '''
    Combines two modules to create a new user with a matching set of RSA keys.
    '''

    if add_user(user, passphrase):
        if keygen(user, passphrase):
            return True
        else:
            return False
    else:
        return False


if __name__ == '__main__':
    '''
    Main control loop. Implements command parsing and checks that other modules
    receive valid data.
    '''

    logged_in = False
    user = None
    passphrase = None
    command = None

    print("Welcome! Type 'help' for a list of commands.")

    while command != 'quit':

        command = input('>')

        if command == 'help':
            print("help/login/logout/register/encrypt/decrypt/quit")

        elif command == 'login':
            user = input("username: ")
            passphrase = input("passphrase: ")

            if validate_user(user, passphrase):
                logged_in = True
                print("Success!")
            else:
                user = None
                passphrase = None
                print("Failed!")

        elif command == 'logout':
            logged_in = False
            user = None
            passphrase = None

        elif command == 'register':
            new_user = input("username: ")
            new_passphrase = input("passphrase: ")

            if create_user(new_user, new_passphrase):
                print("Success!")
            else:
                print("Failed!")

        elif command == 'encrypt':
            keyfile = input("recipient: ") + "_public.der"
            filename = input("input file: ")
            input_data = read_file(filename)

            if len(input_data) > 0:

                input_data = encrypt(input_data, keyfile)

                imgname = input("GIF file: ")

                if not encode(input_data, imgname, 'cipher.gif', 2):
                    print("\nInvalid file or not enough space!\n")


        elif command == 'decrypt':
            if logged_in:
                imgname1 = input("Original GIF file: ")
                imgname2 = input("Encoded GIF file: ")

                recovered_data = decode(imgname1, imgname2)

                if len(recovered_data) > 0:
                    keyfile = user + ".der"
                    filename = input("output file: ")

                    recovered_data = decrypt(recovered_data, keyfile, passphrase)
                    write_file(filename, recovered_data)

                else:
                    print("\nInvalid file(s)!\n")

            else:
                print("Not logged in!")

        elif command != 'quit':
            print("Unknown command!")
