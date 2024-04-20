from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import WriteConcern
import json
import argparse
import dotenv
import os

dotenv.load_dotenv()

uri = os.getenv("MONGODB_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def main():
    
    parser = argparse.ArgumentParser(description="Import radiance data into the radiance collection.")
    parser.add_argument('file', help="The JSON file to import.")
    args = parser.parse_args()

    # Open the JSON file and load the data
    with open(args.file, 'r') as file:
        data = json.load(file)

    # Get the database and collection
    db = client.astroshoots
    collection = db.radiance

    # Set the write concern for the collection
    collection = collection.with_options(write_concern=WriteConcern(w=1, j=True))

    # Insert the data into the collection
    print(f"Inserting {len(data['features'])} documents into the radiance collection.")
    result = collection.insert_many(data['features'], ordered=False)
    print(f"Inserted {len(result.inserted_ids)} documents into the radiance collection.")

if __name__ == "__main__":
    main()
