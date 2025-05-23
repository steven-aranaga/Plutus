#!/usr/bin/env python3
"""
Sharded TSV Parser with Bloom Filter implementation

This script parses TSV data, filters records based on specified criteria,
and implements a sharded database approach with Bloom filters for efficient lookups.
This approach aligns with the existing load_database_efficiently function.

Usage:
    python sharded_tsv_parser.py input.tsv output_dir
"""

import sys
import os
import csv
import hashlib
import math
import bitarray  # Install with: pip install bitarray
from pathlib import Path
from typing import List, Dict, Tuple, Set

class BloomFilter:
    def __init__(self, size: int, hash_count: int):
        """Initialize a Bloom filter with given size and number of hash functions."""
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray.bitarray(size)
        self.bit_array.setall(0)  # Initialize all bits to 0
    
    def _hash(self, item: str, seed: int) -> int:
        """Generate a hash for the item with a specific seed."""
        h = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.size
    
    def add(self, item: str) -> None:
        """Add an item to the Bloom filter."""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = 1
    
    def might_contain(self, item: str) -> bool:
        """Check if an item might be in the Bloom filter."""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True
    
    def save(self, filename: str) -> None:
        """Save the Bloom filter to a file."""
        with open(filename, 'wb') as f:
            self.bit_array.tofile(f)
    
    @classmethod
    def load(cls, filename: str, size: int, hash_count: int) -> 'BloomFilter':
        """Load a Bloom filter from a file."""
        bloom = cls(size, hash_count)
        with open(filename, 'rb') as f:
            bloom.bit_array = bitarray.bitarray()
            bloom.bit_array.fromfile(f)
        return bloom
    
    @classmethod
    def create_optimal(cls, n: int, p: float = 0.001) -> 'BloomFilter':
        """
        Create a Bloom filter with optimal size and hash count.
        
        Args:
            n: Expected number of elements
            p: False positive probability
            
        Returns:
            A BloomFilter instance with optimal parameters
        """
        m = int(-n * math.log(p) / (math.log(2) ** 2))  # Number of bits
        k = math.ceil((m / n) * math.log(2))            # Number of hash functions
        return cls(size=m, hash_count=k)

def get_shard_key(address: str, num_shards: int) -> int:
    """Determine which shard an address belongs to."""
    # Use first character of address for simple sharding
    # For more even distribution, could use a hash function
    if address.startswith('1'):  # P2PKH addresses
        # Use the last few characters for sharding, similar to your load function
        hash_val = int(hashlib.md5(address[-8:].encode()).hexdigest(), 16)
        return hash_val % num_shards
    else:
        # For non-P2PKH addresses, use a hash of the full address
        hash_val = int(hashlib.md5(address.encode()).hexdigest(), 16)
        return hash_val % num_shards

def count_valid_records(file_path: str) -> int:
    """
    Count the number of valid records in the TSV file based on balance criteria.
    
    Valid records have a balance between 100,000,000 and 80,000,000,000.
    """
    valid_count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                try:
                    balance = int(row[1])
                    # Keep records where balance is INSIDE the range 80000000000 > x > 100000000
                    if balance > 100000000 and balance < 80000000000:
                        valid_count += 1
                except ValueError:
                    continue
    return valid_count

def process_records_sharded(
    file_path: str, 
    output_dir: Path, 
    num_shards: int, 
    bloom_filters: Dict[int, BloomFilter]
) -> Tuple[int, int]:
    """
    Process records from the TSV file, add valid ones to sharded text files and Bloom filters.
    
    Returns:
        Tuple of (total processed records, added records)
    """
    # Create shard file handles
    shard_files = {}
    for i in range(num_shards):
        shard_path = output_dir / f"shard_{i}.txt"
        shard_files[i] = open(shard_path, 'w', encoding='utf-8')
    
    processed = 0
    added = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)  # Skip header
            
            for row in reader:
                processed += 1
                if processed % 1000000 == 0:
                    print(f"Processed {processed} records...")
                
                if len(row) >= 2:
                    try:
                        address = row[0]
                        balance = int(row[1])
                        
                        # Keep records where balance is INSIDE the range 80000000000 > x > 100000000
                        if balance > 100000000 and balance < 80000000000:
                            # Determine which shard this address belongs to
                            shard_id = get_shard_key(address, num_shards)
                            
                            # Write to the appropriate shard file
                            shard_files[shard_id].write(f"{address}\t{balance}\n")
                            
                            # Add to the appropriate Bloom filter
                            bloom_filters[shard_id].add(address)
                            
                            added += 1
                                
                    except ValueError:
                        continue
    finally:
        # Close all shard files
        for file in shard_files.values():
            file.close()
    
    return processed, added

def load_database_efficiently(db_dir: str, address: str) -> int:
    """
    Load balance for an address efficiently using sharded database and Bloom filters.
    
    Args:
        db_dir: Directory containing sharded database files
        address: Bitcoin address to look up
        
    Returns:
        Balance for the address or 0 if not found
    """
    db_path = Path(db_dir)
    num_shards = len([f for f in db_path.glob("shard_*.txt")])
    
    if num_shards == 0:
        print("No database shards found")
        return 0
    
    # Determine which shard to check
    shard_id = get_shard_key(address, num_shards)
    
    # Check if Bloom filter exists
    bloom_file = db_path / f"shard_{shard_id}.bloom"
    params_file = db_path / f"shard_{shard_id}.params"
    
    if bloom_file.exists() and params_file.exists():
        # Load Bloom filter parameters
        params = {}
        with open(params_file, 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                params[key] = int(value)
        
        # Load Bloom filter
        bloom = BloomFilter.load(str(bloom_file), params['m'], params['k'])
        
        # Check if address might be in the filter
        if not bloom.might_contain(address):
            return 0  # Definitely not in the database
    
    # Address might be in the database, check the shard file
    shard_file = db_path / f"shard_{shard_id}.txt"
    if not shard_file.exists():
        return 0
    
    # Search for the address in the shard file
    with open(shard_file, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2 and parts[0] == address:
                try:
                    return int(parts[1])
                except ValueError:
                    return 0
    
    return 0  # Address not found

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.tsv output_dir")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Number of shards to create
    num_shards = 128  # Adjust based on your needs
    
    # First pass: count valid records for Bloom filter sizing
    print("Counting valid records...")
    valid_count = count_valid_records(input_file)
    print(f"Found {valid_count} valid records")
    
    # Estimate records per shard (for Bloom filter sizing)
    records_per_shard = math.ceil(valid_count / num_shards)
    
    # Create Bloom filters for each shard
    print(f"Creating {num_shards} Bloom filters...")
    bloom_filters = {}
    for i in range(num_shards):
        bloom_filters[i] = BloomFilter.create_optimal(records_per_shard)
    
    # Process records into sharded files
    print("Processing records into shards...")
    processed, added = process_records_sharded(input_file, output_dir, num_shards, bloom_filters)
    
    # Save Bloom filters
    print("Saving Bloom filters...")
    for i, bloom in bloom_filters.items():
        bloom_file = output_dir / f"shard_{i}.bloom"
        bloom.save(str(bloom_file))
        
        # Save Bloom filter parameters
        params_file = output_dir / f"shard_{i}.params"
        with open(params_file, 'w') as f:
            f.write(f"k={bloom.hash_count}\nm={bloom.size}\nn={records_per_shard}")
    
    print(f"Done! Processed {processed} records, added {added} records to {num_shards} shards.")
    print(f"Sharded files and Bloom filters saved to {output_dir}")

    # Example usage of the Bloom filters for testing
    print("\nBloom filter test:")
    test_addresses = ["example_address1", "example_address2"]
    for address in test_addresses:
        shard_id = get_shard_key(address, num_shards)
        result = bloom_filters[shard_id].might_contain(address)
        print(f"'{address}' might be in shard {shard_id}: {result}")
    
    # Example of using the load function
    print("\nDatabase lookup test:")
    for address in test_addresses:
        balance = load_database_efficiently(str(output_dir), address)
        print(f"Balance for '{address}': {balance}")

if __name__ == "__main__":
    main()