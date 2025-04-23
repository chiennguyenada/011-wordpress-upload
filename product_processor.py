# product_processor.py
import re
import os
import json
from media import upload_image_to_media, delete_media_by_filename, find_media_by_filename

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

IMAGE_PREFIX = config['image_prefix']
DEFAULT_SECONDARY_KEYWORDS = config.get('default_secondary_keywords', [])

def process_product_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Loại bỏ khoảng trắng thừa và dòng trống
    lines = [line.strip() for line in lines if line.strip()]

    # 1. Lấy 4 dòng đầu tiên làm short_description
    short_description_lines = lines[:4]
    short_description = short_description_lines[0]  # Dòng đầu tiên là đoạn văn
    # Định dạng các dòng tiếp theo thành danh sách gạch đầu dòng
    short_description += "<ul>\n"
    for line in short_description_lines[1:]:
        # Xử lý các mục như "Mã sản phẩm:", "Thương hiệu:", "Xuất xứ:"
        if ":" in line:
            # Xóa dấu "•" hoàn toàn và chỉ giữ nội dung thực
            content = line.replace("•", "").strip()
            
            # Tách key và value
            key, value = content.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Thêm vào short_description với định dạng không có dấu "•"
            short_description += f"<li>{key}: {value}</li>\n"
        else:
            # Đối với các dòng khác, vẫn loại bỏ dấu "•" nếu có
            cleaned_line = line.replace("•", "").strip()
            short_description += f"<li>{cleaned_line}</li>\n"
    short_description += "</ul>"

    # 2. Lấy dòng thứ 5 làm description cho Edit Snippet
    if len(lines) < 5:
        raise ValueError("File không đủ 5 dòng để lấy description cho Edit Snippet.")
    rank_math_description = lines[4].strip()  # Dòng thứ 5

    # 3. Lấy dòng thứ 6 (nếu có) làm từ khóa phụ
    secondary_keywords = DEFAULT_SECONDARY_KEYWORDS  # Mặc định từ config.json
    if len(lines) >= 6 and lines[5].startswith("Từ khóa phụ:"):
        secondary_keywords_line = lines[5].strip()
        secondary_keywords = [keyword.strip() for keyword in secondary_keywords_line.replace("Từ khóa phụ:", "").split(",") if keyword.strip()]
        print(f"Từ khóa phụ từ file .txt: {secondary_keywords}")
    else:
        print(f"Không tìm thấy dòng 'Từ khóa phụ' trong file .txt, sử dụng từ khóa phụ mặc định: {secondary_keywords}")

    # 4. Tìm tiêu đề sản phẩm (dòng có thẻ <H1>)
    product_name = None
    h1_index = None
    for i, line in enumerate(lines):
        if line.startswith("<H1>"):
            product_name = re.search(r'<H1>(.*?)</H1>', line).group(1)
            h1_index = i
            break
    
    if not product_name:
        raise ValueError("Không tìm thấy thẻ <H1> trong file.")

    # 5. Lấy nội dung bài viết (từ sau thẻ <H1> đến hết file)
    description_lines = lines[h1_index + 1:]
    # Xử lý description để giữ định dạng và chuyển danh sách gạch đầu dòng thành HTML
    description = ""
    in_list = False  # Biến để kiểm tra xem đang trong danh sách <ul> hay không
    last_line_was_heading = False  # Biến để kiểm tra dòng trước có phải là heading không
    for line in description_lines:
        if line.startswith("•"):
            if not in_list:
                description += "<ul>\n"
                in_list = True
            description += f"<li>{line.lstrip('• ').strip()}</li>\n"
            last_line_was_heading = False
        else:
            if in_list:
                description += "</ul>\n"
                in_list = False
            # Nếu dòng là heading, không thêm ký tự xuống dòng sau nó
            if line.startswith("<H"):
                description += line  # Giữ nguyên các thẻ heading
                last_line_was_heading = True
            else:
                # Nếu dòng trước là heading, không thêm xuống dòng trước đoạn văn
                if last_line_was_heading:
                    description += f"<p>{line}</p>\n"
                else:
                    description += f"\n<p>{line}</p>\n"
                last_line_was_heading = False
    # Đóng thẻ <ul> nếu vẫn đang trong danh sách
    if in_list:
        description += "</ul>\n"

    # 6. Tìm focus keyword (tên sản phẩm, ví dụ: x20ai2222)
    focus_keyword = None
    for line in short_description_lines:
        # Tìm linh hoạt hơn: không cần dấu "•", chỉ cần có "Mã sản phẩm"
        if "Mã sản phẩm" in line:
            focus_keyword = line.split("Mã sản phẩm:")[-1].strip().lower()
            break
    
    # Nếu không tìm thấy focus keyword, dùng mã sản phẩm từ tiêu đề (lấy phần cuối của tiêu đề)
    if not focus_keyword:
        focus_keyword = product_name.split()[-1].strip().lower()
        print(f"Không tìm thấy mã sản phẩm trong short_description, dùng mặc định từ tiêu đề: {focus_keyword}")

    # Kết hợp focus keyword và secondary keywords
    all_keywords = [focus_keyword] + secondary_keywords
    combined_keywords = ", ".join(all_keywords)  # Kết hợp thành chuỗi, phân tách bằng dấu phẩy

    # Xử lý IMAGE_PREFIX để bỏ dấu "-" và thay bằng khoảng trắng
    image_prefix_cleaned = IMAGE_PREFIX.replace("-", " ")

    # 7. Xử lý hình bài viết
    # Tạo tên file hình bài viết với tiền tố "so-do-chan-"
    image_filename_png = f"so-do-chan-{IMAGE_PREFIX}-{focus_keyword}.png"
    image_filename_jpg = f"so-do-chan-{IMAGE_PREFIX}-{focus_keyword}.jpg"
    image_path_png = os.path.join("hinh-sp", image_filename_png)
    image_path_jpg = os.path.join("hinh-sp", image_filename_jpg)
    
    # Kiểm tra xem file hình bài viết có tồn tại không (cả PNG và JPG)
    image_path = None
    image_filename = None
    if os.path.exists(image_path_png):
        image_path = image_path_png
        image_filename = image_filename_png
    elif os.path.exists(image_path_jpg):
        image_path = image_path_jpg
        image_filename = image_filename_jpg
    
    # Kiểm tra và xử lý hình ảnh
    image_info = None
    if image_path:
        # Kiểm tra và xóa hình cũ (nếu có) trước khi tải lên hình mới
        existing_images = find_media_by_filename(image_filename)
        if existing_images:
            print(f"Đã tìm thấy {len(existing_images)} hình ảnh sản phẩm trùng lặp trong thư viện media.")
            confirm = input(f"Bạn có muốn xóa các hình ảnh cũ '{image_filename}' trước khi tải lên hình mới không? (yes/no): ").strip().lower()
            if confirm == 'yes':
                delete_media_by_filename(image_filename)
                print("Đang tiếp tục quá trình tải lên hình mới...")
            else:
                print("Bỏ qua việc xóa hình cũ, tiếp tục tải lên hình mới...")
        
        # Tạo metadata cho hình bài viết
        image_alt_text = product_name
        image_name = os.path.splitext(image_filename)[0]  # Bỏ phần đuôi .png/.jpg
        image_parts = image_name.split("-")
        relevant_parts = image_parts[3:]  # Bỏ phần "so-do-chan"
        prefix_parts = relevant_parts[:-1]  # Lấy tất cả phần trước focus_keyword
        focus_keyword_part = relevant_parts[-1]  # Phần cuối là focus_keyword
        focus_keyword_upper = focus_keyword_part.upper()
        image_name_cleaned = " ".join(prefix_parts) + " " + focus_keyword_upper
        image_caption = f"Sơ đồ chân {image_name_cleaned}"
        image_description = f"Sơ đồ chân của module {product_name} thuộc dòng {image_prefix_cleaned} của B&R Automation."

        # Upload hình bài viết lên WordPress và lấy thông tin
        image_info = upload_image_to_media(
            image_path,
            alt_text=image_alt_text,
            caption=image_caption,
            description=image_description
        )
        if image_info:
            # Sử dụng style trực tiếp và cấu trúc HTML tương thích với WordPress để canh giữa
            image_html = f'''
<div class="wp-block-image" style="text-align: center; display: block; margin-left: auto; margin-right: auto;">
    <figure class="aligncenter" style="margin-left: auto; margin-right: auto; text-align: center;">
        <img src="{image_info["url"]}" alt="{product_name}" class="wp-image-{image_info["id"]}" style="margin: 0 auto; display: block;"/>
        <figcaption class="wp-element-caption" style="text-align: center;">{image_caption}</figcaption>
    </figure>
</div>
'''
            description = description.replace("[INSERT_IMAGE_HERE]", image_html)
        else:
            print("Không thể upload hình bài viết, giữ nguyên [INSERT_IMAGE_HERE].")
    else:
        print(f"Không tìm thấy file hình bài viết PNG ({image_path_png}) hoặc JPG ({image_path_jpg}). Bỏ qua chèn hình.")

    # 8. Xử lý hình đại diện
    # Tạo tên file hình đại diện
    avatar_filename_png = f"{IMAGE_PREFIX}-{focus_keyword}.png"
    avatar_filename_jpg = f"{IMAGE_PREFIX}-{focus_keyword}.jpg"
    avatar_path_png = os.path.join("hinh-avata", avatar_filename_png)
    avatar_path_jpg = os.path.join("hinh-avata", avatar_filename_jpg)
    
    # Kiểm tra xem file hình đại diện có tồn tại không (cả PNG và JPG)
    avatar_path = None
    avatar_filename = None
    if os.path.exists(avatar_path_png):
        avatar_path = avatar_path_png
        avatar_filename = avatar_filename_png
    elif os.path.exists(avatar_path_jpg):
        avatar_path = avatar_path_jpg
        avatar_filename = avatar_filename_jpg
    
    # Kiểm tra và xử lý hình đại diện
    avatar_info = None
    if avatar_path:
        # Kiểm tra và xóa hình đại diện cũ (nếu có) trước khi tải lên hình mới
        existing_avatars = find_media_by_filename(avatar_filename)
        if existing_avatars:
            print(f"Đã tìm thấy {len(existing_avatars)} hình đại diện trùng lặp trong thư viện media.")
            if 'confirm' not in locals() or confirm != 'yes':  # Nếu chưa hỏi người dùng trước đó
                confirm = input(f"Bạn có muốn xóa các hình đại diện cũ '{avatar_filename}' trước khi tải lên hình mới không? (yes/no): ").strip().lower()
            if confirm == 'yes':
                delete_media_by_filename(avatar_filename)
                print("Đang tiếp tục quá trình tải lên hình đại diện mới...")
            else:
                print("Bỏ qua việc xóa hình đại diện cũ, tiếp tục tải lên hình mới...")
                
        # Tạo metadata cho hình đại diện
        avatar_alt_text = product_name
        avatar_caption = f"Hình đại diện module {focus_keyword.upper()}"
        avatar_description = f"Hình đại diện của module {product_name} thuộc dòng {image_prefix_cleaned} của B&R Automation."

        # Upload hình đại diện lên WordPress và lấy thông tin
        avatar_info = upload_image_to_media(
            avatar_path,
            alt_text=avatar_alt_text,
            caption=avatar_caption,
            description=avatar_description
        )
        if not avatar_info:
            print("Không thể upload hình đại diện.")
    else:
        print(f"Không tìm thấy file hình đại diện PNG ({avatar_path_png}) hoặc JPG ({avatar_path_jpg}). Bỏ qua hình đại diện.")

    return product_name, short_description, description, focus_keyword, rank_math_description, avatar_info, combined_keywords