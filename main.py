# main.py
import os
import json
import re
import html  # Thêm module html để giải mã HTML entities
import time
import argparse
from product_processor import process_product_file
from product_uploader import upload_product, update_product_media, check_and_update_or_create, check_product_exists
from get_categories import get_all_categories
from get_tags import get_all_tags
from media import check_image_exists, upload_image_to_media, find_media_by_filename, delete_media_by_filename

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Hàm lấy focus keyword từ file .txt (dùng để kiểm tra hình ảnh)
def get_focus_keyword(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Loại bỏ khoảng trắng thừa và dòng trống
    lines = [line.strip() for line in lines if line.strip()]

    # 1. Lấy 4 dòng đầu tiên làm short_description
    short_description_lines = lines[:4]

    # 2. Tìm focus keyword (tên sản phẩm, ví dụ: x20ai2222)
    focus_keyword = None
    for line in short_description_lines:
        # Tìm linh hoạt hơn: không cần dấu "•", chỉ cần có "Mã sản phẩm"
        if "Mã sản phẩm" in line:
            focus_keyword = line.split("Mã sản phẩm:")[-1].strip().lower()
            break

    # Nếu không tìm thấy focus keyword, tìm tiêu đề (dòng có thẻ <H1>)
    if not focus_keyword:
        for line in lines:
            if line.startswith("<H1>"):
                product_name = re.search(r'<H1>(.*?)</H1>', line).group(1)
                focus_keyword = product_name.split()[-1].strip().lower()
                break

    if not focus_keyword:
        raise ValueError(f"Không tìm thấy focus keyword trong file {file_path}")

    return focus_keyword

# Hàm kiểm tra hình ảnh cho tất cả các file .txt
def check_images_for_all_files(txt_files, image_prefix):
    missing_images = []
    
    for txt_file in txt_files:
        file_path = os.path.join("bai-viet", txt_file)
        try:
            focus_keyword = get_focus_keyword(file_path)
        except Exception as e:
            missing_images.append(f"File {txt_file}: Lỗi khi lấy focus keyword - {str(e)}")
            continue

        # Tạo tên file hình sản phẩm và hình đại diện (kiểm tra cả .png và .jpg)
        image_filename_png = f"so-do-chan-{image_prefix}-{focus_keyword}.png"
        image_filename_jpg = f"so-do-chan-{image_prefix}-{focus_keyword}.jpg"
        avatar_filename_png = f"{image_prefix}-{focus_keyword}.png"
        avatar_filename_jpg = f"{image_prefix}-{focus_keyword}.jpg"
        
        image_path_png = os.path.join("hinh-sp", image_filename_png)
        image_path_jpg = os.path.join("hinh-sp", image_filename_jpg)
        avatar_path_png = os.path.join("hinh-avata", avatar_filename_png)
        avatar_path_jpg = os.path.join("hinh-avata", avatar_filename_jpg)

        # Kiểm tra sự tồn tại của hình ảnh (cả .png và .jpg)
        image_exists = os.path.exists(image_path_png) or os.path.exists(image_path_jpg)
        avatar_exists = os.path.exists(avatar_path_png) or os.path.exists(avatar_path_jpg)
        
        if not image_exists:
            missing_images.append(f"File {txt_file}: Thiếu hình sản phẩm (kiểm tra {image_path_png} hoặc {image_path_jpg})")
        if not avatar_exists:
            missing_images.append(f"File {txt_file}: Thiếu hình đại diện (kiểm tra {avatar_path_png} hoặc {avatar_path_jpg})")

    return missing_images

# Hàm kiểm tra hình ảnh đã tồn tại trên WordPress Media
def check_existing_images(txt_files, image_prefix):
    existing_images = []
    
    for txt_file in txt_files:
        file_path = os.path.join("bai-viet", txt_file)
        try:
            focus_keyword = get_focus_keyword(file_path)
        except Exception as e:
            print(f"Lỗi khi lấy focus keyword từ file {txt_file}: {str(e)}")
            continue

        # Tạo tên file hình sản phẩm và hình đại diện (kiểm tra không phụ thuộc phần mở rộng)
        image_filename = f"so-do-chan-{image_prefix}-{focus_keyword}"
        avatar_filename = f"{image_prefix}-{focus_keyword}"
        
        # Kiểm tra sự tồn tại của hình ảnh trên WordPress Media
        # Kiểm tra cả .png và .jpg và các biến thể có thể có
        image_exists = check_image_exists(f"{image_filename}.png")
        if not image_exists:
            image_exists = check_image_exists(f"{image_filename}.jpg")
            
        avatar_exists = check_image_exists(f"{avatar_filename}.png")
        if not avatar_exists:
            avatar_exists = check_image_exists(f"{avatar_filename}.jpg")
        
        if image_exists:
            existing_images.append(f"File {txt_file}: Hình sản phẩm đã tồn tại trong thư viện media (ID: {image_exists['id']}, URL: {image_exists['url']})")
        
        if avatar_exists:
            existing_images.append(f"File {txt_file}: Hình đại diện đã tồn tại trong thư viện media (ID: {avatar_exists['id']}, URL: {avatar_exists['url']})")

    return existing_images

# Hàm đối chiếu ID với tên cho categories
def get_category_names(category_ids, all_categories):
    category_info = []
    for cat in category_ids:
        cat_id = cat['id']
        # Tìm tên category tương ứng với ID
        category_name = "Không tìm thấy"
        for category in all_categories:
            if category['id'] == cat_id:
                category_name = html.unescape(category['name'])  # Giải mã HTML entities
                break
        category_info.append({'id': cat_id, 'name': category_name})
    return category_info

# Hàm đối chiếu ID với tên cho tags
def get_tag_names(tag_ids, all_tags):
    tag_info = []
    for tag in tag_ids:
        tag_id = tag['id']
        # Tìm tên tag tương ứng với ID
        tag_name = "Không tìm thấy"
        for t in all_tags:
            if t['id'] == tag_id:
                tag_name = html.unescape(t['name'])  # Giải mã HTML entities
                break
        tag_info.append({'id': tag_id, 'name': tag_name})
    return tag_info

def get_category_name(category_id, all_categories):
    """
    Tìm tên category từ ID
    """
    for category in all_categories:
        if category['id'] == category_id:
            return html.unescape(category['name'])
    return f"Unknown Category (ID: {category_id})"

def get_tag_name(tag_id, all_tags):
    """
    Tìm tên tag từ ID
    """
    for tag in all_tags:
        if tag['id'] == tag_id:
            return html.unescape(tag['name'])
    return f"Unknown Tag (ID: {tag_id})"

def main():
    # Phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(description='Upload sản phẩm lên WordPress/WooCommerce.')
    parser.add_argument('--skip-exist', action='store_true', help='Bỏ qua sản phẩm đã tồn tại thay vì hiển thị lỗi')
    parser.add_argument('--force-update', action='store_true', help='Cập nhật sản phẩm đã tồn tại mà không hỏi')
    parser.add_argument('--delay', type=int, default=2, help='Độ trễ giữa các lần tải lên (giây), mặc định là 2')
    parser.add_argument('--file', type=str, help='Chỉ tải lên một file cụ thể')
    args = parser.parse_args()
    
    # Thư mục chứa các file .txt
    input_dir = "bai-viet"

    # Load categories, tags, and image_prefix from config
    categories = config['categories']
    tags = config['tags']
    image_prefix = config['image_prefix']
    
    if not args.file:  # Nếu không chỉ định file cụ thể, hiển thị menu
        print("Chọn chế độ:")
        print("1. Đăng các bài viết mới")
        print("2. Cập nhật hình đại diện cho sản phẩm đã tồn tại")
        print("3. Quản lý hình ảnh trong thư viện media")
        print("4. Thay đổi cấu hình (categories, tags, image_prefix)")
        choice = input("Nhập lựa chọn của bạn (1-4): ").strip()
        
        if choice == "2":
            update_existing_product_media()
            return
        elif choice == "3":
            manage_media_library()
            return
        elif choice == "4":
            update_configuration()
            return
    
    # Xác định danh sách file cần xử lý
    if args.file:
        txt_files = [args.file] if args.file.endswith('.txt') else [args.file + '.txt']
        # Kiểm tra xem file có tồn tại không
        if not all(os.path.exists(os.path.join(input_dir, f)) for f in txt_files):
            print(f"Không tìm thấy file: {args.file}")
            return
    else:
        # Quét tất cả các file .txt trong thư mục bai-viet
        txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        if not txt_files:
            print(f"Không tìm thấy file .txt nào trong thư mục {input_dir}!")
            return
    
    print(f"Tìm thấy {len(txt_files)} file .txt: {txt_files}")
    
    # Bước 1: Kiểm tra hình ảnh local cho tất cả các file
    print("\nKiểm tra hình ảnh local cho tất cả các file...")
    missing_images = check_images_for_all_files(txt_files, image_prefix)
    
    if missing_images:
        print("\nCó lỗi: Một số sản phẩm thiếu hình ảnh local:")
        for error in missing_images:
            print(f"- {error}")
        print("Chương trình sẽ dừng lại. Vui lòng bổ sung hình ảnh trước khi chạy lại.")
        return
    else:
        print("Tất cả các sản phẩm đều có đủ hình sản phẩm và hình đại diện local.")
    
    # BƯỚC MỚI: Kiểm tra hình ảnh đã tồn tại trên WordPress Media
    print("\nKiểm tra hình ảnh đã tồn tại trên WordPress Media...")
    existing_images = check_existing_images(txt_files, image_prefix)
    
    if existing_images and not args.skip_exist and not args.force_update:
        print("\nCảnh báo: Một số hình ảnh đã tồn tại trong thư viện media của WordPress:")
        for warning in existing_images:
            print(f"- {warning}")
        
        choice = input("\nBạn muốn tiếp tục không? (yes/no): ").strip().lower()
        if choice != 'yes':
            print("Chương trình sẽ dừng lại. Vui lòng kiểm tra lại trước khi tiếp tục.")
            return
    elif existing_images:
        print("\nCảnh báo: Một số hình ảnh đã tồn tại trong thư viện media của WordPress.")
        print("Chế độ bỏ qua hoặc cập nhật đã được kích hoạt, tiếp tục xử lý...")
    else:
        print("Không có hình ảnh nào đã tồn tại trong thư viện media của WordPress.")

    # Bước 2: Lấy danh sách categories và tags từ API
    print("\nĐang tải danh sách danh mục và tags từ WordPress...")
    try:
        all_categories = get_all_categories()
        all_tags = get_all_tags()
        
        # Chuyển đổi category IDs thành tên
        category_info = []
        for cat_id_dict in categories:
            cat_id = cat_id_dict["id"]
            category_name = get_category_name(cat_id, all_categories)
            category_info.append({"id": cat_id, "name": category_name})
        
        # Chuyển đổi tag IDs thành tên
        tag_info = []
        for tag_id_dict in tags:
            tag_id = tag_id_dict["id"]
            tag_name = get_tag_name(tag_id, all_tags)
            tag_info.append({"id": tag_id, "name": tag_name})
        
    except Exception as e:
        print(f"Lỗi khi lấy danh sách categories và tags: {str(e)}")
        return
    
    # Hiển thị thông tin cấu hình cho người dùng xác nhận
    print("\nThông tin cấu hình sắp được sử dụng:")
    print("\nCATEGORIES:")
    for cat in category_info:
        print(f"- ID: {cat['id']} - Tên: {cat['name']}")
    
    print("\nTAGS:")
    for tag in tag_info:
        print(f"- ID: {tag['id']} - Tên: {tag['name']}")
    
    print(f"\nIMAGE PREFIX: {image_prefix}")
    print(f"Ví dụ tên file hình đại diện: {image_prefix}-x20ai2222.png/jpg")
    print(f"Ví dụ tên file hình sơ đồ chân: so-do-chan-{image_prefix}-x20ai2222.png/jpg")
    
    if not args.force_update:
        confirmation = input("\nBạn có muốn tiếp tục với cấu hình này không? Nhập 'yes' để xác nhận hoặc 'no' để thay đổi cấu hình: ").strip().lower()
        if confirmation != 'yes':
            choice = input("Bạn muốn dừng chương trình hay thay đổi cấu hình? (stop/change): ").strip().lower()
            if choice == 'change':
                update_configuration()
            print("Chương trình sẽ dừng lại.")
            return

    # Bước 3: Xử lý từng file .txt
    print("\nBắt đầu xử lý các file...")
    for i, txt_file in enumerate(txt_files):
        file_path = os.path.join(input_dir, txt_file)
        print(f"\nĐang xử lý file {i+1}/{len(txt_files)}: {file_path}")

        try:
            # Xử lý file và lấy thông tin
            product_name, short_description, description, focus_keyword, rank_math_description, avatar_info, combined_keywords = process_product_file(file_path)
            print(f"Tiêu đề sản phẩm: {product_name}")
            print(f"Mô tả ngắn: {short_description}")
            print(f"Focus keyword: {focus_keyword}")
            print(f"Rank Math Description: {rank_math_description}")
            print(f"Tất cả từ khóa (focus + secondary): {combined_keywords}")
            print(f"Nội dung bài viết (description):\n{description[:200]}...\n")

            # Hiển thị thông tin hình đại diện
            if avatar_info:
                print(f"Thông tin hình đại diện:")
                print(f"URL: {avatar_info['url']}")
                print(f"ID: {avatar_info['id']}")

            # Upload sản phẩm với các tùy chọn
            if args.skip_exist:
                # Gọi hàm kiểm tra và tải lên/cập nhật
                result = check_and_update_or_create(focus_keyword, product_name, short_description, description, 
                                       rank_math_description, avatar_info, combined_keywords, categories, tags, 
                                       force_update=args.force_update)
                if not result:
                    print(f"Bỏ qua sản phẩm '{product_name}' với SKU '{focus_keyword}'")
            else:
                # Upload sản phẩm mới bình thường
                upload_product(product_name, short_description, description, focus_keyword, 
                              rank_math_description, avatar_info, combined_keywords, categories, tags)
            
            # Thêm độ trễ giữa các lần tải lên để tránh quá tải server
            if i < len(txt_files) - 1:  # Không cần trễ sau file cuối cùng
                print(f"Đợi {args.delay} giây trước khi xử lý file tiếp theo...")
                time.sleep(args.delay)
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {txt_file}: {str(e)}")
            continue

def update_existing_product_media():
    """
    Hàm cho phép cập nhật hình đại diện cho sản phẩm đã tồn tại.
    """
    # Load image_prefix from config
    image_prefix = config['image_prefix']
    
    product_id = input("\nNhập ID sản phẩm cần cập nhật hình đại diện: ").strip()
    if not product_id.isdigit():
        print("ID sản phẩm không hợp lệ!")
        return
    
    focus_keyword = input("Nhập mã sản phẩm (focus_keyword), ví dụ: x20ai2222: ").strip().lower()
    if not focus_keyword:
        print("Mã sản phẩm không được để trống!")
        return
    
    # Tạo tên file hình đại diện (kiểm tra cả PNG và JPG)
    avatar_filename_png = f"{image_prefix}-{focus_keyword}.png"
    avatar_filename_jpg = f"{image_prefix}-{focus_keyword}.jpg"
    avatar_path_png = os.path.join("hinh-avata", avatar_filename_png)
    avatar_path_jpg = os.path.join("hinh-avata", avatar_filename_jpg)
    
    # Kiểm tra sự tồn tại của file hình
    avatar_path = None
    if os.path.exists(avatar_path_png):
        avatar_path = avatar_path_png
    elif os.path.exists(avatar_path_jpg):
        avatar_path = avatar_path_jpg
    
    if not avatar_path:
        print(f"Không tìm thấy file hình đại diện PNG ({avatar_path_png}) hoặc JPG ({avatar_path_jpg})")
        return
    
    # Tạo metadata cho hình đại diện
    product_name = input("Nhập tên sản phẩm: ").strip()
    if not product_name:
        print("Tên sản phẩm không được để trống!")
        return
    
    # Xử lý IMAGE_PREFIX để bỏ dấu "-" và thay bằng khoảng trắng
    image_prefix_cleaned = image_prefix.replace("-", " ")
    
    avatar_alt_text = product_name
    avatar_caption = f"Hình đại diện module {focus_keyword.upper()}"
    avatar_description = f"Hình đại diện của module {product_name} thuộc dòng {image_prefix_cleaned} của B&R Automation."
    
    print(f"\nĐang upload hình đại diện: {avatar_path}")
    
    # Upload hình đại diện
    avatar_info = upload_image_to_media(
        avatar_path,
        alt_text=avatar_alt_text,
        caption=avatar_caption,
        description=avatar_description
    )
    
    if not avatar_info:
        print("Không thể upload hình đại diện!")
        return
    
    print(f"Hình đại diện đã được upload thành công!")
    print(f"URL: {avatar_info['url']}")
    print(f"ID: {avatar_info['id']}")
    
    # Cập nhật hình đại diện cho sản phẩm
    confirmation = input("\nBạn có muốn cập nhật hình đại diện cho sản phẩm không? Nhập 'yes' để xác nhận: ").strip().lower()
    if confirmation != 'yes':
        print("Người dùng không xác nhận. Hủy cập nhật.")
        return
    
    print(f"\nĐang cập nhật hình đại diện cho sản phẩm ID: {product_id}")
    update_product_media(product_id, avatar_info)

def manage_media_library():
    """
    Hàm quản lý thư viện media, cho phép tìm kiếm và xóa hình ảnh.
    """
    print("\n===== QUẢN LÝ THƯ VIỆN MEDIA =====")
    print("1. Tìm kiếm hình ảnh theo tên file")
    print("2. Xóa hình ảnh theo tên file")
    print("3. Xóa hình ảnh của một sản phẩm")
    print("4. Quay lại")
    
    choice = input("Nhập lựa chọn của bạn (1-4): ").strip()
    
    if choice == "1":
        filename = input("\nNhập tên file cần tìm (không cần phần mở rộng, ví dụ: safety-plc-x20sl8110): ").strip()
        if not filename:
            print("Tên file không được để trống!")
            return
        
        # Tìm kiếm cả .png và .jpg
        print(f"\nĐang tìm kiếm hình ảnh có tên: {filename}")
        media_items = find_media_by_filename(filename)
        
        if media_items:
            print(f"\nTìm thấy {len(media_items)} hình ảnh:")
            for i, item in enumerate(media_items, 1):
                print(f"{i}. ID: {item['id']}, URL: {item['url']}, Filename: {item['filename']}")
        else:
            print("Không tìm thấy hình ảnh nào phù hợp.")
    
    elif choice == "2":
        filename = input("\nNhập tên file cần xóa (không cần phần mở rộng, ví dụ: safety-plc-x20sl8110): ").strip()
        if not filename:
            print("Tên file không được để trống!")
            return
        
        # Tìm kiếm cả .png và .jpg
        print(f"\nĐang tìm kiếm hình ảnh có tên: {filename}")
        media_items = find_media_by_filename(filename)
        
        if media_items:
            print(f"\nTìm thấy {len(media_items)} hình ảnh:")
            for i, item in enumerate(media_items, 1):
                print(f"{i}. ID: {item['id']}, URL: {item['url']}, Filename: {item['filename']}")
            
            confirm = input("\nBạn có chắc chắn muốn xóa (các) hình ảnh này không? (yes/no): ").strip().lower()
            if confirm == 'yes':
                delete_media_by_filename(filename)
            else:
                print("Đã hủy thao tác xóa.")
        else:
            print("Không tìm thấy hình ảnh nào phù hợp để xóa.")
    
    elif choice == "3":
        focus_keyword = input("\nNhập mã sản phẩm (focus_keyword), ví dụ: x20ai2222: ").strip().lower()
        if not focus_keyword:
            print("Mã sản phẩm không được để trống!")
            return
        
        # Load image_prefix from config
        image_prefix = config['image_prefix']
        
        # Tạo tên file hình đại diện và hình sản phẩm (không có phần mở rộng)
        avatar_filename = f"{image_prefix}-{focus_keyword}"
        image_filename = f"so-do-chan-{image_prefix}-{focus_keyword}"
        
        print(f"\nĐang tìm kiếm hình ảnh của sản phẩm {focus_keyword.upper()}...")
        avatar_items = find_media_by_filename(avatar_filename)
        image_items = find_media_by_filename(image_filename)
        
        total_items = len(avatar_items) + len(image_items)
        if total_items > 0:
            print(f"\nTìm thấy {total_items} hình ảnh liên quan đến sản phẩm {focus_keyword.upper()}:")
            
            if avatar_items:
                print("\nHình đại diện:")
                for i, item in enumerate(avatar_items, 1):
                    print(f"{i}. ID: {item['id']}, URL: {item['url']}, Filename: {item['filename']}")
            
            if image_items:
                print("\nHình sản phẩm:")
                for i, item in enumerate(image_items, 1):
                    print(f"{i}. ID: {item['id']}, URL: {item['url']}, Filename: {item['filename']}")
            
            confirm = input("\nBạn có chắc chắn muốn xóa tất cả hình ảnh này không? (yes/no): ").strip().lower()
            if confirm == 'yes':
                deleted_avatar = delete_media_by_filename(avatar_filename) if avatar_items else False
                deleted_image = delete_media_by_filename(image_filename) if image_items else False
                
                if deleted_avatar or deleted_image:
                    print("Đã xóa thành công các hình ảnh của sản phẩm.")
                else:
                    print("Không có hình ảnh nào được xóa.")
            else:
                print("Đã hủy thao tác xóa.")
        else:
            print(f"Không tìm thấy hình ảnh nào liên quan đến sản phẩm {focus_keyword.upper()}.")
    
    elif choice == "4":
        return
    
    else:
        print("Lựa chọn không hợp lệ!")
    
    # Hỏi người dùng có muốn tiếp tục quản lý thư viện media không
    continue_choice = input("\nBạn có muốn tiếp tục quản lý thư viện media không? (yes/no): ").strip().lower()
    if continue_choice == 'yes':
        manage_media_library()

def update_configuration():
    """
    Hàm cho phép người dùng thay đổi cấu hình (categories, tags, image_prefix) và lưu vào config.json
    """
    print("\n===== CẬP NHẬT CẤU HÌNH =====")
    
    # Load cấu hình hiện tại
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
            current_config = json.load(config_file)
    except Exception as e:
        print(f"Lỗi khi đọc file config.json: {str(e)}")
        return
    
    # Hiển thị thông tin cấu hình hiện tại
    print("\nCấu hình hiện tại:")
    
    # Hiển thị thông tin categories
    print("\nCATEGORIES:")
    try:
        all_categories = get_all_categories()
        for cat in current_config.get('categories', []):
            cat_id = cat["id"]
            category_name = get_category_name(cat_id, all_categories)
            print(f"- ID: {cat_id} - Tên: {category_name}")
    except Exception as e:
        print(f"Lỗi khi lấy thông tin categories: {str(e)}")
    
    # Hiển thị thông tin tags
    print("\nTAGS:")
    try:
        all_tags = get_all_tags()
        for tag in current_config.get('tags', []):
            tag_id = tag["id"]
            tag_name = get_tag_name(tag_id, all_tags)
            print(f"- ID: {tag_id} - Tên: {tag_name}")
    except Exception as e:
        print(f"Lỗi khi lấy thông tin tags: {str(e)}")
    
    # Hiển thị các thông tin khác
    print(f"\nIMAGE PREFIX: {current_config.get('image_prefix', '')}")
    print(f"DEFAULT SECONDARY KEYWORDS: {current_config.get('default_secondary_keywords', [])}")
    
    # Hỏi người dùng xem muốn thay đổi thông tin nào
    print("\nBạn muốn thay đổi thông tin nào?")
    print("1. Categories")
    print("2. Tags")
    print("3. Image Prefix")
    print("4. Default Secondary Keywords")
    print("5. Quay lại")
    
    choice = input("Nhập lựa chọn của bạn (1-5): ").strip()
    
    if choice == "1":
        # Cập nhật categories
        print("\n===== CẬP NHẬT CATEGORIES =====")
        print("Lưu ý: Cần nhập danh sách ID các categories, cách nhau bằng dấu phẩy")
        print("Ví dụ: 677,678,134")
        new_categories_str = input("Nhập danh sách ID categories mới: ").strip()
        try:
            new_category_ids = [int(cat_id.strip()) for cat_id in new_categories_str.split(",") if cat_id.strip()]
            new_categories = [{"id": cat_id} for cat_id in new_category_ids]
            current_config['categories'] = new_categories
            print(f"Đã cập nhật categories thành: {new_categories}")
        except Exception as e:
            print(f"Lỗi khi cập nhật categories: {str(e)}")
    
    elif choice == "2":
        # Cập nhật tags
        print("\n===== CẬP NHẬT TAGS =====")
        print("Lưu ý: Cần nhập danh sách ID các tags, cách nhau bằng dấu phẩy")
        print("Ví dụ: 725,726,688")
        new_tags_str = input("Nhập danh sách ID tags mới: ").strip()
        try:
            new_tag_ids = [int(tag_id.strip()) for tag_id in new_tags_str.split(",") if tag_id.strip()]
            new_tags = [{"id": tag_id} for tag_id in new_tag_ids]
            current_config['tags'] = new_tags
            print(f"Đã cập nhật tags thành: {new_tags}")
        except Exception as e:
            print(f"Lỗi khi cập nhật tags: {str(e)}")
    
    elif choice == "3":
        # Cập nhật image_prefix
        print("\n===== CẬP NHẬT IMAGE PREFIX =====")
        print("Ví dụ: safety-plc")
        new_image_prefix = input("Nhập image prefix mới: ").strip()
        if new_image_prefix:
            current_config['image_prefix'] = new_image_prefix
            print(f"Đã cập nhật image_prefix thành: {new_image_prefix}")
        else:
            print("Image prefix không được để trống!")
    
    elif choice == "4":
        # Cập nhật default_secondary_keywords
        print("\n===== CẬP NHẬT DEFAULT SECONDARY KEYWORDS =====")
        print("Lưu ý: Cần nhập danh sách từ khóa, cách nhau bằng dấu phẩy")
        print("Ví dụ: B&R Automation,x20 safety PLC")
        new_keywords_str = input("Nhập danh sách từ khóa mới: ").strip()
        new_keywords = [keyword.strip() for keyword in new_keywords_str.split(",") if keyword.strip()]
        current_config['default_secondary_keywords'] = new_keywords
        print(f"Đã cập nhật default_secondary_keywords thành: {new_keywords}")
    
    elif choice == "5":
        return
    
    else:
        print("Lựa chọn không hợp lệ!")
        return
    
    # Lưu cấu hình mới vào file
    try:
        with open('config.json', 'w', encoding='utf-8') as config_file:
            json.dump(current_config, config_file, indent=4, ensure_ascii=False)
        print("\nĐã lưu cấu hình mới vào file config.json")
    except Exception as e:
        print(f"Lỗi khi lưu file config.json: {str(e)}")
    
    # Hỏi người dùng có muốn tiếp tục cập nhật cấu hình không
    continue_choice = input("\nBạn có muốn tiếp tục cập nhật cấu hình không? (yes/no): ").strip().lower()
    if continue_choice == 'yes':
        update_configuration()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nChương trình đã bị dừng bởi người dùng.")
    except Exception as e:
        print(f"\nĐã xảy ra lỗi không xử lý được: {str(e)}")
    finally:
        print("\nChương trình kết thúc. Nếu gặp lỗi 'SKU đang được xử lý', hãy thử lại sau vài phút hoặc sử dụng tùy chọn --skip-exist")
        print("Ví dụ: python main.py --skip-exist [--file tên_file]")
        print("Hoặc kiểm tra trang quản trị WordPress xem sản phẩm đã được tạo thành công chưa.")
        print("\nCảm ơn bạn đã sử dụng công cụ này!")