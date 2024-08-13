script_data = product_detail_soup.find('script', text=lambda x: x and 'all_product' in x)
if script_data:
    print(script_data.string)
else:
    print("Lỗi: Không tìm thấy dữ liệu script chứa 'all_product'.")
