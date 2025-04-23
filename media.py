# media.py
import requests
import json
import base64
import os
import time

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

WP_URL = config['WP_URL']
WP_USERNAME = config['wp_username']
WP_PASSWORD = config['wp_password']
AUTH_METHOD = config['auth_method']

# Tạo header cho Basic Authentication hoặc Application Password
WP_CREDENTIALS = f"{WP_USERNAME}:{WP_PASSWORD}"
WP_TOKEN = base64.b64encode(WP_CREDENTIALS.encode())
WP_HEADER = {'Authorization': 'Basic ' + WP_TOKEN.decode('utf-8')}

def upload_image_to_media(image_path, alt_text=None, caption=None, description=None):
    """
    Upload hình ảnh lên WordPress Media với retry logic
    
    Args:
        image_path (str): Đường dẫn đến file hình ảnh cần upload
        alt_text (str, optional): Văn bản thay thế cho hình ảnh
        caption (str, optional): Chú thích cho hình ảnh
        description (str, optional): Mô tả chi tiết cho hình ảnh
        
    Returns:
        dict or None: Thông tin hình ảnh đã upload (id, url) hoặc None nếu có lỗi
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Đọc file hình ảnh dưới dạng nhị phân
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()

            # Xác định MIME type dựa trên phần mở rộng của file
            file_extension = os.path.splitext(image_path)[1].lower()
            content_type = "image/png"  # Mặc định là PNG
            if file_extension == '.jpg' or file_extension == '.jpeg':
                content_type = "image/jpeg"
            elif file_extension == '.gif':
                content_type = "image/gif"
            elif file_extension == '.webp':
                content_type = "image/webp"

            # Headers cho request upload media
            headers = {
                "Content-Disposition": f"attachment; filename={os.path.basename(image_path)}",
                "Content-Type": content_type,
                **WP_HEADER
            }

            # Dữ liệu bổ sung (metadata) cho hình ảnh
            params = {}
            if alt_text:
                params["alt_text"] = alt_text
            if caption:
                params["caption"] = caption
            if description:
                params["description"] = description

            # Gửi request để upload hình
            print(f"Đang upload hình ({attempt+1}/{max_retries}): {image_path}")
            print(f"Sử dụng phương pháp xác thực: {AUTH_METHOD}")
            
            # Gửi request với retry logic
            response = requests.post(
                f"{WP_URL}/wp/v2/media",
                headers=headers,
                data=image_data,
                params=params,
                timeout=60  # Tăng timeout để xử lý file lớn
            )

            if response.status_code == 201:
                # Lấy URL và ID của hình từ response
                response_data = response.json()
                image_url = response_data.get('source_url')
                image_id = response_data.get('id')
                
                if image_url and image_id:
                    print(f"Hình đã được upload thành công: {image_url} (ID: {image_id})")
                    # Đợi một chút để đảm bảo WordPress đã xử lý xong hình ảnh
                    time.sleep(1)
                    return {"url": image_url, "id": image_id}
                else:
                    print("Lỗi: Response không chứa URL hoặc ID của hình ảnh")
                    print(f"Response data: {response_data}")
            else:
                error_message = f"Lỗi khi upload hình: {response.status_code}"
                try:
                    error_details = response.json()
                    error_message += f" - {error_details.get('message', '')}"
                except:
                    error_message += f" - {response.text}"
                
                print(error_message)
                
                # Xử lý các lỗi cụ thể có thể xảy ra
                if response.status_code == 401:
                    print("Lỗi xác thực. Vui lòng kiểm tra thông tin đăng nhập.")
                    break  # Không cần retry với lỗi xác thực
                elif response.status_code == 413:
                    print("File quá lớn. Vui lòng giảm kích thước file.")
                    break  # Không cần retry với file quá lớn
                
                # Đợi và thử lại
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)  # Tăng thời gian đợi với mỗi lần thử
                    print(f"Đợi {wait_time} giây và thử lại...")
                    time.sleep(wait_time)
                
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối khi upload hình: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 3 * (attempt + 1)
                print(f"Đợi {wait_time} giây và thử lại...")
                time.sleep(wait_time)
            
        except Exception as e:
            print(f"Lỗi không xác định khi upload hình: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 3 * (attempt + 1)
                print(f"Đợi {wait_time} giây và thử lại...")
                time.sleep(wait_time)
    
    print(f"Đã thử {max_retries} lần nhưng không thể upload hình ảnh.")
    return None

def check_image_exists(filename):
    """
    Kiểm tra xem một hình ảnh đã tồn tại trong thư viện media của WordPress hay chưa.
    Xử lý trường hợp WordPress chuyển đổi PNG thành JPG.
    
    Args:
        filename (str): Tên file hình ảnh cần kiểm tra
        
    Returns:
        dict or None: Trả về thông tin của hình ảnh nếu đã tồn tại (bao gồm id, url), 
                     None nếu không tồn tại
    """
    try:
        # Xử lý tên file để tạo search term
        base_name, extension = os.path.splitext(filename)
        search_term = base_name  # Bỏ phần đuôi file (.png, .jpg, etc.)
        
        # Tạo danh sách các tên file có thể đã được chuyển đổi định dạng
        possible_filenames = [
            filename,  # Tên file gốc
            f"{base_name}.jpg",  # Có thể đã chuyển đổi từ PNG sang JPG
            f"{base_name}.jpeg",  # Có thể là định dạng JPEG
            f"{base_name}.png"   # Có thể đã chuyển từ JPG sang PNG
        ]
        
        # Tạo params cho request search media
        params = {
            "search": search_term,
            "per_page": 20,  # Giới hạn số lượng kết quả trả về
            "_fields": "id,source_url,slug,title,media_details"  # Chỉ lấy các trường cần thiết
        }
        
        # Gửi request để tìm kiếm trong thư viện media
        print(f"Đang kiểm tra hình ảnh: {filename} (và các định dạng tương tự)")
        response = requests.get(
            f"{WP_URL}/wp/v2/media",
            headers=WP_HEADER,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            media_items = response.json()
            
            # Kiểm tra xem có item nào có filename trùng khớp không
            for item in media_items:
                source_url = item.get('source_url', '')
                item_filename = os.path.basename(source_url)
                item_base_name = os.path.splitext(item_filename)[0]
                
                # So sánh tên cơ bản (không có phần mở rộng)
                if item_base_name == base_name or item_filename in possible_filenames:
                    print(f"Đã tìm thấy hình ảnh trong thư viện media: {source_url} (ID: {item['id']})")
                    print(f"Lưu ý: WordPress có thể đã chuyển đổi từ {extension} sang {os.path.splitext(item_filename)[1]}")
                    return {
                        "id": item['id'],
                        "url": source_url,
                        "filename": item_filename
                    }
                
                # Kiểm tra cả trường hợp WordPress thêm hậu tố như -1, -2
                if item_base_name.startswith(f"{base_name}-"):
                    print(f"Đã tìm thấy hình ảnh tương tự với hậu tố trong thư viện media: {source_url} (ID: {item['id']})")
                    return {
                        "id": item['id'],
                        "url": source_url,
                        "filename": item_filename
                    }
            
            print(f"Không tìm thấy hình ảnh '{filename}' trong thư viện media.")
            return None
        else:
            print(f"Lỗi khi kiểm tra hình ảnh: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Lỗi khi kiểm tra hình ảnh: {str(e)}")
        return None

def delete_media_by_filename(filename):
    """
    Xóa hình ảnh từ thư viện media của WordPress dựa vào tên file.
    
    Args:
        filename (str): Tên file hình ảnh cần xóa (ví dụ: so-do-chan-analog-input-modules-x20ai2222.png)
        
    Returns:
        bool: True nếu xóa thành công ít nhất một file, False nếu không có file nào được xóa
    """
    try:
        # Tìm kiếm hình ảnh trong thư viện media
        media_items = find_media_by_filename(filename)
        
        if not media_items:
            print(f"Không tìm thấy hình ảnh '{filename}' trong thư viện media để xóa.")
            return False
        
        deleted_count = 0
        # Xóa từng hình ảnh tìm thấy
        for item in media_items:
            media_id = item.get('id')
            if not media_id:
                continue
                
            # Gửi request để xóa hình ảnh với retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.delete(
                        f"{WP_URL}/wp/v2/media/{media_id}",
                        headers=WP_HEADER,
                        params={"force": True},  # Xóa vĩnh viễn
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        print(f"Đã xóa hình ảnh ID: {media_id}, URL: {item.get('url')}")
                        deleted_count += 1
                        break  # Thoát khỏi vòng lặp retry nếu thành công
                    else:
                        print(f"Lỗi khi xóa hình ảnh ID {media_id}: {response.status_code}")
                        # Nếu hình ảnh đang được sử dụng bởi bài viết
                        if response.status_code == 400 and "Cannot delete" in response.text:
                            print("Hình ảnh đang được sử dụng bởi bài viết/sản phẩm. Không thể xóa.")
                            break
                        
                        # Nếu còn lần thử, đợi và thử lại
                        if attempt < max_retries - 1:
                            wait_time = 2 * (attempt + 1)
                            print(f"Đợi {wait_time} giây và thử lại ({attempt+2}/{max_retries})...")
                            time.sleep(wait_time)
                
                except Exception as e:
                    print(f"Lỗi khi xóa hình ảnh ID {media_id}: {str(e)}")
                    # Nếu còn lần thử, đợi và thử lại
                    if attempt < max_retries - 1:
                        wait_time = 2 * (attempt + 1)
                        print(f"Đợi {wait_time} giây và thử lại ({attempt+2}/{max_retries})...")
                        time.sleep(wait_time)
        
        print(f"Đã xóa thành công {deleted_count}/{len(media_items)} hình ảnh.")
        return deleted_count > 0
    except Exception as e:
        print(f"Lỗi khi xóa hình ảnh: {str(e)}")
        return False

def find_media_by_filename(filename):
    """
    Tìm kiếm hình ảnh trong thư viện media của WordPress dựa vào tên file.
    Xử lý trường hợp WordPress chuyển đổi PNG thành JPG.
    
    Args:
        filename (str): Tên file hình ảnh cần tìm
        
    Returns:
        list: Danh sách các hình ảnh tìm thấy, mỗi phần tử là một dict với id và url
    """
    try:
        # Xử lý tên file để tạo search term
        base_name, extension = os.path.splitext(filename)
        search_term = base_name  # Bỏ phần đuôi file (.png, .jpg, etc.)
        
        # Tạo params cho request search media
        params = {
            "search": search_term,
            "per_page": 20,  # Giới hạn số lượng kết quả trả về
            "_fields": "id,source_url,slug,title,media_details"  # Chỉ lấy các trường cần thiết
        }
        
        # Gửi request để tìm kiếm trong thư viện media
        print(f"Đang tìm kiếm hình ảnh: {filename} (và các định dạng tương tự)")
        
        # Thêm retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{WP_URL}/wp/v2/media",
                    headers=WP_HEADER,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    media_items = response.json()
                    result = []
                    
                    # Lọc các item có tên file phù hợp
                    for item in media_items:
                        source_url = item.get('source_url', '')
                        item_filename = os.path.basename(source_url)
                        item_base_name, item_ext = os.path.splitext(item_filename)
                        
                        # So sánh tên cơ bản (không có phần mở rộng)
                        if item_base_name == base_name or item_base_name.startswith(f"{base_name}-"):
                            print(f"Đã tìm thấy hình ảnh: {source_url} (ID: {item['id']})")
                            result.append({
                                "id": item['id'],
                                "url": source_url,
                                "filename": item_filename
                            })
                    
                    if not result:
                        print(f"Không tìm thấy hình ảnh '{filename}' trong thư viện media.")
                    else:
                        print(f"Tìm thấy {len(result)} hình ảnh phù hợp.")
                    
                    return result
                    
                else:
                    print(f"Lỗi khi tìm kiếm hình ảnh: {response.status_code} - {response.text}")
                    # Nếu còn lần thử, đợi và thử lại
                    if attempt < max_retries - 1:
                        wait_time = 2 * (attempt + 1)
                        print(f"Đợi {wait_time} giây và thử lại ({attempt+2}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        return []
                        
            except requests.exceptions.RequestException as e:
                print(f"Lỗi kết nối khi tìm kiếm hình ảnh: {str(e)}")
                # Nếu còn lần thử, đợi và thử lại
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"Đợi {wait_time} giây và thử lại ({attempt+2}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    return []
                    
            except Exception as e:
                print(f"Lỗi không xác định khi tìm kiếm hình ảnh: {str(e)}")
                # Nếu còn lần thử, đợi và thử lại
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"Đợi {wait_time} giây và thử lại ({attempt+2}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    return []
                    
        return []
    except Exception as e:
        print(f"Lỗi khi tìm kiếm hình ảnh: {str(e)}")
        return []