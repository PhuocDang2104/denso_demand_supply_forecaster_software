
# Data Dictionary: Sparkplug Demand Dataset (Final)
Bộ dữ liệu tổng hợp (synthetic) mô phỏng nhu cầu bugi hàng tuần (W-MON) tại Việt Nam, phân tách theo kênh OEM và Aftermarket.

**Tần suất:** Hàng tuần (W-MON)
**Phạm vi:** 2022-01-03 đến 2025-10-20
**File:** 10_sparkplug_dataset_final.csv

---

## 1. Biến Mục tiêu (Targets)
| Cột | Kiểu | Mô tả |
|---|---|---|
| y | int | **Mục tiêu chính.** Tổng doanh số bugi quan sát (đã bị ảnh hưởng stockout). `y = y_oem + y_aftermarket` |
| y_oem | int | Doanh số kênh OEM (B2B, bán cho nhà sản xuất xe). |
| y_aftermarket | int | Doanh số kênh Aftermarket (B2C, bán lẻ, đã bị ảnh hưởng stockout). |
| y_true | int | (Tham chiếu) Tổng cầu thực tế (nếu không bị stockout). `y_true = y_oem + y_aftermarket_true` |
| stockout_flag | int | Cờ (0/1). 1 = Tuần này kênh Aftermarket bị thiếu hàng. |

## 2. Cột Thời gian (Time)
| Cột | Kiểu | Mô tả |
|---|---|---|
| ds | date | Ngày đầu tuần (luôn là Thứ Hai, W-MON). **Đây là cột thời gian chính.** |
| year | int | Năm (từ ds). |
| week | int | Số thứ tự tuần trong năm (ISO week). |
| month | int | Tháng (từ ds). |
| quarter | int | Quý (từ ds). |

## 3. Drivers: Yếu tố Bên ngoài (External - Từ PART 2)
Đây là các yếu tố thị trường mà DENSO không kiểm soát được.

| Cột | Kiểu | Mô tả |
|---|---|---|
| gdp_growth | float | Tốc độ tăng trưởng GDP (%, so với cùng kỳ năm trước). |
| cpi | float | Lạm phát (Chỉ số Giá Tiêu dùng, %, so với cùng kỳ năm trước). |
| gas_price | float | Giá xăng trung bình hàng tuần (VND/lít). |
| total_new_vehicle_sales| int | (Nội suy tuần) Tổng dung lượng thị trường xe mới (ICE, Hybrid, BEV). |
| bev_penetration_rate | float | (Nội suy tuần) Tỷ lệ thâm nhập thị trường của xe điện thuần (BEV). |
| new_ice_and_hybrid_sales| int | (Tính toán) Doanh số xe Có dùng bugi (ICE + Hybrid). **Driver chính cho OEM.** |
| total_ice_and_hybrid_on_road| int | (Tính toán) Tổng số xe Có dùng bugi đang lưu hành. **Driver nền cho Aftermarket.** |
| weather_impact_score | int | (MỚI) Thang điểm 0-5. 0=Bình thường, 5=Bão lũ nghiêm trọng. |
| logistics_risk_score | int | (MỚI) Thang điểm 0-10. 0=An toàn, 10=Cú sốc Cung ứng (vd: cấm vận). |

## 4. Drivers: Yếu tố Nội bộ (Internal - Từ PART 3)
Đây là các yếu tố DENSO kiểm soát được.

| Cột | Kiểu | Mô tả |
|---|---|---|
| own_price_oem | int | Giá bán hợp đồng trung bình cho kênh OEM (VND/chiếc). Rất ổn định. |
| own_price_aftermarket | int | Giá bán lẻ trung bình của DENSO (VND/chiếc). |
| comp_price_aftermarket | int | Giá bán lẻ trung bình của Đối thủ (VND/chiếc). |
| promo_flag | int | Cờ (0/1). 1 = Tuần DENSO có chạy khuyến mãi Aftermarket. |
| promo_depth | float | Độ sâu khuyến mãi (ví dụ: 0.1 = giảm 10%). 0 nếu promo_flag=0. |
| holiday_flag | int | Cờ (0/1). 1 = Tuần thuộc "Mùa Tết" (tuần 4-8) hoặc tuần lễ (1/1, 30/4, 2/9). |
