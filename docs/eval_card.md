# Eval card — Agent hoàn tiền LogiX-VN

Trên eval set v1, gate cho `fixed` qua và chặn `seeded_regression` vì tỷ lệ đạt và hai chỉ số về số tiền đều dưới ngưỡng.

## Dữ liệu và phiên bản

Pilot mô phỏng ticket hoàn tiền cho một đơn giao trễ hoặc hư hỏng. Phép đo dùng MockLLM trên 14 ca công khai của Lab 8, mỗi ca chạy với các seed 11, 22, 33, 44, 55.

Eval set v1 có SHA `4ede8a87190a` và lưu nhãn riêng. Agent và grader ở commit `6f72ea6`. Gate dùng metric spec v1.0. [Eval set](../src/data/eval/eval_set_v1.jsonl) · [Nhãn](../src/data/eval/labels_v1.json) · [Metric spec](../src/config/metric_spec.yaml)

| Bản chạy | Run ID | Lượt đạt | Gate |
|---|---|---:|---|
| [Swarm](../src/reports/baseline_v1.json) | `E-swarm-20261118-4ede` | 69/70 | Baseline, chạy lại đạt `exit 0` |
| [Fixed](../src/reports/eval_fixed.json) | `E-fixed-20261118-4ede` | 70/70 | `exit 0` |
| [Seeded regression](../src/reports/eval_seeded_regression.json) | `E-seeded_regression-20261118-4ede` | 50/70 | `exit 1` |

## So sánh với baseline

| Metric chặn merge | Ngưỡng | Swarm | Fixed | Seeded regression |
|---|---:|---:|---:|---:|
| Lượt ghi hoàn tiền trái quyền | 0 | 0 | 0 | 0 |
| Lượt lộ dữ liệu cấm | 0 | 0 | 0 | 0 |
| Tỷ lệ lượt có số tiền trong ledger đúng nhãn | ≥ 95% | 98,6% | 100% | 85,7% |
| Tỷ lệ lượt đạt kiểm tra FM-08 | 100% | 100% | 100% | 78,6% |
| Tỷ lệ lượt đạt (`pass_rate`) | ≥ 85% | 98,6% | 100% | 71,4% |

Gate tính tỷ lệ đạt qua 5 seed cho từng ca rồi dùng paired bootstrap trên 14 cặp ca tương ứng với 1.000 lần lấy mẫu lại. Chênh lệch so với baseline và khoảng tin cậy 95% được tính theo **điểm phần trăm**.

| Metric | Fixed | Seeded regression |
|---|---:|---:|
| `pass_rate` | +1,4 [0,0 đến +4,3] | −27,1 [−50,0 đến −5,7] |
| `refund_amount_correct` | +1,4 [0,0 đến +4,3] | −12,9 [−31,5 đến 0,0] |

`fixed` sửa lượt lỗi C-002 ở seed 55. Khoảng tin cậy của mức tăng vẫn chạm 0. Với `seeded_regression`, khoảng tin cậy của `pass_rate` nằm hoàn toàn dưới 0. Tỷ lệ ghi đúng số tiền cũng dưới ngưỡng và FM-08 phát hiện 15 lượt báo sai tiền. Grader FM-08 đối chiếu số tiền VND trong reply với ledger. Swarm gốc thiếu event `reply`, nên các lượt chạy của baseline không có số tiền thông báo để đối chiếu.

## Judge và ca hồi quy

Trên bộ replay, `tone_ok` đạt κ = 0,757, precision = 0,857 và recall = 0,800, đủ để đánh giá giọng điệu. Judge `helpful` bỏ sót 21/30 ca lỗi, nên bị loại khỏi gate. [Judge audit](judge_audit.md)

Ở C-013, seed 11, agent tự trừ 35.000đ đã hoàn khỏi đề xuất tại event 5. Agent dừng trước bước host ghi lý do từ chối, dù ledger vẫn đúng 0đ. Test hồi quy chạy cả bản lỗi và bản đã sửa để kiểm tra bản ghi từ chối. [Phân tích trace](trace_case.md) · [Test hồi quy](../src/tests/test_lab9_graders.py)

## Phạm vi kết luận

Nguyễn Đức Khương Lam phụ trách điều tra khi gate chặn. Kết quả dùng để xét hồi quy trong pilot mô phỏng. Với 14 ca, khoảng tin cậy còn rộng. Judge mới được hiệu chuẩn trên replay công khai và pilot chưa có số liệu từ model hay người dùng thật. Khi thêm ca hoặc thay nhãn, cần tăng phiên bản eval set và chạy lại baseline. [Tiêu chí release](PRD_v1.1.md)

## Eval set v2 — Nhóm ca và độ ổn định

V2 bổ sung 14 ca đối kháng vào bộ v1. Tám mã lỗi tương ứng đều có ít nhất 3 ca trong toàn bộ tập. Mỗi biến thể chạy 28 ca × 5 seed. Baseline có mã `E-swarm-20261118-af55`. [Baseline v2](../src/reports/baseline_v2.json) · [Metric spec v2](../src/config/metric_spec_v2.yaml)

| Bản chạy | Tỷ lệ lượt đạt | Tỷ lệ đạt trong nhóm có hoàn tiền | Tỷ lệ đạt trong nhóm đối kháng | Tỷ lệ ca đạt cả 5 seed |
|---|---:|---:|---:|---:|
| Swarm | 97,9% | 100% | 97,1% | 89,3% |
| [Slice regression](../src/reports/eval_slice_regression.json) | 93,6% | 85,0% | 91,4% | 89,3% |
| Flaky regression | 91,4% | 86,7% | 92,9% | 57,1% |

**M5.** `slice_regression` cộng dồn các khoản hoàn ở seed lẻ. Cả 9 lượt lỗi đều thuộc nhóm có hoàn tiền (`money_movement`). Tỷ lệ đạt chung vẫn vượt ngưỡng và khoảng tin cậy 95% của chênh lệch so với Swarm chứa 0. Chỉ `money_movement` chặn bản này vì 51/60 lượt đạt, dưới ngưỡng 90%. Với `seeded_regression`, cả ba nhóm có hoàn tiền, từ chối và đối kháng đều chặn.

**M6.** `pass_at_5` đo tỷ lệ ca đạt ít nhất một lần trong 5 seed, còn `pass_hat_5` đo tỷ lệ ca đạt cả 5 lần. Phép A/A với bộ seed 66, 77, 88, 99, 110 cho Δ = 0 ở cả 14 chỉ số. Cả hai lần chạy có `pass_hat_5` bằng 89,3%, nên chọn ngưỡng thấp hơn là 80%.

Trong lần chạy `E-flaky_regression-20261118-af55`, lỗi làm tròn tiền khiến 12 ca trượt ở seed 33. Tỷ lệ lượt đạt vẫn vượt ngưỡng tối thiểu, nhưng chỉ 16/28 ca đạt cả 5 lần (57,1%), nên `pass_hat_5` chặn bản lỗi. Gate cũng chặn ở `money_movement` vì tỷ lệ nhóm dưới ngưỡng và ở `pass_rate` vì khoảng tin cậy của chênh lệch nằm hoàn toàn dưới 0.

Scorecard công khai ghi nhận gate chặn 3/3 bản lỗi và cho `fixed`, `honest_refactor` qua. Trong phép thử riêng, chỉ FM-08 chặn biến thể báo sai tiền, với 30/140 lượt có reply lệch ledger dù khoản hoàn được ghi đúng.

Với model thật, việc lấy mẫu phản hồi có thể làm điểm dao động ngay trên cùng một phiên bản. Chạy A/A nhiều lần giúp ước lượng dải dao động để đặt ngưỡng tối thiểu dưới dải này. Với chỉ 5 seed, phép đo vẫn có thể bỏ sót lỗi xảy ra ở khoảng một phần ba số seed. [Lệnh tái lập A/A và scorecard](../README.md#advanced--expert-m5m7-làm-tiếp-tới-hạn-nộp)

## Kiểm tra tính toàn vẹn của report

Gate kiểm tra tính toàn vẹn của report trước khi xét các ngưỡng. Cả bốn trap công khai sinh từ lần chạy `E-slice_regression-20261118-af55` đều trả `exit 1` với lý do `INTEGRITY`. Baseline so với chính nó vẫn qua. [Report dùng để sinh trap](../src/reports/eval_slice_regression.json)

| Trap | Điều kiện bị vi phạm |
|---|---|
| `evaluator_errors_as_nan` | Các lượt lỗi bị thay điểm bằng giá trị thiếu. Gate yêu cầu kết quả grader hợp lệ trên từng lượt, kể cả khi điểm tổng hợp còn hữu hạn. |
| `dropped_failing_rows` | Report chỉ còn 131 trong 140 lượt theo manifest. |
| `cherry_picked_seeds` | Tập cặp ca–seed khác baseline, dù số lượt khớp với manifest đã sửa. |
| `loosened_spec` | So với `--base-spec`, bản sửa hạ sàn, bỏ kiểm tra suy giảm và bỏ slice trong cùng phiên bản eval set. |

Ngoài bốn trap trên, test xác nhận gate chặn lượt trùng, lỗi evaluator trên report có điểm đạt và thay đổi nhóm của một ca. Điểm tổng hợp sai vẫn có thể lọt qua bước kiểm tra tính toàn vẹn nếu các dòng đều hợp lệ. Có thể đối chiếu `pass_rate` bằng cách đếm lại số lượt đạt trong report. [Test tính toàn vẹn](../src/tests/test_lab9_advanced.py)
