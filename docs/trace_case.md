# Phân tích trace C-013

Ca `seeded_regression C-013@11` minh họa lỗi trừ trước khoản đã hoàn (FM-05). Ca này nằm trong lần đánh giá `E-seeded_regression-20261118-4ede`. [Report](../src/reports/eval_seeded_regression.json)

| Nội dung | Kết quả |
|---|---|
| Triệu chứng | Agent báo đơn chưa đủ điều kiện hoàn tiền. Ledger ghi 0đ cho claim này, đúng nhãn. Grader Day 8 báo `proposal_mismatch` và `PolicyDenialRecorded` phát hiện thiếu bản ghi từ chối của host. |
| Bước sai đầu tiên | Event 5 `proposal` có payload `{"amount_vnd": 0}`. Agent tự trừ khoản 35.000đ đã hoàn khỏi quote, nên dừng trước khi host kiểm tra và ghi lý do từ chối. |
| Các bước trước đó | Event 3 tính đúng quote 35.000đ. Event 4 đọc đúng lịch sử đã hoàn 35.000đ. |
| Đối chứng | `fixed C-013@11` giữ đề xuất 35.000đ. Host từ chối vì đơn đã được hoàn và ghi `policy_denied` vào audit. Ledger vẫn không có khoản hoàn. |
| Test hồi quy | Grader kiểm tra bản ghi `policy_denied` trong audit của host. Cùng ca và seed, `seeded_regression` trượt, còn `fixed` đạt. [test_policy_denial_audit_on_pre_deducted_claim](../src/tests/test_lab9_graders.py#L70) |
| Giới hạn | Kết quả hồi quy áp dụng cho ca đã có khoản hoàn trước đó trong bộ dữ liệu mô phỏng. |

Để xem lại trace và chạy phép đo M3, chạy các lệnh sau trong `src/`.

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-013 --seed 11
python -m lab9.trace_case --shape fixed --claim C-013 --seed 11
python -m lab9.mutation --detect
```

Trong phép đo M3, các grader đánh dấu cả 20 lượt lỗi của `seeded_regression` và không báo nhầm ở 70 lượt `fixed`. Metric `policy_denial_recorded` theo dõi bản ghi từ chối của host. Metric `reply_amount_matches_ledger` chặn merge nếu số tiền báo trong reply khác số tiền đã ghi vào ledger.
