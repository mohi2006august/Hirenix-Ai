import argparse
import csv
import sys
import os

# Add current dir to path to import pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.stage1_filter import process_file_in_chunks
from pipeline.stage2_semantic import semantic_rank
from pipeline.stage3_signals import apply_signals_and_reasoning

def main():
    parser = argparse.ArgumentParser(description="Intelligent Candidate Discovery & Ranking")
    parser.add_argument("--candidates", type=str, required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", type=str, required=True, help="Path to output CSV file")
    args = parser.parse_args()

    print("Stage 1: Heuristic Filtering...")
    top_k_filtered = process_file_in_chunks(args.candidates, top_k=2000)
    print(f"Stage 1 complete. Extracted {len(top_k_filtered)} candidates.")

    print("Stage 2: Semantic Similarity Scoring...")
    semantically_ranked = semantic_rank(top_k_filtered, top_k=150)
    print(f"Stage 2 complete.")

    print("Stage 3: Behavioral Signals and Reasoning...")
    final_top_100 = apply_signals_and_reasoning(semantically_ranked)
    
    # Generate output CSV

    print(f"Generating output CSV to {args.out}...")
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for c in final_top_100:
            writer.writerow([
                c['candidate_id'],
                c['rank'],
                f"{c['final_score']:.4f}",
                c['reasoning']
            ])
            
    print("Ranking complete!")

if __name__ == "__main__":
    main()
