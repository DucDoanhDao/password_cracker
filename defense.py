"""Đội A: python defense.py hoặc python defense.py --demo"""
import argparse
from datetime import date
import getpass
import hashlib
import json
from pathlib import Path
import secrets
from rules import CHARSET, SPECIALS, generate_dictionary_candidates, name_roots

BASE = Path(__file__).resolve().parent


def modulo_hash(password):
    return sum(ord(c) for c in password) % 1000


def sha256_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_secure_password(length=16):
    if length < 12:
        raise ValueError('Mật khẩu ngẫu nhiên phải dài ít nhất 12 ký tự')
    return ''.join(secrets.choice(CHARSET) for _ in range(length))


def input_profile():
    full_name = input('Họ tên (dùng hồ sơ giả cho demo): ').strip()
    nickname = input('Biệt danh: ').strip()
    while True:
        year = input('Năm sinh (4 chữ số): ').strip()
        if year.isascii() and year.isdigit() and len(year) == 4 and 1900 <= int(year) <= date.today().year:
            break
        print('Năm sinh chưa hợp lệ.')
    profile = {'full_name': full_name, 'nickname': nickname, 'birth_year': int(year)}
    if not next(generate_dictionary_candidates(profile), None):
        raise ValueError('Hồ sơ không tạo được ứng viên dài 8–12 ký tự. Hãy chọn biệt danh khác.')
    return profile


def input_profile_password(profile):
    print('Gốc từ:', ', '.join(name_roots(profile)))
    print(f'Quy tắc: gốc từ + 1 ký tự trong {SPECIALS} + năm sinh (4 hoặc 2 số).')
    print('Dài 8–12 ký tự; có thể viết hoa chữ đầu, thay tối đa 2 vị trí a→@, e→3, o→0.')
    while True:
        password = getpass.getpass('Mật khẩu theo hồ sơ: ')
        if any(password == c for c in generate_dictionary_candidates(profile)):
            return password
        print('Mật khẩu chưa thuộc bộ quy tắc. Hãy nhập lại.')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def save_private_data(path, username, profile_pwd, random_pwd):
    write_json(path, {'username': username, 'profile_password': profile_pwd,
                      'random_password': random_pwd})


def save_shared_data(path, username, profile, hashes):
    write_json(path, {'schema_version': 1, 'username': username,
                      'profile': profile, 'hashes': hashes})


def main():
    parser = argparse.ArgumentParser(description='Tạo dữ liệu thí nghiệm mật khẩu cục bộ')
    parser.add_argument('--demo', action='store_true', help='Dùng hồ sơ giả và Bust3r!1998')
    parser.add_argument('--length', type=int, default=16)
    parser.add_argument('--out-dir', type=Path, default=BASE / 'data')
    args = parser.parse_args()
    if args.length < 12:
        parser.error('--length phải >= 12')
    if args.demo:
        username = 'nguyenvana'
        profile = {'full_name': 'Nguyen Van A', 'birth_year': 1998, 'nickname': 'Bust3r'}
        profile_pwd = 'Bust3r!1998'
    else:
        username = input('Tên tài khoản: ').strip() or 'demo'
        profile = input_profile()
        profile_pwd = input_profile_password(profile)
    random_pwd = generate_secure_password(args.length)
    passwords = {'profile_password': profile_pwd, 'random_password': random_pwd}
    hashes = {kind: {'modulo_hash': modulo_hash(pwd), 'sha256_hash': sha256_hash(pwd),
                     'length': len(pwd)} for kind, pwd in passwords.items()}
    save_private_data(args.out_dir / 'private' / 'private_data.json', username, profile_pwd, random_pwd)
    save_shared_data(args.out_dir / 'shared_data.json', username, profile, hashes)
    print(json.dumps(hashes, indent=2))
    print(f'Đã lưu tại {args.out_dir.resolve()}. Chỉ bàn giao shared_data.json cho đội B.')
    print('private/private_data.json chứa plaintext để đối chiếu bài tập; giữ riêng.')


if __name__ == '__main__':
    main()
