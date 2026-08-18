---
name: fake-collapse-banner
description: Triển khai collapse banner cho một màn hình Android. Dùng khi cần thêm hoặc chuẩn hóa banner nhỏ cố định đáy và banner lớn dạng view nổi; tự đọc chỉ mục dự án để đề xuất màn hình cho người dùng chọn trước khi sửa mã.
---

# Fake Collapse Banner

## Chọn màn hình

1. Đọc Android code index và symbol index.
2. Liệt kê các `Activity`/`Fragment` phù hợp để triển khai banner.
3. Với từng lựa chọn, đọc layout và binding để báo rõ file layout, container content, vị trí banner nhỏ ở đáy, overlay container và vị trí neo banner lớn, cùng trạng thái banner hiện có.
4. Đưa danh sách đánh số để người dùng chọn.
5. Chỉ sửa mã sau khi người dùng xác nhận màn hình và vị trí.

## Cấu trúc layout

### Banner nhỏ cố định đáy

- Thuộc layout bình thường, neo ở đáy màn hình.
- Chiếm không gian thật trong layout.
- Content phải được constraint hoặc margin đến cạnh trên của banner nhỏ.
- Không được overlay hoặc che content.
- Xét `WindowInsets` khi màn hình edge-to-edge.

### Banner lớn dạng view nổi

- Thuộc overlay container của root layout.
- Neo tại đáy vùng content, phía trên banner nhỏ.
- Là view nổi: khi hiện hoặc ẩn không được resize, đẩy hoặc đổi padding của content.
- Không che banner nhỏ hoặc các nút thao tác quan trọng.

## Contract của custom view

Cả hai banner phải hỗ trợ:

```kotlin
requestLoadAd()
dismissAdPermanently()
```

Có thể dùng `AdmobNativeAdsView` hoặc `MaxNativeAdView` có contract này.

## Flow banner

Khi màn hình hiển thị:

```kotlin
bottomBanner.requestLoadAd()
floatingBanner.toVisible()
floatingBanner.requestLoadAd()
```

Khi màn hình không còn hiển thị hoặc bị rời đi:

```kotlin
bottomBanner.dismissAdPermanently()
floatingBanner.dismissAdPermanently()
```

## Premium

- Dùng `MainApplication.isPremium` làm nguồn state duy nhất tại màn hình; không tạo hoặc cập nhật state premium riêng.
- Với `Fragment`, observe bằng `viewLifecycleOwner`; với `Activity`, observe bằng `this`.
- Khi premium là `true`, dismiss cả hai banner và không gọi `requestLoadAd()`.
- Khi premium là `false`, áp dụng flow load banner nếu màn hình đang hiển thị.
- Khi trạng thái premium đổi lúc màn đang mở, cập nhật ngay hai banner.
- Ads view/manager được phép kiểm tra premium như lớp bảo vệ thứ hai để chặn request SDK, nhưng màn hình vẫn chịu trách nhiệm ẩn/hiện layout.

## Ràng buộc

- Không thay đổi interstitial, rewarded, app-open ads, premium gating hoặc navigation nếu không được yêu cầu.
- `dismissAdPermanently()` phải chặn lifecycle/visibility tự load lại quảng cáo cho đến lần `requestLoadAd()` tiếp theo.

## Kiểm tra

- Banner nhỏ đẩy content lên và không che nội dung.
- Banner lớn là overlay, không làm content thay đổi layout.
- Premium ẩn cả hai banner; non-premium load cả hai banner khi màn hình hiển thị.
- Cả hai banner được dismiss khi rời màn.
- Biên dịch module phù hợp.
- Cập nhật code index và symbol index cho các file đã thay đổi.
