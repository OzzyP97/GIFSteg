import numpy as np
import hashlib
from PIL import Image, GifImagePlugin
from math import ceil

'''
Image processing module. Encodes and decodes data on animate GIF files.

Security considerations:
Data is encrypted beforehand, the primary consideration here is file handling
and reliable retrieval of information. Try-except blocks are used where applicable,
and a checksum is used to avoid issues when the user accidentally inputs an
incorrect file for decoding.
'''

def generate_checksum(filename):
    '''
    Generates an MD5 checksum of a file specified by filename.
    Returns a Numpy array, or an empty array if file could not be read.

    MD5 isn't a secure hash function, but this isn't a requirement for a
    checksum.
    '''

    try:
        with open(filename, 'rb') as file:
            checksum = np.frombuffer(hashlib.md5(file.read()).digest(), dtype=np.uint8)
            return checksum

    except IOError:
        return []


def spread_data(data_in, bit_depth):
    '''
    Formats data to be XORed with the image pixels. Bit depth specifies
    the amount of bits used per pixel, starting from lsb.
    '''

    byte_ratio = 8 // bit_depth
    data_out = np.zeros( byte_ratio * len(data_in) + 1, dtype=np.uint8 )

    for i in range(1, len(data_out), byte_ratio):
        for j in range(byte_ratio):
            data_out[i + j] = ( data_in[(i - 1)//byte_ratio] >> ( j * bit_depth )
                            ) % ( 2 ** bit_depth )

    data_out[0] = bit_depth

    return data_out


def compact_data(data_in):
    '''
    Inverse of spread_data, returns the data to it's original format.
    '''

    bit_depth = data_in[0]
    byte_ratio = 8 // bit_depth
    data_out = np.zeros( ( len(data_in) - 1 ) // byte_ratio , dtype=np.uint8 )

    for i in range(1, len(data_in), byte_ratio):
        for j in range(byte_ratio):
           data_out[(i - 1) // byte_ratio] += ( data_in[i + j] << ( j * bit_depth )  )

    return data_out


def encode(data_in, input_image, output_image, bit_depth = 2):
    '''
    Encodes the data and header information decessary for decoding in an
    animated GIF image. XORs formatted data with input_image and saves the result
    as output image.
    '''
    input_data = data_in

    # Generate a checksum for verifying the original image during decoding
    try:
        img = Image.open(input_image)
        checksum = generate_checksum(input_image)
    except IOError:
        return False

    # Frames have to be stored individually due to Pillow limitations
    frames_total = img.n_frames
    current_frame = 0
    images = []

    # Calculate how much of the image will be used
    width, height = img.size
    frame_size = width * height
    frames_needed = ceil( ( 1 + 8 // bit_depth * ( len( input_data ) ) + 20  ) / frame_size )
    data_end = 8 // bit_depth * ( len( input_data ) + 20 ) - ( frames_needed - 1 ) * frame_size + 1
    data_end_bytes = data_end.to_bytes(3, 'little')

    print("\nFrames used:")
    print(frames_needed)
    print("\nBytes on last frame:")
    print(data_end)

    # Abort if data can't fit with current settings
    if frames_needed > img.n_frames or data_end > 2**24 - 1:
        return False

    # Construct header
    header = np.zeros(4, dtype=np.uint8)
    header[0] = frames_needed
    header[1] = data_end_bytes[0]
    header[2] = data_end_bytes[1]
    header[3] = data_end_bytes[2]

    header = np.concatenate([header, checksum])

    input_data = np.concatenate([header, input_data])

    input_data = spread_data(input_data, bit_depth)

    print("\nData stream")
    print(input_data)

    # Encode data
    for frame in range(frames_needed):

        # Load current frame as img
        img.seek(frame)

        # Calculate how much data will be written on the current frame
        if frame + 1 == frames_needed:
            data_end = len(input_data) - frame * frame_size
            current_frame = frame
        else:
            data_end = frame_size

        img_data = list(img.getdata())

        # Write header on the first frame
        if frame == 0:
            for i in range(1 + 8 // bit_depth * 20):
                img_data[i] = input_data[i + frame * frame_size]

            for i in range(1 + 8 // bit_depth * 20, data_end):
                img_data[i] = img_data[i] ^ input_data[i + frame * frame_size]
        else:
            for i in range(data_end):
                img_data[i] = img_data[i] ^ input_data[i + frame * frame_size]

        img.putdata(img_data)

        # Store frame in an array
        images.append(img.copy())

    if current_frame < frames_total - 1:
        for frame in range(current_frame, frames_total):
            # Load current frame as img
            img.seek(frame)
            # Store frame in an array
            images.append(img.copy())

    # Save the individual frames as a new GIF
    images[0].save(output_image,
               save_all=True, append_images=images[1:], optimize=False)

    img.close()

    return True


def decode(original_image, cipher_image):
    '''
    Decodes data from an encoded GIF using encoded header information and the
    original, unencoded GIF.
    '''

    checksum = generate_checksum(original_image)

    try:
        img1 = Image.open(cipher_image)
        img2 = Image.open(original_image)
    except IOError:
        return []

    img1_data = list(img1.getdata())
    img2_data = list(img2.getdata())
    frames_needed = 0
    data_end = 0

    # Recover header
    bit_depth = img1_data[0]

    print("Bit depth: ", bit_depth)

    header_end = 1 + 8 // bit_depth * 20

    header = np.zeros(header_end, dtype=np.uint8)

    for i in range(header_end):
        header[i] = img1_data[i]

    header = compact_data(header)

    frames_needed = header[0]

    for i in range(1,4):
        data_end += ( header[i] ) << 8 * (i - 1)

    print("\nFrames used:")
    print(frames_needed)
    print("\nBytes on last frame:")
    print(data_end)

    # Verify the original image
    if not np.array_equal(checksum, header[4:20]):
        print("\nInvalid checksum! Is the original GIF file correct?")
        query = input("Try to decode anyway? May crash the program! (y/n): ")

        while(query != 'n'):
            if query == 'y':
                return []
            query = input("Try to decode anyway? May crash the program! (y/n): ")

    width, height = img1.size
    frame_size = width * height

    output_data = np.zeros(frame_size * (frames_needed - 1) + data_end, dtype=np.uint8)

    # Recover data stream
    for frame in range(frames_needed):

        img1.seek(frame)
        img2.seek(frame)
        img1_data = list(img1.getdata())
        img2_data = list(img2.getdata())

        if frame + 1 == frames_needed:
            data_end = len(output_data) - frame * frame_size

        else:
            data_end = frame_size

        if frame == 0:

            output_data[0] = img1_data[0]

            for i in range(1 + 8 // bit_depth * 20):
                output_data[i + frame * frame_size] = img1_data[i]

            for i in range(1 + 8 // bit_depth * 20, data_end):
                output_data[i + frame * frame_size] = img1_data[i] ^ img2_data[i]

        else:

            for i in range(data_end):
                output_data[i + frame * frame_size] = img1_data[i] ^ img2_data[i]

    print("\nData stream:")
    print(output_data)

    # Recover original format
    output_data = compact_data( np.array( output_data ))
    output_data = output_data[20:]

    return output_data
