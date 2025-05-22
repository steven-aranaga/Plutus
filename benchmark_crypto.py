#!/usr/bin/env python3
"""
Benchmark different cryptographic libraries for Bitcoin key operations
"""

import time
import os
import binascii
import hashlib
import sys

# Number of keys to generate for benchmarking
NUM_KEYS = 1000

def generate_private_keys(num_keys):
    """Generate random private keys"""
    return [binascii.hexlify(os.urandom(32)).decode('utf-8').upper() 
            for _ in range(num_keys)]

def benchmark_fastecdsa():
    """Benchmark fastecdsa library"""
    try:
        from fastecdsa import keys, curve
        
        def pk_to_pubkey(private_key):
            key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
            return '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)
        
        private_keys = generate_private_keys(NUM_KEYS)
        
        start = time.time()
        for pk in private_keys:
            pubkey = pk_to_pubkey(pk)
        end = time.time()
        
        return end - start
    except ImportError:
        print("fastecdsa not installed")
        return None

def benchmark_starkbank():
    """Benchmark starkbank-ecdsa library"""
    try:
        from ellipticcurve.privateKey import PrivateKey
        
        def pk_to_pubkey(private_key):
            # For starkbank, we need to create a new private key from bytes
            private_key_bytes = bytes.fromhex(private_key)
            pk = PrivateKey.fromString(private_key_bytes)
            return '04' + pk.publicKey().toString().hex().upper()
        
        private_keys = generate_private_keys(NUM_KEYS)
        
        start = time.time()
        for pk in private_keys:
            try:
                pubkey = pk_to_pubkey(pk)
            except Exception:
                # Skip any problematic keys
                continue
        end = time.time()
        
        return end - start
    except (ImportError, Exception) as e:
        print(f"starkbank-ecdsa error: {e}")
        return None

def benchmark_coincurve():
    """Benchmark coincurve library"""
    try:
        import coincurve
        
        def pk_to_pubkey(private_key):
            private_key_bytes = bytes.fromhex(private_key)
            public_key = coincurve.PublicKey.from_secret(private_key_bytes)
            return '04' + public_key.format(compressed=False)[1:].hex().upper()
        
        private_keys = generate_private_keys(NUM_KEYS)
        
        start = time.time()
        for pk in private_keys:
            pubkey = pk_to_pubkey(pk)
        end = time.time()
        
        return end - start
    except ImportError:
        print("coincurve not installed")
        return None

def benchmark_all():
    """Run all benchmarks and print results"""
    print(f"Benchmarking with {NUM_KEYS} keys...")
    
    results = {}
    
    # Benchmark fastecdsa
    time_fastecdsa = benchmark_fastecdsa()
    if time_fastecdsa:
        results["fastecdsa"] = time_fastecdsa
        print(f"fastecdsa: {time_fastecdsa:.4f} seconds ({NUM_KEYS/time_fastecdsa:.2f} keys/sec)")
    
    # Benchmark starkbank-ecdsa
    time_starkbank = benchmark_starkbank()
    if time_starkbank:
        results["starkbank"] = time_starkbank
        print(f"starkbank: {time_starkbank:.4f} seconds ({NUM_KEYS/time_starkbank:.2f} keys/sec)")
    
    # Benchmark coincurve
    time_coincurve = benchmark_coincurve()
    if time_coincurve:
        results["coincurve"] = time_coincurve
        print(f"coincurve: {time_coincurve:.4f} seconds ({NUM_KEYS/time_coincurve:.2f} keys/sec)")
    
    # Print the fastest library
    if results:
        fastest = min(results.items(), key=lambda x: x[1])
        print(f"\nFastest library: {fastest[0]} ({NUM_KEYS/fastest[1]:.2f} keys/sec)")
        
        # Compare to the slowest
        slowest = max(results.items(), key=lambda x: x[1])
        speedup = slowest[1] / fastest[1]
        print(f"Speedup over {slowest[0]}: {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_all()