# Global Mobile & Android Bug Prevention Patterns (Hybrid Architecture)

> Tài liệu tri thức toàn cục đúc kết từ các lỗi thực tế (verified bugs) qua các dự án.
> Mục đích: Ngăn ngừa lỗi ngay từ khâu thiết kế và sinh code, áp dụng chung cho mọi dự án Android Kotlin/Java & Mobile.

---

## 1. Lifecycle & Component State Restoration

### Pattern ID: `PAT-LIFECYCLE-001`
- **Tên mẫu**: Tránh Constructor Parameters trong Fragment và BottomSheetDialog.
- **Triệu chứng lỗi**: App crash khi xoay màn hình (orientation change), đổi theme Day/Night, hoặc hệ thống kill app và restore state (`Fragment.InstantiationException: could not find Fragment constructor`).
- **Nguyên nhân gốc**: AndroidX `FragmentManager` chỉ sử dụng constructor mặc định (không tham số) thông qua reflection để tái tạo lại Fragment sau process death.
- **Quy tắc vàng (Golden Rule)**:
  1. KHÔNG BAO GIỜ truyền tham số qua constructor của `Fragment`, `DialogFragment`, `BottomSheetDialogFragment`.
  2. Dùng `setArguments(Bundle)` và `arguments` để truyền dữ liệu khởi tạo nguyên thủy/Parcelable.
  3. Dùng `setFragmentResultListener` / `setFragmentResult` để truyền callback hoặc nhận kết quả giữa các Fragment thay vì truyền interface/lambda qua constructor.
  4. Quản lý trạng thái màn hình bằng `SavedStateHandle` trong `ViewModel`.

---

## 2. Thread Safety & Asynchronous SDK Callbacks

### Pattern ID: `PAT-THREADING-001`
- **Tên mẫu**: Bắt buộc Dispatch về Main Thread cho các Callback từ SDK bên thứ ba.
- **Triệu chứng lỗi**: Crash `IllegalStateException: Method navigate cannot be accessed from outside the main thread` hoặc crash khi cập nhật View/Fragment transaction.
- **Nguyên nhân gốc**: Các SDK quảng cáo (Google Mobile Ads / AdMob Next-Gen), Billing, Analytics, Background Worker thường dispatch các sự kiện (`onAdDismissedFullScreenContent`, `onAdFailedToShow`, `onPurchasesUpdated`,...) trên background thread hoặc binder thread.
- **Quy tắc vàng (Golden Rule)**:
  1. Mọi tương tác với `NavController.navigate()`, `FragmentManager`, Dialog `show()/dismiss()`, hoặc thay đổi View visibility từ callback bên thứ ba BẮT BUỘC phải bọc trong `activity.runOnUiThread { ... }` hoặc `withContext(Dispatchers.Main)`.
  2. Khi dùng Coroutine Flow/StateFlow từ SDK, luôn collect trong `lifecycleScope.launch { repeatOnLifecycle(Lifecycle.State.STARTED) { ... } }`.

---

## 3. Realtime Camera & GPU Image Processing

### Pattern ID: `PAT-CAMERAX-001`
- **Tên mẫu**: Tách biệt luồng GPU Processing và CPU Heavy Computation trong CameraX.
- **Triệu chứng lỗi**: Camera Preview bị đơ, giật khung hình (frame drops), nút chụp ảnh (take picture) phản hồi chậm hoặc phải nhấn nhiều lần mới chụp được.
- **Nguyên nhân gốc**: Decode full-resolution bitmap, xử lý biến đổi ma trận màu (color transform/gamma/contrast) trên CPU ngay trên luồng ImageAnalysis hoặc UI thread, gây nghẽn hàng đợi frames.
- **Quy tắc vàng (Golden Rule)**:
  1. Với hiệu ứng hình ảnh trực tiếp (color filters, contrast, matrix): Dùng `SurfaceProcessor` / `Media3Effect` (GPU shader) của CameraX để GPU render đồng thời cho cả Preview và ImageCapture.
  2. Tách biệt `ImageAnalysis` (dành riêng cho AI/ML inference) và `ImageCapture` (lấy ảnh chất lượng cao).
  3. Các tác vụ nặng (như tính toán fingerprint aHash/dHash, duplicate detection) phải chạy trên `Dispatchers.IO` hoặc dedicated background executor.
  4. Vô hiệu hóa nút chụp (`isEnabled = false`) trong lúc đang xử lý frame hoặc đang review duplicate để tránh người dùng nhấn liên tục.

---

## 4. Google Play Billing Integration

### Pattern ID: `PAT-BILLING-001`
- **Tên mẫu**: Phân định BasePlan/Offer trong Play Billing v6+ và Chặn Cấp Quyền Giả Lập.
- **Triệu chứng lỗi**: Mua subscription thất bại do map sai product ID, hoặc người dùng được cấp Premium miễn phí dù giao dịch Play Billing chưa hoàn tất.
- **Nguyên nhân gốc**: Từ Google Play Billing v5/v6+, Google chuyển sang mô hình 1 subscription product chứa nhiều `basePlanId` và `offerId`. Cấp quyền premium chỉ dựa trên click event mà không đợi verify purchase token.
- **Quy tắc vàng (Golden Rule)**:
  1. Tách rõ luồng Subscription (`queryProductDetails` với `ProductType.SUBS`) và In-App Purchase vĩnh viễn (`ProductType.INAPP`).
  2. Lọc chính xác `basePlanId` và kiểm tra eligibility của `offerId` (ví dụ free trial); nếu không đủ điều kiện, bắt buộc fallback về base plan chuẩn (`offerId == null`).
  3. CHỈ cập nhật trạng thái `isPremium = true` khi Purchase có trạng thái `PurchaseState.PURCHASED` VÀ đã gọi `acknowledgePurchase` thành công.
  4. Xử lý trường hợp Activity bị pause/resume khi Google Play UI hiển thị bằng cách dùng buffered Channel/StateFlow để không làm rơi mất kết quả trả về.

---

## 5. AdMob Layout, Policy & UX Safety

### Pattern ID: `PAT-ADMOB-001`
- **Tên mẫu**: Định dạng kích thước cố định cho Banner và Phân tách rõ ràng Native Ad với nội dung App.
- **Triệu chứng lỗi**: Layout bị nhảy đột ngột (layout shift), che mất Bottom Navigation, người dùng click nhầm vào quảng cáo dẫn đến vi phạm chính sách Google AdMob (Accidental Clicks Policy).
- **Nguyên nhân gốc**: Dùng `wrap_content` cho banner container; đặt Native Overlay đè lên navigation bar; thiếu viền và độ nổi (elevation) khiến quảng cáo tiệp màu với nền app.
- **Quy tắc vàng (Golden Rule)**:
  1. Banner ad host: Dùng chiều cao cố định chuẩn hóa (`banner_ad_height`, e.g. `60dp`), thêm viền phân cách mỏng (`1dp` top border) để tách biệt rõ với content bên trên.
  2. Native ad dạng collapse/overlay: Bắt buộc có elevation tối thiểu `16dp`, viền tương phản (`1dp` border), và anchor neo phía trên Bottom Navigation bar.
  3. Luôn gán `AdChoicesPlacement.TOP_RIGHT` để Google SDK hiển thị biểu tượng AdChoices đúng chuẩn chính sách.
  4. Native Full Screen ad: Gắn countdown hiển thị tối thiểu 3 giây trước khi cho phép bấm nút Close (32dp) để tránh click tặc và vi phạm chính sách.

---

## 6. System UI & Immersive Window Management

### Pattern ID: `PAT-SYSTEMUI-001`
- **Tên mẫu**: Tái áp dụng Immersive Mode trên Secondary Windows (Dialogs & Bottom Sheets).
- **Triệu chứng lỗi**: Thanh điều hướng hệ thống (Navigation Bar / Gesture bar) tự động hiện lại mỗi khi mở Dialog, DatePicker hoặc BottomSheet, làm vỡ trải nghiệm Fullscreen.
- **Nguyên nhân gốc**: Window của Dialog/BottomSheet là window độc lập được quản lý bởi `WindowManager`, không tự động thừa hưởng flag ẩn navigation bar của Activity cha.
- **Quy tắc vàng (Golden Rule)**:
  1. Trong app Immersive: Bắt buộc can thiệp vào `onCreateDialog` hoặc `onStart` của `BaseDialogFragment` và `BaseBottomSheetDialog`.
  2. Sử dụng `WindowInsetsControllerCompat(window, window.decorView)` với behavior `BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE` và gọi `hide(WindowInsetsCompat.Type.navigationBars())`.
  3. Trong `MainActivity.onWindowFocusChanged(hasFocus)`: Luôn re-apply lại immersive flag khi Activity lấy lại tiêu điểm.

---

## 7. Machine Learning / TFLite Tensor Contracts

### Pattern ID: `PAT-TFLITE-001`
- **Tên mẫu**: Kiểm soát chặt chẽ Tensor Order, Output Shapes và Coordinate Normalization.
- **Triệu chứng lỗi**: Bounding box hoặc overlay của nhận diện văn bản (Document Detection) bị lệch góc, biến mất hoặc nhận diện nhầm nền trắng.
- **Nguyên nhân gốc**: Thứ tự map tensor đầu ra bị đảo ngược giữa class logits và corner coordinates; chuẩn hóa tọa độ không khớp giữa model space (`[0, 1]`) và image pixel space.
- **Quy tắc vàng (Golden Rule)**:
  1. Kiểm tra contract đầu vào: Chuẩn hóa kích thước input (`[1, 224, 224, 3]`, Float32).
  2. Output tensor: Đọc đúng thứ tự `class_logits [1, 3]` trước, sau đó mới đọc `corners [1, 8]`.
  3. Softmax & Argmax: Áp dụng softmax trên logits, chỉ chấp nhận nhãn mục tiêu (Paper/Screen) nếu confidence vượt ngưỡng an toàn (e.g. `>= 0.5`).
  4. Thứ tự 4 góc: Chuẩn hóa thống nhất `Top-Left, Top-Right, Bottom-Right, Bottom-Left` trong toàn bộ pipeline từ detection sang crop.
