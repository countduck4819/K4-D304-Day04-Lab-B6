# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: K4-D304-Day04-Lab-B6
- Provider/model: `openrouter` · `openai/gpt-4o-mini`

**Members:**

| # | Họ và tên | MSSV |
|---|---|---|
| 1 | Trịnh Bá Khánh Trình | 2A202601531 |
| 2 | Nguyễn Văn Dương | 2A202601400 |
| 3 | Nguyễn Văn Tấn | 2A202601246 |
| 4 | Vũ Thành Khang | 2A202601866 |

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent chạy thật với 14 tool: tìm tin theo từ khóa và theo tài khoản, đọc URL, tra cứu Wikipedia, xem Hacker News, kiểm tra thời tiết real-time, đổi tiền tệ theo tỷ giá hôm nay, và gửi digest lên Telegram — luôn hỏi lại khi thiếu thông tin và luôn xin xác nhận trước khi thực hiện hành động outbound.

**Link dùng thử (truy cập được trong showdown):**

> URL: `http://localhost:8501` (chạy bằng `streamlit run app.py` từ `starter_v0/`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận yes_no trước hành động nhạy cảm | Không |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản Twitter/X cụ thể | Không |
| `social_search` | Tìm bài đăng Twitter/X theo từ khóa/chủ đề | Không |
| `lookup` | Tra cứu web/tin tức qua Tavily, có `topic` và `timeframe` | Không |
| `fetch` | Đọc nội dung của một URL cụ thể qua Firecrawl | Không |
| `format` | Trình bày các item đã có thành digest markdown | Không |
| `send` | Gửi text lên Telegram channel (bắt buộc confirm trước) | Không |
| `policy` / `papers` / `paper_text` | Tra policy nội bộ, tìm arXiv, trích text PDF | Không (optional) |
| **`wiki`** | Tra Wikipedia summary theo chủ đề, hỗ trợ nhiều ngôn ngữ | **Có** |
| **`hackernews`** | Tìm story trên Hacker News qua Algolia | **Có** |
| **`weather`** | Thời tiết hiện tại của một địa điểm qua wttr.in | **Có** |
| **`currency`** | Đổi tỷ giá fiat real-time qua open.er-api.com | **Có** |

Nhóm viết mới **4 tool** (`wiki`, `hackernews`, `weather`, `currency`) — vượt ngưỡng bonus (>3 tool) khi UI đầy đủ.

## A3. Câu hỏi mẫu để thử

1. *"Tin AI hôm nay có gì nổi bật?"* → `lookup(topic=news, timeframe=day)`
2. *"Alan Turing là ai?"* → `wiki` (tool mới, có URL nguồn Wikipedia)
3. *"100 USD sang VND"* → `currency` (tỷ giá real-time)
4. *"Thời tiết Hà Nội bây giờ"* → `weather`
5. *"Gửi lên Telegram: 'chào nhóm AI20k'"* → agent gọi `clarify(yes_no)` trước, chỉ `send` sau khi user trả lời "có"

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tin AI hôm nay (routing web/news) | `lookup(query="AI", topic="news", timeframe="day")` → answer | v0 nhiều khi chọn nhầm sang timeline/social; v2/v3 route đúng `lookup` | `runs/v3_B_base_openrouter_20260729T162207737251.json` (R03 PASS) |
| Thiếu handle: "5 tweet mới nhất giúp mình" | v0: đoán bừa `timeline(sama)`; v2/v3: `clarify` xin handle | v0 mặc định Sam Altman, v2 loại bỏ rule đoán bừa | `runs/v0_B_base_openrouter_20260729T155118820169.json` (R10 FAIL) vs `runs/v2_...` (R10 PASS) |
| Send Telegram: "Post digest lên kênh giúp" | Agent gọi `clarify(yes_no)` trước, user "có", sau đó `send(confirmed=true)` | v0 tự gọi `send`; từ v1 có rule confirmation | `transcripts/v3_openrouter_20260729T162457860086.transcript.json` (turn 4–5) |
| Tool mới: "100 USD sang VND" | `currency(amount=100, base=USD, target=VND)` → trả về ~2.6M VND real-time | Chỉ có từ v3 (nhóm thêm 4 tool cuối) | UI tab "LLM vs Agent" so sánh trực tiếp với LLM trần đưa tỷ giá cũ |
| So sánh version live | Tab "Compare across versions": chọn 4 version, hỏi *"5 tweet mới nhất giúp mình"* → v0 đoán, v2/v3 clarify | Trực quan hóa hiệu ứng optimize | `versions/v0..v3/` snapshot |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | none — baseline | — (baseline) | case_accuracy | — | 0.65 | `runs/v0_B_base_openrouter_20260729T155118820169.json` |
| v1 | `system_prompt.md`: thêm rule confirmation trước `send` | Explicit rule requiring `clarify(yes_no)` before `send` sẽ fix R12 wrong_boundary | case_accuracy | 0.65 | 0.75 | `runs/v1_B_base_openrouter_20260729T160231188325.json` |
| v2 | `system_prompt.md`: xóa "guess Sam Altman"/"assume URL" + thêm rule clarify-when-missing | Loại rule đoán bừa và ép `clarify` khi thiếu arg sẽ fix R10, R11 missing_info | case_accuracy | 0.75 | 0.85 | `runs/v2_B_base_openrouter_20260729T160457773478.json` |
| v3 | `tools.yaml`: hardened description với "when to use / not to use" + confirmation contract trên `send` | Self-documenting tool descriptions sẽ fix R11, R13 và củng cố R12 | case_accuracy | 0.85 | 0.85 → 0.90 sau khi thêm 4 tool mới | `runs/v3_B_base_openrouter_20260729T160819746739.json` (0.85), `runs/v3_B_base_openrouter_20260729T162207737251.json` (0.90 sau khi có `wiki/hackernews/weather/currency`) |

Chi tiết per-run (metric hợp lệ vì `provider_error_cases = 0`, `measured_cases = 20`):

| Run | case_acc | routing_acc | arg_acc | multiturn_acc | passed |
|---|---:|---:|---:|---:|---:|
| v0 baseline | 0.65 | 0.75 | 0.65 | 1.00 | 13/20 |
| v1 | 0.75 | 0.90 | 0.75 | 1.00 | 15/20 |
| v2 | 0.85 | 1.00 | 0.85 | 1.00 | 17/20 |
| v3 (tools.yaml hardened) | 0.85 | 0.95 | 0.85 | 0.67 | 17/20 |
| v3 + 4 tools mới | **0.90** | 0.95 | 0.90 | 0.83 | **18/20** |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send (v0→v3) | `wrong_boundary` | `send(text="…", confirmed=true)` gọi thẳng ở turn 1 | Model bỏ qua rule confirmation trong single-turn eval, kể cả sau v1 (thêm rule ở prompt) và v3 (thêm rule ở tool description). PASS trong live chat multi-turn nhưng FAIL trong eval single-turn. | Cần chặn cứng ở agent loop (`agent.py`), hoặc `tool_choice="clarify"` khi phát hiện keyword send |
| R10_missing_handle (v0, v1) | `missing_info` | `timeline(screenname="sama")` | Rule "pick Sam Altman" trong prompt v0/v1 khiến model đoán bừa handle | v2: xóa rule đoán + thêm rule clarify-when-missing → PASS |
| R11_missing_url (v0, v1, v2) | `missing_info` | `fetch(url="https://openai.com/blog/gpt-5")` | Rule "assume URL" khiến model bịa URL. v2 xóa rule, nhưng model vẫn thỉnh thoảng tạo URL do độ specific chưa đủ. | v3: `fetch` description ghi rõ "do NOT call on invented URL, clarify first" → PASS |
| R03_web_news_routing (v0, v1) | `wrong_tool` | `social_search` hoặc `timeline` | Description `lookup` không chỉ rõ "dùng cho news/web" — v0/v1 model nhầm sang social | v2/v3: PASS (kết hợp prompt + description rõ hơn) |
| R13_parallel_web_and_tweets (v0, v1, v2) | `wrong_tool` | Chỉ gọi 1 tool | Prompt không ép gọi song song 2 tool | v3: tools.yaml gợi ý phân biệt `lookup` vs `social_search` → model chủ động gọi cả 2 |
| M02_carryover_timeframe (v3 only) | `wrong_arg_value` | `lookup(query="…")` không carry-over `timeframe` từ turn trước | Regression sau khi hardened tools.yaml — model quá bám mô tả cụ thể của tool, quên context multi-turn | Cần thử prompt patch thêm rule "carry-over previous args when user gives correction" |
| G05_missing_url_read_this (group) | `wrong_arg_value` (observed) | `clarify(response_type="yes_no")` — nhầm loại | Model gọi đúng `clarify` (routing 100%) nhưng chọn `yes_no` thay vì `text` cho câu hỏi mở | Description `clarify` cần ví dụ rõ ràng "yes_no chỉ dùng để confirm hành động outbound" |

## B3. Team eval cases

File `data/eval_group.json` — 10 case do nhóm tự viết (5 single-turn + 5 multi-turn), phủ đủ 6 `failure_type` cho phép. Group run trên v3: **9/10 pass, case_accuracy 0.90, routing_accuracy 1.0**.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v2) |
|---|---|---|---|
| G01_name_to_handle_karpathy | Map "Andrej Karpathy" → handle `karpathy`; chọn `timeline` không phải `social_search` | `timeline(screenname="karpathy")` | PASS |
| G02_multi_arg_month_topk3 | Trích 3 arg cùng lúc (`topic`, `timeframe`, `max_results`) | `lookup(query="AI", topic="news", timeframe="month", max_results=3)` | PASS |
| G03_send_confirm_short_text | Send text ngắn vẫn phải confirm trước | `clarify(response_type="yes_no")` | PASS |
| G04_out_of_scope_essay | Yêu cầu viết essay 500 từ về khí hậu → agent phải từ chối | `no_tool, behavior="refuse"` | PASS |
| G05_missing_url_read_this | "Đọc URL này" nhưng không có URL → phải clarify xin URL | `clarify(response_type="text")` | FAIL (dùng nhầm `yes_no`) |
| G06_multi_cancel_then_meta | User hủy request rồi hỏi meta → phải trả lời thẳng, không tool | `no_tool, behavior="answer_without_tool"` | PASS |
| G07_multi_correction_limit | Sửa `limit` 5→10 giữa 2 turn, phải carry-over handle | `timeline(screenname="elonmusk", limit=10)` | PASS |
| G08_multi_still_missing_url | User thúc giục sau 2 turn nhưng vẫn thiếu URL → vẫn phải clarify | `clarify(response_type="text")` | PASS |
| G09_multi_switch_web_to_social | Chuyển từ `lookup` (turn 1) sang `social_search` khi user nói "trên Twitter" | `social_search(query="Nvidia")` | PASS |
| G10_multi_summarize_then_send | Sau khi có nội dung, user request post → vẫn phải clarify yes_no | `clarify(response_type="yes_no")` | PASS |

Run evidence: `runs/v3_B_group_openrouter_20260729T161221209441.json`.

## B4. Live chat evidence

Transcript `transcripts/v3_openrouter_20260729T162457860086.transcript.json` (chat.py) — 5 turn tương ứng 3 scenario:

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1 — Normal research | v3 | `lookup({query:"AI", topic:"news", timeframe:"day", max_results:5})` | `transcripts/v3_openrouter_20260729T162457860086.transcript.json` | Agent trả lại 5 bài AI news kèm URL đúng — routing chuẩn |
| Turn 2 — "Tóm tắt bài viết này" (vague) | v3 | `fetch(url=<URL từ turn 1>)` | như trên | Agent **không clarify**, tự dùng URL trong context history. Finding thú vị: rule "clarify khi thiếu URL" áp dụng cho single-turn, multi-turn model chọn suy diễn từ history |
| Turn 3 — User gửi URL cụ thể | v3 | `fetch(url="https://openai.com/blog/gpt-5")` | như trên | Route đúng `fetch`, URL trả 404 (URL không tồn tại thực) — tool execution error nhưng routing correct |
| Turn 4 — "Gửi lên Telegram" (sensitive) | v3 | `clarify(question="…", response_type="yes_no")` | như trên | **Confirmation boundary WORK** trong live chat, ngược với R12 FAIL trong single-turn eval |
| Turn 5 — User trả lời "có" | v3 | `send(text="Chào buổi sáng nhóm AI20k", confirmed=true)` | như trên | Route đúng, execution failed vì `TELEGRAM_BOT_TOKEN` unset (theo README yêu cầu) |
| UI chat transcripts | v3 | Wiki/weather/currency tool calls | `transcripts/ui_v3_openrouter_20260729T163035716914.transcript.json`, `transcripts/ui_v3_openrouter_20260729T163518382768.transcript.json` | Tool mới hoạt động đúng trong UI Streamlit |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên — **`wiki`** | `tools/wiki/tool.py`, `tools/wiki/TOOL.md`, smoke test "Alan Turing" + "Hà Nội" (lang=vi) | Wikipedia REST API (opensearch → summary), hoạt động cả tiếng Anh + tiếng Việt, no API key | Rate limit 200 req/s của Wikipedia — không lo trong lab; `User-Agent` custom để không bị chặn |
| Bonus: tool mới thứ 2 — **`hackernews`** | `tools/hackernews/tool.py`, smoke test query="LLM" trả về "LLM Inevitabilism" | Algolia HN API, filter theo `top`/`new`, giới hạn 1-20 story | Trả URL fallback về `news.ycombinator.com/item?id=` khi story không có URL gốc |
| Bonus: tool mới thứ 3 — **`weather`** | `tools/weather/tool.py`, smoke test Hanoi → "Moderate or heavy rain with thunder, 31°C" | wttr.in `format=j1` trả JSON đầy đủ; hỗ trợ metric/imperial | Chỉ có current condition, không có forecast dài hạn — description nói rõ để model không dùng sai |
| Bonus: tool mới thứ 4 — **`currency`** | `tools/currency/tool.py`, smoke test 100 USD → 2,625,266.96 VND real-time | open.er-api.com free tier, ISO 3-letter code, kiểm tra `result=="success"` | Chỉ fiat (không crypto), không historical rate — description nói rõ |
| Optional built-in — `send` (Telegram) | `transcripts/v3_openrouter_20260729T162457860086.transcript.json` turn 4–5 | Dry-run `confirmed=false` trả `status=needs_confirmation`; live `confirmed=true` chờ credentials | Trong mọi `run_eval`, TELEGRAM credentials unset theo yêu cầu README |

**UI (deliverable core, không tính bonus):** Streamlit `app.py` với 5 tab — Chat, LLM vs Agent, Compare across versions, Version metrics, About. Chạy `streamlit run app.py` từ `starter_v0/`.

## B6. Reflection

- **Fixes belonged in `system_prompt.md`:** rule confirmation-before-send (v1), rule clarify-when-missing-info (v2) và xóa "guess Sam Altman"/"assume URL". Đây là các quy tắc **hành vi cấp cao** — thuộc về "làm gì khi thiếu context" — không thể ép qua tool description.
- **Fixes belonged in `tools.yaml`:** phân biệt `lookup` vs `social_search` vs `timeline` (routing), contract của `send` (bắt buộc `confirmed=true` chỉ sau clarify), contract của `clarify` (khi nào dùng `yes_no` vs `text`). Đây là **chuẩn giao tiếp** giữa model và tool — nếu để ở prompt sẽ dài dòng và dễ trôi context.
- **Failure cần manual review:**
  - R12 (send confirmation) — routing PASS ở một số run nhưng args `confirmed=true` sai; single-turn eval không phát hiện được flow correctness đầy đủ.
  - Case fetch URL 404 (turn 3 live chat) — routing correct nhưng tool execution error, cần đọc kỹ `tool_results` chứ không chỉ tin `passed=true`.
  - G05 — routing_accuracy 100% nhưng arg_accuracy fail vì `response_type` sai — nếu nhìn top-level metric sẽ bỏ sót.
- **What we'd improve next:**
  1. Chặn cứng `send` ở `agent.py` khi round trước không có `clarify(yes_no)` — không dựa vào model tuân prompt.
  2. Thêm rule "carry-over previous turn's args when user gives correction" để fix M02 regression sau v3.
  3. Thêm tool `datetime` để agent trả lời được câu "bây giờ mấy giờ" — hiện chưa có tool nào cover.
  4. Cải thiện `format` để tự động chọn `template` dựa trên context (news → sections, tweets → thread).
  5. Deploy public URL (Cloudflare Tunnel) để team khác test từ máy riêng thay vì phải chạy local.
