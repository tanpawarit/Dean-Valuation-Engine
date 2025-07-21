#!/usr/bin/env python3
"""
Command-line utility to view and manage Dean Valuation Engine analysis runs.
Usage: python list_runs.py [options]
"""

import argparse
import sys
from pathlib import Path

from src.utils.run_manager import (
    print_runs_table, 
    list_runs_by_datetime, 
    get_run_details, 
    cleanup_old_runs_by_date
)
from src.utils.checkpoint_manager import CheckpointManager
from src.utils.recovery_handler import RecoveryHandler


def main():
    parser = argparse.ArgumentParser(
        description="Manage and view Dean Valuation Engine analysis runs"
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true",
        help="List all runs sorted by datetime (default)"
    )
    parser.add_argument(
        "--details", "-d",
        metavar="RUN_ID",
        help="Show detailed information for specific run"
    )
    parser.add_argument(
        "--cleanup", "-c",
        type=int,
        metavar="N",
        help="Keep only the N most recent runs, delete the rest"
    )
    parser.add_argument(
        "--recovery-info", "-r",
        action="store_true",
        help="Show recovery information for the most recent run"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw JSON output instead of formatted table"
    )
    
    args = parser.parse_args()
    
    # Default to listing if no specific action
    if not any([args.details, args.cleanup, args.recovery_info]):
        args.list = True
    
    try:
        if args.list:
            if args.raw:
                import json
                runs = list_runs_by_datetime()
                print(json.dumps(runs, indent=2))
            else:
                print_runs_table()
        
        elif args.details:
            details = get_run_details(args.details)
            if details:
                print(f"\n📋 Run Details: {args.details}")
                print("=" * 60)
                print(f"Directory: {details['run_directory']}")
                print(f"Created: {details['metadata'].get('created_at', 'Unknown')}")
                print(f"Query: {details['state_summary']['query']}")
                print(f"Progress: {details['completed_steps']}/{details['state_summary']['total_steps']} steps")
                print(f"Status: {'✅ Complete' if details['state_summary']['has_final_result'] else '❌ Error' if details['state_summary']['has_error'] else '🔄 In Progress'}")
                print(f"Final Result: {details['final_result_length']} characters")
                print(f"Checkpoints: {len(details['checkpoints'])}")
                
                if details['plan']:
                    print(f"\n📝 Execution Plan:")
                    for i, step in enumerate(details['plan'], 1):
                        status = "✅" if i <= details['completed_steps'] else "⏳"
                        print(f"  {status} Step {i}: {step.get('task_description', 'Unknown')[:60]} ({step.get('assigned_agent', 'Unknown')})")
            else:
                print(f"❌ Run {args.details} not found or corrupted")
                sys.exit(1)
        
        elif args.cleanup:
            print(f"🧹 Cleaning up old runs, keeping {args.cleanup} most recent...")
            success = cleanup_old_runs_by_date(keep_last_n=args.cleanup)
            if success:
                print("✅ Cleanup completed successfully")
            else:
                print("❌ Cleanup failed")
                sys.exit(1)
        
        elif args.recovery_info:
            # Get the most recent run for recovery info
            runs = list_runs_by_datetime()
            if runs:
                latest_run = runs[0]
                manager = CheckpointManager(run_id=latest_run['run_id'])
                recovery = RecoveryHandler(manager)
                
                print(f"\n🔄 Recovery Information for {latest_run['directory']}")
                print("=" * 60)
                
                if recovery.can_recover():
                    info = recovery.get_recovery_info()
                    if info:
                        print("✅ Recovery possible")
                        print(f"Current state: {info['current_state']['completed_steps']}/{info['current_state']['total_steps']} steps")
                        print(f"Query: {info['current_state']['query']}")
                        print(f"Can resume: {'✅ Yes' if info['recovery_options']['resume'] else '❌ No'}")
                        print(f"Can rollback: {'✅ Yes' if info['recovery_options']['rollback'] else '❌ No'}")
                        print(f"Available checkpoints: {info['available_checkpoints']}")
                    else:
                        print("❌ Recovery info not available")
                else:
                    print("❌ No recovery possible for latest run")
            else:
                print("❌ No runs found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()