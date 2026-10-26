"""Đội B: chỉ đọc hồ sơ và hash trong shared_data.json."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import time
from rules import CHARSET, generate_dictionary_candidates

BASE = Path(__file__).resolve().parent


def modulo_hash(password):
    return sum(ord(c) for c in password) % 1000


def sha256_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def load_shared_data(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    return data if isinstance(data, list) else [data]


def generate_bruteforce_candidates(charset, length, max_attempts):
    # Duyệt không lặp; random sampling không phải vét cạn.
    if not charset or length < 1 or max_attempts < 1:
        raise ValueError('Bảng ký tự, độ dài và giới hạn phải hợp lệ')
    combinations = itertools.product(dict.fromkeys(charset), repeat=length)
    for chars in itertools.islice(combinations, max_attempts):
        yield ''.join(chars)


def crack_password(candidates, target_modulo, target_sha256, max_attempts, timeout_seconds):
    started = time.perf_counter()
    attempts = modulo_hits = false_positives = 0
    found = None
    iterator = iter(candidates)
    while True:
        if time.perf_counter() - started >= timeout_seconds:
            reason = 'timeout_reached'
            break
        if attempts >= max_attempts:
            reason = 'max_attempts_reached'
            break
        try:
            candidate = next(iterator)
        except StopIteration:
            reason = 'candidate_space_exhausted'
            break
        if time.perf_counter() - started >= timeout_seconds:
            reason = 'timeout_reached'
            break
        attempts += 1
        if modulo_hash(candidate) == target_modulo:
            modulo_hits += 1
            if sha256_hash(candidate) == target_sha256:
                found = candidate
                reason = 'found'
                break
            false_positives += 1
    elapsed = time.perf_counter() - started
    return {'attempts': attempts, 'time_seconds': elapsed,
            'speed_per_sec': attempts / elapsed if elapsed else 0,
            'modulo_hits': modulo_hits, 'false_positives': false_positives,
            'cracked': found is not None, 'stop_reason': reason, 'recovered_password': found or ''}


def estimate_full_bruteforce_time(speed_per_sec, keyspace_size):
    return keyspace_size / speed_per_sec if speed_per_sec > 0 else float('inf')


def benchmark_generator(profile):
    started = time.perf_counter()
    count = sum(1 for _ in generate_dictionary_candidates(profile))
    elapsed = time.perf_counter() - started
    return count, count / elapsed if elapsed else 0


def save_result(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.exists() or path.stat().st_size == 0
    with path.open('a', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=list(row))
        if header:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Thí nghiệm offline trên dữ liệu do đội A tạo')
    parser.add_argument('--input', type=Path, default=BASE / 'data' / 'shared_data.json')
    parser.add_argument('--results', type=Path, default=BASE / 'results' / 'results.csv')
    parser.add_argument('--max-attempts', type=int, default=100000)
    parser.add_argument('--timeout', type=float, default=5.0)
    args = parser.parse_args()
    if args.max_attempts < 1 or not 0 < args.timeout < float('inf'):
        parser.error('Giới hạn số lần thử và thời gian phải là số dương hữu hạn')
    for user in load_shared_data(args.input):
        count, gen_speed = benchmark_generator(user['profile'])
        print(f"{user['username']}: {count} ứng viên hồ sơ, sinh {gen_speed:,.0f} ứng viên/giây")
        for kind in ('profile_password', 'random_password'):
            target = user['hashes'][kind]
            for method in ('dictionary', 'bruteforce'):
                candidates = (generate_dictionary_candidates(user['profile']) if method == 'dictionary'
                              else generate_bruteforce_candidates(CHARSET, target['length'], args.max_attempts))
                result = crack_password(candidates, target['modulo_hash'], target['sha256_hash'],
                                        args.max_attempts, args.timeout)
                keyspace = len(CHARSET) ** target['length']
                estimate = (estimate_full_bruteforce_time(result['speed_per_sec'], keyspace)
                            if method == 'bruteforce' else '')
                row = {'run_utc': datetime.now(timezone.utc).isoformat(),
                       'username': user['username'], 'password_type': kind, 'attack_method': method,
                       **result, 'dictionary_size': count, 'generation_speed_per_sec': gen_speed,
                       'max_attempts': args.max_attempts, 'timeout_seconds': args.timeout,
                       'keyspace_size': keyspace if method == 'bruteforce' else count,
                       'estimated_full_seconds': estimate}
                save_result(args.results, row)
                print(f"  {kind:18} {method:10} {result['stop_reason']:26} "
                      f"{result['attempts']:>7} lần / {result['time_seconds']:.6f}s; "
                      f"false positives={result['false_positives']}")
                if result['cracked']:
                    print('    Tìm thấy:', result['recovered_password'])
    print('CSV:', args.results.resolve())


if __name__ == '__main__':
    main()
