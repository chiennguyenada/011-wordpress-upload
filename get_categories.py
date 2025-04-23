# get_categories.py
import requests
import json

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

WP_URL = config['WP_URL']
CONSUMER_KEY = config['CONSUMER_KEY']
CONSUMER_SECRET = config['CONSUMER_SECRET']

# Headers và params cơ bản cho request
headers = {
    "Content-Type": "application/json"
}
base_params = {
    "consumer_key": CONSUMER_KEY,
    "consumer_secret": CONSUMER_SECRET,
    "per_page": 100  # Lấy tối đa 100 danh mục mỗi trang
}

def get_all_categories():
    all_categories = []
    page = 1
    while True:
        # Thêm tham số page vào params
        params = base_params.copy()
        params["page"] = page
        
        # Gửi request
        response = requests.get(
            f"{WP_URL}/wc/v3/products/categories",
            headers=headers,
            params=params
        )
        
        # Kiểm tra kết quả
        if response.status_code == 200:
            categories = response.json()
            if not categories:  # Nếu không còn danh mục nào trả về
                break
                
            all_categories.extend(categories)
            print(f"Đã lấy trang {page} - Số danh mục: {len(categories)}")
            page += 1
        else:
            print(f"Lỗi: {response.status_code}")
            print(response.text)
            break
    
    return all_categories

# Chạy độc lập để kiểm tra
if __name__ == "__main__":
    categories = get_all_categories()
    print(f"\nTổng số danh mục: {len(categories)}")
    print("Danh sách danh mục sản phẩm:")
    for category in categories:
        print(f"ID: {category['id']} - Tên: {category['name']} - Slug: {category['slug']}")