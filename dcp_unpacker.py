import os
import zlib
import argparse

def delete_last_x00 (s: bytes) -> bytes:
    last_byte_n = len(s)-1
    if s[last_byte_n] == 0:
        return s[0:last_byte_n]
    return s

encoding = 'ascii'

parser = argparse.ArgumentParser(
                        prog = 'dcp_unpacker.py',
                        description = 'Unpack DCP files of Wintermute Engine games')
parser.add_argument('filename', help='Path to a DCP file', type=str)
parser.add_argument('-e', help='Use custom encoding for intertal paths (default one is ascii)', type=str)
args = parser.parse_args()

if os.path.isfile(args.filename) == False:
        print("File doesn't exist")
        exit()

if args.e:
    print(f"Using encoding: {args.e}")
    encoding = args.e

try:
    dcp_file = open(args.filename, 'rb')
except OSError:
    print("Failed to open a file")
    exit()

dcp_file.seek(0x80, 0)
tableOff = int.from_bytes(dcp_file.read(4), byteorder='little', signed=False)
dcp_file.seek(tableOff, 0)
length = int.from_bytes(dcp_file.read(1), byteorder='little', signed=False)
name = delete_last_x00( dcp_file.read(length) ).decode(encoding)
print(f"Archive name: {name}")

if os.path.isdir(name):
    print(f"Folder '{name}' already exists")
    exit()

export_dir = os.path.abspath(name)
print(f"Extracting data to: {export_dir}")

dcp_file.seek(1,1)
num = int.from_bytes(dcp_file.read(4), byteorder='little', signed=False)
print(f"Extracting {num} files")

for i in range(0, num):
    length = int.from_bytes(dcp_file.read(1), byteorder='little', signed=False)
    internal_path = bytearray(dcp_file.read(length))
    for x in range(0, length):
        internal_path[x] = internal_path[x]^0x44; # DirTree decrypted
    internal_path = delete_last_x00(internal_path).decode(encoding)
    internal_path = internal_path.replace('/', os.sep).replace('\\', os.sep) # normalizing path for all OSs
    joined_path = os.path.join(export_dir, internal_path)
    (dirs, name) = os.path.split(joined_path)
    os.makedirs(dirs, exist_ok=True)
    ext_file = open(dirs + os.sep + name, "wb")
    print(f"Extracting '{internal_path}' [{i+1} of {num}]")

    pointer = int.from_bytes(dcp_file.read(4), byteorder='little', signed=False)
    decsize = int.from_bytes(dcp_file.read(4), byteorder='little', signed=False)
    compsize = int.from_bytes(dcp_file.read(4), byteorder='little', signed=False)
    dcp_file.seek(0x0C, 1) #gotta check this jump
    tableOff = dcp_file.tell()
    dcp_file.seek(pointer, 0)
    if compsize == 0:
        inners = dcp_file.read(decsize)
        ext_file.write(inners)
    else:
        compressed_inners = dcp_file.read(compsize)
        inners = zlib.decompress(compressed_inners)
        ext_file.write(inners)

    ext_file.close()
    dcp_file.seek(tableOff, 0)

dcp_file.close()
