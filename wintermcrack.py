#!/usr/bin/env python3

import argparse
import math
import mmap
import random
import struct
import sys

# Bytes that identify RTL8100CL EEPROM image
EEPROM_HEADER = bytes([
    0x29, 0x81, 0xEC, 0x10, 0x39,
    0x81, 0xEC, 0x10, 0x39, 0x81
])

EXPECTED_EEPROM_SIZE = 0x80

DEFAULT_PASSWORD = "Fireport"
DEFAULT_PASSWORD_HASH = 0x4B
DEFAULT_PASSWORD_LENGTH = 0x8

MAX_PASSWORD_GENERATION_ATTEMPTS = 1337

class EepromValue:
    def __init__(self, address : int, mask : int, offset : int):
        self.address = address
        self._mask = mask
        self._offset = offset

    def extract_from_map(self, file_map) -> int:
        # TODO: Assert if map has enough space
        raw_value_struct = struct.unpack("<h",
            file_map[self.address:self.address + 2])

        # TODO: Validate length
        raw_value = raw_value_struct[0]
        return (raw_value & self._mask) >> self._offset

PASSWORD_HASH = EepromValue(0x42, 0x1FE0, 0x05)
PASSWORD_LENGTH = EepromValue(0x43, 0x7E0, 0x05)
PASSWORD_MAX_LENGTH = 63

def eeprom_check(map):
    eeprom_size = len(map)
    if eeprom_size != EXPECTED_EEPROM_SIZE:
        raise RuntimeError("Unexpected EEPROM size. Expected: "
            f"{hex(EXPECTED_EEPROM_SIZE)}, got: {eeprom_size}")

    if EEPROM_HEADER != map[0:len(EEPROM_HEADER)]:
        raise RuntimeError("EEPROM header mismatch")
        
def generate_random_char() -> chr:
    return chr(random.randint(ord('!'), ord('~')))

def is_printable(character : chr) -> bool:
    return ord(character) in range(ord('!'), ord('~'))
    
def generate_password(hash_value : int, length : int) -> str:
    if length > PASSWORD_MAX_LENGTH:
        raise ValueError("EEPROM password too long. Report this as a bug")
                    
    for attempt in range(MAX_PASSWORD_GENERATION_ATTEMPTS):
        out = ""
        computed_hash = 0

        for _ in range(length - 1):
            character = generate_random_char()
            out += character
            computed_hash += ord(character)
            
        last_char = chr(abs(hash_value - (computed_hash & 0xFF)))
        if not is_printable(last_char):
            continue

        return out + last_char

    raise StopIteration("Unable to generate password after "
        f"{MAX_PASSWORD_GENERATION_ATTEMPTS} attempts. "
        "Please report this as a bug.")
    
def process_eeprom_image(path : str):
    with open(path, "rb") as file:
        with mmap.mmap(file.fileno(), 0, prot=mmap.PROT_READ) as file_map:
            eeprom_check(file_map)

            password_length = PASSWORD_LENGTH.extract_from_map(file_map)
            password_hash = PASSWORD_HASH.extract_from_map(file_map)
            
            if (password_hash == DEFAULT_PASSWORD_HASH and
                password_length == DEFAULT_PASSWORD_LENGTH):
                print('The password is probably the default one. '
                    f'Please try "{DEFAULT_PASSWORD}"')
                return

            password = generate_password(password_hash, password_length) 
            print(f"Please try the password ({password_length} characters):")
            print(password)
            print("After accessing BIOS, it is recommended to change the "
                "password to something sane")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=str, help="Path to EEPROM dump")
    args = parser.parse_args()

    try:
        process_eeprom_image(args.rom)
    except Exception as ex:
        print(ex)
        return 1

    return 0

if __name__ == "__main__":
    # TODO: Error handling
    sys.exit(main())