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
    "image_prefix": "your-image-prefix",
    "image_prefix_diagram": "block-diagram",
    "image_caption_prefix": "Block diagram",
    "image_description_prefix": "Block diagram of module",
    "categories": [
        {"id": 123},
        {"id": 456}
    ],
    "tags": [
        {"id": 789},
        {"id": 101}
    ],
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

2. Hình chi tiết: `{image_prefix_diagram}-{image_prefix}-{focus_keyword}.png` hoặc `.jpg`  
   Ví dụ: `block-diagram-safety-plc-x20sl8110.png`

## Cấu hình hình ảnh

1. `image_prefix`: Tiền tố cho tên file hình ảnh avata (ví dụ tên hình avata là "automation-pc-4100-5apc4100.sx00-000.jpg" thì `image_prefix` là "automation-pc-4100")
2. `image_prefix_diagram`: Tiền tố cho tên file hình sản phẩm ở trong bài (ví dụ tên file hình ảnh sản phẩm trong bài là "block-diagram-automation-pc-4100-5apc4100.sx00-000" thì `image_prefix_diagram` là "block-diagram")
3. `image_caption_prefix`: Tiền tố cho chú thích hình ảnh (ví dụ: "Block diagram")
4. `image_description_prefix`: Tiền tố cho mô tả hình ảnh (ví dụ: "Block diagram of module")

## Sử dụng

### Upload sản phẩm mới

```