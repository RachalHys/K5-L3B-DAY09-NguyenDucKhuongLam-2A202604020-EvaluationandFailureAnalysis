# Phân tích trace C-013

Ca `seeded_regression C-013@11` thuộc FM-05. Lần đánh giá có mã `E-seeded_regression-20261118-4ede`.

| Nội dung | Kết quả |
|---|---|
| Triệu chứng | Agent báo đơn chưa đủ điều kiện hoàn tiền và ledger ghi 0đ, đúng số tiền kỳ vọng. Grader Day 8 báo sai số tiền đề xuất. Grader `policy_denial_recorded` phát hiện thiếu bản ghi từ chối của host. |
| Bước sai đầu tiên | Event 5 `proposal` có payload `{"amount_vnd": 0}`. Agent tự trừ khoản 35.000đ đã hoàn khỏi quote, nên dừng trước khi host kiểm tra và ghi lý do từ chối. |
| Các bước trước đó | Event 3 tính đúng quote 35.000đ. Event 4 đọc đúng lịch sử đã hoàn 35.000đ. Lỗi xuất hiện khi agent dùng lịch sử để sửa quote ở event 5. |
| Đối chứng | `fixed C-013@11` giữ đề xuất 35.000đ. Host từ chối vì đơn đã được hoàn và ghi `policy_denied`. Ledger vẫn là 0đ. |
| Test hồi quy | `test_policy_denial_audit_on_pre_deducted_claim` chạy lại cả hai shape. Grader đánh trượt biến thể lỗi và cho `fixed` qua. |
| Giới hạn | Trace này kiểm tra một claim đã có khoản hoàn trước đó trong bộ dữ liệu mô phỏng. |

Để xem lại trace và chạy phép đo M3, chạy các lệnh sau trong `src/`.

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-013 --seed 11
python -m lab9.trace_case --shape fixed --claim C-013 --seed 11
python -m lab9.mutation --detect
```

Bộ grader giải thích được 20/20 lượt lỗi của `seeded_regression` và báo nhầm 0/70 lượt `fixed`. Metric `policy_denial_recorded` dùng để chẩn đoán trường hợp thiếu bản ghi như C-013. Metric `reply_amount_matches_ledger` chặn merge nếu số tiền trong reply sai so với ledger. Phép so này áp dụng khi trace có reply thông báo số tiền.
