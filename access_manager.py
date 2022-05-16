from Crypto.Hash import SHA256
from Crypto import Random
import csv

'''
Access management module. Implements a simple login system with password storage.
These passwords are then used to decrypt RSA key files for decryption.

Security considerations:

Passwords are hashed with random salt for storage. The hash function is a
trusted library implementation of SHA256, and a cryptographic RNG from
the same library is used for salt.

File handling is implemented similarly to other modules, using try-except
blocks to catch any errors due to missing or invalid files.
'''

def find_user(user):
    '''
    Checks if a particular user already exists in the system
    '''
    try:
        with open('users.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                if user == row[0]:
                        return True
        return False

    except IOError:
        return False


def validate_user(user, passphrase):
    '''
    Checks if a user exists and verifies that their passphrase mathces
    to the stored hash
    '''
    try:
        with open('users.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                if user == row[0]:
                    hash = SHA256.new()
                    hash.update(bytes.fromhex(row[2]))
                    hash.update(passphrase.encode())
                    if hash.hexdigest() == row[1]:
                        return True

        return False

    except IOError:
        return False


def add_user(user, passphrase):
    '''
    Checks if a user exists and creates a new input in the system if not
    '''

    if find_user(user):
        return False

    hash = SHA256.new()
    salt = Random.new().read(32)
    hash.update(salt)
    hash.update(passphrase.encode())

    try:
        with open('users.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([user, hash.hexdigest(), salt.hex()])

        return True

    except IOError:
        return False



if __name__ == '__main__':
    '''
    Standalone testing function
    '''
    print("TESTING MODE!\n")

    mode = input("login or register? ")
    user = input("username: ")
    passphrase = input("passphrase: ")

    if mode == 'login':
        if validate_user(user, passphrase):
            print("Success!")
        else:
            print("Failed!")

    elif mode == 'register':
        if add_user(user, passphrase):
            print("Success!")
        else:
            print("Failed!")

    else:
        print("Invalid mode!")
