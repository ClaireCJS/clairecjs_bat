import argparse
import pickle
from pprint import PrettyPrinter

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='View the contents of a pickle cache file.')
parser.add_argument('cache_file_name', type=str, help='The name of the cache file to read.')
args = parser.parse_args()

# Read the contents of the cache file
with open(args.cache_file_name, 'rb') as cache_file:
    cache_contents = pickle.load(cache_file)

# Print the contents of the cache file in a more readable format
pp = PrettyPrinter(indent=2)
print("Contents of the cache file:")
pp.pprint(cache_contents)

