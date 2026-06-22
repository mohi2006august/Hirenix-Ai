import argparse
import csv
import json
import sys
import os

# Add current dir to path to import pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.stage1_filter import process_file_in_chunks
from pipeline.stage2_semantic import semantic_rank
from pipeline.stage3_signals import apply_signals_and_reasoning

def load_jd_config(config_path: str) -> dict:
    """Load job description config from a JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Intelligent Candidate Discovery & Ranking")
    parser.add_argument("--candidates", type=str, required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", type=str, required=True, help="Path to output CSV file")
    parser.add_argument("--jd-config", type=str, default=None,
                        help="Path to job_config.json (optional). If not provided, uses built-in defaults.")
    args = parser.parse_args()

    # Load JD config if provided
    jd_config = None
    if args.jd_config:
        print(f"Loading job config from {args.jd_config}...")
        jd_config = load_jd_config(args.jd_config)
        print(f"  Job Title: {jd_config.get('job_title', 'N/A')}")
    else:
        # Try to auto-detect job_config.json in the same directory as candidates
        auto_config = os.path.join(os.path.dirname(os.path.abspath(args.candidates)), 'job_config.json')
        if os.path.exists(auto_config):
            print(f"Auto-detected job config at {auto_config}")
            jd_config = load_jd_config(auto_config)
            print(f"  Job Title: {jd_config.get('job_title', 'N/A')}")
        else:
            print("No job config provided — using built-in defaults.")

    # Extract pipeline settings
    pipeline_settings = (jd_config or {}).get('pipeline_settings', {})
    stage1_top_k = pipeline_settings.get('stage1_top_k', 2000)
    stage2_top_k = pipeline_settings.get('stage2_top_k', 150)
    final_top_k = pipeline_settings.get('final_top_k', 100)

    print(f"\nPipeline Settings: Stage1={stage1_top_k}, Stage2={stage2_top_k}, Final={final_top_k}\n")

    print("Stage 1: Heuristic Filtering...")
    top_k_filtered = process_file_in_chunks(args.candidates, jd_config=jd_config, top_k=stage1_top_k)
    print(f"Stage 1 complete. Extracted {len(top_k_filtered)} candidates.")

    print("Stage 2: Semantic Similarity Scoring...")
    jd_text = (jd_config or {}).get('job_description', None)
    semantically_ranked = semantic_rank(top_k_filtered, jd_text=jd_text, top_k=stage2_top_k)
    print(f"Stage 2 complete.")

    print("Stage 3: Behavioral Signals and Reasoning...")
    final_ranked = apply_signals_and_reasoning(semantically_ranked, final_top_k=final_top_k)
    
    # Generate output CSV
    print(f"Generating output CSV to {args.out}...")
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for c in final_ranked:
            writer.writerow([
                c['candidate_id'],
                c['rank'],
                f"{c['final_score']:.4f}",
                c['reasoning']
            ])
            
    print("Ranking complete!")

if __name__ == "__main__":
    main()
