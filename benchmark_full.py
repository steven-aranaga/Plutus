#!/usr/bin/env python3
"""
Benchmark different cryptographic libraries for full Bitcoin address generation
"""

import time
import os
import binascii
import hashlib
import sys

# Number of addresses to generate for benchmarking
NUM_ADDRESSES = 1000

def generate_private_keys(num_keys):
    """Generate random private keys"""
    return [binascii.hexlify(os.urandom(32)).decode('utf-8').upper() 
            for _ in range(num_keys)]

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

def benchmark_fastecdsa():
    """Benchmark fastecdsa library for full address generation"""
    try:
        from fastecdsa import keys, curve
        
        def generate_address(private_key):
            # Generate public key
            key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
            public_key = '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)
            
            # Convert to address
            return public_key_to_address(public_key)
        
        private_keys = generate_private_keys(NUM_ADDRESSES)
        
        start = time.time()
        for pk in private_keys:
            address = generate_address(pk)
        end = time.time()
        
        return end - start
    except ImportError:
        print("fastecdsa not installed")
        return None

def benchmark_starkbank():
    """Benchmark starkbank-ecdsa library for full address generation"""
    try:
        from ellipticcurve.privateKey import PrivateKey
        
        def generate_address(private_key):
            # Generate public key
            private_key_bytes = bytes.fromhex(private_key)
            pk = PrivateKey.fromString(private_key_bytes)
            public_key = '04' + pk.publicKey().toString().hex().upper()
            
            # Convert to address
            return public_key_to_address(public_key)
        
        private_keys = generate_private_keys(NUM_ADDRESSES)
        
        start = time.time()
        for pk in private_keys:
            try:
                address = generate_address(pk)
            except Exception:
                # Skip any problematic keys
                continue
        end = time.time()
        
        return end - start
    except (ImportError, Exception) as e:
        print(f"starkbank-ecdsa error: {e}")
        return None

def benchmark_coincurve():
    """Benchmark coincurve library for full address generation"""
    try:
        import coincurve
        
        def generate_address(private_key):
            # Generate public key
            private_key_bytes = bytes.fromhex(private_key)
            public_key = coincurve.PublicKey.from_secret(private_key_bytes)
            public_key_hex = '04' + public_key.format(compressed=False)[1:].hex().upper()
            
            # Convert to address
            return public_key_to_address(public_key_hex)
        
        private_keys = generate_private_keys(NUM_ADDRESSES)
        
        start = time.time()
        for pk in private_keys:
            address = generate_address(pk)
        end = time.time()
        
        return end - start
    except ImportError:
        print("coincurve not installed")
        return None

def benchmark_all():
    """Run all benchmarks and print results"""
    print(f"Benchmarking full address generation with {NUM_ADDRESSES} addresses...")
    
    results = {}
    
    # Benchmark fastecdsa
    time_fastecdsa = benchmark_fastecdsa()
    if time_fastecdsa:
        results["fastecdsa"] = time_fastecdsa
        print(f"fastecdsa: {time_fastecdsa:.4f} seconds ({NUM_ADDRESSES/time_fastecdsa:.2f} addr/sec)")
    
    # Benchmark starkbank-ecdsa
    time_starkbank = benchmark_starkbank()
    if time_starkbank:
        results["starkbank"] = time_starkbank
        print(f"starkbank: {time_starkbank:.4f} seconds ({NUM_ADDRESSES/time_starkbank:.2f} addr/sec)")
    
    # Benchmark coincurve
    time_coincurve = benchmark_coincurve()
    if time_coincurve:
        results["coincurve"] = time_coincurve
        print(f"coincurve: {time_coincurve:.4f} seconds ({NUM_ADDRESSES/time_coincurve:.2f} addr/sec)")
    
    # Print the fastest library
    if results:
        fastest = min(results.items(), key=lambda x: x[1])
        print(f"\nFastest library: {fastest[0]} ({NUM_ADDRESSES/fastest[1]:.2f} addr/sec)")
        
        # Compare to the slowest
        slowest = max(results.items(), key=lambda x: x[1])
        speedup = slowest[1] / fastest[1]
        print(f"Speedup over {slowest[0]}: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_all()