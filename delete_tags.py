# delete_tags.py
import requests
import json
import html
from get_tags import get_all_tags  # Tái sử dụng hàm từ get_tags.py

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
params = {
    "consumer_key": CONSUMER_KEY,
    "consumer_secret": CONSUMER_SECRET,
    "force": True  # Thêm tham số force=true để xóa hẳn
}

def delete_tag(tag_id):
    """Xóa một tag dựa trên ID."""
    try:
        response = requests.delete(
            f"{WP_URL}/wc/v3/products/tags/{tag_id}",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            print(f"Đã xóa tag ID {tag_id} thành công!")
            return True
        else:
            print(f"Lỗi khi xóa tag ID {tag_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Lỗi khi xóa tag ID {tag_id}: {str(e)}")
        return False

def main():
    # Bước 1: Lấy danh sách tất cả tags
    print("Đang lấy danh sách tags từ API...")
    all_tags = get_all_tags()
    
    if not all_tags:
        print("Không tìm thấy tag nào trên website.")
        return

    # Bước 2: Hiển thị danh sách tags
    print("\nDanh sách tất cả tags sản phẩm:")
    for tag in all_tags:
        tag_name = html.unescape(tag['name'])  # Giải mã HTML entities
        print(f"ID: {tag['id']} - Tên: {tag_name} - Slug: {tag['slug']}")
    print(f"Tổng số tags: {len(all_tags)}")

    # Bước 3: Yêu cầu người dùng nhập danh sách ID tag cần xóa
    tag_ids_input = input("\nNhập danh sách ID của các tag cần xóa (cách nhau bằng dấu phẩy, ví dụ: 684,685,686; hoặc 'exit' để thoát): ").strip()
    if tag_ids_input.lower() == 'exit':
        print("Đã thoát chương trình.")
        return

    try:
        tag_ids = [int(id.strip()) for id in tag_ids_input.split(',')]
    except ValueError:
        print("ID phải là số nguyên và cách nhau bằng dấu phẩy. Vui lòng thử lại.")
        return

    # Kiểm tra xem các tag_id có tồn tại không
    tags_to_delete = []
    for tag_id in tag_ids:
        tag_exists = False
        tag_name = ""
        for tag in all_tags:
            if tag['id'] == tag_id:
                tag_exists = True
                tag_name = html.unescape(tag['name'])
                break
        if tag_exists:
            tags_to_delete.append({'id': tag_id, 'name': tag_name})
        else:
            print(f"Không tìm thấy tag với ID {tag_id}. Sẽ bỏ qua tag này.")

    if not tags_to_delete:
        print("Không có tag nào hợp lệ để xóa.")
        return

    # Bước 4: Xác nhận trước khi xóa
    print("\nBạn sắp xóa các tag sau:")
    for tag in tags_to_delete:
        print(f"- ID: {tag['id']} - Tên: {tag['name']}")
    confirmation = input("Bạn có chắc chắn muốn xóa các tag này không? Nhập 'yes' để xác nhận: ").strip().lower()
    if confirmation != 'yes':
        print("Đã hủy xóa tags.")
        return

    # Bước 5: Xóa các tag
    for tag in tags_to_delete:
        tag_id = tag['id']
        if delete_tag(tag_id):
            all_tags = [t for t in all_tags if t['id'] != tag_id]
    print(f"Danh sách tags còn lại: {len(all_tags)} tags.")

if __name__ == "__main__":
    main()