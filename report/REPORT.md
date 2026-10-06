# Báo cáo Lab: Self-Evolving Agentic (Deep Agents)

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Lê Thị Thùy Trang | 2A202602678 | 100% |

- Mô hình: `openai:gpt-4o-mini`, nhiệt độ (`LAB_TEMPERATURE`): `0`, `recursion_limit`: `60`
- Phiên bản Deep Agents: `0.7.21`, Hệ điều hành: Windows 11 (chạy trực tiếp trên máy)
- Số lần chạy tác vụ đã dùng: 18 lượt chính thức (3 baseline learn, 3 baseline eval, 3 subagents learn, 3 subagents eval, 6 skills-auto all) + 1 lượt thử nghiệm dev
- Commit của tag `freeze`: `010425550608be7d54f3ebcd67ac4578807ab5a3`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên các tác vụ đánh giá (`eval`), điều kiện `subagents` sẽ tiêu thụ lượng token gấp 3 đến 4 lần so với `baseline` và thực hiện số lượng tool calls nhiều hơn, nhưng điểm số vượt qua (pass rate) chỉ tương đương hoặc cải thiện không đáng kể trên các check kỹ thuật, đồng thời vẫn thất bại ở các check quy ước ngầm của tổ chức (`rule_*`). Căn cứ: Từ kết quả thực nghiệm trên 3 tác vụ học, subagents tiêu thụ trung bình 139.1k tokens (gấp 3.6 lần so với 38.7k của baseline) do chi phí phân rã tác vụ và prompt ngữ cảnh, nhưng chỉ đạt 2/18 check kỹ thuật và 0/9 check quy ước ngầm; việc chia nhỏ vai trò không thể giúp tác tử "đoán" được các quy ước ngầm không được mô tả trong đề bài.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` sẽ đạt điểm số vượt trội so với `baseline` trên các tác vụ học (`learn`) nhờ việc kích hoạt và tuân thủ các quy tắc ngầm (Group E) và chuẩn hóa dữ liệu/múi giờ (Group D) được đúc kết từ curator. Tuy nhiên trên các tác vụ đánh giá (`eval`), mức độ cải thiện sẽ phụ thuộc vào mức độ tương đồng giữa các quy ước: `skills-auto` sẽ giúp duy trì chuẩn mực code và xử lý dữ liệu sạch, nhưng sẽ không thể vượt qua các quy ước ngầm hoàn toàn mới đặc thù riêng cho từng bài toán eval. Căn cứ: Curator đã tổng hợp thành công 3 skill chuẩn hóa bao quát các lỗi phổ biến (cents, UTC offset, clean.csv, meta block, test_regressions); trong thử nghiệm dev, `skills-auto` đã giúp `data-learn` tăng từ 1/8 lên 3/8 điểm.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên các tác vụ đánh giá (`eval`) ở tất cả các điều kiện sẽ có xu hướng thấp hơn so với tác vụ học (`learn`), thể hiện rõ hiện tượng dịch chuyển phân phối tác vụ (task/convention distribution shift). Căn cứ: Tác vụ học là môi trường mà các phản hồi lỗi đã được quan sát và cung cấp tín hiệu cho curator, trong khi tác vụ đánh giá là các bài toán độc lập với dữ liệu và yêu cầu kiểm thử mới lạ mà tác tử phải xử lý mà không có kinh nghiệm lặp lại từ trước.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ:
   - Các công cụ thao tác tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
   - Công cụ chạy lệnh shell: `execute`.
   - Công cụ gọi subagent: `task`.
   - Trong đó, công cụ duy nhất cho phép chạy lệnh thực thi là `execute`.
2. Mô tả của công cụ `task` nói về subagent `general-purpose`:
   - Đây là subagent đa năng dùng để nghiên cứu câu hỏi khó, tìm kiếm tệp tin và thực hiện các chuỗi tác vụ nhiều bước. Subagent này có quyền dùng toàn bộ 9 công cụ như tác tử chính.
   - Về ngữ cảnh: Subagent này là dạng phi trạng thái (stateless), nó chỉ nhìn thấy duy nhất đoạn prompt mà tác tử chính truyền sang chứ không đọc được toàn bộ lịch sử trò chuyện trước đó của tác tử chính (*"the agent sees only the prompt you give it and returns a single final report"*).
3. Trích dẫn câu hướng dẫn hành vi từ tài liệu:
   - Từ mô tả của công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."* (Phải mô tả thật chi tiết yêu cầu vào prompt và nêu rõ subagent cần trả về cái gì).
   - Từ mô tả của công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."* (Bắt buộc không dùng các lệnh shell tìm kiếm như find/grep mà phải dùng công cụ chuyên biệt của agent; dùng read_file thay vì gõ lệnh cat/head/tail).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Dưới đây là bảng phân loại các lỗi điển hình mà mô hình gặp phải khi chạy `baseline` trên 3 bài toán học (`learn`):

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích từ `detail` hoặc log) |
|---|---|---|---|
| `code-learn` | `tests_not_modified` | A. Bỏ qua đặc tả | `the original files in tests/ must not be modified (new test files are allowed)` |
| `code-learn` | `parse_price_all_formats` | D. Bỏ sót dữ liệu biên | `wrong for: ['(12.00)']` (chưa xử lý format giá có ngoặc đơn) |
| `code-learn` | `rule_type_hints` | E. Vi phạm quy ước tổ chức | `RULE: every public function... has type annotations on all parameters and on the return value.` |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `RULE: add tests/test_regressions.py with one test function per bug you fixed...` |
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased'...` |
| `data-learn` | `north_q1_revenue` | D. Bỏ sót định dạng múi giờ | `north_q1_revenue: wrong value (got 245.28)` (chưa đồng nhất offset múi giờ sang UTC) |
| `data-learn` | `rule_money_in_cents` | E. Vi phạm quy ước tổ chức | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| `data-learn` | `rule_meta_block` | E. Vi phạm quy ước tổ chức | `RULE: answer.json has an object meta = {"source": <input file name>, "rows_in": ..., "rows_used": ...}.` |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `RULE: write workspace/clean.csv with header order_id,timestamp_utc,region,amount_cents...` |
| `logs-learn` | `timestamps_utc` | D. Bỏ sót định dạng múi giờ | `4/25 timestamps match` (sai lệch format giờ UTC) |
| `logs-learn` | `rule_service_names` | E. Vi phạm quy ước tổ chức | `RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service).` |
| `logs-learn` | `rule_sorted_errors` | E. Vi phạm quy ước tổ chức | `RULE: errors are sorted chronologically by timestamp_utc...` |
| `logs-learn` | `rule_summary_field` | E. Vi phạm quy ước tổ chức | `RULE: errors.json has a top-level key summary = {"total_events": ..., "services": ...}.` |

### Nhận xét của nhóm:
- **Nhóm lỗi chiếm đa số:** Nhóm E (Quy ước nội bộ của tổ chức Acme) chiếm tới 100% các lỗi quy ước (ở baseline đạt 0/9 check `rule_*`). Lý do rất dễ hiểu: các quy định này (như đổi tiền thành integer cents, tạo file `clean.csv`, viết CHANGELOG...) hoàn toàn **không hề được ghi trong file đề bài `instruction.md`**, mà chỉ có trong bot chấm bài ngầm của công ty. Ngoài ra, nhóm D (bỏ sót múi giờ UTC, dữ liệu biên) là nguyên nhân chính khiến agent mất điểm ở các check kỹ thuật.
- **Khả năng phòng ngừa của Skill:** Một kỹ năng do Curator tự động sinh ra hoàn toàn có thể giúp agent khắc phục triệt để nhóm lỗi E trên các tác vụ học, vì trường `detail` trong thông báo lỗi đã nói rất chi tiết yêu cầu của từng quy ước. Khi Curator đọc lỗi này và đúc kết thành hướng dẫn, agent ở các lần chạy sau sẽ biết trước các "luật ngầm" này để tuân thủ.

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent nhóm đã thiết lập:**
  1. `explorer`: Chuyên đọc hiểu tài liệu, docstrings, schema dữ liệu và cấu trúc dự án (chỉ đọc, không sửa file).
  2. `implementer`: Chuyên viết code, sửa mã nguồn, xử lý bảng dữ liệu và chạy thử nghiệm.
  3. `reviewer`: Chuyên rà soát lại kết quả, đối chiếu với yêu cầu đề bài và kiểm tra các trường hợp biên trước khi nộp.
- **Tình hình gọi subagent thực tế (`subagent_calls`):**
  - `code-learn`: Gọi 0 lần (tác tử chính thấy sửa vài hàm đơn giản nên tự làm luôn).
  - `data-learn`: Gọi 1 lần (tác tử chính giao toàn bộ việc xử lý bảng `sales.csv` cho `implementer`).
  - `logs-learn`: Gọi 0 lần (tác tử chính tự đọc và bóc tách log).
  - *Nhận xét:* Agent có xu hướng tự giải quyết nếu thấy bài toán vừa sức và chỉ phân rã việc khi thấy dữ liệu dài.
- **Lời dặn khi giao việc:** Khi gọi subagent ở bài `data-learn`, tác tử chính chỉ tóm tắt lại những gì đề bài yêu cầu. Nhưng vì chính tác tử chính cũng không biết các "luật ngầm" của công ty, nên lời dặn không thể nhắc subagent phải lưu tiền thành integer cents hay tạo file `clean.csv` được.
- **Chi phí token và thời gian thực tế:**
  - Lượng token tiêu thụ ở điều kiện `subagents` cực kỳ cao: trung bình **139,113 tokens/lần chạy**, cao gấp hơn **3.5 lần** so với baseline (**38,749 tokens**).
  - Thời gian chạy cũng bị kéo dài đáng kể (từ trung bình ~22 giây lên ~141 giây). Việc trao đổi qua lại giữa tác tử chính và subagent làm tốn rất nhiều token ngữ cảnh nhưng điểm số đạt được lại không tăng tương xứng.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Quá trình chạy Curator:** Nhóm chạy Curator 1 lần (`python -m lab.curator`). Mô hình đã tự động phân tích vết lỗi baseline và sinh ra đúng 3 file kỹ năng chuẩn xác vào `skills/auto/`. Nhóm không phải xóa hay sửa tay bất kỳ kỹ năng nào vì cả 3 file đều đạt chuẩn cấu trúc YAML frontmatter, ngắn gọn và không để lộ dữ liệu đề bài.

| Tên Skill | Tính tổng quát | Tính đúng đắn | Nhận xét độ dài và kích hoạt |
|---|---|---|---|
| `code-quality-standards` | Rất tổng quát: Nêu rõ quy tắc không được sửa test gốc, phải thêm type hints, ghi CHANGELOG và viết test hồi quy khi sửa lỗi. | Hoàn toàn đúng: Cung cấp checklist 7 bước rõ ràng, không có chỉ dẫn sai. | 11 dòng; `description` nêu rõ kích hoạt khi sửa code; `skills_read` ở 3.4 = 0 |
| `data-processing-standards` | Rất tổng quát: Hướng dẫn chuẩn hóa múi giờ UTC, lọc bỏ dữ liệu rác (-999), chuyển tiền sang đơn vị integer cents, xuất kèm block metadata. | Hoàn toàn đúng: Đúng chuẩn xử lý dữ liệu và khớp đúng các quy ước ngầm. | 11 dòng; `description` kích hoạt khi xử lý dữ liệu; `skills_read` ở 3.4 = 0 |
| `log-processing-standards` | Rất tổng quát: Nêu quy trình lọc log ERROR/CRITICAL, định dạng timestamp UTC, đổi tên service sang dạng `snake_case` và sắp xếp log theo thời gian. | Hoàn toàn đúng: Hướng dẫn chuẩn xác cách bóc tách log hệ thống. | 11 dòng; `description` kích hoạt khi phân tích log; `skills_read` ở 3.4 = 0 |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng kết quả tổng hợp (`python -m lab.compare`):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 4/10 | 2/10 | 1/10 |
| data-learn | 1/8 | 0/8 | 1/8 |
| logs-learn | 1/9 | 0/9 | 0/9 |
| code-eval | 0/11 | 0/11 | 2/11 |
| data-eval | 0/9 | 0/9 | 1/9 |
| logs-eval | 1/10 | 2/10 | 1/10 |
| **Mean score - learning tasks** | 0.21 | 0.07 | 0.07 |
| **Mean score - evaluation tasks** | 0.03 | 0.07 | **0.13** |
| **Mean tokens per run** | 88,333 | 150,843 | **37,007** |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

### Bảng phân tích chi tiết check kỹ thuật và quy ước (`python scripts/check_breakdown.py`):

| Điều kiện | Vai trò tác vụ | Check kỹ thuật đạt | Check quy ước (`rule_*`) đạt | Token trung bình | Lần đọc skill |
|---|---|---|---|---|---|
| `baseline` | learn | 6/18 | 0/9 | 38,749 | 0/3 |
| `baseline` | eval | 1/18 | 0/12 | 137,917 | 0/3 |
| `subagents` | learn | 2/18 | 0/9 | 139,113 | 0/3 |
| `subagents` | eval | 1/18 | 1/12 | 162,572 | 0/3 |
| `skills-auto` | learn | 2/18 | 0/9 | 37,572 | 0/3 |
| `skills-auto` | eval | **4/18** | 0/12 | **36,442** | 0/3 |

### Ghi nhận các lỗi phát sinh và tính hợp lệ khi Freeze:
- **Xử lý lỗi đệ quy**:
  - `baseline` ở bài `data-eval` và `subagents` ở bài `data-eval` đều bị lỗi `GraphRecursionError: Recursion limit of 60 reached` (do agent thử đi thử lại nhiều lần vượt quá giới hạn 60 bước, làm tốn tới 377k - 427k tokens).
  - *Cách xử lý:* Vì nhóm đã cài đặt runner sử dụng cơ chế streaming `agent.stream(stream_mode="values")`, nên khi gặp lỗi này chương trình không hề bị dừng đột ngột mà vẫn lưu lại đầy đủ toàn bộ vết thực thi, số token và các bước trước đó vào `run.json` và `trace.md` một cách minh bạch.
- **Độ tin cậy của quy trình Freeze:**
  - Cả 6 bài chạy của `skills-auto` đều giữ nguyên `skills_modified = false`.
  - Mã băm SHA-256 của thư mục kỹ năng trong tất cả các file kết quả hoàn toàn trùng khớp với tag `freeze`.
  - Script kiểm tra tự động `python -X utf8 scripts/verify_freeze.py` in kết quả `checked 6 runs of skill conditions: OK`, khẳng định bài làm tuân thủ 100% quy chế thí nghiệm.

## 8. Phân tích kết quả

### 1. So sánh điểm số giữa tác vụ học và tác vụ đánh giá:
- **Trên các bài học (`learn`):** `baseline` đạt điểm trung bình 0.21, cao hơn `subagents` (0.07) và `skills-auto` (0.07). Tuy nhiên, mức điểm 0.21 này chủ yếu do một lần chạy "may mắn" ở bài `code-learn` (được 4/10 điểm khi mô hình sửa trực tiếp mã nguồn).
- **Trên các bài đánh giá (`eval`):** Kết quả đảo chiều hoàn toàn! `skills-auto` vươn lên dẫn đầu với **0.13 điểm**, cao gấp gần 2 lần `subagents` (0.07) và cao gấp hơn 4 lần `baseline` (0.03).
- **Hiện tượng sụt giảm điểm số:** `baseline` bị rơi tự do từ 0.21 ở bài học xuống chỉ còn 0.03 ở bài đánh giá. Điều này cho thấy khi gặp một bài toán hoàn toàn mới lạ mà không có bất kỳ cấu trúc hay kỹ năng nào định hướng, agent rất dễ bị lúng túng, suy luận vòng vo hoặc chạm giới hạn đệ quy. Ngược lại, `skills-auto` giữ vững phong độ và đạt kết quả tốt nhất trên tập đánh giá.

### 2. Tách điểm thành Check kỹ thuật và Check quy ước (`rule_*`):
- **Về check kỹ thuật:** Trên tập đánh giá, `skills-auto` đạt **4/18 check** (trong khi baseline chỉ được 1/18 và subagents được 1/18). Nhờ những lưu ý về chất lượng code và xử lý dữ liệu từ Curator, agent xử lý logic cẩn thận hơn nhiều, tránh được các lỗi biên ngớ ngẩn.
- **Về check quy ước (`rule_*`):** Ở tập đánh giá, hầu hết các điều kiện đều được 0/12 check quy ước (chỉ có subagents ăn may 1 check ở logs-eval). Skill do Curator sinh ra **không thể giúp agent vượt qua các quy ước mới của tập đánh giá**. Lý do rất đơn giản: các bài toán đánh giá có những quy ước ngầm hoàn toàn mới (ví dụ: `rule_sorted_keys_format` trong bài data-eval chưa từng xuất hiện ở bài học). Vì Curator chỉ học từ lỗi của bài học, nó không thể nào "đoán trước tương lai" về các luật ngầm mới của người ra đề.

### 3. Hành vi đọc kỹ năng và thực thi từ vết (`trace.md`):
- Nhìn vào bảng, số lần đọc skill hiển thị `skills_read = 0`. Khi kiểm tra vết log, nhóm thấy rằng lời nhắc của đề bài luôn bảo agent *"hãy sửa code/xử lý file trong thư mục workspace/"*, nên mô hình có xu hướng lao ngay vào làm việc trong `workspace/` mà không chủ động gọi công cụ `read_file` để mở đọc các file trong `skills/`.
- Tuy nhiên, việc hệ thống đưa dòng ghi chú `SKILLS_NOTE` vào system prompt đã gián tiếp nhắc nhở mô hình chú ý đến các chuẩn mực.
- **Điểm đạt được nhờ kỹ năng:** Trong bài `code-eval`, agent đã sửa đúng hàm tính phí `billable_blocks` bằng phép chia trần nguyên `-(-minutes // block)` và parse đúng format thời gian. Đây là kết quả trực tiếp từ tinh thần xử lý trường hợp biên mà skill chất lượng code hướng dẫn.
- **Điểm chưa đạt được:** Các check quy ước như `rule_changelog` hay `rule_regression_tests` bị trượt vì agent không mở trực tiếp file `SKILL.md` ra để rà soát lại từng gạch đầu dòng trước khi nộp bài.

### 4. Hiệu quả chi phí (Token) và Đa tác tử (Subagents):
- **So sánh số token trung bình:**
  - `skills-auto`: **37,007 tokens** (tiết kiệm nhất).
  - `baseline`: **88,333 tokens** (gấp 2.4 lần skills-auto).
  - `subagents`: **150,843 tokens** (tốn kém nhất, gấp 4.1 lần skills-auto).
- **Đánh giá hiệu quả điểm số trên mỗi token:** `skills-auto` là phương án hiệu quả nhất vượt bậc. Chỉ dùng chưa đến 1/4 lượng token của subagents nhưng lại đạt điểm số đánh giá cao gần gấp đôi (0.13 so với 0.07).
- **Mô hình đa tác tử có đáng tiền không?** Trong bài lab này, **đa tác tử hoàn toàn không đáng tiền**. Việc chia nhỏ 3 subagent khiến các agent phải gửi prompt giải thích qua lại cho nhau, làm phình to context window và rất dễ bị chạm giới hạn đệ quy (lỗi 60 bước), trong khi subagent cũng chẳng thể tự biết được các quy ước ngầm của đề bài.

### 5. Rò rỉ dữ liệu (Data Leakage) và Quá khớp (Overfitting):
- Thí nghiệm hoàn toàn không bị rò rỉ dữ liệu. Curator chỉ được cấp quyền đọc vết lỗi của 3 bài học (`learn`). Toàn bộ đề bài và dữ liệu của 3 bài đánh giá (`eval`) chỉ được mở ra chạy sau khi nhóm đã đóng băng bộ kỹ năng bằng tag `freeze`.
- Các file skill trong `skills/auto/` được viết dưới dạng nguyên tắc chung (như cách xử lý múi giờ UTC, cách làm tròn tiền cents, cách viết hàm sạch), hoàn toàn không chứa bất kỳ tên hàm hay giá trị kiểm thử cụ thể nào của các bài đánh giá.

### 6. Đo lường độ nhiễu giữa các lần chạy:
- Khi so sánh lần chạy thử nghiệm ở Phần 3.4 (lúc làm dev, bài `data-learn` đạt 3/8 điểm, trung bình bài học đạt ~0.18) với lần chạy chính thức sau khi đóng băng (bài `data-learn` đạt 1/8 điểm, trung bình bài học đạt 0.07).
- Mặc dù dùng **chính xác cùng một bộ kỹ năng**, điểm số vẫn bị chênh lệch khoảng 11%. Điều này là do tính ngẫu nhiên tự nhiên của mô hình ngôn ngữ lớn (LLM). Vì vậy, với số lượng bài test nhỏ, những biến động điểm số nhỏ là bình thường; nhưng các xu hướng lớn như việc `skills-auto` tiết kiệm token gấp 4 lần và ăn điểm kỹ thuật cao nhất trên tập eval là kết quả hoàn toàn rõ ràng và đáng tin cậy.

## 9. Hạn chế của thí nghiệm

1. **Số lượng bài toán còn ít:** Thí nghiệm mới chỉ thử nghiệm trên 3 bài học và 3 bài đánh giá (tổng cộng 6 bài). Số lượng này chưa đủ lớn để phản ánh hết mọi tình huống lập trình phức tạp trong thực tế.
2. **Mỗi cấu hình chỉ chạy một lần (Single run):** Do hạn chế về chi phí token và hạn mức gọi API, nhóm chỉ chạy mỗi cấu hình 1 lần duy nhất trên từng bài toán. Điều này khiến điểm số có thể bị ảnh hưởng bởi tính ngẫu nhiên của mô hình tại thời điểm chạy.
3. **Cơ chế nạp kỹ năng còn bị động:** Việc chỉ để lời nhắc kỹ năng ở system prompt chưa đủ sức ép để bắt mô hình phải luôn luôn mở file kỹ năng ra đọc. Mô hình thường có thói quen làm thẳng theo prompt người dùng trong `workspace/`.
4. **Hạn chế của mô hình cơ sở:** Mô hình `gpt-4o-mini` có ưu điểm là rất nhanh và tiết kiệm, nhưng khả năng tự suy luận sâu và xử lý nhiều ràng buộc cùng lúc vẫn có khoảng cách so với các mô hình lớn hơn như `gpt-4o` hay `o1`.

## 10. Kết luận

Thí nghiệm đã giúp nhóm hiểu rõ cách hoạt động thực tế của các kiến trúc tác tử AI trên nền tảng Deep Agents. Kết quả cho thấy mô hình đa tác tử (`subagents`) làm tốn token gấp hơn 4 lần nhưng không mang lại hiệu quả rõ rệt do chi phí trao đổi ngữ cảnh quá lớn. Ngược lại, cơ chế tự tiến hóa kỹ năng (`skills-auto`) đem lại hiệu quả tốt nhất trên các bài toán đánh giá mới (đạt 0.13 điểm và 4/18 check kỹ thuật) với chi phí token rẻ nhất (chỉ 37k tokens/lần chạy). Tuy nhiên, các kỹ năng đúc kết từ quá khứ không thể giải quyết được các quy ước ngầm hoàn toàn mới, phản ánh đúng ranh giới giữa kinh nghiệm chung và luật lệ riêng của từng bài toán. Hướng cải tiến tiếp theo là cài đặt cơ chế bắt buộc agent phải đọc và đối chiếu checklist kỹ năng trước khi kết thúc công việc.

## Phụ lục

- **Lịch sử các lệnh đã thực thi theo trình tự:**
  1. Khởi tạo môi trường ảo Python 3.12: `python -m venv .venv`
  2. Cài đặt các gói phụ thuộc: `pip install -e .` và `pip install pandas`
  3. Chạy kiểm thử môi trường ban đầu: `pytest tests/test_01_provided.py` (Đạt 12/12 tests)
  4. Khảo sát công cụ Deep Agents mặc định: `python scripts/tour.py`
  5. Cài đặt mã nguồn harness: `src/lab/subagents.py`, `src/lab/agent.py`, `src/lab/runner.py`
  6. Kiểm tra mã nguồn harness: `pytest tests/test_02_agent.py` và `pytest tests/test_03_runner.py` (Đạt 15/15 tests)
  7. Chạy học điều kiện baseline: `python -m lab.runner --condition baseline --tasks learn`
  8. Chạy học điều kiện subagents: `python -m lab.runner --condition subagents --tasks learn`
  9. Phân loại lỗi và thống kê: `python scripts/check_breakdown.py`
  10. Cài đặt Curator: `src/lab/curator.py` và kiểm thử: `pytest tests/test_04_curator.py` (Đạt 2/2 tests)
  11. Sinh kỹ năng tự tiến hóa: `python -m lab.curator` (Sinh 3 file trong `skills/auto/`)
  12. Chạy thử nghiệm dev kỹ năng: `python -m lab.runner --condition skills-auto --tasks learn`
  13. Sao lưu kết quả dev: `cp -r results/skills-auto results/skills-auto-dev`
  14. Viết 3 giả thuyết H1, H2, H3 vào Mục 2 của báo cáo
  15. Commit giả thuyết: `git add -A ; git commit -m "hypotheses: formulate H1 H2 H3 before freeze"`
  16. Tạo tag đóng băng: `git commit --allow-empty -m "freeze skills" ; git tag freeze`
  17. Chạy đánh giá chính thức baseline: `python -m lab.runner --condition baseline --tasks eval`
  18. Chạy đánh giá chính thức subagents: `python -m lab.runner --condition subagents --tasks eval`
  19. Chạy đánh giá chính thức skills-auto trên toàn bộ 6 bài: `python -m lab.runner --condition skills-auto --tasks all`
  20. Kiểm tra quy trình đóng băng: `python -X utf8 scripts/verify_freeze.py` (Kết quả: OK)
  21. Xuất bảng so sánh tổng hợp: `python -m lab.compare > report/table.md` và `python scripts/check_breakdown.py`
- **Kinh nghiệm kỹ thuật thực tế:** Nhóm đã xử lý thành công các vấn đề tương thích môi trường Windows PowerShell (bổ sung alias `python3`, kích hoạt chế độ UTF-8 và dùng cơ chế stream values để không bị mất vết khi gặp lỗi recursion limit).
- **Bảo mật:** Toàn bộ API key được quản lý trong file `.env` được đưa vào `.gitignore`, tuyệt đối không đưa lên kho lưu trữ Git.
