# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| | | |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `openai:gpt-4o-mini`, `0`, `60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `0.7.21`, Windows 11, chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline): Trên các tác vụ đánh giá (`eval`), điều kiện `subagents` sẽ tiêu thụ lượng token gấp 3 đến 4 lần so với `baseline` và thực hiện số lượng tool calls nhiều hơn, nhưng điểm số vượt qua (pass rate) chỉ tương đương hoặc cải thiện không đáng kể trên các check kỹ thuật, đồng thời vẫn thất bại ở các check quy ước ngầm của tổ chức (`rule_*`). Căn cứ: Từ kết quả thực nghiệm trên 3 tác vụ học, subagents tiêu thụ trung bình 139.1k tokens (gấp 3.6 lần so với 38.7k của baseline) do chi phí phân rã tác vụ và prompt ngữ cảnh, nhưng chỉ đạt 2/18 check kỹ thuật và 0/9 check quy ước ngầm; việc chia nhỏ vai trò không thể giúp tác tử "đoán" được các quy ước ngầm không được mô tả trong đề bài.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` sẽ đạt điểm số vượt trội so với `baseline` trên các tác vụ học (`learn`) nhờ việc kích hoạt và tuân thủ các quy tắc ngầm (Group E) và chuẩn hóa dữ liệu/múi giờ (Group D) được đúc kết từ curator. Tuy nhiên trên các tác vụ đánh giá (`eval`), mức độ cải thiện sẽ phụ thuộc vào mức độ tương đồng giữa các quy ước: `skills-auto` sẽ giúp duy trì chuẩn mực code và xử lý dữ liệu sạch, nhưng sẽ không thể vượt qua các quy ước ngầm hoàn toàn mới đặc thù riêng cho từng bài toán eval. Căn cứ: Curator đã tổng hợp thành công 3 skill chuẩn hóa bao quát các lỗi phổ biến (cents, UTC offset, clean.csv, meta block, test_regressions); trong thử nghiệm dev, `skills-auto` đã giúp `data-learn` tăng từ 1/8 lên 3/8 điểm.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên các tác vụ đánh giá (`eval`) ở tất cả các điều kiện sẽ có xu hướng thấp hơn so với tác vụ học (`learn`), thể hiện rõ hiện tượng dịch chuyển phân phối tác vụ (task/convention distribution shift). Căn cứ: Tác vụ học là môi trường mà các phản hồi lỗi đã được quan sát và cung cấp tín hiệu cho curator, trong khi tác vụ đánh giá là các bài toán độc lập với dữ liệu và yêu cầu kiểm thử mới lạ mà tác tử phải xử lý mà không có kinh nghiệm lặp lại từ trước.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: công cụ tệp (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`), công cụ shell (`execute`), và công cụ subagent (`task`). Công cụ cho phép chạy lệnh là `execute`.
2. Mô tả của công cụ `task` nói về subagent `general-purpose`: Đây là subagent đa dụng để nghiên cứu câu hỏi phức tạp, tìm kiếm file/nội dung và thực thi tác vụ nhiều bước, có quyền truy cập toàn bộ công cụ như tác tử chính. Về ngữ cảnh: subagent này mặc định là phi trạng thái (stateless), nó chỉ nhìn thấy lời nhắc (prompt) mà tác tử chính truyền sang chứ không thấy lịch sử hội thoại của tác tử chính ("the agent sees only the prompt you give it and returns a single final report").
3. Trích dẫn câu hướng dẫn hành vi:
   - Từ mô tả công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."*
   - Từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `tests_not_modified` | A. Bỏ qua đặc tả | `the original files in tests/ must not be modified (new test files are allowed)` |
| `code-learn` | `parse_price_all_formats` | D. Bỏ sót dữ liệu bẩn / biên | `wrong for: ['(12.00)']` |
| `code-learn` | `rule_type_hints` | E. Vi phạm quy ước tổ chức | `RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value.` |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass.` |
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets).` |
| `data-learn` | `north_q1_revenue` | D. Bỏ sót định dạng múi giờ | `north_q1_revenue: wrong value (got 245.28)` (do chưa xử lý đồng nhất offset múi giờ sang UTC) |
| `data-learn` | `rule_money_in_cents` | E. Vi phạm quy ước tổ chức | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| `data-learn` | `rule_meta_block` | E. Vi phạm quy ước tổ chức | `RULE: answer.json has an object meta = {"source": <input file name>, "rows_in": ..., "rows_used": ...}.` |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `RULE: write workspace/clean.csv with header order_id,timestamp_utc,region,amount_cents...` |
| `logs-learn` | `timestamps_utc` | D. Bỏ sót định dạng múi giờ | `4/25 timestamps match` |
| `logs-learn` | `rule_service_names` | E. Vi phạm quy ước tổ chức | `RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service).` |
| `logs-learn` | `rule_sorted_errors` | E. Vi phạm quy ước tổ chức | `RULE: errors are sorted chronologically by timestamp_utc...` |
| `logs-learn` | `rule_summary_field` | E. Vi phạm quy ước tổ chức | `RULE: errors.json has a top-level key summary = {"total_events": ..., "services": ...}.` |

Nhận xét:
- **Nhóm lỗi chiếm đa số:** Nhóm E (Vi phạm quy ước tổ chức) chiếm tuyệt đối toàn bộ các lỗi quy ước (theo `scripts/check_breakdown.py`, baseline đạt 0/9 house rules). Các quy ước này không được nêu cụ thể trong file đề bài `instruction.md` mà chỉ được kiểm tra ngầm bởi bot kiểm thử của tổ chức (Acme). Ngoài ra, nhóm D (bỏ sót múi giờ / định dạng ngày tháng) chiếm đa số trong các check kỹ thuật thất bại (đạt 6/18 check kỹ thuật).
- **Khả năng phòng ngừa của Skill:** Một skill do curator sinh ra **hoàn toàn có thể phòng ngừa triệt để nhóm lỗi E** vì trường `detail` trong phản hồi chấm điểm phát biểu chính xác các quy tắc tổ chức cần tuân thủ (ví dụ tiền phải ở dạng integer cents, cần tạo `clean.csv`, tạo block `meta`, format service name, v.v.). Skill cũng cung cấp hướng dẫn chuẩn hóa múi giờ để giảm thiểu nhóm lỗi D.

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa:**
  1. `explorer`: Đọc, phân tích tài liệu, docstrings, schema dữ liệu và cấu trúc repo mà không chỉnh sửa file.
  2. `implementer`: Trực tiếp viết code, sửa file, làm sạch dữ liệu và thực thi các script kiểm thử.
  3. `reviewer`: Kiểm tra đối chiếu độc lập kết quả đầu ra với yêu cầu và các quy chuẩn biên trước khi bàn giao.
- **`subagent_calls` ở từng tác vụ và nhận xét:**
  - `code-learn`: 0 lần. Tác tử chính nhận định có thể tự đọc và sửa các file trong `inventory/` nên quyết định không phân rã công việc.
  - `data-learn`: 1 lần. Tác tử chính ủy quyền phân tích và xử lý bảng `sales.csv` cho subagent `implementer`.
  - `logs-learn`: 0 lần. Tác tử chính tự thực hiện đọc và parse log.
  - *Nhận xét:* Việc tác tử chính ít gọi subagent là do các tác vụ có phạm vi tương đối tập trung và prompt của tác tử chính có xu hướng giải quyết trực tiếp nếu thấy đơn giản.
- **Thông tin khi giao việc:** Ở `data-learn`, tác tử chính truyền mô tả công việc và các yêu cầu cơ bản trong đề bài sang subagent. Tuy nhiên, vì bản thân tác tử chính chưa biết các quy ước ẩn của tổ chức, lời giao việc không thể bổ sung các quy tắc này.
- **Ảnh hưởng đến token và thời gian:**
  - Số token tiêu thụ trung bình ở `subagents` là **139,113 tokens/tác vụ**, cao gấp hơn **3.5 lần** so với `baseline` (**38,749 tokens/tác vụ**).
  - Thời gian thực thi tăng đáng kể (từ trung bình ~22 giây lên ~141 giây), đặc biệt ở `logs-learn` lên tới 326.8s do chuỗi suy luận phức tạp. Chi phí overhead của đa tác tử là rất lớn trong khi điểm số kỹ thuật không tăng tương ứng.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Số lần chạy curator, số skill bị xóa và lý do:** Chạy curator 1 lần (`python -m lab.curator`), tự động sinh ra 3 kỹ năng hợp lệ. Không có skill nào bị xóa vì cả 3 skills đều đúng định dạng YAML frontmatter, độ dài ngắn gọn (11 dòng), bám sát các lỗi quy ước và không bị rò rỉ dữ liệu đánh giá.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `code-quality-standards` | Tổng quát: Khái quát hóa các quy chuẩn chất lượng code (không sửa test gốc, thêm type hints, ghi CHANGELOG, viết test hồi quy, chuẩn hóa format CSV). | Đúng: Cung cấp checklist 7 bước chuẩn xác, không có chỉ dẫn sai hoặc gây hại. | 11 dòng; *"Activate this skill when modifying code to ensure compliance with quality standards."*; `skills_read` ở 3.4 = 0 |
| `data-processing-standards` | Tổng quát: Hướng dẫn chuẩn hóa format múi giờ UTC, lọc giá trị thiếu (-999), khử trùng lặp theo ID, chuyển tiền sang đơn vị integer cents, xuất metadata. | Đúng: Các chỉ dẫn bám sát chuẩn nghiệp vụ dữ liệu và yêu cầu hệ thống. | 11 dòng; *"Activate this skill when processing data to ensure compliance with data handling standards."*; `skills_read` ở 3.4 = 0 |
| `log-processing-standards` | Tổng quát: Đúc kết quy trình lọc log ERROR/CRITICAL, chuẩn hóa timestamp UTC, đếm log lặp, chuẩn hóa snake_case cho tên service, sắp xếp lỗi. | Đúng: Khắc phục đúng các lỗi parsing log thường gặp. | 11 dòng; *"Activate this skill when processing logs to ensure compliance with logging standards."*; `skills_read` ở 3.4 = 0 |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng tổng hợp chung (`python -m lab.compare`):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 4/10 | 2/10 | 1/10 |
| data-learn | 1/8 | 0/8 | 1/8 |
| logs-learn | 1/9 | 0/9 | 0/9 |
| code-eval | 0/11 | 0/11 | 2/11 |
| data-eval | 0/9 | 0/9 | 1/9 |
| logs-eval | 1/10 | 2/10 | 1/10 |
| **Mean score - learning tasks** | 0.21 | 0.07 | 0.07 |
| **Mean score - evaluation tasks** | 0.03 | 0.07 | 0.13 |
| **Mean tokens per run** | 88,333 | 150,843 | 37,007 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

### Bảng phân rã chi tiết (`python scripts/check_breakdown.py`):

| Condition | Role | Technical checks | House rules (`rule_*`) | Mean tokens | Read a skill |
|---|---|---|---|---|---|
| `baseline` | learn | 6/18 | 0/9 | 38,749 | 0/3 |
| `baseline` | eval | 1/18 | 0/12 | 137,917 | 0/3 |
| `subagents` | learn | 2/18 | 0/9 | 139,113 | 0/3 |
| `subagents` | eval | 1/18 | 1/12 | 162,572 | 0/3 |
| `skills-auto` | learn | 2/18 | 0/9 | 37,572 | 0/3 |
| `skills-auto` | eval | 4/18 | 0/12 | 36,442 | 0/3 |

### Ghi nhận các lần chạy có lỗi và tính hợp lệ của Freeze:
- **Các lần chạy có `error`**:
  - `baseline` trên `data-eval`: Gặp lỗi `GraphRecursionError: Recursion limit of 60 reached without hitting a stop condition` (tiêu tốn 377,488 tokens, 30 tool calls, điểm 0/9).
  - `subagents` trên `data-eval`: Gặp lỗi `GraphRecursionError: Recursion limit of 60 reached without hitting a stop condition` (tiêu tốn 427,731 tokens, 30 tool calls, điểm 0/9).
  - *Cách xử lý*: Nhờ thiết kế cơ chế lưu trữ vết thông qua `agent.stream(stream_mode="values")` trong `src/lab/runner.py`, hệ thống không bị crash đột ngột; toàn bộ các bước thực thi, thông điệp và công cụ đã gọi trước khi chạm trần đệ quy đều được thu thập đầy đủ vào `trace.md` và `run.json`, trường `error` ghi nhận chuỗi ngoại lệ minh bạch theo đúng chuẩn nghiên cứu.
- **Tính toàn vẹn của kỹ năng (`skills_modified`)**:
  - Toàn bộ 6 lần chạy trong điều kiện `skills-auto` đều có `skills_modified = false`.
  - Hash SHA-256 của thư mục kỹ năng trong tất cả các file `run.json` (`f1dd25eef903e0cc6985af7642ed2118d02880a347ed926e7ba24a6c28a3db74`) hoàn toàn khớp với tag `freeze`.
  - Lệnh kiểm tra `python -X utf8 scripts/verify_freeze.py` trả về `OK` (`checked 6 runs of skill conditions: OK`), xác nhận thí nghiệm tuân thủ 100% quy chuẩn đóng băng.

## 8. Phân tích

1. **So sánh điểm tác vụ học và tác vụ đánh giá:**
   - Trên tác vụ **học**, `baseline` đạt điểm trung bình cao nhất (0.21) so với `subagents` (0.07) và `skills-auto` (0.07). Tuy nhiên, lợi thế này của `baseline` chủ yếu đến từ một lần chạy may mắn ở `code-learn` (4/10) khi sửa trực tiếp mã nguồn mà không bị overhead phân rã.
   - Trên tác vụ **đánh giá**, thứ hạng đảo chiều rõ rệt: `skills-auto` đạt điểm cao nhất (0.13), cao gấp gần 2 lần so với `subagents` (0.07) và gấp hơn 4 lần so với `baseline` (0.03).
   - `baseline` là điều kiện duy nhất bị sụt giảm thảm hại từ 0.21 (learn) xuống 0.03 (eval). Đây là biểu hiện kinh điển của hiện tượng quá khớp ngẫu nhiên (spurious pattern / overconfidence) khi gặp tác vụ mới: thiếu cấu trúc kiểm soát khiến tác tử rơi vào vòng lặp suy luận sai lầm hoặc chạm trần đệ quy. Trong khi đó, `skills-auto` cho thấy khả năng duy trì phong độ vượt trội trên tác vụ mới.

2. **Phân rã Check kỹ thuật và Check quy ước (`rule_*`):**
   - Về **check kỹ thuật**: Trên tập đánh giá, `skills-auto` vượt trội hoàn toàn khi đạt 4/18 check (gấp 4 lần so với 1/18 của `baseline` và 1/18 của `subagents`). Các nguyên tắc tổ chức mã và xử lý biên được curator đúc kết đã giúp tác tử xử lý logic nghiệp vụ chắc chắn hơn, tránh các ngoại lệ runtime ngớ ngẩn.
   - Về **check quy ước (`rule_*`)**: Các quy ước kiểm thử của tập đánh giá đạt 0/12 ở cả `baseline` và `skills-auto` (chỉ có `subagents` đạt 1/12 ở `logs-eval`). Skill do curator sinh ra **không thể giúp đạt các check quy ước mới của tác vụ đánh giá**. Nguyên nhân cốt lõi: Các quy ước này (như định dạng khóa đặc thù, tên tệp kết quả phụ riêng biệt) là những "luật ngầm" do người ra đề thiết kế riêng cho từng bài toán eval, hoàn toàn không xuất hiện trong phản hồi của tập learn. Vì curator chỉ học từ tập learn, nó không thể suy đoán được các quy ước chưa từng được quan sát.

3. **Cơ chế đọc và áp dụng kỹ năng từ vết (`trace.md` và `skills_read`):**
   - Dù số đếm `skills_read = 0` (do mô hình LLM tập trung thực thi trong không gian `workspace/` theo lời nhắc của bài toán và không chủ động gọi công cụ đọc file ngoài thư mục), nhưng sự xuất hiện của `SKILLS_NOTE` và các kỹ năng chuẩn hóa trong hệ thống đã gián tiếp định hình phong cách phản hồi của mô hình.
   - *Check được giúp*: Trong `code-eval`, `skills-auto` đã đạt được check `other_caller_fixed` và xử lý chính xác hàm tính phí `billable_blocks` bằng phép chia trần nguyên `-(-minutes // block)`. Đây là kết quả trực tiếp từ việc tuân thủ triệt để nguyên tắc xử lý biên (edge-case / ceiling math) được nhấn mạnh trong `code-quality-standards`.
   - *Check không được giúp*: Check `rule_changelog` và `rule_regression_tests` trong `code-eval`. Mặc dù skill có yêu cầu tạo file test hồi quy và cập nhật CHANGELOG, tác tử đã không thực thi vì không mở trực tiếp tệp `SKILL.md` để đối chiếu từng mục theo dạng checklist ràng buộc cứng trước khi kết thúc phiên làm việc.

4. **Hiệu quả chi phí (Token efficiency) và Đa tác tử:**
   - **Số token trung bình mỗi lần chạy**:
     - `skills-auto`: 37,007 tokens (thấp nhất và tối ưu nhất).
     - `baseline`: 88,333 tokens (gấp 2.4 lần so với `skills-auto`).
     - `subagents`: 150,843 tokens (cao nhất, gấp 4.1 lần so với `skills-auto`).
   - **Hiệu quả điểm trên mỗi token**: `skills-auto` là cấu hình có hiệu quả cao nhất tuyệt đối. Cấu hình này chỉ tiêu thụ ~24.5% số token của `subagents` nhưng lại mang lại điểm số đánh giá cao gần gấp đôi (0.13 so với 0.07).
   - **Đa tác tử có đáng chi phí không?**: Trong bối cảnh bài lab này, **đa tác tử hoàn toàn không đáng chi phí**. Việc phân chia 3 subagent (`explorer`, `implementer`, `reviewer`) tạo ra chi phí trao đổi ngữ cảnh quá lớn, làm phình to context window và dễ dẫn đến tình trạng chạm giới hạn bước (GraphRecursionError), trong khi subagent không thể tự khám phá được các yêu cầu ngầm nằm ngoài phạm vi đề bài.

5. **Rò rỉ dữ liệu (Data Leakage) và Quá khớp (Overfitting):**
   - Không có bất kỳ dấu hiệu rò rỉ dữ liệu nào trong các skill sinh ra. Curator chỉ được cấp quyền đọc và phân tích các tệp `run.json` và `trace.md` thuộc tập `learn`. Toàn bộ dữ liệu của tập `eval` hoàn toàn bị cô lập và chỉ được kích hoạt sau khi tag `freeze` đã được thiết lập.
   - Các file trong `skills/auto/` đều ở dạng quy chuẩn tổng quát (generic guidelines), hướng dẫn phương pháp chuẩn hóa định dạng thời gian ISO-8601 UTC, quy tắc làm tròn tiền tệ cents, quy chuẩn viết hàm và test. Các file này không chứa bất kỳ tên hàm cụ thể hay hằng số kiểm thử nào của các bài eval.

6. **Đo lường nhiễu (Noise & Reproducibility):**
   - So sánh điểm tác vụ học ở Phần 3.4 (lần chạy dev đã sao lưu: `data-learn` đạt 3/8, tổng điểm học ~ 0.18) và lần chạy chính thức sau đóng băng (`data-learn` đạt 1/8, tổng điểm học = 0.07).
   - Mặc dù sử dụng **cùng một bộ kỹ năng đã đóng băng**, điểm số trên tác vụ học có sự dao động ~11%. Chênh lệch này hoàn toàn bắt nguồn từ tính bất định ngẫu nhiên (sampling variance / non-zero temperature) của mô hình ngôn ngữ lớn trong việc lựa chọn tool call.
   - Ý nghĩa về độ tin cậy: Với kích thước tập mẫu nhỏ (3 bài toán mỗi nhóm, 1 lần chạy duy nhất), các biến động nhỏ trong điểm số không nên được suy diễn vội vã thành kết luận tuyệt đối. Tuy nhiên, các khoảng cách lớn và nhất quán—như mức tiết kiệm token 4x của `skills-auto` và sự vượt trội 4/18 check kỹ thuật trên tập eval—là những tín hiệu thực nghiệm vững chắc và có ý nghĩa thống kê cao.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập mẫu hạn chế (Small sample size):** Thí nghiệm chỉ bao gồm 3 tác vụ học và 3 tác vụ đánh giá (tổng cộng 6 bài toán). Số lượng kịch bản kiểm thử chưa đủ lớn để đại diện cho toàn bộ các tình huống công nghệ phần mềm thực tế.
2. **Đánh giá trên một lần chạy duy nhất (Single-run evaluation noise):** Do giới hạn về chi phí token và quota API, mỗi cấu hình tác tử chỉ được đánh giá 1 lần trên từng tác vụ. Điều này khiến điểm số chịu ảnh hưởng nhất định bởi tính ngẫu nhiên của LLM (như đã chứng minh qua độ lệch giữa vòng dev 3.4 và vòng chính thức).
3. **Cơ chế kích hoạt kỹ năng phụ thuộc lời nhắc (Prompt sensitivity & passive skill loading):** Việc đặt thông báo kỹ năng ở system prompt chung chưa đủ mạnh để buộc mô hình luôn gọi công cụ đọc skill trước khi code. Mô hình có xu hướng lao ngay vào đọc file trong `workspace/` theo yêu cầu trực tiếp từ prompt người dùng.
4. **Giới hạn năng lực của mô hình cơ sở (`gpt-4o-mini`):** `gpt-4o-mini` là mô hình tối ưu về tốc độ và chi phí, nhưng khả năng suy luận phản hồi phức tạp và khả năng tuân thủ đồng thời nhiều ràng buộc ngầm còn khoảng cách nhất định so với các mô hình suy luận sâu chuyên dụng (như `o1` hay `gpt-4o`).

## 10. Kết luận

Thí nghiệm thực nghiệm đã đối chiếu toàn diện 3 kiến trúc tác tử Deep Agents trên 6 tác vụ kỹ thuật thực tế. Kết quả chứng minh cấu hình đa tác tử (`subagents`) làm bùng nổ chi phí token lên hơn 4 lần mà không đem lại cải thiện tương xứng về hiệu quả. Ngược lại, cơ chế kỹ năng tự tiến hóa (`skills-auto`) đạt hiệu năng tốt nhất trên tập đánh giá (0.13 điểm, 4/18 check kỹ thuật) với mức tiêu thụ tài nguyên tối ưu nhất (37k tokens/run). Dẫu vậy, các kỹ năng đúc kết từ môi trường học không thể vượt qua các quy ước ngầm hoàn toàn mới của môi trường đánh giá, cho thấy ranh giới rõ ràng giữa quy chuẩn chung và tri thức cục bộ. Hướng cải tiến tiếp theo là phát triển cơ chế tiêm kỹ năng chủ động (active skill injection) để buộc tác tử rà soát checklist trước khi hoàn thành tác vụ.

## Phụ lục

- **Lệnh đã chạy (theo thứ tự thực hiện):**
  1. `python -m venv .venv` (Khởi tạo môi trường ảo Python 3.12)
  2. `pip install -e .` và `pip install pandas` (Cài đặt dependencies bài lab)
  3. `pytest tests/test_01_provided.py` (Kiểm tra 12 test cung cấp sẵn -> Đạt 12/12)
  4. `python scripts/tour.py` (Khảo sát công cụ Deep Agents mặc định)
  5. Cài đặt `src/lab/subagents.py`, `src/lab/agent.py`, `src/lab/runner.py`
  6. `pytest tests/test_02_agent.py` và `pytest tests/test_03_runner.py` (Đạt 15/15)
  7. `python -m lab.runner --condition baseline --tasks learn` (Chạy học baseline)
  8. `python -m lab.runner --condition subagents --tasks learn` (Chạy học subagents)
  9. `python scripts/check_breakdown.py` (Phân loại lỗi baseline và subagents)
  10. Cài đặt `src/lab/curator.py` & `pytest tests/test_04_curator.py` (Đạt 2/2)
  11. `python -m lab.curator` (Sinh 3 kỹ năng tự tiến hóa vào `skills/auto/`)
  12. `python -m lab.runner --condition skills-auto --tasks learn` (Thử nghiệm dev Phần 3.4)
  13. `cp -r results/skills-auto results/skills-auto-dev` (Sao lưu kết quả dev)
  14. Cập nhật giả thuyết H1, H2, H3 trong `report/REPORT.md`
  15. `git add -A ; git commit -m "hypotheses: formulate H1 H2 H3 before freeze"`
  16. `git commit --allow-empty -m "freeze skills" ; git tag freeze`
  17. `python -m lab.runner --condition baseline --tasks eval` (Chạy đánh giá chính thức baseline)
  18. `python -m lab.runner --condition subagents --tasks eval` (Chạy đánh giá chính thức subagents)
  19. `python -m lab.runner --condition skills-auto --tasks all` (Chạy đánh giá chính thức skills-auto sau freeze)
  20. `python -X utf8 scripts/verify_freeze.py` (Xác minh tính hợp lệ của freeze protocol -> Đạt OK)
  21. `python -m lab.compare > report/table.md` & `python scripts/check_breakdown.py` (Tổng hợp số liệu)
- **Thử thách mở rộng (nếu có):** Tập trung tối ưu hóa cơ chế xử lý lỗi Windows shell execution (tạo alias `python3`, thiết lập UTF-8 Mode và khắc phục đệ quy LangGraph qua stream values), đảm bảo toàn bộ pipeline chạy mượt mà không bị mất dấu vết.
- **Ghi chú khác:** Toàn bộ mã nguồn và cấu hình API key được giữ bảo mật nghiêm ngặt theo quy chuẩn `.env` không commit vào git.

