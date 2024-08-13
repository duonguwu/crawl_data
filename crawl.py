import requests
from bs4 import BeautifulSoup
import json
import re

# URL của trang web cần crawl
url = "https://matviet.vn/collections/kinh-mat?page=2"  # Thay thế bằng URL chính xác

# Gửi yêu cầu GET để lấy nội dung trang web
response = requests.get(url)
response.raise_for_status()  # Kiểm tra xem yêu cầu có thành công không

# Phân tích nội dung HTML bằng BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Tìm tất cả sản phẩm trên trang
products = soup.find_all('div', class_='product-loop')

# Danh sách để chứa tất cả dữ liệu sản phẩm
product_data = []

# Hàm để trích xuất JSON từ nội dung script
def extract_json(script_content):
    try:
        match = re.search(r'all_product\[\d+\]\s*=\s*(\{.*\});', script_content, re.DOTALL)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            return data
        else:
            print("Không tìm thấy dữ liệu JSON trong script.")
            return None
    except json.JSONDecodeError as e:
        print(f"Lỗi khi phân tích JSON: {e}")
        return None

# Lặp qua từng sản phẩm và trích xuất thông tin liên quan
for product in products:
    # try:
        # Trích xuất tên sản phẩm
        name_element = product.find('a', class_='tracking_product')
        if not name_element:
            print("Lỗi: Không tìm thấy tên sản phẩm.")
            continue
        name = name_element.get('title')    
        print(name)
        
        # Trích xuất link sản phẩm
        product_link_element = product.find('a', class_='tracking_product')
        if not product_link_element:
            print("Lỗi: Không tìm thấy liên kết sản phẩm.")
            continue
        product_link = product_link_element['href']

        # Trích xuất link hình ảnh
        image_tag = product.find('img', class_='lazyload')
        if not image_tag:
            print("Lỗi: Không tìm thấy link hình ảnh.")
            continue
        image_url = image_tag['src'] if 'src' in image_tag.attrs else image_tag['data-src']
        if image_url.startswith('//'):
            image_url = 'https:' + image_url

        # Trích xuất giá và giá đã giảm
        price_element = product.find('span')
        if not price_element:
            print("Lỗi: Không tìm thấy giá sản phẩm.")
            continue
        price = price_element.text.strip().replace('₫', '').replace(',', '')
        
        discounted_price_element = product.find('del')
        discounted_price = discounted_price_element.text.strip().replace('₫', '').replace(',', '') if discounted_price_element else price
        
        # Trích xuất mô tả chi tiết từ thẻ script (dữ liệu dạng JSON-like)
        script_tag = product.find('script', text=lambda x: x and 'all_product' in x)
        if not script_tag:
            print("Lỗi: Không tìm thấy dữ liệu script chứa 'all_product'.")
            continue
        
        script_content = script_tag.string
        product_json = extract_json(script_content)
        if not product_json:
            print("Lỗi: Không trích xuất được dữ liệu sản phẩm từ JSON.")
            continue
        # print(product_json)
        
        # Lấy giá trị option2 từ product_json
        option2_value = product_json.get('variants', [{}])[0].get('option2', 'Unknown')

        # Kiểm tra và xử lý chuỗi option2_value
        if option2_value != 'Unknown':
            try:
                # Tách chuỗi dựa trên dấu "-"
                dimensions = option2_value.split('-')
                
                # Gán các giá trị tương ứng
                lens_width = dimensions[0] if len(dimensions) > 0 else 'Unknown'
                bridge_width = dimensions[1] if len(dimensions) > 1 else 'Unknown'
                temple_length = dimensions[2] if len(dimensions) > 2 else 'Unknown'
            except Exception as e:
                print(f"Lỗi khi xử lý dimension string: {e}")
                lens_width = bridge_width = temple_length = 'Unknown'
        else:
            lens_width = bridge_width = temple_length = 'Unknown'

        # Tạo dictionary sản phẩm phù hợp với cấu trúc của bạn
        product_dict = {
            "_id": product_json.get('id', "Unknown"),
            "name": name,
            "description": product_json.get('description', 'Unknown'),
            "brand": product_json.get('vendor', 'Unknown'),
            "category": product_json.get('type', 'Unknown'),
            "gender": "Unknown",  # Cần suy ra hoặc thêm thủ công
            "weight": f"{product_json.get('variants', [{}])[0].get('weight', 'Unknown')}g",
            "quantity": product_json.get('variants', [{}])[0].get('inventory_quantity', 'Unknown'),
            "image": image_url,
            "rating": 0.0,  # Cần lấy nếu có sẵn
            "price": int(price),
            "newPrice": int(discounted_price),
            "trending": False,  # Cần suy ra hoặc thêm thủ công
            "frameMaterial": next((tag.split(': ')[1] for tag in product_json.get('tags', []) if 'filter_material' in tag), 'Unknown'),
            "lensMaterial": next((tag.split(': ')[1] for tag in product_json.get('tags', []) if 'filter_lens_material' in tag), 'Unknown'),
            "lensFeatures": "Unknown", #[tag.split(': ')[1] for tag in product_json.get('tags', []) if 'Polarized' in tag],
            "frameShape": next((tag.split(': ')[1] for tag in product_json.get('tags', []) if 'filter_shape' in tag), 'Unknown'),
            "frameSize": {
                "lensWidth": lens_width,
                "bridgeWidth": bridge_width,
                "templeLength": temple_length
            },
            "color": next((tag.split(': ')[1] for tag in product_json.get('tags', []) if 'filter_gong' in tag), 'Unknown'),
            "availability": "In Stock" if product_json.get('available', False) else "Out of Stock"
        }
        
        print("product_dict: ", product_dict)
        # Thêm sản phẩm vào danh sách
        product_data.append(product_dict)
    
    # except Exception as e:
    #     print(f"Lỗi khi trích xuất dữ liệu sản phẩm: {e}")
    #     continue
print(product_data)
# Lưu dữ liệu đã trích xuất vào file JSON
with open('product_data.json', 'w', encoding='utf-8') as f:
    json.dump(product_data, f, ensure_ascii=False, indent=4)

print("Hoàn thành trích xuất dữ liệu. Dữ liệu đã được lưu vào product_data.json")
