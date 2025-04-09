import requests
import sqlite3
import json
import time  

#database 
DB_NAME = "open_meteo.db"

def extract_relevant_info(products):
    filtered_data = []
    for product in products:
        info = {
            "product_name": product.get("product_name"),
            "category": product.get("categories"),
            "calories": product.get("nutriments", {}).get("energy-kcal_100g"),
            "protein": product.get("nutriments", {}).get("proteins_100g"),
            "fat": product.get("nutriments", {}).get("fat_100g"),
            "sugar": product.get("nutriments", {}).get("sugars_100g"),
            "sodium": product.get("nutriments", {}).get("sodium_100g"),
            "serving_size": product.get("serving_size")
        }
        filtered_data.append(info)
    return filtered_data

def fetch_food_data(category, max_pages=10):
    all_data = []
    page = 1
    page_size = 100 

    while page <= max_pages:
        print(f"  🔄 Fetching page {page} for {category}...")
        url = f"https://world.openfoodfacts.org/category/{category}.json"
        params = {"page_size": page_size, "page": page}
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"  ❌ Error on page {page}: Status {response.status_code}")
            break

        if 'application/json' not in response.headers.get('Content-Type', ''):
            print(f"  ❌ Unexpected content type: {response.headers.get('Content-Type')}")
            break

        try:
            products = response.json().get("products", [])
        except json.JSONDecodeError:
            print("  ❌ JSON decoding failed.")
            break

        if not products:
            print("  🛑 No more products found.")
            break

        all_data.extend(extract_relevant_info(products))
        page += 1

        time.sleep(1)  

    return all_data
    

def save_data_to_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved {len(data)} entries to {filename}")

def main():
    categories = ["cereals", "granola-bars", "juices"]
    for category in categories:
        print(f"\n📦 Getting data for: {category}")
        data = fetch_food_data(category, max_pages=5)
        if data:
            save_data_to_json(data, f"{category}_data.json")

if __name__ == "__main__":
    main()