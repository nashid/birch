import csv
import os
import argparse

def analyze_results(input_csv_file, output_csv_file):
    total_entries = 0
    pass_count = 0
    test_fail_count = 0
    compile_fail_count = 0

    try:
        # Read the input CSV file
        with open(input_csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                total_entries += 1
                if row['pass'].strip().lower() == 'yes':
                    pass_count += 1
                if row['test_fail'].strip().lower() == 'yes':
                    test_fail_count += 1
                if row['compile_fail'].strip().lower() == 'yes':
                    compile_fail_count += 1

        if total_entries == 0:
            print("No entries found in the CSV.")
            return

        # Calculate the pass rate
        pass_rate = (pass_count / total_entries) * 100

        # Print results
        print(f"Pass rate: {pass_rate:.2f}%")
        print(f"Total Passes: {pass_count}")
        print(f"Total Test Failures: {test_fail_count}")
        print(f"Total Compile Failures: {compile_fail_count}")
        print(f"Total Bugs: {total_entries}")

        # Write results to the output CSV file
        with open(output_csv_file, mode='w', newline='', encoding='utf-8') as out_file:
            writer = csv.DictWriter(out_file, fieldnames=[
                "Total Bugs", "Total Passes", "Total Test Failures", "Total Compile Failures", "Pass Rate"
            ])
            writer.writeheader()
            writer.writerow({
                "Total Bugs": total_entries,
                "Total Passes": pass_count,
                "Total Test Failures": test_fail_count,
                "Total Compile Failures": compile_fail_count,
                "Pass Rate": f"{pass_rate:.2f}%"
            })

        print(f"Results have been written to {output_csv_file}")

    except FileNotFoundError:
        print(f"Error: File not found at {input_csv_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze the results from a CSV file.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Relative path to the CSV file under 'results/final-results/'. Example: mode_1_model_gpt4o/test_results.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Relative path to the CSV file under 'results/final-results/'. Example: mode_1_model_gpt4o/test_statistics.csv"
    )
    args = parser.parse_args()

    base_path = os.path.join(os.getcwd(), "results", "final-results")
    csv_file_path = os.path.join(base_path, args.csv_file)

    analyze_results(csv_file_path)