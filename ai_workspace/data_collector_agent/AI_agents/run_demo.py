# C:\Users\Lenovo\AI_LLM_Agent\run_demo.py

from agent.main_agent import agent_executor

# THAY ĐỔI: Thêm câu hỏi về VAMA vào yêu cầu
user_request = """
Tôi cần một báo cáo tổng hợp nhanh về thị trường Việt Nam.

1.  **(VAMA)** Từ báo cáo VAMA, hãy tìm tổng doanh số (Unit) của **"Total Thaco"** trong tháng gần nhất (ví dụ: Oct-25).
2.  **(RỦI RO)** Có tin tức nào về gián đoạn chuỗi cung ứng hoặc logistics do THIÊN TAI (bão, lũ) gây ra không?
3.  **(THỜI TIẾT)** Tình hình thời tiết có cảnh báo bão nào SẮP TỚI không?
"""

print("=============================================")
print(f"ĐANG GỬI YÊU CẦU CHO AGENT (BAO GỒM VAMA):\n{user_request}")
print("=============================================")

# Gọi agent để thực thi yêu cầu
response = agent_executor.invoke({
    "input": user_request
})

print("\n=============================================")
print("BÁO CÁO PHÂN TÍCH TỔNG HỢP (OUTPUT BẰNG TIẾNG VIỆT):")
print(response['output'])
print("=============================================")