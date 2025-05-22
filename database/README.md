# Bitcoin Address Database

This directory contains a collection of text files with funded Bitcoin addresses downloaded from http://addresses.loyce.club/

## Database Information

- **Total Addresses**: 43,212,954 Bitcoin addresses with positive balances
- **Last Updated**: 11/13/2022 (format: month_day_year)
- **Update Frequency**: Every 3-6 months
- **Format**: Plain text files with one Bitcoin address per line

## File Structure

The database is split into multiple files (database_aa, database_ab, etc.) because GitHub limits file uploads to 50 MB. Each file contains a subset of addresses, all in the standard Bitcoin P2PKH format (starting with '1').

## Using the Database

The main Plutus script automatically loads these files and uses them to check for matches with generated addresses. For memory efficiency, only the last N characters of each address are loaded (controlled by the `substring` parameter).

## Updating the Database

To update the database with the latest Bitcoin addresses:

1. Download the latest database from http://addresses.loyce.club/
2. Split the file into smaller chunks if needed:
   ```bash
   split -l 1000000 downloaded_addresses.txt database_
   ```
3. Place the files in this directory
4. Update this README with the new date and address count

## Performance Considerations

- Loading the entire database requires significant memory
- The `substring` parameter in Plutus controls memory usage vs. accuracy
- For extremely large databases, consider using the Bloom filter implementation
- SSD storage will significantly improve database loading speed

## Verification

To verify the database integrity, you can count the total number of addresses:

```bash
cat database_* | wc -l
```

## Alternative Database Formats

For advanced users, converting the database to more efficient formats may improve performance:

- **SQLite**: Good for structured queries
- **LMDB**: Excellent for memory-mapped access
- **Binary formats**: Reduced size and faster loading

## Legal Notice

This database contains only public Bitcoin addresses. No private keys or personal information are included.

