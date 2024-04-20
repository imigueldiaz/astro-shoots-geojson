from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import WriteConcern
import json
import time
import dotenv
import os
import argparse


dotenv.load_dotenv()

uri = os.getenv("MONGODB_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def main():
    
    parser = argparse.ArgumentParser(description="Searches radiance data into the radiance collection.")
    parser.add_argument('--lat', help="The Point latitude", type=float, required=True)
    parser.add_argument('--lon', help="The Point longitude", type=float, required=True)
    parser.add_argument('--dist', help="Maximum distance in meters", type=int, default=1000)
    args = parser.parse_args()

    # Get the database and collection
    db = client.astroshoots
    collection = db.radiance

    filter = [
        {
            '$geoNear': {
                'near': {
                    'type': 'Point',
                    'coordinates': [args.lat, args.lon]
                },
                'distanceField': 'distance',
                'spherical': True,
                'maxDistance': args.dist
            }
        },
        {
            '$match': {
                'properties.Bortle': {
                    '$exists': True
                }
            }
        },
        {
            '$sort': {
                'distance': 1
            }
        },
        {
            '$group': {
                '_id': None,
                'meanBortle': {
                    '$avg': '$properties.Bortle'
                },
                'nearestDistance': {
                    '$first': '$distance'
                },
                'furthestDistance': {
                    '$last': '$distance'
                },

            }
        }
    ]


    result = client['astroshoots']['radiance'].aggregate(filter)

    for doc in result:
        print(doc)

if __name__ == '__main__':
    main()
