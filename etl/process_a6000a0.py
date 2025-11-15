"""
Process A6000A0 (Reclassifications) worksheet only
"""
import sys
sys.path.append('..')
from create_all_worksheets import process_worksheet
import duckdb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to database
con = duckdb.connect('../data/DuckDB/nmrc.duckdb', read_only=True)

# Process only A6000A0
logger.info("Processing A6000A0...")
process_worksheet('A6000A0', con)

con.close()
logger.info("Done!")
