import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://172.24.247.186:27017/")
DB_NAME = os.getenv("DB_NAME", "cloud_pricing")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pricing_catalog")

def run():
    print(f"🔌 Conectando ao Mongo: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    collection.delete_many({})

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    file_names = ["aws.json", "gcp.json", "azure.json", "catalog_seed.json"]

    try:
        all_data = []
        for name in file_names:
            file_path = os.path.join(data_dir, name)
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r") as f:
                content = json.load(f)
                if isinstance(content, list):
                    all_data.extend(content)
                else:
                    all_data.append(content)

        if all_data:
            collection.insert_many(all_data)
            print(f"✅ Sucesso! {len(all_data)} itens inseridos.")
        else:
            print("⚠️ JSON vazio.")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    run()