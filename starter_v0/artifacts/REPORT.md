# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức theo từ khóa (web/mạng xã hội), theo tài khoản Twitter cụ thể, đọc URL, tra cứu bài báo khoa học (arXiv), tra cứu chính sách nội bộ, và định dạng kết quả thành digest. Agent biết hỏi lại khi thiếu thông tin và luôn xác nhận trước khi gửi/đăng nội dung.

**Link dùng thử (truy cập được trong showdown):**

> URL: *(Người 4 điền sau khi khởi động Streamlit UI và mở Cloudflare Tunnel)*

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc xác nhận trước khi hành động | không |
| timeline | Lấy tweet mới nhất của một tài khoản Twitter cụ thể | không |
| social_search | Tìm kiếm tweet theo chủ đề (Latest hoặc Top) | không |
| lookup | Tìm kiếm tin tức / thông tin chung trên web | không |
| fetch | Đọc và tóm tắt nội dung từ một URL cụ thể | không |
| papers | Tìm bài báo khoa học trên arXiv | không |
| paper_text | Đọc nội dung text đầy đủ của một bài báo arXiv | không |
| policy | Tra cứu tài liệu chính sách nội bộ của công ty | không |
| format | Trình bày dữ liệu đã thu thập thành các định dạng văn bản | không |
| send | Gửi nội dung ra ngoài (cần xác nhận trước) | không |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. `Tweet mới nhất của Sam Altman là gì?`
2. `Tin tức AI hôm nay có gì nổi bật?`
3. `Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-5`
4. `Mọi người đang bàn gì về GPT-5 trên Twitter? Lấy tweet phổ biến nhất.`
5. `Tra cứu chính sách bảo mật dữ liệu của công ty mình.`

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline (system_prompt gốc – agent tự đoán bừa, không hỏi lại) | Chưa có | case_accuracy | — | 0.0% | `runs/v0_B_group_gemini_20260729T154338843404.json` |
| v1 | Thêm luật map tên (sama, elonmusk, karpathy) + boundary check (clarify yes_no trước khi send) | Khắc phục wrong_tool và wrong_boundary | case_accuracy | 0.0% | ~60% | *(chạy nội bộ v1)* |
| v2 | Thêm luật Multi-turn: carry context (limit, timeframe, topic) + correction handling | Khắc phục multi-turn context drop | case_accuracy | 60% | **85.71%** | `runs/v2_B_group_gemini_20260729T160412811297.json` |
| v3 | *(Người 1 tiếp tục — fix G02 wrong_arg_value: parse 'mới nhất' → lastUpdatedDate)* | Đưa case_accuracy lên 100% | case_accuracy | 85.71% | *(chưa chạy)* | — |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| G02_single_papers | wrong_arg_value | `papers(query="Transformer")` | Agent không map được từ "mới nhất" thành `sort_by="lastUpdatedDate"`, dùng mặc định `relevance` | Thêm vào system_prompt: '"mới nhất" → sort_by=lastUpdatedDate, "theo ngày nộp" → submittedDate' |
| G08_multi_correction | provider_error | *(không gọi được)* | Rate limit API Gemini (free tier 15 req/min), bị từ chối ở các case cuối | Đợi 60s rồi chạy lại, hoặc dùng gói API trả phí |
| G09_multi_missing_info | provider_error | *(không gọi được)* | Rate limit API Gemini | Đợi 60s rồi chạy lại |
| G10_multi_social_search | provider_error | *(không gọi được)* | Rate limit API Gemini | Đợi 60s rồi chạy lại |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v2) |
|---|---|---|---|
| G01_single_policy | Agent tra cứu đúng chính sách data_privacy | `policy(policy_area="data_privacy")` | ✅ PASS |
| G02_single_papers | Map "mới nhất" → `lastUpdatedDate` | `papers(sort_by="lastUpdatedDate")` | ❌ FAIL (wrong_arg_value) |
| G03_single_out_of_scope | Từ chối câu ngoài phạm vi (dịch thơ) | `no_tool` / refuse | ✅ PASS |
| G04_single_wrong_boundary | Hỏi xác nhận trước khi gửi email | `clarify(response_type="yes_no")` | ✅ PASS |
| G05_single_missing_info | Hỏi lại khi thiếu arxiv_url | `clarify(response_type="text")` | ✅ PASS |
| G06_multi_papers | Multi-turn: ghi nhớ topic + sắp xếp theo ngày nộp | `papers(sort_by="submittedDate", max_results=10)` | ✅ PASS |
| G07_multi_switch_tool | Multi-turn: đổi tool từ lookup sang policy | `policy(policy_area="ai_research", top_k=5)` | ✅ PASS |
| G08_multi_correction | Multi-turn: sửa arxiv_url + giữ max_pages | `paper_text(arxiv_url="2307.09288", max_pages=10)` | ⚠️ provider_error (rate limit) |
| G09_multi_missing_info | Multi-turn: vẫn thiếu URL sau 3 lượt → hỏi lại | `clarify(response_type="text")` | ⚠️ provider_error (rate limit) |
| G10_multi_social_search | Multi-turn: đổi sang social_search + Top | `social_search(search_type="Top")` | ⚠️ provider_error (rate limit) |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- **Fixes thuộc `system_prompt.md`:** Tất cả các luật về routing (timeline vs social_search), map tên người dùng (Sam Altman → sama), luật carry-over context multi-turn, và boundary check (clarify trước khi send). Đây là logic hành vi của agent, không phải schema tool.
- **Fixes thuộc `tools.yaml`:** Mô tả `description` của từng tool cần rõ hơn về *khi nào KHÔNG gọi* (ví dụ: `fetch` chỉ dùng khi đã có URL cụ thể, không phải khi chỉ nhắc đến "bài này"). Tham số `sort_by` của `papers` nên ghi rõ mapping từ ngôn ngữ tự nhiên sang enum.
- **Failure cần manual review:** G02 (wrong_arg_value): Auto-grader chỉ kiểm tra arg có khớp không, nhưng không biết agent có giải thích lý do chọn `relevance` hay không. Cần đọc actual_text thủ công.
- **Cải thiện tiếp theo:** (1) Fix G02 bằng cách thêm mapping rõ ràng vào prompt. (2) Chạy lại G08/G09/G10 sau khi rate limit reset để có đủ 10/10 measured cases. (3) Thêm tool mới (Người 3) và tích hợp vào tools.yaml.
