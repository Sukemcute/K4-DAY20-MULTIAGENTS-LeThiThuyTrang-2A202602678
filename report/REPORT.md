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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
