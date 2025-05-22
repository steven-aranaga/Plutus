#!/usr/bin/env python3
"""
Demonstrate Bloom filter usage for efficient Bitcoin address database lookups
"""

import os
import time
import sys
import random
import string
import psutil
from pybloom_live import ScalableBloomFilter

# Set the path to the database directory
DATABASE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database/11_13_2022')

def get_memory_usage():
    """Return the memory usage in MB"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / 1024 / 1024  # Convert to MB

def load_database_with_bloom_filter(substring_length=6):
    """Load database into a Bloom filter for efficient lookups"""
    print('Reading database files into Bloom filter...')
    
    # Create a scalable Bloom filter with a low false positive probability
    # This will automatically scale as more items are added
    bloom_filter = ScalableBloomFilter(initial_capacity=1000000, error_rate=0.000001)
    
    total_addresses = 0
    start_time = time.time()
    start_memory = get_memory_usage()
    
    # Get all database files
    file_paths = [os.path.join(DATABASE, filename) for filename in os.listdir(DATABASE)]
    
    # Process each file
    for file_path in file_paths:
        file_total = 0
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    address = line.strip()
                    if address and address.startswith('1'):  # Only process P2PKH addresses
                        # Add the suffix to the Bloom filter
                        bloom_filter.add(address[-substring_length:])
                        file_total += 1
                        total_addresses += 1
                        
                        # Print progress every 1 million addresses
                        if total_addresses % 1000000 == 0:
                            elapsed = time.time() - start_time
                            memory_used = get_memory_usage() - start_memory
                            print(f"Processed {total_addresses:,} addresses in {elapsed:.2f} seconds "
                                  f"({total_addresses/elapsed:.2f} addr/sec) - "
                                  f"Memory: {memory_used:.2f} MB")
            
            print(f"Processed {file_path} - {file_total:,} addresses")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    elapsed = time.time() - start_time
    memory_used = get_memory_usage() - start_memory
    print(f'DONE - Loaded {total_addresses:,} addresses into Bloom filter')
    print(f'Time: {elapsed:.2f} seconds ({total_addresses/elapsed:.2f} addr/sec)')
    print(f'Memory used: {memory_used:.2f} MB')
    print(f'Bytes per address: {(memory_used * 1024 * 1024) / total_addresses:.2f} bytes')
    
    return bloom_filter, total_addresses

def benchmark_bloom_filter(bloom_filter, num_lookups=1000000):
    """Benchmark Bloom filter lookup performance"""
    print(f"Benchmarking {num_lookups:,} lookups in Bloom filter...")
    
    # Generate random suffixes for testing
    random_suffixes = [''.join(random.choices(string.ascii_letters + string.digits, k=6)) 
                       for _ in range(num_lookups)]
    
    # Measure lookup time
    start_time = time.time()
    
    for suffix in random_suffixes:
        _ = suffix in bloom_filter
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Time for {num_lookups:,} lookups: {total_time:.4f} seconds")
    print(f"Lookups per second: {num_lookups/total_time:,.2f}")
    print(f"Time per lookup: {total_time/num_lookups*1000000:.2f} nanoseconds")

def compare_with_set(bloom_filter, num_lookups=1000000):
    """Compare Bloom filter with Python set for lookup performance"""
    print("\nComparing Bloom filter with Python set...")
    
    # Generate random suffixes for testing
    random_suffixes = [''.join(random.choices(string.ascii_letters + string.digits, k=6)) 
                       for _ in range(num_lookups)]
    
    # Add a subset of these to both data structures
    test_set = set()
    subset_size = min(1000000, num_lookups // 10)
    
    for i in range(subset_size):
        test_set.add(random_suffixes[i])
        bloom_filter.add(random_suffixes[i])
    
    # Benchmark set lookups
    start_time = time.time()
    
    for suffix in random_suffixes:
        _ = suffix in test_set
    
    end_time = time.time()
    set_time = end_time - start_time
    
    # Benchmark Bloom filter lookups
    start_time = time.time()
    
    for suffix in random_suffixes:
        _ = suffix in bloom_filter
    
    end_time = time.time()
    bloom_time = end_time - start_time
    
    print(f"Set lookup time: {set_time:.4f} seconds ({num_lookups/set_time:,.2f} lookups/sec)")
    print(f"Bloom filter lookup time: {bloom_time:.4f} seconds ({num_lookups/bloom_time:,.2f} lookups/sec)")
    
    if bloom_time < set_time:
        print(f"Bloom filter is {set_time/bloom_time:.2f}x faster than set")
    else:
        print(f"Set is {bloom_time/set_time:.2f}x faster than Bloom filter")
    
    # Memory usage comparison
    import sys
    bloom_size = sys.getsizeof(bloom_filter)
    set_size = sys.getsizeof(test_set)
    
    print(f"\nBloom filter size: {bloom_size/1024/1024:.2f} MB")
    print(f"Set size: {set_size/1024/1024:.2f} MB")
    
    if bloom_size < set_size:
        print(f"Bloom filter uses {set_size/bloom_size:.2f}x less memory than set")
    else:
        print(f"Set uses {bloom_size/set_size:.2f}x less memory than Bloom filter")

def test_false_positives(bloom_filter, num_tests=1000000):
    """Test the false positive rate of the Bloom filter"""
    print("\nTesting Bloom filter false positive rate...")
    
    # Generate random addresses that are definitely not in the filter
    random_addresses = []
    for _ in range(num_tests):
        # Generate a random Bitcoin-like address (not a real address generation algorithm)
        addr = '1' + ''.join(random.choices(string.ascii_letters + string.digits, k=33))
        random_addresses.append(addr)
    
    # Count false positives
    false_positives = 0
    for addr in random_addresses:
        # Check if the address suffix is in the filter
        if addr[-6:] in bloom_filter:
            false_positives += 1
    
    false_positive_rate = false_positives / num_tests
    print(f"False positive tests: {num_tests:,}")
    print(f"False positives: {false_positives:,}")
    print(f"Measured false positive rate: {false_positive_rate:.8f}")
    print(f"Expected false positive rate: {bloom_filter.error_rate:.8f}")
    print(f"This means approximately 1 in {1/false_positive_rate:.0f} lookups might incorrectly return True")

def main():
    """Main function to run the Bloom filter demo"""
    # Parse command line arguments
    substring_length = 6
    num_lookups = 1000000
    
    for arg in sys.argv[1:]:
        if arg.startswith('substring='):
            try:
                substring_length = int(arg.split('=')[1])
            except (ValueError, IndexError):
                print(f"Invalid substring value: {arg}")
                sys.exit(1)
        elif arg.startswith('lookups='):
            try:
                num_lookups = int(arg.split('=')[1])
            except (ValueError, IndexError):
                print(f"Invalid lookups value: {arg}")
                sys.exit(1)
    
    # Load database into Bloom filter
    bloom_filter, total_addresses = load_database_with_bloom_filter(substring_length)
    
    # Benchmark Bloom filter performance
    benchmark_bloom_filter(bloom_filter, num_lookups)
    
    # Compare with Python set
    compare_with_set(bloom_filter, num_lookups)
    
    # Test false positive rate
    test_false_positives(bloom_filter, num_lookups)
    
    print("\nBloom Filter Summary:")
    print(f"Total addresses loaded: {total_addresses:,}")
    print(f"Substring length: {substring_length}")
    print(f"Estimated false positive probability: {bloom_filter.error_rate:.8f}")
    print(f"This means approximately 1 in {1/bloom_filter.error_rate:.0f} lookups might incorrectly return True")
    print("\nTo use Bloom filters in the main Plutus script, run:")
    print("python3 plutus.py use_bloom=1")

if __name__ == "__main__":
    main()
