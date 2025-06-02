import csv
from collections import defaultdict

# Accumulators for each component and pair count
sums = defaultdict(lambda: {
    'lexical': 0.0,
    'ast': 0.0,
    'file': 0.0,
    'divergence': 0.0,
    'pairs': 0
})

# Read pairwise divergence CSV
with open("./pairwise_hunk_divergence_results.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        bug_id = row['bug_id']
        sums[bug_id]['lexical'] += float(row['lexical_distance'])
        sums[bug_id]['ast'] += float(row['ast_distance'])
        sums[bug_id]['file'] += float(row['package_distance'])
        sums[bug_id]['divergence'] += float(row['pair_divergence'])
        sums[bug_id]['pairs'] += 1

# Write average values per bug using the n(n-1)/2 formula
with open("bugwise_average_divergence.csv", mode='w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow([
        'bug_id', 
        'hunk_count', 
        'pair_count',
        'avg_lexical', 
        'avg_ast', 
        'avg_file', 
        'avg_divergence'
    ])

    for bug_id in sorted(sums):
        pair_count = sums[bug_id]['pairs']
        n = int((1 + (1 + 8 * pair_count) ** 0.5) / 2) if pair_count > 0 else 1

        denom = n * (n - 1) / 2 if n > 1 else 1

        avg_lexical = sums[bug_id]['lexical'] / denom
        avg_ast = sums[bug_id]['ast'] / denom
        avg_package = sums[bug_id]['file'] / denom
        avg_divergence = sums[bug_id]['divergence'] / denom

        writer.writerow([
            bug_id, n, pair_count,
            round(avg_lexical, 6),
            round(avg_ast, 6),
            round(avg_package, 6),
            round(avg_divergence, 6)
        ])

print("Saved bugwise_average_divergence.csv")