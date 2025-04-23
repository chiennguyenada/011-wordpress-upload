# WordPress Product Uploader

Công cụ tự động upload và quản lý sản phẩm WooCommerce từ file văn bản và hình ảnh.

## Giới thiệu

WordPress Product Uploader là công cụ dòng lệnh Python giúp tự động hóa việc tạo và quản lý sản phẩm WooCommerce từ các file văn bản (.txt). Công cụ này hỗ trợ:

- Upload sản phẩm mới với mô tả, từ khóa SEO và hình ảnh
- Cập nhật sản phẩm đã tồn tại
- Quản lý thư viện media (tìm kiếm, xóa)
- Tùy chỉnh cấu hình danh mục, thẻ và tiền tố hình ảnh

## Yêu cầu

- Python 3.6+
- WordPress với WooCommerce và Rank Math SEO
- Quyền truy cập API WooCommerce

## Cài đặt

1. Clone hoặc tải repository này về máy
2. Cài đặt các thư viện cần thiết:

```
pip install requests
```

3. Tạo file `config.json` với cấu hình như sau:

```json
{
    "WP_URL": "https://your-wordpress-site.com",
    "CONSUMER_KEY": "your_consumer_key",
    "CONSUMER_SECRET": "your_consumer_secret",
    "categories": [
        {"id": 123},
        {"id": 456}
    ],
    "tags": [
        {"id": 789},
        {"id": 101}
    ],
    "image_prefix": "your-image-prefix",
    "default_secondary_keywords": ["keyword1", "keyword2"]
}
```

## Cấu trúc thư mục

```
project-root/
  ├── main.py
  ├── product_processor.py
  ├── product_uploader.py
  ├── media.py
  ├── get_categories.py
  ├── get_tags.py
  ├── config.json
  ├── bai-viet/
  │   └── (các file .txt)
  ├── hinh-avata/
  │   └── (hình đại diện)
  └── hinh-sp/
      └── (hình chi tiết sản phẩm)
```

## Định dạng file sản phẩm

Mỗi file .txt trong thư mục `bai-viet/` phải có định dạng:

```
Dòng 1: Tên sản phẩm
Dòng 2: Mô tả ngắn (phần 1)
Dòng 3: Mô tả ngắn (phần 2)
Dòng 4: Mã sản phẩm: [mã]

<H2>Tiêu đề 1</H2>
<p>Nội dung chi tiết...</p>

<H2>Tiêu đề 2</H2>
<p>Nội dung chi tiết...</p>
...
```

## Quy ước đặt tên file hình ảnh

1. Hình đại diện: `{image_prefix}-{focus_keyword}.png` hoặc `.jpg`  
   Ví dụ: `safety-plc-x20sl8110.png`

2. Hình chi tiết: `so-do-chan-{image_prefix}-{focus_keyword}.png` hoặc `.jpg`  
   Ví dụ: `so-do-chan-safety-plc-x20sl8110.png`

## Sử dụng

### Upload sản phẩm mới

```
python main.py
```

Hoặc chỉ định file cụ thể:

```
python main.py --file X20SL8110
```

### Bỏ qua sản phẩm đã tồn tại

```
python main.py --skip-exist
```

### Cập nhật sản phẩm đã tồn tại

```
python main.py --force-update
```

### Đặt độ trễ giữa các lần upload

```
python main.py --delay 5
```

## Các tính năng

1. **Đăng sản phẩm mới**
   - Tự động kiểm tra hình ảnh local
   - Tự động upload hình ảnh lên WordPress Media
   - Tạo sản phẩm với đầy đủ thông tin SEO (Rank Math)

2. **Cập nhật hình đại diện cho sản phẩm đã tồn tại**
   - Tìm sản phẩm theo SKU
   - Thay thế hình đại diện

3. **Quản lý thư viện media**
   - Tìm kiếm hình ảnh theo tên file
   - Xóa hình ảnh theo tên file
   - Xóa hình ảnh của một sản phẩm

4. **Cập nhật cấu hình**
   - Thay đổi danh mục, thẻ
   - Thay đổi tiền tố hình ảnh
   - Thêm từ khóa phụ mặc định

## Xử lý lỗi

- **SKU đang được xử lý**: Đợi vài phút và thử lại, hoặc sử dụng `--skip-exist`
- **Thiếu hình ảnh local**: Đảm bảo hình ảnh tồn tại trong thư mục tương ứng
- **Cache WordPress**: Nếu gặp vấn đề, hãy xóa cache của WordPress

## Đóng góp

Vui lòng gửi yêu cầu tính năng hoặc báo cáo lỗi qua phần Issues.

## Giấy phép

Phát hành dưới giấy phép MIT. 