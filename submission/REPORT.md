# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** `Nguyễn Đình Anh Đức`
- **MSSV:** `2A202602856`
- **Lớp:** `K4-L3B`
- **Repository URL:** `https://github.com/ducnda0212/K4-L3-DAY13-NguyenDinhAnhDuc-2A202602856-Monitoring-LLMOps`
- **Commit SHA cuối:** `23a76fb`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602856`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08a-trace-metadata.png` |
| Trace generation | `evidence/08b-trace-generation.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt promote | `evidence/10a-prompt-promote.png` |
| Prompt rollback | `evidence/10b-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Kết quả cuối cần đạt tối thiểu 80/100 |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Dashboard contract có đủ sáu panel bắt buộc |
| `pytest` | 22 passed trong 1.92s | 24 passed in 1.80s | Thêm 2 test PII |
| Số traces hợp lệ | 0 | 10 | Các trace được tạo trong project Langfuse cá nhân |
| Số PII leak | 0 | 0 | Email, điện thoại Việt Nam, CCCD và thẻ thanh toán được redact |
| Latency P95 / TTFT P95 | Chưa đo từ structured log | 2652 / 50 ms | P95 tăng mạnh khi chạy challenge nhưng vẫn thấp hơn threshold 3000 ms |
| Retrieval success rate | Chưa ghi nhận | 100% | Challenge làm tăng latency, không gây retrieval failure |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa logging context cũ ở đầu mỗi request, nhận `x-request-id` từ client nếu ID hợp lệ hoặc tự sinh ID theo định dạng `req-<8-hex>`. ID được bind vào logging context, truyền xuyên suốt quá trình xử lý, ghi vào structured log và trả lại qua response header `x-request-id`. Response cũng trả `x-response-time-ms` để client quan sát thời gian xử lý
- **Các metadata được ghi vào structured log:** Log JSON chứa các trường bắt buộc `ts`, `level`, `service`, `event`, `correlation_id` và các metadata `env`, `feature`, `session_id`, `user_id_hash`, `model`. Event response_sent bổ sung `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name` và `tool_success`
- **Cách bảo đảm PII được scrub trước khi ghi:** PII processor được đặt trước bước JSON renderer và file writer. Processor tìm và thay thế email, số điện thoại Việt Nam, CCCD và số thẻ thanh toán trong cả field trực tiếp lẫn cấu trúc payload. `user_id` không được ghi nguyên văn mà được chuyển thành `user_id_hash`
- **Cách kiểm chứng kết quả:** Gửi request chứa dữ liệu PII mẫu, sau đó kiểm tra `data/logs.jsonl` và chạy `python scripts/validate_logs.py`. Evidence tại `evidence/04-structured-log.png` và `evidence/05-pii-redaction.png` cho thấy log có đầy đủ correlation ID/metadata và không còn PII mẫu ở dạng nguyên văn

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Tôi sử dụng project Langfuse `day13-k4-l3b-2A202602856` với key riêng trong `.env`, tự chạy workload và chụp danh sách trace tại `evidence/06-trace-list.png`. Không sử dụng trace ID hoặc project dùng chung của học viên khác
- **Cấu trúc root/retrieval/generation observations:** Mỗi request tạo trace `day13-agent-request`, bên trong có root observation `lab-agent-run`. Root chứa child observation `retrieval` để đo bước lấy context và child observation `generation` để đo bước sinh câu trả lời. Generation ghi model, input/output token và cost nhưng không lưu PII thô
- **Cách nối trace với log:**
- **Prompt name:** Cùng một `correlation_id` được ghi trong `data/logs.jsonl` và metadata của `lab-agent-run`. Khi cần điều tra, tôi lấy correlation ID từ log rồi lọc trace trên Langfuse bằng `metadata.correlation_id`
- **Version/label baseline:** Version 1, label `baseline`; trạng thái cuối có thêm label `production` sau rollback
- **Version/label candidate:** Version 2, label `candidate`
- **Trace ID của mỗi version:**
    - Version 1/baseline: Trace ID `883b811bede08cb74ee977ab78b9cb46`, correlation ID `req-ba5e0001`.
    - Version 2/candidate: Trace ID `76b65b13b5c0b3eb9e1ce371f01028a6`, correlation ID `req-ca1d0002`.
- **Cách promote và rollback `production`:** Tạo version 2 với một thay đổi nhỏ trong prompt, gắn label `candidate`, sau đó chuyển label `production` từ version 1 sang version 2 và gửi request kiểm tra. Khi rollback, tôi chuyển `production` về version 1, restart API và gửi lại cùng input. Evidence `evidence/09-prompt-versions.png` và `evidence/10-prompt-rollback.png` cho thấy trạng thái label trước và sau rollback.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard được dựng bằng Streamlit, đọc dữ liệu thật từ `data/logs.jsonl`, sử dụng time range 60 phút và tự refresh sau 30 giây. Dashboard gồm đúng sáu panel: Latency hiển thị P50/P95/P99 và TTFT P95; Traffic hiển thị số request và request/phút; Errors hiển thị error rate và retrieval success; Cost hiển thị tổng chi phí; Tokens hiển thị input/output tokens; Quality hiển thị quality score trung bình. Evidence: `evidence/11-dashboard-overview.png`
- **SLO và lý do chọn:** SLO `fast_successful_requests` yêu cầu 99.5% request trong cửa sổ 28 ngày phải trả response thành công với `latency_ms <= 3000`. Ngưỡng 3000 ms được chọn vì đây là giới hạn latency P95 trong dashboard contract; nó phản ánh trải nghiệm chờ của người dùng và phù hợp để phát hiện các request chậm ở phần đuôi phân phối
- **Cách tính error budget:** SLO 99.5% tương ứng error budget `100% - 99.5% = 0.5%`. Số request được phép không đạt SLO được tính bằng `total_requests × 0.005`. Ví dụ, với 10,000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc có latency lớn hơn 3000 ms
- **Ba alert và runbook tương ứng:** `HighLatencyP95` cảnh báo khi P95 latency lớn hơn 3000 ms trong 5 phút, runbook tại `docs/alerts.md#alert-1`; `HighErrorRate` cảnh báo khi error rate lớn hơn 2% trong 5 phút, runbook tại `docs/alerts.md#alert-2`; `LowRetrievalSuccess` cảnh báo khi retrieval success rate thấp hơn 90% trong 10 phút, runbook tại `docs/alerts.md#alert-3`. Cả ba alert đều là symptom-based, có severity, owner `student-2A202602856` và gửi tới Slack `#k4-l3b-alerts`

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30 13:56`
- **Triệu chứng từ metrics:** Sau khi tạo baseline và bật challenge, dashboard ghi nhận 15 request. Latency P50 là 152 ms, trong khi P95 và P99 tăng lên 2652 ms; TTFT P95 vẫn ở mức 50 ms. Error rate bằng 0% và retrieval success rate bằng 100%. Điều này cho thấy triệu chứng chính là latency tăng mạnh so với baseline, không phải request failure hoặc retrieval failure. Giá trị P95 vẫn thấp hơn threshold 3000 ms nên chưa thể kết luận vi phạm SLO
- **Log line và correlation ID liên quan:** Log `response_sent` tại thời điểm `2026-09-30 13:56:04.819` có `correlation_id`=`req-a340780f`, `latency_ms`=`2652ms`, `ttft_ms`=`50`, `tool_name`=`retrieval` và `tool_success`=`true`. Log này đại diện cho một request chậm trong workload challenge. Evidence tại `evidence/13-incident-log.png`
- **Trace ID và span gây ảnh hưởng:** Trace ID `a5d273546d4c7694e48fa0bd52172d30` có cùng `correlation_id`=`req-a340780f`. Waterfall cho thấy span retrieval mất 2.5s, trong khi span generation mất 0.15s. Vì retrieval chiếm phần lớn tổng thời gian nên đây là span gây ảnh hưởng chính. Evidence tại `evidence/14-incident-trace.png`
- **Root cause:** Incident `rag_slow` làm bước retrieval bị tăng thời gian xử lý. Kết luận này dựa trên chuỗi bằng chứng: dashboard cho thấy latency tăng, log xác định một request chậm cụ thể và trace cùng correlation ID cho thấy thời gian tập trung chủ yếu ở span retrieval
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable`, sau đó kiểm tra `/health` để xác nhận `rag_slow`, `tool_fail` và `cost_spike` đều trở về `false`. Chạy lại workload để xác nhận latency quay về mức baseline
- **Preventive measure:** Duy trì alert `HighLatencyP95`, theo dõi P95/P99 thay vì chỉ theo dõi average, giữ correlation ID xuyên suốt Metrics → Logs → Traces và sử dụng runbook yêu cầu kiểm tra riêng duration của retrieval và generation. Khi thay đổi retrieval configuration hoặc prompt, cần đo lại trên cùng workload trước khi promote lên production

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Sử dụng cùng một correlation ID trong response header, structured log và trace metadata. Quyết định này cho phép đi từ một metric bất thường trên dashboard đến đúng log line và đúng trace thay vì mở trace ngẫu nhiên
- **Một lỗi/blocker đã gặp:** Ở lần chạy CP3 đầu tiên, tôi chưa chuyển log cũ ra ngoài repo, chưa tạo baseline sạch và sử dụng thời gian phía client do `load_test.py` in ra để đánh giá latency. Khi chạy concurrency 5, thời gian phía client có thể bao gồm cả thời gian chờ hàng đợi nên không phản ánh chính xác thời gian xử lý phía server
- **Cách tìm nguyên nhân và xử lý:** Đọc lại hướng dẫn CP3, tắt incident cũ, dừng API, chuyển `data/logs.jsonl` cũ ra ngoài repo, khởi động API không có `--reload`, tạo baseline mới rồi mới bật challenge. Khi điều tra, tôi sử dụng `latency_ms` trong structured log/dashboard thay cho thời gian phía client
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics giúp xác định loại triệu chứng và khoảng thời gian xảy ra. Logs giúp chọn một request bất thường cụ thể thông qua correlation ID. Trace có cùng correlation ID cho biết span retrieval hay generation bị chậm hoặc lỗi. Root cause chỉ được kết luận khi ba nguồn bằng chứng cùng chỉ về một nguyên nhân
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version giúp xác định chính xác request đã sử dụng prompt nào. Token và cost giúp phát hiện prompt hoặc output dài bất thường. SLO định nghĩa mức chất lượng vận hành chấp nhận được, còn error budget cho biết hệ thống được phép có bao nhiêu request không đạt. Label `production` cho phép promote hoặc rollback prompt mà không phải hard-code version trong ứng dụng
- **Điều quan trọng nhất đã học:** Observability không chỉ là tạo log hoặc trace riêng lẻ mà là bảo đảm metric, log và trace có thể liên kết thành một chuỗi bằng chứng. Không nên đoán root cause từ tên incident hoặc mở trace ngẫu nhiên
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Alert hiện được mô tả trong config và runbook nhưng chưa tích hợp gửi thông báo thật tới Slack. Các giá trị validator, pytest, trace ID và correlation ID được đánh dấu `[CẦN ĐIỀN]` cần được cập nhật từ lần chạy cuối trước khi nộp

## 9. Checklist trước khi nộp

- [X] Kết quả và evidence thuộc commit SHA cuối.
- [X] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [X] Incident evidence nối đúng metric → log → trace.
- [X] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [X] Repository chạy lại được theo README.
- [X] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [X] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
