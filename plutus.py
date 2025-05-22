# Plutus Bitcoin Brute Forcer
# Made by Isaac Delly
# https://github.com/Isaacdelly/Plutus
# Optimized version with high-performance cryptography

import platform
import multiprocessing
from multiprocessing import Pool, Manager, Value, Lock
import hashlib
import binascii
import os
import sys
import time
import concurrent.futures
import itertools
import mmap
import psutil
import tqdm

# Import the fastest available cryptography library
try:
    # First choice: coincurve (very fast and reliable)
    import coincurve
    CRYPTO_LIB = "coincurve"
except ImportError:
    try:
        # Second choice: fastecdsa (slower)
        from fastecdsa import keys, curve
        CRYPTO_LIB = "fastecdsa"
    except ImportError:
        try:
            # Third choice: starkbank-ecdsa (can be fastest but less reliable)
            from ellipticcurve.privateKey import PrivateKey
            from ellipticcurve.curve import secp256k1
            CRYPTO_LIB = "starkbank"
        except ImportError:
            print("ERROR: No ECC library found. Install one of: coincurve, fastecdsa, or starkbank-ecdsa")
            sys.exit(1)

# Try to import Bloom filter for faster lookups
try:
    from pybloom_live import ScalableBloomFilter
    BLOOM_FILTER_AVAILABLE = True
except ImportError:
    BLOOM_FILTER_AVAILABLE = False

print(f"Using {CRYPTO_LIB} cryptography library")
if BLOOM_FILTER_AVAILABLE:
    print("Bloom filter support available (faster lookups)")
else:
    print("Bloom filter not available. Install pybloom-live for faster lookups")

DATABASE = r'database/11_13_2022/'

# Use a batch size for generating multiple keys at once
BATCH_SIZE = 1000

# Memory usage monitoring
def get_memory_usage():
    """Return the memory usage in MB"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / 1024 / 1024  # Convert to MB

def generate_private_keys(batch_size=BATCH_SIZE):
    """Generate multiple private keys at once for better efficiency"""
    return [binascii.hexlify(os.urandom(32)).decode('utf-8').upper() 
            for _ in range(batch_size)]

def private_key_to_public_key(private_key, _unused=None):
    """Convert private key to public key using the fastest available library"""
    try:
        if CRYPTO_LIB == "coincurve":
            # Coincurve (very fast and reliable)
            private_key_bytes = bytes.fromhex(private_key)
            public_key = coincurve.PublicKey.from_secret(private_key_bytes)
            return '04' + public_key.format(compressed=False)[1:].hex().upper()
        elif CRYPTO_LIB == "fastecdsa":
            # Fastecdsa (slower)
            key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
            return '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)
        else:
            # Starkbank-ecdsa
            pk_int = int(private_key, 16)
            pk = PrivateKey(pk_int, curve=secp256k1)
            return '04' + pk.publicKey().toString().hex().upper()
    except Exception as e:
        # Fall back to fastecdsa as last resort
        if 'fastecdsa' in sys.modules:
            key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
            return '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)
        else:
            raise Exception(f"Failed to generate public key: {e}")

def public_key_to_address(public_key):
    """Convert public key to Bitcoin address"""
    output = []
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    var = hashlib.new('ripemd160')
    encoding = binascii.unhexlify(public_key.encode())
    var.update(hashlib.sha256(encoding).digest())
    var_encoded = ('00' + var.hexdigest()).encode()
    digest = hashlib.sha256(binascii.unhexlify(var_encoded)).digest()
    var_hex = '00' + var.hexdigest() + hashlib.sha256(digest).hexdigest()[0:8]
    count = [char != '0' for char in var_hex].index(True) // 2
    n = int(var_hex, 16)
    while n > 0:
        n, remainder = divmod(n, 58)
        output.append(alphabet[remainder])
    for i in range(count): output.append(alphabet[0])
    return ''.join(output[::-1])

def private_key_to_wif(private_key):
    """Convert private key to WIF format"""
    digest = hashlib.sha256(binascii.unhexlify('80' + private_key)).hexdigest()
    var = hashlib.sha256(binascii.unhexlify(digest)).hexdigest()
    var = binascii.unhexlify('80' + private_key + var[0:8])
    alphabet = chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    value = pad = 0
    result = ''
    for i, c in enumerate(var[::-1]): value += 256**i * c
    while value >= len(alphabet):
        div, mod = divmod(value, len(alphabet))
        result, value = chars[mod] + result, div
    result = chars[value] + result
    for c in var:
        if c == 0: pad += 1
        else: break
    return chars[0] * pad + result

def process_key_batch(args):
    """Process a batch of keys and check against the database"""
    database, config, batch_size = args
    found_addresses = []
    
    # Generate a batch of private keys
    private_keys = generate_private_keys(batch_size)
    
    # Process keys in parallel using a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count())) as executor:
        # Create public keys in parallel
        public_keys = list(executor.map(
            lambda pk: private_key_to_public_key(pk, config['fastecdsa']), 
            private_keys
        ))
        
        # Create addresses in parallel
        addresses = list(executor.map(public_key_to_address, public_keys))
    
    # Check addresses against database
    for i, address in enumerate(addresses):
        if config['verbose']:
            print(address)
        
        # Check if using bloom filter or set
        if isinstance(database, ScalableBloomFilter):
            # Use bloom filter for fast lookup
            if address[-config['substring']:] in database:
                # Verify the full address in the database files (bloom filter can have false positives)
                found = verify_address_in_database(address, config['substring'])
                if found:
                    found_addresses.append((private_keys[i], public_keys[i], address))
                    save_found_address(private_keys[i], public_keys[i], address)
        else:
            # Use set for lookup
            if address[-config['substring']:] in database:
                # Verify the full address in the database files
                found = verify_address_in_database(address, config['substring'])
                if found:
                    found_addresses.append((private_keys[i], public_keys[i], address))
                    save_found_address(private_keys[i], public_keys[i], address)
    
    return found_addresses

def verify_address_in_database(address, substring_length):
    """Verify if the full address exists in any database file using binary search"""
    suffix = address[-substring_length:]
    
    # Only check files if the suffix matches
    for filename in os.listdir(DATABASE):
        file_path = os.path.join(DATABASE, filename)
        
        # Use memory mapping for faster file searching
        try:
            with open(file_path, 'r') as f:
                # First check if the file contains the address using a faster method
                # Read the file in chunks and check for the address
                chunk_size = 1024 * 1024  # 1MB chunks
                
                # Read the file in chunks for better memory efficiency
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                        
                    # If the address is in this chunk, do a more detailed search
                    if address in chunk:
                        # Go back to the beginning of the file for a line-by-line search
                        f.seek(0)
                        for line in f:
                            if address == line.strip():
                                return True
                        break
        except Exception as e:
            print(f"Error checking file {file_path}: {e}")
    
    return False

def save_found_address(private_key, public_key, address):
    """Save found address information to plutus.txt"""
    with open('plutus.txt', 'a') as plutus:
        plutus.write('hex private key: ' + str(private_key) + '\n' +
                     'WIF private key: ' + str(private_key_to_wif(private_key)) + '\n' +
                     'public key: ' + str(public_key) + '\n' +
                     'uncompressed address: ' + str(address) + '\n\n')
    
    # Also print to console for immediate notification
    print("\n" * 50)
    print(f"FOUND ADDRESS WITH BALANCE: {address}")
    print("=" * 50 + "\n")

def main(database, args):
    """Main function that processes batches of keys in parallel"""
    # Create a thread pool for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=args['cpu_count']) as executor:
        # Process batches of keys
        batch_args = [(database, args, BATCH_SIZE) for _ in range(args['cpu_count'])]
        
        # Track statistics
        start_time = time.time()
        total_addresses = 0
        last_report_time = start_time
        report_interval = 10  # Report every 10 seconds
        
        print(f"Starting brute force with {args['cpu_count']} workers, batch size {BATCH_SIZE}")
        print(f"Memory usage at start: {get_memory_usage():.2f} MB")
        
        while True:
            # Submit batch processing tasks
            futures = [executor.submit(process_key_batch, arg) for arg in batch_args]
            
            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed(futures):
                found_addresses = future.result()
                total_addresses += BATCH_SIZE * args['cpu_count']
                
                # Periodically report statistics
                current_time = time.time()
                if current_time - last_report_time > report_interval:
                    elapsed = current_time - start_time
                    addresses_per_second = total_addresses / elapsed
                    print(f"Processed {total_addresses:,} addresses in {elapsed:.2f} seconds "
                          f"({addresses_per_second:.2f} addr/sec) - "
                          f"Memory: {get_memory_usage():.2f} MB")
                    last_report_time = current_time
                
                if found_addresses:
                    print(f"Found {len(found_addresses)} addresses with balances!")

def print_help():
    print('''Plutus homepage: https://github.com/Isaacdelly/Plutus
Plutus QA support: https://github.com/Isaacdelly/Plutus/issues

Speed test: 
execute 'python3 plutus.py time', the output will be the time it takes to bruteforce a batch of addresses in seconds

Quick start: run command 'python3 plutus.py'

By default this program runs with parameters:
python3 plutus.py verbose=0 substring=8 batch_size=1000

verbose: must be 0 or 1. If 1, then every bitcoin address that gets bruteforced will be printed to the terminal. This has the potential to slow the program down. An input of 0 will not print anything to the terminal and the bruteforcing will work silently. By default verbose is 0.

substring: to make the program memory efficient, the entire bitcoin address is not loaded from the database. Only the last <substring> characters are loaded. This significantly reduces the amount of RAM required to run the program. if you still get memory errors then try making this number smaller, by default it is set to 8. This opens us up to getting false positives (empty addresses mistaken as funded) with a probability of 1/(16^<substring>), however it does NOT leave us vulnerable to false negatives (funded addresses being mistaken as empty) so this is an acceptable compromise.

batch_size: number of addresses to generate and check in a single batch. Higher values can improve performance but use more memory. Default is 1000.

cpu_count: number of cores to run concurrently. More cores = more resource usage but faster bruteforcing. Omit this parameter to run with the maximum number of cores

use_bloom: 0 or 1. If 1, uses a Bloom filter for faster lookups (requires pybloom-live). Default is 1 if available.''')
    sys.exit(0)

def timer(args):
    """Measure the time it takes to process a batch of addresses"""
    start = time.time()
    batch_size = min(100, args.get('batch_size', BATCH_SIZE))  # Use a smaller batch for timing
    
    # Generate a batch of private keys
    private_keys = generate_private_keys(batch_size)
    
    # Process each key
    for private_key in private_keys:
        public_key = private_key_to_public_key(private_key, args['fastecdsa'])
        address = public_key_to_address(public_key)
    
    end = time.time()
    total_time = end - start
    per_address = total_time / batch_size
    
    print(f"Total time for {batch_size} addresses: {total_time:.6f} seconds")
    print(f"Time per address: {per_address:.6f} seconds")
    print(f"Addresses per second: {batch_size/total_time:.2f}")
    
    # Run a more comprehensive benchmark if requested
    if args.get('extended_benchmark', False):
        print("\nRunning extended benchmark...")
        
        # Test different batch sizes
        batch_sizes = [10, 100, 1000, 5000]
        for size in batch_sizes:
            start = time.time()
            private_keys = generate_private_keys(size)
            for private_key in private_keys:
                public_key = private_key_to_public_key(private_key, args['fastecdsa'])
                address = public_key_to_address(public_key)
            end = time.time()
            print(f"Batch size {size}: {size/(end-start):.2f} addr/sec, {end-start:.4f} seconds total")
        
        # Test parallel processing
        print("\nTesting parallel processing...")
        for num_workers in [1, 2, 4, 8]:
            if num_workers > os.cpu_count():
                continue
                
            start = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                private_keys = generate_private_keys(1000)
                list(executor.map(lambda pk: public_key_to_address(private_key_to_public_key(pk, args['fastecdsa'])), private_keys))
            end = time.time()
            print(f"Workers: {num_workers}, Speed: {1000/(end-start):.2f} addr/sec")
    
    sys.exit(0)

def load_database_efficiently(substring_length, use_bloom=False):
    """Load database more efficiently with reduced memory usage"""
    print('Reading database files...')
    
    if use_bloom and BLOOM_FILTER_AVAILABLE:
        print("Using Bloom filter for database lookups")
        # Create a scalable Bloom filter with a low false positive probability
        database = ScalableBloomFilter(initial_capacity=1000000, error_rate=0.000001)
    else:
        database = set()
        
    total_addresses = 0
    max_files_at_once = 5  # Process only a few files at a time to reduce memory usage
    
    # Get all database files
    file_paths = [os.path.join(DATABASE, filename) for filename in os.listdir(DATABASE)]
    
    # Show progress bar
    with tqdm.tqdm(total=len(file_paths), desc="Loading database") as pbar:
        # Process files in smaller batches to reduce memory usage
        for i in range(0, len(file_paths), max_files_at_once):
            batch = file_paths[i:i+max_files_at_once]
            
            # Process this batch of files
            for file_path in batch:
                file_total = 0
                try:
                    with open(file_path, 'r') as file:
                        # Process the file line by line to minimize memory usage
                        for line in file:
                            address = line.strip()
                            if address and address.startswith('1'):  # Only process P2PKH addresses
                                if use_bloom and BLOOM_FILTER_AVAILABLE:
                                    database.add(address[-substring_length:])
                                else:
                                    database.add(address[-substring_length:])
                                file_total += 1
                                total_addresses += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                
                pbar.update(1)
    
    print(f'DONE - Loaded {total_addresses:,} addresses into database')
    print(f'Memory usage after loading: {get_memory_usage():.2f} MB')
    return database, total_addresses

if __name__ == '__main__':
    args = {
        'verbose': 0,
        'substring': 8,
        'fastecdsa': platform.system() in ['Linux', 'Darwin'],
        'cpu_count': multiprocessing.cpu_count(),
        'batch_size': BATCH_SIZE,
        'use_bloom': BLOOM_FILTER_AVAILABLE,
        'extended_benchmark': False,
    }
    
    # Parse command line arguments
    for arg in sys.argv[1:]:
        if '=' in arg:
            command, value = arg.split('=', 1)
        else:
            command, value = arg, None
            
        if command == 'help':
            print_help()
        elif command == 'time':
            args['extended_benchmark'] = True if value == 'extended' else False
            timer(args)
        elif command == 'cpu_count' and value:
            cpu_count = int(value)
            if cpu_count > 0 and cpu_count <= multiprocessing.cpu_count():
                args['cpu_count'] = cpu_count
            else:
                print(f'Invalid input. cpu_count must be greater than 0 and less than or equal to {multiprocessing.cpu_count()}')
                sys.exit(-1)
        elif command == 'verbose' and value:
            if value in ['0', '1']:
                args['verbose'] = int(value)
            else:
                print('Invalid input. verbose must be 0(false) or 1(true)')
                sys.exit(-1)
        elif command == 'substring' and value:
            substring = int(value)
            if substring > 0 and substring < 27:
                args['substring'] = substring
            else:
                print('Invalid input. substring must be greater than 0 and less than 27')
                sys.exit(-1)
        elif command == 'batch_size' and value:
            batch_size = int(value)
            if batch_size > 0:
                args['batch_size'] = batch_size
                # Update the module-level batch size
                BATCH_SIZE = batch_size
            else:
                print('Invalid input. batch_size must be greater than 0')
                sys.exit(-1)
        elif command == 'use_bloom' and value:
            if value in ['0', '1']:
                use_bloom = int(value) == 1
                if use_bloom and not BLOOM_FILTER_AVAILABLE:
                    print('Warning: Bloom filter requested but pybloom-live is not installed.')
                    print('Install with: pip install pybloom-live')
                    args['use_bloom'] = False
                else:
                    args['use_bloom'] = use_bloom
            else:
                print('Invalid input. use_bloom must be 0(false) or 1(true)')
                sys.exit(-1)
        else:
            print(f'Invalid input: {command}\nRun `python3 plutus.py help` for help')
            sys.exit(-1)
    
    # Print system information
    print(f"Python version: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"CPU cores: {multiprocessing.cpu_count()}")
    print(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Load the database efficiently
    database, total_addresses = load_database_efficiently(args['substring'], args['use_bloom'])
    
    print(f'Database size: {len(database):,} unique suffixes')
    print(f'Batch size: {args["batch_size"]} addresses per batch')
    print(f'Processes spawned: {args["cpu_count"]}')
    
    # Start the main process
    main(database, args)
