import json

with open('c:\\Users\\mohiuddin\\OneDrive\\Desktop\\[PUB] India_runs_data_and_ai_challenge\\India_runs_data_and_ai_challenge\\sample_candidates.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the first { that marks CAND_0000002
start_idx = 0
for i, line in enumerate(lines):
    if '"candidate_id": "CAND_0000002"' in line:
        start_idx = i - 1 # The { before it
        break

fixed_lines = ['[\n'] + lines[start_idx:]
with open('c:\\Users\\mohiuddin\\OneDrive\\Desktop\\[PUB] India_runs_data_and_ai_challenge\\India_runs_data_and_ai_challenge\\fixed_candidates.json', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Fixed candidate JSON generated.")
