"""Example script for interacting with MongoDB using PyMongo."""

import os
import pymongo
import pandas as pd
from pymongo.errors import BulkWriteError
from pymongo.mongo_client import MongoClient


if __name__ == '__main__':

    client = MongoClient(
           f"mongodb+srv://{os.environ.get('mongodb_username')}:{os.environ.get('mongodb_password')}"
           f"@vinskraper.wykjrgz.mongodb.net/"
           f"?retryWrites=true&w=majority&appName=vinskraper"
    )
    database = client['vinskraper']['vinskraper']


    # REBUILD DATABASE FROM PARQUET FILES
    # ----------------------------------------------------------------------------------------------
    # 1. Delete existing data.
    # 2. Insert new data from parquet files.

    database.delete_many({})
    for file in os.listdir('../storage'):
        result = database.insert_many(
            pd.read_parquet(f'../storage/{file}').reset_index().to_dict('records')
        )
        print(f"{file}: Inserted {len(result.inserted_ids)} records")


    # UPDATE DATA WITH NEW VALUES
    # ----------------------------------------------------------------------------------------------
    # Update current data with additional values.
    # E.g., updated prices.
    # 1. Extract new data.
    # 2. Prepare bulk operations.
    # 3. Execute bulk write operation.

    data = pd.read_parquet('../storage/CIDER.parquet')
    data['pris 2024-07-20'] = 50.0
    data = data.reset_index().to_dict('records')

    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {'$set': record},
            upsert=True
        )
        for record in data
    ]

    try:
        result = database.bulk_write(operations)
        print(f"Modified {result.modified_count} records")
        print(f"Upserted {result.upserted_count} records")
    except BulkWriteError as bwe:
        print(f"Error during bulk write operation: {bwe.details}")


    # FETCH ALL DATA
    # ----------------------------------------------------------------------------------------------
    # Read all data from the database and store it in a DataFrame.

    data = pd.DataFrame(list(database.find())).drop(columns=['_id']).set_index('index')
    print(data.head())

    client.close()
