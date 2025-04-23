# get_tags.py
import requests
import json

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

WP_URL = config['WP_URL']
CONSUMER_KEY = config['CONSUMER_KEY']
CONSUMER_SECRET = config['CONSUMER_SECRET']

# Headers và params cơ bản
headers = {
    "Content-Type": "application/json"
}
base_params = {
    "consumer_key": CONSUMER_KEY,
    "consumer_secret": CONSUMER_SECRET,
    "per_page": 100,  # Lấy tối đa 100 tags mỗi trang
    "page": 1         # Bắt đầu từ trang 1
}

def get_all_tags():
    all_tags = []
    page = 1
    while True:
        params = base_params.copy()
        params["page"] = page
        
        # Gửi request để lấy tags
        response = requests.get(
            f"{WP_URL}/wc/v3/products/tags",
            headers=headers,
            params=params
        )

        # Kiểm tra kết quả
        if response.status_code == 200:
            tags = response.json()
            if not tags:  # Nếu không còn tags, thoát vòng lặp
                break
            
            all_tags.extend(tags)  # Thêm tags vào danh sách tổng
            print(f"Đã lấy trang {page} - Số tags hiện tại: {len(all_tags)}")
            
            # Tăng số trang để lấy tiếp
            page += 1
        else:
            print(f"Lỗi: {response.status_code}")
            print(response.text)
            break

    return all_tags

# Chạy độc lập để kiểm tra
if __name__ == "__main__":
    all_tags = get_all_tags()
    print("\nDanh sách tất cả tags sản phẩm:")
    for tag in all_tags:
        print(f"ID: {tag['id']} - Tên: {tag['name']} - Slug: {tag['slug']}")
    print(f"Tổng số tags: {len(all_tags)}")