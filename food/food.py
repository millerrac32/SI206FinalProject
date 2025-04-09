import requests
import sqlite3
import json
import time  

#database 
DB_NAME = "open_meteo.db"

HEADERS = {
    "User-Agent": "FoodDataApp/1.0 (kdlviana@umich.edu)"
}

def extract_relevant_info(products):
    """
    Extract relevant fields from the API response.
    """
    filtered_data = []
    for product in products:
        info = {
            "product_name": product.get("product_name"),
            "category": product.get("categories_tags", [None])[0],  # Use the first category tag
            "calories": product.get("nutriments", {}).get("energy-kcal_100g"),
            "protein": product.get("nutriments", {}).get("proteins_100g"),
            "fat": product.get("nutriments", {}).get("fat_100g"),
            "sugar": product.get("nutriments", {}).get("sugars_100g"),
            "sodium": product.get("nutriments", {}).get("sodium_100g"),
            "serving_size": product.get("serving_size")
        }
        filtered_data.append(info)
    return filtered_data

def fetch_food_data(category, max_pages=5):
    """
    Fetch data from the Open Food Facts API for a specific category.
    """
    all_data = []
    page = 1
    page_size = 25  # Limit to 25 items per page as per assignment requirements

    while page <= max_pages:
        print(f"🔄 Fetching page {page} for category: {category}...")
        url = f"https://world.openfoodfacts.org/category/{category}.json"
        params = {
            "page_size": page_size,
            "page": page,
            "fields": "product_name,categories_tags,nutriments,serving_size"  # Limit fields
        }
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code} on page {page}")
            break

        try:
            products = response.json().get("products", [])
        except json.JSONDecodeError:
            print("❌ JSON decoding failed.")
            break

        if not products:
            print("🛑 No more products found.")
            break

        all_data.extend(extract_relevant_info(products))
        page += 1

        # Respect API rate limits
        time.sleep(6)  # 10 requests per minute = 6 seconds per request

    return all_data

def save_data_to_json(data, filename):
    """
    Save the fetched data to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved {len(data)} entries to {filename}")

def main():
    """
    Main function to fetch and save data for multiple categories.
    """
    categories = ["cereals", "granola-bars", "juices"]
    for category in categories:
        print(f"\n📦 Fetching data for category: {category}")
        data = fetch_food_data(category, max_pages=5)
        if data:
            save_data_to_json(data, f"{category}_data.json")

if __name__ == "__main__":
    main()