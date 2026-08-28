import os

md_file = r'd:\Kaeha\tableConvert.com_3x9z2h.md'

with open(md_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in file: {len(lines)}")

seqs = []
for idx, line in enumerate(lines):
    l = line.strip()
    if l.startswith('|'):
        parts = [p.strip() for p in l.split('|')[1:-1]]
        if parts and parts[0].isdigit():
            seqs.append((idx + 1, int(parts[0]), parts[1], parts[2]))

print(f"Total data rows parsed: {len(seqs)}")
print(f"First seq: {seqs[0] if seqs else None}")
print(f"Last seq: {seqs[-1] if seqs else None}")

# Check missing sequence numbers
all_nums = [s[1] for s in seqs]
missing = []
for n in range(1, max(all_nums) + 1):
    if n not in all_nums:
        missing.append(n)

print(f"Missing sequence numbers: {missing}")
