"""
migrate_jobs.py — Normalize job directory names to {id:03d}_{company}_{role} format.

Usage:
    python util/migrate_jobs.py --user JackyTao                  # dry-run (default)
    python util/migrate_jobs.py --user JackyTao --execute         # actually rename
    python util/migrate_jobs.py --user JackyTao --backup          # create ZIP first, then execute

Preserves Tracker ID as the stable key. Only sanitizes Windows-invalid path characters.
"""

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
USERS_DIR = SKILL_ROOT / "users"

# Known mapping: existing directory name -> tracker ID
# Built from manual inspection of company/role matches
KNOWN_MAPPING = {
    "aliyun_commercial_data_analyst": 1,
    "antgroup_ai_product_manager": 2,
    "airliquide_project_logistics_enginer": 3,
    "chagee_supply_chain_digital_expert": 4,
    "bosch_supply_chain_pm_apac": 5,
    "bosch_ai_opex_expert": 6,
    "alibaba_procurement_ai": 7,
    "alibaba_ai_pm_enterprise_intelligence": 10,
    "deepseek_agi_core_business_trainee": 15,
    "amec_lean_digitalization_expert": 16,
    "alibaba_ai_pm_platform_logistics": 17,
    "saidou_ai_efficiency": 18,
    "seres_ai_efficiency": 18,  # duplicate - merge into saidou
    "netease_elite_talent": 19,
    "alibaba_qwen_solution": 20,
    "central_research_llm_production": 21,
}


def sanitize_dirname(name: str) -> str:
    """Remove Windows-invalid path characters, transliterate to ASCII-safe."""
    # Remove characters invalid in Windows paths
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    # Replace common Chinese punctuation and separators with underscore
    name = re.sub(r"[\s\-()（）/·&]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_").lower()
    return name


def build_target_name(row: dict) -> str:
    """Build target directory name from tracker row: {id:03d}_{company}_{role}."""
    tid = int(row["id"])
    company = sanitize_dirname(row["company"])
    role = sanitize_dirname(row["role"])
    # Truncate to keep path reasonable
    max_role_len = 40
    if len(role) > max_role_len:
        role = role[:max_role_len].rstrip("_")
    return f"{tid:03d}_{company}_{role}"


def load_tracker(user_dir: Path) -> list[dict]:
    tracker_path = user_dir / "tracker.csv"
    if not tracker_path.exists():
        print(f"ERROR: {tracker_path} not found")
        sys.exit(1)
    with open(tracker_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def plan_migration(user_dir: Path) -> list[dict]:
    """Return list of planned actions: rename, create, merge."""
    rows = load_tracker(user_dir)
    jobs_dir = user_dir / "jobs"
    existing_dirs = {d.name: d for d in jobs_dir.iterdir() if d.is_dir()} if jobs_dir.exists() else {}

    actions = []

    for row in rows:
        tid = int(row["id"])
        target_name = build_target_name(row)
        target_path = jobs_dir / target_name

        # Find source directory
        sources = [name for name, mapped_id in KNOWN_MAPPING.items() if mapped_id == tid]
        existing_sources = [name for name in sources if name in existing_dirs]

        if len(existing_sources) == 0:
            # No directory exists — create minimal
            actions.append({
                "action": "create",
                "target": target_name,
                "tracker_id": tid,
                "note": "No existing directory; will create with minimal timeline.md",
            })
        elif len(existing_sources) == 1:
            src_name = existing_sources[0]
            if src_name == target_name:
                actions.append({
                    "action": "skip",
                    "target": target_name,
                    "tracker_id": tid,
                    "note": "Already correctly named",
                })
            else:
                actions.append({
                    "action": "rename",
                    "source": src_name,
                    "target": target_name,
                    "tracker_id": tid,
                })
        else:
            # Multiple sources (merge case, e.g. saidou + seres)
            primary = existing_sources[0]
            actions.append({
                "action": "merge",
                "sources": existing_sources,
                "target": target_name,
                "tracker_id": tid,
                "note": f"Merge {existing_sources} into {target_name}",
            })

    return actions


def create_minimal_timeline(user_dir: Path, row: dict, target_name: str):
    """Create a minimal timeline.md from verifiable tracker fields only."""
    jobs_dir = user_dir / "jobs" / target_name
    jobs_dir.mkdir(parents=True, exist_ok=True)
    timeline_path = jobs_dir / "timeline.md"
    if timeline_path.exists():
        return

    lines = [f"# Timeline: {row['company']} — {row['role']}\n"]
    lines.append("")
    lines.append("| 日期 | 事件 | 备注 |")
    lines.append("|------|------|------|")

    last_updated = row.get("last_updated", "")
    status = row.get("status", "evaluating")
    if last_updated:
        lines.append(f"| {last_updated} | {status} | (migrated from tracker) |")
    else:
        lines.append(f"| — | {status} | (migrated from tracker, date unknown) |")

    lines.append("")
    timeline_path.write_text("\n".join(lines), encoding="utf-8")


def execute_migration(user_dir: Path, actions: list[dict], rows: list[dict]):
    """Execute the planned migration actions."""
    jobs_dir = user_dir / "jobs"
    jobs_dir.mkdir(exist_ok=True)

    rows_by_id = {int(r["id"]): r for r in rows}

    for action in actions:
        tid = action["tracker_id"]
        target = action["target"]

        if action["action"] == "skip":
            continue
        elif action["action"] == "rename":
            src = jobs_dir / action["source"]
            dst = jobs_dir / target
            print(f"  RENAME: {action['source']} -> {target}")
            src.rename(dst)
        elif action["action"] == "merge":
            sources = action["sources"]
            dst = jobs_dir / target
            # Use first source as primary, copy unique files from others
            primary = jobs_dir / sources[0]
            if primary.name != target:
                primary.rename(dst)
            for extra_name in sources[1:]:
                extra = jobs_dir / extra_name
                if extra.exists():
                    for f in extra.iterdir():
                        target_file = dst / f.name
                        if not target_file.exists():
                            shutil.copy2(f, target_file)
                            print(f"    MERGE FILE: {f.name} from {extra_name}")
                    shutil.rmtree(extra)
                    print(f"    REMOVED: {extra_name} (merged)")
        elif action["action"] == "create":
            row = rows_by_id.get(tid)
            if row:
                create_minimal_timeline(user_dir, row, target)
                print(f"  CREATE: {target}/timeline.md")


def create_backup(user_dir: Path):
    """Create timestamped ZIP of tracker.csv and jobs/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_jobs_{timestamp}"
    jobs_dir = user_dir / "jobs"
    tracker = user_dir / "tracker.csv"

    backup_dir = user_dir / "backups"
    backup_dir.mkdir(exist_ok=True)

    # Create ZIP
    archive_path = backup_dir / backup_name
    shutil.make_archive(str(archive_path), "zip", user_dir, "jobs")

    # Also copy tracker.csv into the backup
    backup_tracker = backup_dir / f"tracker_{timestamp}.csv"
    shutil.copy2(tracker, backup_tracker)

    print(f"  BACKUP: {archive_path}.zip")
    print(f"  BACKUP: {backup_tracker}")


def main():
    parser = argparse.ArgumentParser(description="Normalize job directory names")
    parser.add_argument("--user", required=True, help="Username under users/")
    parser.add_argument("--execute", action="store_true", help="Actually perform renames (default: dry-run)")
    parser.add_argument("--backup", action="store_true", help="Create backup ZIP before executing")
    args = parser.parse_args()

    user_dir = USERS_DIR / args.user
    if not user_dir.exists():
        print(f"ERROR: User directory not found: {user_dir}")
        sys.exit(1)

    rows = load_tracker(user_dir)
    actions = plan_migration(user_dir)

    # Print plan
    print(f"\n{'=' * 60}")
    print(f"Migration plan for: {args.user}")
    print(f"{'=' * 60}\n")

    for a in actions:
        if a["action"] == "skip":
            print(f"  [SKIP]   #{a['tracker_id']:02d} {a['target']}")
        elif a["action"] == "rename":
            print(f"  [RENAME] #{a['tracker_id']:02d} {a['source']} -> {a['target']}")
        elif a["action"] == "merge":
            print(f"  [MERGE]  #{a['tracker_id']:02d} {a['sources']} -> {a['target']}")
        elif a["action"] == "create":
            print(f"  [CREATE] #{a['tracker_id']:02d} {a['target']}")

    renames = sum(1 for a in actions if a["action"] == "rename")
    creates = sum(1 for a in actions if a["action"] == "create")
    merges = sum(1 for a in actions if a["action"] == "merge")
    print(f"\nSummary: {renames} renames, {creates} creates, {merges} merges")

    if not args.execute and not args.backup:
        print("\n[DRY RUN] No changes made. Use --execute or --backup to proceed.")
        return

    if args.backup:
        create_backup(user_dir)

    if args.execute or args.backup:
        print("\nExecuting migration...")
        execute_migration(user_dir, actions, rows)
        print("\n✅ Migration complete.")

        # Validate
        jobs_dir = user_dir / "jobs"
        final_dirs = {d.name for d in jobs_dir.iterdir() if d.is_dir()}
        for row in rows:
            target = build_target_name(row)
            if target not in final_dirs:
                print(f"  ⚠️  WARNING: #{row['id']} expected {target} but not found!")


if __name__ == "__main__":
    main()
