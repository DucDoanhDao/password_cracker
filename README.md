# Mô phỏng mật khẩu: phòng thủ và tấn công

Python 3.9+; chỉ dùng thư viện chuẩn, không cần pip. Bản CLI chạy tuần tự.

## Chạy nhanh

Mở terminal trong thư mục chứa các script:

```powershell
python -X utf8 defense.py --demo
python -X utf8 attack.py
```

`--demo` dùng hồ sơ giả Nguyen Van A / Bust3r / 1998, mật khẩu hồ sơ
`Bust3r!1998`, và sinh mới một mật khẩu ngẫu nhiên 16 ký tự mỗi lần chạy.
Muốn tự nhập hồ sơ và mật khẩu (ẩn khi nhập), chạy:

```powershell
python -X utf8 defense.py
```

Đổi độ dài ngẫu nhiên và giới hạn thử:

```powershell
python -X utf8 defense.py --length 12
python -X utf8 attack.py --max-attempts 200000 --timeout 10
```

Đường dẫn mặc định tính từ thư mục chứa script, không phụ thuộc nơi mở terminal.
`defense.py` ghi đè dữ liệu của lần trước; `attack.py` nối thêm dòng CSV.
Dùng `--out-dir`, `--input`, `--results` để tách các lượt thử. Ví dụ:

```powershell
python -X utf8 defense.py --demo --out-dir data/run2
python -X utf8 attack.py --input data/run2/shared_data.json --results results/run2.csv
python -X utf8 -m unittest -v test_lab.py
```

## Các file

- `defense.py`: nhập hồ sơ, kiểm tra mật khẩu thuộc quy tắc, sinh bằng secrets,
  tính riêng Modulo và SHA-256, lưu JSON.
- `rules.py`: bộ quy tắc công khai; hai đội dùng cùng quy tắc, không chia sẻ bí mật.
- `attack.py`: chỉ đọc shared_data.json, sinh ứng viên, lọc Modulo rồi xác nhận SHA-256.
- `data/private/private_data.json`: plaintext chỉ để đội A đối chiếu trong bài tập.
- `data/shared_data.json`: hồ sơ, hash, độ dài mật khẩu; chỉ bàn giao file này cho đội B.
- `results/results.csv`: kết quả đã chạy thử; mỗi lần chạy atk ghi thêm 4 dòng.
- `test_lab.py`: kiểm tra collision, điều kiện dừng, sinh tổ hợp và quy tắc hồ sơ.

Nếu hai đội dùng máy riêng: đội B cần `attack.py`, `rules.py` và `shared_data.json`.
Ví dụ: `python -X utf8 attack.py --input shared_data.json`.
File riêng được đặt trong thư mục `private` để dễ tách khi bàn giao; đây không phải
cơ chế phân quyền hệ điều hành. ZIP đầy đủ phục vụ người làm bài, có dữ liệu riêng
của hồ sơ giả; không gửi nguyên ZIP này cho đội B trong buổi demo.

## Bộ quy tắc

Bỏ dấu tiếng Việt, lấy từng từ trong họ tên / tên ghép cuối / toàn bộ tên ghép /
chữ cái viết tắt / biệt danh. Thử dạng gốc, viết thường, viết hoa chữ đầu.
Thay 0–2 vị trí theo a→@, e→3, o→0, rồi ghép:

    gốc từ + một ký tự ! @ # . _ + năm sinh (4 hoặc 2 số)

Chỉ giữ ứng viên 8–12 ký tự, loại trùng. `defense.py` chỉ chấp nhận mật khẩu có
trong bộ sinh này để hai đội thống nhất không gian tìm kiếm. Bộ sinh dùng
`itertools.combinations` và `itertools.product`.

Mật khẩu ngẫu nhiên dùng secrets.choice trên 94 ký tự ASCII in được không có dấu
cách; mặc định 16 ký tự, tối thiểu 12. Không bắt buộc đủ mọi nhóm ký tự.

## Đọc kết quả

Chạy ma trận 2 × 2: dictionary và brute-force, mỗi cách thử cả hai mật khẩu.
Brute-force dùng itertools.product theo thứ tự CHARSET, biết trước độ dài từ
shared_data.json. Không chọn ngẫu nhiên ứng viên, không thử lặp. Với giới hạn
100.000, đây chỉ là một tiền tố rất nhỏ của toàn bộ không gian; mật khẩu hồ sơ
cũng có thể không được tìm thấy bằng brute-force mặc dù dictionary tìm rất nhanh.

- `found`: xác nhận SHA-256 trùng, ghi mật khẩu đã tìm được.
- `candidate_space_exhausted`: hết ứng viên của generator, thường là hết từ điển.
- `max_attempts_reached`: chạm giới hạn lần thử.
- `timeout_reached`: chạm giới hạn thời gian cho một phép thử.

Thời gian dùng perf_counter, gồm sinh ứng viên và kiểm tra hash, không gồm ghi CSV.
Timeout kiểm tra giữa các ứng viên nên có thể vượt nhẹ bởi một bước xử lý.
`generation_speed_per_sec` đo riêng việc sinh toàn bộ từ điển; tốc độ cracking
là attempts / thời gian. Với bộ từ điển nhỏ, số đo rất ngắn có thể dao động mạnh.

`modulo_hits` đếm các lần qua bộ lọc. `false_positives` đếm trùng Modulo nhưng sai
SHA-256; có thể bằng 0 trong một lượt thử. Chạy test collision để thấy rõ:
`ab` và `ba` cùng tổng mã ký tự nhưng SHA-256 khác nhau.

`estimated_full_seconds` chỉ có ở brute-force, bằng 94^length / tốc độ đo.
Đây là ước lượng vét cạn với giả định tốc độ không đổi, không phải thời gian đã
thực chạy và không phải phép đo trên phần cứng chuyên dụng. Với mật khẩu ngẫu
nhiên đồng đều, số lần thử trung bình xấp xỉ một nửa toàn bộ không gian.

Không tìm thấy trong giới hạn không chứng minh mật khẩu không thể bị bẻ.
Mật khẩu ngẫu nhiên 12 ký tự vẫn có thể tình cờ thuộc từ điển, dù xác suất nhỏ;
chương trình kiểm tra và báo kết quả thực tế. Mặc định 16 ký tự nên nằm ngoài từ
điển giới hạn 8–12 ký tự.

## Diễn giải khi trình bày

Hash là hàm băm, không phải mã hóa có thể giải mã. Hai hash được tính độc lập,
không phải SHA-256(Modulo(password)). Modulo không phải hash mật mã: chỉ có 1000
giá trị, hoán vị ký tự giữ nguyên tổng, và phân bố ứng viên không đồng đều.
Bộ lọc Modulo chỉ minh họa collision, không bảo đảm tăng tốc so với SHA-256 trực
 tiếp vì việc cộng ord trong Python cũng tốn thời gian.

SHA-256 ở đây để làm đúng thí nghiệm; ứng dụng thật cần hàm băm mật khẩu có salt
và chi phí tính toán thích hợp (như Argon2id), thay vì SHA-256 thuần. Plaintext
trong file private chỉ phục vụ đối chiếu bài tập. Dùng hồ sơ và mật khẩu giả.
