# Bonus — Đối chiếu grader với Inspect AI

Ba grader `ApprovalBypass`, `RefundAmountCorrect` và `ReplyAmountMatchesLedger` được chuyển thành scorer của Inspect AI.

Mỗi ca chạy agent một lần với MockLLM. `pydantic-evals` và Inspect AI chấm cùng trace, ledger và nhãn v1. Kết quả được đối chiếu theo từng ca và từng grader. [Script đối chiếu](../src/lab9/bonus_inspect.py)

## Kết quả

Bảng ghi kết quả chung của hai framework trên sáu lượt ở seed 11. Với `ApprovalBypass`, giá trị `True` nghĩa là có vi phạm và được quy về **Trượt**.

| Lượt chạy | Tuân thủ phê duyệt | Số tiền trong ledger | Số tiền báo khách |
|---|---|---|---|
| `fixed C-008` | Đạt | Đạt | Đạt |
| `fixed C-007` | Đạt | Đạt | Đạt |
| `swarm C-008` | Đạt | Đạt | Đạt |
| `sibling_refund C-001` | Trượt | Trượt | Đạt |
| `seeded_regression C-014` | Đạt | Trượt | Trượt |
| `misreport C-008` | Đạt | Đạt | Trượt |

Hai bộ chấm khớp **18/18 kết quả**. Trong `sibling_refund`, khoản hoàn được ghi dưới một claim khác. Với `seeded_regression`, ledger ghi 90.000đ, thấp hơn mức 120.000đ trong nhãn. Ở `misreport`, ledger ghi đúng 20.000đ nhưng agent báo 35.000đ, nên chỉ trượt FM-08. Lượt Swarm qua FM-08 vì trace không có event `reply` để đối chiếu số tiền.

## Chạy lại

Trong môi trường đã cài thư viện của Lab 9, chạy từ thư mục `src/`.

```bash
python -m pip install -r requirements-bonus.txt
python -m lab9.bonus_inspect
```

Nếu dùng uv, cài bằng `uv pip install -r requirements-bonus.txt`. Script chạy offline, in hai kết quả cho từng ca và trả mã lỗi nếu có chênh lệch.
