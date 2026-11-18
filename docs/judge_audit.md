# Judge audit

Hai tiêu chí được hiệu chuẩn trên dữ liệu replay công khai. Chạy các lệnh sau trong `src/`.

```bash
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Lớp dương là `FAIL`. Ngưỡng sử dụng là κ ≥ 0,6, precision ≥ 0,8 và recall ≥ 0,7.

| Tiêu chí | n | κ | Precision | Recall | TP / FP / FN / TN | Quyết định |
|---|---:|---:|---:|---:|---|---|
| `tone_ok` | 100 | 0,757 | 0,857 | 0,800 | 24 / 4 / 6 / 66 | Đạt ba ngưỡng, dùng để chấm giọng điệu |
| `helpful` | 100 | 0,375 | 1,000 | 0,300 | 9 / 0 / 21 / 70 | Trượt κ và recall, loại khỏi gate |

Judge đánh dấu FAIL ở 28% ca `tone_ok` và 9% ca `helpful`. Hiệu chỉnh Rogan–Gladen đưa cả hai về 30% khi dùng độ nhạy và độ đặc hiệu từ chính bộ replay. Phép hiệu chỉnh áp dụng cho tỉ lệ chung. Khi xét từng ca, `helpful` vẫn bỏ sót 21 lỗi.

## Audit các ca bất đồng

Các nhận định dựa trên nội dung phản hồi và ghi chú của từng ca. Cột nhãn người lấy từ bộ replay.

| Ca | Judge | Nhãn người | Nhận định và bằng chứng | Đề xuất sửa rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Người đúng. Cách xưng “em” đi cùng “nha” và “check giúp em” quá suồng sã với phản hồi khiếu nại. | Thêm ví dụ đối chiếu giữa xưng hô chuẩn của CS và các cụm quá thân mật. |
| H-029 | PASS | FAIL | Người đúng. Câu “không cần nhắn thêm” có giọng ra lệnh dù mở đầu bằng “Dạ, vui lòng”. | Chấm giọng điệu của toàn câu. Thêm ví dụ lời đề nghị chờ lịch sự và lời ngăn khách liên hệ tiếp. |
| H-042 | FAIL | PASS | Người đúng. Phản hồi ngắn nhưng lịch sự, có số tiền và thời gian dự kiến, trong khi ghi chú cho biết judge phạt vì thiếu lời xin lỗi. | Cho phép phản hồi ngắn, đúng mực. Chỉ yêu cầu lời xin lỗi khi tình huống trong rubric cần. |
| H-051 | FAIL | PASS | Người đúng. Cách gọi “refund” được CS LogiX chấp nhận theo ghi chú của case. | Liệt kê thuật ngữ CS được phép và đánh giá mức dễ hiểu của cả câu. |
| H-063 | PASS | FAIL | Người đúng theo ghi chú về kết quả hệ thống. Câu trả lời tự hứa hoàn thêm ngoài phần đã được xác nhận. | Đưa cam kết hoàn thêm vào tiêu chí đúng nghiệp vụ và đối chiếu với trạng thái do host xác nhận. |
| H-081 | FAIL | PASS | Ghi chú cho biết người chấm đọc nhầm ticket và judge đúng. Cần ticket gốc để xác nhận lại. | Đối chiếu đúng ticket trước khi chốt nhãn. |
| HL-015 | PASS | FAIL | Người đúng theo bằng chứng trong ghi chú. Reply báo 55.000đ, ledger ghi 40.000đ. | Dùng phép so sánh số tiền bằng code và yêu cầu kết quả khớp ledger trước khi chấm tính hữu ích. |
| HL-016 | PASS | FAIL | Người đúng theo ghi chú. Reply xin lỗi dài nhưng báo 55.000đ, ledger ghi 35.000đ. | Thêm cặp ví dụ reply lịch sự nhưng sai tiền và reply ngắn báo đúng tiền. Chấm lễ phép ở tiêu chí tone. |
| HL-047 | PASS | FAIL | Người đúng theo chuẩn xưng hô trong CSV. Reply mở đầu “Ok bạn” và chỉ nói đơn đã “xử lý rồi”. | Đưa xưng hô về tiêu chí tone. Với tính hữu ích, yêu cầu nêu kết quả cụ thể hoặc bước tiếp theo. |

## Kết luận

Judge `helpful` chỉ phát hiện 9 trong 30 ca FAIL, dù cả 9 cảnh báo đều đúng theo nhãn người. Trong 21 ca bị bỏ sót có 18 ca sai tiền và 3 ca sai xưng hô. Vì vậy, loại `helpful` khỏi gate và tiếp tục chấm số tiền và phê duyệt bằng code. Có thể dùng `tone_ok` để chấm giọng điệu trong phạm vi bài lab.

Kết quả dựa trên nhãn replay công khai, gồm cả ca H-081 cần đối chiếu lại. Cần một tập kiểm tra mới có ticket, ledger và nhãn người độc lập để đánh giá rubric đã sửa.
