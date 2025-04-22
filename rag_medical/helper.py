def format_results(results):
    """
    Định dạng kết quả từ hybrid_search:
    - Chỉ lấy các kết quả có độ tương đồng (distance) > 0.7
    - In ra theo định dạng đẹp bằng tiếng Việt
    """
    formatted = []

    for idx, result in enumerate(results[0], 1):
        distance = result.get('distance', 0)
        if distance > 0.7:
            text = result.get('entity', {}).get('text', 'Không có trường text')
            formatted.append(f"Nội dung {idx}:\n{text}")

    if not formatted:
        return "Không tìm thấy dữ liệu liên quan trong cơ sở dữ liệu nội bộ."

    return "\n".join(formatted)

