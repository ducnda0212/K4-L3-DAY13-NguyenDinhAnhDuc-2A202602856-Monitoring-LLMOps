# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: P95 của `response_sent.latency_ms`.
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn trước khi nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency, xác nhận P95/P99 và khoảng thời gian bắt đầu tăng.
  2. Lọc `data/logs.jsonl` trong khoảng thời gian đó và lấy một `correlation_id` có `latency_ms > 3000`.
  3. Mở trace tương ứng trên Langfuse, so sánh thời gian của retrieval và generation để xác định bước chậm.
- Mitigation tạm thời: Rollback prompt production nếu latency tăng sau khi đổi prompt; tắt incident practice hoặc giảm concurrency nếu hệ thống đang quá tải.
- Owner: `student-2A202602856`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỷ lệ `request_failed` trên tổng `request_received`.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Một phần request không trả được câu trả lời thành công.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors để xác nhận error rate và nhóm `error_type` tăng.
  2. Lọc các log có `event == "request_failed"` và lấy một `correlation_id`.
  3. Mở trace cùng `correlation_id`, kiểm tra observation bị lỗi và metadata liên quan.
- Mitigation tạm thời: Rollback thay đổi gần nhất, khôi phục cấu hình ổn định và tắt practice scenario nếu sự cố đến từ dữ liệu mô phỏng.
- Owner: `student-2A202602856`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỷ lệ thành công của tool retrieval.
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90%` liên tục trong 10 phút.
- Ảnh hưởng tới người dùng: Câu trả lời có thể thiếu context, không chính xác hoặc giảm quality score.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors và Quality, xác nhận retrieval success giảm và quality có bị ảnh hưởng hay không.
  2. Lọc log có `tool_name == "retrieval"` và `tool_success == false`, sau đó lấy `correlation_id`.
  3. Mở trace tương ứng và kiểm tra observation retrieval trước khi kiểm tra generation.
- Mitigation tạm thời: Khôi phục cấu hình retrieval ổn định, rollback thay đổi liên quan và sử dụng phản hồi fallback an toàn khi không lấy được context.
- Owner: `student-2A202602856`
