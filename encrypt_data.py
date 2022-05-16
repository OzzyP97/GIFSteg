import numpy as np
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto import Random
'''
Encryption module

Security considerations:
Trusted library implementations of secure standards are for encryption
and decryption. Try-except blocks are used to catch errors during, including
from file handling.
'''

def keygen(filename, passphrase):
    '''
    Takes a passphrase and a file name without extension,
    Generates corresponding public and private key files.
    Returns True on success and False on failure
    '''

    #Generate keys
    key = RSA.generate(2048)
    public = key.public_key()

    #Save keys in passphrase protected file
    try:
        with open(filename + ".der", 'wb') as f:
            f.write(key.export_key('DER', passphrase, 8))


        with open(filename + "_public.der", 'wb') as f:
            f.write(public.export_key('DER'))

        return True

    except IOError:
        return False

#Encryption with RSA and AES
def encrypt(plaintext, keyfile):
    '''
    Takes plaintext bytes and the name of a key file, then
    encrypts plaintext with RSA and AES. Returns encrypted data
    in a Numpy array, or on empty array on failure.
    '''

    #AES
    #Encrypt data with AES
    try:
        aes_key = Random.new().read(32)
        aes_cipher = AES.new(aes_key, AES.MODE_EAX)
        nonce = aes_cipher.nonce
        ciphertext, tag = aes_cipher.encrypt_and_digest(plaintext)
    except ValueError:
        print("AES encryption failed!")
        return []

    #RSA
    #Encrypt AES key with RSA
    try:
        rsa_key = RSA.importKey(open(keyfile, 'rb').read())
        rsa_cipher = PKCS1_OAEP.new(rsa_key)
        aes_key = rsa_cipher.encrypt(aes_key)
    except ValueError:
        print("RSA encryption failed!")
        return []
    except IOError:
        print("AES encryption failed!")
        return []

    #Data formatting
    aes_key = np.frombuffer(aes_key, dtype=np.uint8)
    nonce = np.frombuffer(nonce, dtype=np.uint8)
    tag = np.frombuffer(tag, dtype=np.uint8)
    ciphertext = np.frombuffer(ciphertext, dtype=np.uint8)

    cipher_data = np.concatenate([aes_key, nonce, tag, ciphertext])

    return cipher_data

#Decryption with RSA and AES
def decrypt(cipher_data, keyfile, passphrase):
    '''
    Takes encrypted data in a Numpy array and the name of a key file, then
    decrypts with RSA and AES. Returns decrypted bytes on success, or an empty
    sequence on failure.

    AES is used with the EAX mode of operation. This allows us to verify data
    integrity during transport.
    '''

    #Data formatting
    aes_key = cipher_data[0:256].tobytes()
    nonce = cipher_data[256:272].tobytes()
    tag = cipher_data[272:288].tobytes()
    ciphertext = cipher_data[288:].tobytes()

    #RSA
    #Open key file and decrypt AES key with RSA
    try:
        with open(keyfile, 'rb') as kf:
            rsa_key = RSA.importKey(kf.read(), passphrase)

        rsa_cipher = PKCS1_OAEP.new(rsa_key)
        aes_key = rsa_cipher.decrypt(aes_key)
    except ValueError:
        print("RSA decryption failed! Are you logged in as the recipient?")
        return []
    except IOError:
        print("RSA decryption failed! Are you logged in as the recipient?")
        return []

    #AES
    aes_cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    #Decrypt data with AES
    try:
        plaintext = aes_cipher.decrypt(ciphertext)
    except ValueError:
        print("AES decryption failed!")
        return []

    #Verify data integrity
    try:
        aes_cipher.verify(tag)
        print("Integrity check succeeded!")
    except ValueError:
        print("Integrity check failed!")

    return plaintext
