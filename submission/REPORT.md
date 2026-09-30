# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:**
- **MSSV:**
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-<MSSV>`

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
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | 21 records; 20 thiếu required fields, 20 thiếu enrichment, 0 correlation ID hợp lệ |
| `validate_dashboard.py` | 6/6 panel | | Mới xác nhận dashboard contract YAML |
| `pytest` | 22 passed trong 1.92s | | |
| Số traces hợp lệ | Chưa kiểm chứng | | 10 request HTTP 200 nhưng đều trả `correlation_id=MISSING` |
| Số PII leak | 0 | | PII scrubbing đạt tại baseline |
| Latency P95 / TTFT P95 | Chưa đo từ structured log | | `load_test.py` ghi nhận client latency cao nhất 2074.1 ms nhưng không có TTFT |
| Retrieval success rate | Chưa ghi nhận | | Baseline chưa log trường `tool_success` |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
- **Các metadata được ghi vào structured log:**
- **Cách bảo đảm PII được scrub trước khi ghi:**
- **Cách kiểm chứng kết quả:**

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard được dựng bằng Streamlit, đọc dữ liệu thật từ `data/logs.jsonl`, sử dụng time range 60 phút và tự refresh sau 30 giây. Dashboard gồm đúng sáu panel: Latency hiển thị P50/P95/P99 và TTFT P95; Traffic hiển thị số request và request/phút; Errors hiển thị error rate và retrieval success; Cost hiển thị tổng chi phí; Tokens hiển thị input/output tokens; Quality hiển thị quality score trung bình. Evidence: `evidence/11-dashboard-overview.png`
- **SLO và lý do chọn:** SLO `fast_successful_requests` yêu cầu 99.5% request trong cửa sổ 28 ngày phải trả response thành công với `latency_ms <= 3000`. Ngưỡng 3000 ms được chọn vì đây là giới hạn latency P95 trong dashboard contract; nó phản ánh trải nghiệm chờ của người dùng và phù hợp để phát hiện các request chậm ở phần đuôi phân phối
- **Cách tính error budget:** SLO 99.5% tương ứng error budget `100% - 99.5% = 0.5%`. Số request được phép không đạt SLO được tính bằng `total_requests × 0.005`. Ví dụ, với 10,000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc có latency lớn hơn 3000 ms
- **Ba alert và runbook tương ứng:** `HighLatencyP95` cảnh báo khi P95 latency lớn hơn 3000 ms trong 5 phút, runbook tại `docs/alerts.md#alert-1`; `HighErrorRate` cảnh báo khi error rate lớn hơn 2% trong 5 phút, runbook tại `docs/alerts.md#alert-2`; `LowRetrievalSuccess` cảnh báo khi retrieval success rate thấp hơn 90% trong 10 phút, runbook tại `docs/alerts.md#alert-3`. Cả ba alert đều là symptom-based, có severity, owner `student-2A202602856` và gửi tới Slack `#k4-l3b-alerts`

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
