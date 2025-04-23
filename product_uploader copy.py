# product_uploader.py
import requests
import json
import time

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

WP_URL = config['WP_URL']
CONSUMER_KEY = config['CONSUMER_KEY']
CONSUMER_SECRET = config['CONSUMER_SECRET']

def upload_product(product_name, short_description, description, focus_keyword, rank_math_description, avatar_info, combined_keywords, categories, tags):
    # Chuẩn bị dữ liệu sản phẩm với cấu trúc tương thích với phiên bản WP/WooCommerce mới
    product_data = {
        "name": product_name,
        "type": "simple",
        "description": description,
        "short_description": short_description,
        "categories": categories,  # Danh sách categories (từ config.json)
        "tags": tags,              # Danh sách tags (từ config.json)
        "status": "publish",
        "sku": focus_keyword,  # Dùng focus keyword làm SKU
        "meta_data": [
            {
                "key": "rank_math_title",
                "value": f"{product_name} Hãng B&R"
            },
            {
                "key": "rank_math_description",
                "value": rank_math_description
            },
            {
                "key": "rank_math_focus_keyword",
                "value": combined_keywords  # Kết hợp focus keyword và secondary keywords
            },
            # Thêm các trường meta khác của Rank Math để đảm bảo SEO hoạt động đúng
            {
                "key": "_rank_math_title",
                "value": f"{product_name} Hãng B&R"
            },
            {
                "key": "_rank_math_description",
                "value": rank_math_description
            },
            {
                "key": "_rank_math_focus_keyword",
                "value": combined_keywords
            },
            {
                "key": "rank_math_seo_score",
                "value": "75"
            },
            {
                "key": "_rank_math_seo_score",
                "value": "75"
            }
        ]
    }

    # Không thêm cả featured_media vì có thể không tương thích với WP mới
    # Chỉ sử dụng phương thức WooCommerce tiêu chuẩn để thiết lập hình đại diện
    if avatar_info:
        product_data["images"] = [
            {
                "id": avatar_info["id"],
                "src": avatar_info["url"],
                "position": 0  # Hình đại diện chính (featured image)
            }
        ]

    # In toàn bộ dữ liệu gửi lên để kiểm tra
    print("\nDữ liệu sản phẩm gửi lên (product_data):")
    print(json.dumps(product_data, indent=2, ensure_ascii=False))

    # Headers và params cho request
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "consumer_key": CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET
    }

    # Gửi request để tạo sản phẩm, thêm retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{WP_URL}/wc/v3/products",
                json=product_data,
                headers=headers,
                params=params,
                timeout=30  # Thêm timeout để tránh treo
            )

            # Kiểm tra kết quả
            if response.status_code == 201:
                print("Sản phẩm đã được đăng thành công!")
                print(f"Link sản phẩm: {response.json().get('permalink', 'Không có permalink')}")
                
                # Kiểm tra xem hình đại diện có được gắn thành công không
                if 'images' in response.json() and len(response.json()['images']) > 0:
                    print("Thông tin hình đại diện từ response:")
                    for img in response.json()['images']:
                        print(f"ID: {img.get('id')}, src: {img.get('src')}")
                else:
                    print("CẢNH BÁO: Không tìm thấy thông tin hình đại diện trong response!")
                    
                # Lưu thông tin sản phẩm mới tạo để có thể cập nhật sau này nếu cần
                product_id = response.json().get('id')
                if product_id:
                    print(f"ID sản phẩm: {product_id}")
                    
                    # Nếu không có hình đại diện, thử cập nhật lại sản phẩm sau một chút thời gian
                    if ('images' not in response.json() or len(response.json()['images']) == 0) and avatar_info:
                        print("\nThử cập nhật lại hình đại diện cho sản phẩm sau 2 giây...")
                        time.sleep(2)  # Đợi 2 giây để đảm bảo sản phẩm đã được tạo hoàn toàn
                        update_product_media(product_id, avatar_info)
                else:
                    print("Không thể lấy ID sản phẩm từ response")
                
                return True
            elif response.status_code == 400 and "being processed" in response.text:
                # Đợi một khoảng thời gian và thử lại
                print(f"SKU đang được xử lý. Đợi 5 giây và thử lại... (Lần thử {attempt+1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                print(f"Lỗi: {response.status_code}")
                print(response.text)
                
                # Kiểm tra nếu lỗi xảy ra là do SKU đã tồn tại
                if response.status_code == 400 and "already exists" in response.text:
                    print("Lỗi: SKU đã tồn tại. Thử thực hiện cập nhật thay vì tạo mới.")
                    check_and_update_or_create(focus_keyword, product_name, short_description, description, 
                                               rank_math_description, avatar_info, combined_keywords, categories, tags)
                    return True
                
                # Nếu đã thử lại đủ số lần, báo lỗi và thoát
                if attempt == max_retries - 1:
                    print(f"Đã thử lại {max_retries} lần. Không thể tải lên sản phẩm.")
                    return False
                    
                print(f"Đợi 3 giây và thử lại... (Lần thử {attempt+1}/{max_retries})")
                time.sleep(3)
                
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối: {str(e)}")
            if attempt == max_retries - 1:
                print(f"Đã thử lại {max_retries} lần. Không thể tải lên sản phẩm.")
                return False
                
            print(f"Đợi 3 giây và thử lại... (Lần thử {attempt+1}/{max_retries})")
            time.sleep(3)
        except Exception as e:
            print(f"Lỗi khác: {str(e)}")
            if attempt == max_retries - 1:
                print(f"Đã thử lại {max_retries} lần. Không thể tải lên sản phẩm.")
                return False
                
            print(f"Đợi 3 giây và thử lại... (Lần thử {attempt+1}/{max_retries})")
            time.sleep(3)
    
    return False

def check_and_update_or_create(focus_keyword, product_name, short_description, description, 
                                rank_math_description, avatar_info, combined_keywords, categories, tags):
    """
    Kiểm tra xem sản phẩm với SKU đã tồn tại chưa, nếu có thì cập nhật, nếu không thì tạo mới
    """
    # Tìm kiếm sản phẩm theo SKU
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "consumer_key": CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET,
        "sku": focus_keyword
    }
    
    try:
        response = requests.get(
            f"{WP_URL}/wc/v3/products",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            products = response.json()
            if products and len(products) > 0:
                # Sản phẩm đã tồn tại, cập nhật
                product_id = products[0]['id']
                print(f"Tìm thấy sản phẩm có SKU '{focus_keyword}' với ID: {product_id}")
                
                choice = input("Sản phẩm đã tồn tại. Bạn có muốn cập nhật không? (yes/no): ").strip().lower()
                if choice == 'yes':
                    update_existing_product(product_id, product_name, short_description, description, 
                                            rank_math_description, avatar_info, combined_keywords, categories, tags)
                else:
                    print("Bỏ qua việc cập nhật sản phẩm này.")
            else:
                # Không tìm thấy sản phẩm, có thể là lỗi khác
                print(f"Không tìm thấy sản phẩm với SKU '{focus_keyword}' nhưng API trả về lỗi khi tạo mới.")
                print("Vui lòng kiểm tra lại các thông tin cấu hình và API.")
        else:
            print(f"Lỗi khi kiểm tra sản phẩm tồn tại: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Lỗi khi kiểm tra sản phẩm tồn tại: {str(e)}")

def update_existing_product(product_id, product_name, short_description, description, 
                          rank_math_description, avatar_info, combined_keywords, categories, tags):
    """
    Cập nhật sản phẩm đã tồn tại thay vì tạo mới.
    """
    update_data = {
        "name": product_name,
        "description": description,
        "short_description": short_description,
        "categories": categories,
        "tags": tags,
        "meta_data": [
            {
                "key": "rank_math_title",
                "value": f"{product_name} Hãng B&R"
            },
            {
                "key": "rank_math_description",
                "value": rank_math_description
            },
            {
                "key": "rank_math_focus_keyword",
                "value": combined_keywords
            },
            {
                "key": "_rank_math_title",
                "value": f"{product_name} Hãng B&R"
            },
            {
                "key": "_rank_math_description",
                "value": rank_math_description
            },
            {
                "key": "_rank_math_focus_keyword",
                "value": combined_keywords
            },
            {
                "key": "rank_math_seo_score",
                "value": "75"
            },
            {
                "key": "_rank_math_seo_score",
                "value": "75"
            }
        ]
    }

    # Thêm hình đại diện vào update_data nếu có
    if avatar_info:
        update_data["images"] = [
            {
                "id": avatar_info["id"],
                "src": avatar_info["url"],
                "position": 0
            }
        ]

    # Headers và params cho request
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "consumer_key": CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET
    }

    # Gửi request để cập nhật sản phẩm
    try:
        response = requests.put(
            f"{WP_URL}/wc/v3/products/{product_id}",
            json=update_data,
            headers=headers,
            params=params,
            timeout=30
        )

        # Kiểm tra kết quả
        if response.status_code == 200:
            print("Sản phẩm đã được cập nhật thành công!")
            print(f"Link sản phẩm: {response.json().get('permalink', 'Không có permalink')}")
            
            # Kiểm tra hình đại diện
            if 'images' in response.json() and len(response.json()['images']) > 0:
                print("Thông tin hình đại diện từ response:")
                for img in response.json()['images']:
                    print(f"ID: {img.get('id')}, src: {img.get('src')}")
            else:
                print("CẢNH BÁO: Không tìm thấy thông tin hình đại diện trong response!")
        else:
            print(f"Lỗi khi cập nhật sản phẩm: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Lỗi khi gửi request cập nhật sản phẩm: {str(e)}")

def update_product_media(product_id, avatar_info):
    """
    Hàm cập nhật lại hình đại diện cho sản phẩm đã tạo.
    """
    if not avatar_info:
        print("Không có thông tin hình đại diện để cập nhật.")
        return
    
    update_data = {
        "images": [
            {
                "id": avatar_info["id"],
                "src": avatar_info["url"],
                "position": 0
            }
        ]
    }
    
    print(f"Dữ liệu cập nhật hình đại diện: {json.dumps(update_data, indent=2)}")
    
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "consumer_key": CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET
    }
    
    try:
        update_response = requests.put(
            f"{WP_URL}/wc/v3/products/{product_id}",
            json=update_data,
            headers=headers,
            params=params,
            timeout=30
        )
        
        if update_response.status_code == 200:
            print("Cập nhật hình đại diện thành công!")
            if 'images' in update_response.json():
                print("Thông tin hình đại diện sau khi cập nhật:")
                for img in update_response.json()['images']:
                    print(f"ID: {img.get('id')}, src: {img.get('src')}")
        else:
            print(f"Lỗi khi cập nhật hình đại diện: {update_response.status_code}")
            print(update_response.text)
    except Exception as e:
        print(f"Lỗi khi gửi request cập nhật: {str(e)}")