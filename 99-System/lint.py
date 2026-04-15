#!/usr/bin/env python3
"""
Agent Shared Memory Lint Script v2.1
检查 Obsidian vault 的健康状态，输出 4-Signal 和 Graph Insights。

改进（相对于 v2.0）：
1. 优先使用 PyYAML 解析 frontmatter，没有时才降级到手写解析器
2. 修复 resolve_link 的路径遍历漏洞
3. 增加 10MB 文件大小保护
4. 扫描 log 文件以更准确计算 agent_latest_update
"""
import os
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import date, datetime

# 建议通过环境变量注入，避免硬编码本地路径
VAULT = Path(os.environ.get(
    "AGENT_SHARED_MEMORY_VAULT",
    "/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory"
))
EXCLUDE_DIRS = {".obsidian", "99-System", "_templates"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
TODAY = date.today()

REQUIRED_FIELDS = {"title", "type", "agent", "created", "updated", "tags"}
COVERAGE_DIRS = ["01-Sources", "02-Entities", "04-Tasks", "05-Knowledge", "06-Outputs/queries"]

# 尝试导入标准 YAML 库
try:
    import yaml
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False


def get_all_md_files():
    files = []
    for p in VAULT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.relative_to(VAULT).parts):
            continue
        files.append(p)
    return files


def extract_frontmatter(content):
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()

    if _HAS_YAML:
        try:
            data = yaml.safe_load(fm_text) or {}
            if isinstance(data, dict):
                return data
        except Exception:
            pass  # 降级到手写解析器

    # Fallback 手写解析器（只支持简单键值和单层列表）
    data = {}
    current_key = None
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        if line.strip().startswith("-"):
            val = line.strip().lstrip("-").strip().strip('"').strip("'")
            if current_key:
                if not isinstance(data.get(current_key), list):
                    data[current_key] = [data[current_key]] if current_key in data else []
                data[current_key].append(val)
        elif ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                items = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
                data[key] = items
            else:
                data[key] = val
            current_key = key
    return data


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def extract_wikilinks(content):
    cleaned = re.sub(r"```[\s\S]*?```", "", content)
    cleaned = re.sub(r"`[^`]*`", "", cleaned)
    pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
    return pattern.findall(cleaned)


def resolve_link(link_text, md_files):
    # 防御路径遍历：禁止包含 .. 或绝对路径的链接
    if ".." in link_text or link_text.startswith("/"):
        return None

    target = (VAULT / f"{link_text}.md").resolve()
    # 确保解析后的路径仍在 vault 内
    if not str(target).startswith(str(VAULT.resolve())):
        return None
    if target.exists():
        return target

    link_name = link_text.split("/")[-1].lower()
    link_name_dash = link_name.replace(" ", "-")
    for md in md_files:
        stem = md.stem.lower()
        if stem == link_name or stem.replace(" ", "-") == link_name_dash:
            return md
    return None


def max_connected_component_size(graph, nodes):
    """graph: dict[node] -> set[neighbors] (undirected)"""
    if not nodes:
        return 0
    visited = set()
    max_size = 0

    def dfs(n):
        stack = [n]
        size = 0
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            size += 1
            for nei in graph.get(cur, set()):
                if nei not in visited:
                    stack.append(nei)
        return size

    for n in nodes:
        if n not in visited:
            max_size = max(max_size, dfs(n))
    return max_size


def lint():
    md_files = get_all_md_files()
    all_links = Counter()
    inbound_counts = defaultdict(int)
    inbound_sources = defaultdict(set)
    outbound_targets = defaultdict(set)
    dead_links = []
    malformed_audits = []
    malformed_logs = []
    page_meta = {}
    missing_frontmatter = []
    incomplete_frontmatter = []
    type_counter = Counter()
    tag_counter = Counter()
    agent_latest_update = defaultdict(lambda: date.min)
    stale_pages = []
    summary_pages = []
    task_pages = []
    oversized_files = []

    for md in md_files:
        # 大文件保护
        if md.stat().st_size > MAX_FILE_SIZE:
            oversized_files.append(md.relative_to(VAULT))
            continue

        content = md.read_text(encoding="utf-8")
        rel = md.relative_to(VAULT)
        fm = extract_frontmatter(content)

        # Consistency check
        if not fm:
            missing_frontmatter.append(rel)
        else:
            missing_fields = REQUIRED_FIELDS - set(fm.keys())
            if missing_fields:
                incomplete_frontmatter.append((rel, missing_fields))

        # Parse meta
        page_type = fm.get("type", "unknown")
        agent = fm.get("agent", "unknown")
        updated_str = fm.get("updated", "")
        tags = fm.get("tags", [])
        sources = fm.get("sources", [])
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(sources, str):
            sources = [sources]

        page_meta[rel] = {
            "type": page_type,
            "agent": agent,
            "updated": updated_str,
            "tags": set(tags),
            "sources": set(sources),
        }
        type_counter[page_type] += 1
        for t in tags:
            tag_counter[t] += 1

        updated_dt = parse_date(updated_str)
        if updated_dt:
            agent_latest_update[agent] = max(agent_latest_update[agent], updated_dt)
            age = (TODAY - updated_dt).days
            if age > 30:
                stale_pages.append((rel, age))
            if page_type in ("task-log", "task") or str(rel).startswith("04-Tasks/"):
                task_pages.append((rel, age))

        if page_type == "summary":
            summary_pages.append(rel)

        # Audit/log checks
        if "audit" in str(rel) and rel.name != "resolved":
            if "---" in content:
                if "target:" not in content:
                    malformed_audits.append(f"{rel} missing 'target' in frontmatter")
                if "severity:" not in content:
                    malformed_audits.append(f"{rel} missing 'severity' in frontmatter")
        if rel.parts[0] == "log":
            if not re.match(r"^\d{8}\.md$", rel.name):
                malformed_logs.append(f"{rel} invalid log filename")

        # Links
        links = extract_wikilinks(content)
        for link in links:
            all_links[link] += 1
            target = resolve_link(link, md_files)
            if target:
                target_rel = target.relative_to(VAULT)
                inbound_counts[target_rel] += 1
                inbound_sources[target_rel].add(rel)
                outbound_targets[rel].add(target_rel)
            else:
                dead_links.append((link, str(rel)))

    # Coverage: empty dirs
    empty_dirs = []
    for dname in COVERAGE_DIRS:
        dpath = VAULT / dname
        if dpath.exists() and not list(dpath.rglob("*.md")):
            empty_dirs.append(dname)

    # Orphans
    all_rels = {md.relative_to(VAULT) for md in md_files}
    orphans = [r for r in all_rels if inbound_counts[r] == 0]
    orphans = [
        p for p in orphans
        if str(p) not in {"index.md", "log.md", "欢迎.md", "hot.md"}
        and p.name != "index.md"
        and p.parts[0] not in {"00-SPEC", "log", "audit"}
    ]

    # Frequent missing
    frequent_missing = [
        (link, count) for link, count in all_links.most_common()
        if resolve_link(link, md_files) is None and count >= 3
    ]

    # Source overlap
    source_to_pages = defaultdict(set)
    for rel, meta in page_meta.items():
        for src in meta["sources"]:
            source_to_pages[src].add(rel)

    source_overlaps = []
    for src, pages in source_to_pages.items():
        if len(pages) >= 2:
            page_list = list(pages)
            for i in range(len(page_list)):
                for j in range(i + 1, len(page_list)):
                    a, b = page_list[i], page_list[j]
                    a_links = inbound_sources.get(b, set())
                    b_links = inbound_sources.get(a, set())
                    if a not in a_links and b not in b_links:
                        source_overlaps.append((a, b, src))

    # Bridge nodes
    bridge_nodes = []
    for rel, meta in page_meta.items():
        neighbors = inbound_sources.get(rel, set())
        if len(neighbors) < 3:
            continue
        neighbor_types = Counter()
        for n in neighbors:
            t = page_meta.get(n, {}).get("type", "unknown")
            if t:
                neighbor_types[t] += 1
        if len(neighbor_types) >= 3:
            bridge_nodes.append((rel, dict(neighbor_types)))
    bridge_nodes.sort(key=lambda x: len(x[1]), reverse=True)

    # 4-Signal calculations
    total_pages = len(md_files)
    valid_pages = total_pages - len(missing_frontmatter) - len(incomplete_frontmatter)
    consistency_rate = valid_pages / total_pages if total_pages else 1.0
    orphan_rate = len(orphans) / total_pages if total_pages else 0.0
    avg_indegree = sum(inbound_counts.values()) / total_pages if total_pages else 0.0

    # Connectivity: undirected graph for components
    undirected = defaultdict(set)
    for rel in all_rels:
        for out in outbound_targets.get(rel, set()):
            undirected[rel].add(out)
            undirected[out].add(rel)
    mcc_size = max_connected_component_size(undirected, all_rels)
    connectivity_ratio = mcc_size / total_pages if total_pages else 1.0

    # Freshness: average age of updated pages
    ages = []
    for rel, meta in page_meta.items():
        dt = parse_date(meta.get("updated", ""))
        if dt:
            ages.append((TODAY - dt).days)
    avg_age = sum(ages) / len(ages) if ages else 0

    # GAPS
    agent_blindspots = []

    # 修正：同时扫描 log 文件来更新 agent_latest_update
    log_dir = VAULT / "log"
    if log_dir.exists():
        for log_file in log_dir.glob("*.md"):
            if log_file.stat().st_size > MAX_FILE_SIZE:
                continue
            try:
                log_content = log_file.read_text(encoding="utf-8")
                # 匹配日志行格式：## [HH:MM] action | <agent> | <task>
                for match in re.finditer(r"##\s*\[\d{2}:\d{2}\]\s*[\w-]+\s*\|\s*(\w+)\s*\|", log_content):
                    log_agent = match.group(1).lower()
                    log_date = parse_date(log_file.stem)
                    if log_date:
                        agent_latest_update[log_agent] = max(agent_latest_update[log_agent], log_date)
            except Exception:
                pass

    for a, last_dt in agent_latest_update.items():
        if a != "unknown" and (TODAY - last_dt).days > 7:
            agent_blindspots.append((a, (TODAY - last_dt).days))

    tag_islands = [(tag, count) for tag, count in tag_counter.items() if count == 1]

    # Undigested sources: summary pages not linked from Knowledge/Entities
    undigested_sources = []
    for srel in summary_pages:
        if str(srel) in {"hot.md", "index.md"} or srel.name == "index.md":
            continue
        refs = inbound_sources.get(srel, set())
        has_knowledge_ref = any(
            str(r).startswith("05-Knowledge/") or str(r).startswith("02-Entities/")
            for r in refs
        )
        if not has_knowledge_ref:
            undigested_sources.append(srel)

    stale_tasks = [(rel, age) for rel, age in task_pages if age > 14]

    # Report
    print("=" * 70)
    print("Agent Shared Memory Lint Report")
    print(f"Scan date: {TODAY.isoformat()}")
    print("=" * 70)

    print(f"\n[1] Markdown files scanned: {total_pages}")
    if oversized_files:
        print(f"    Skipped {len(oversized_files)} file(s) > {MAX_FILE_SIZE // (1024 * 1024)} MB")
        for p in oversized_files[:5]:
            print(f"    - {p}")

    print(f"\n--- 4-SIGNAL HEALTH ---")
    print(f"  Coverage    : {len(empty_dirs)} empty dir(s)  " + ("✅ OK" if not empty_dirs else "⚠️  GAP"))
    print(f"  Freshness   : avg age = {avg_age:.1f} days  " + ("✅ OK" if avg_age < 30 else "⚠️  STALE"))
    print(f"  Consistency : {consistency_rate*100:.1f}% compliant  " + ("✅ OK" if consistency_rate == 1.0 else "⚠️  FIX NEEDED"))
    print(f"  Connectivity: orphan_rate={orphan_rate*100:.1f}%, avg_indegree={avg_indegree:.2f}, mcc_ratio={connectivity_ratio*100:.1f}%  " + ("✅ OK" if orphan_rate < 0.1 else "⚠️  LOW"))

    print(f"\n[2] Dead wikilinks: {len(dead_links)}")
    for link, src in dead_links[:10]:
        print(f"    - [[{link}]] from {src}")
    if len(dead_links) > 10:
        print(f"    ... and {len(dead_links) - 10} more")

    print(f"\n[3] Orphan pages: {len(orphans)}")
    for p in orphans[:10]:
        print(f"    - {p}")
    if len(orphans) > 10:
        print(f"    ... and {len(orphans) - 10} more")

    print(f"\n[4] Frequently-linked missing pages (>=3 refs): {len(frequent_missing)}")
    for link, count in frequent_missing[:10]:
        print(f"    - [[{link}]] referenced {count} times")

    print(f"\n--- GRAPH INSIGHTS: SURPRISING CONNECTIONS ---")
    print(f"[5] Bridge nodes (connecting 3+ distinct types): {len(bridge_nodes)}")
    for rel, types in bridge_nodes[:10]:
        types_str = ", ".join([f"{t}({c})" for t, c in types.items()])
        print(f"    - {rel}: {types_str}")

    print(f"\n[6] Source overlap without cross-link: {len(source_overlaps)}")
    for a, b, src in source_overlaps[:10]:
        print(f"    - {a} 和 {b} 共享 source '{src}'，建议互相链接")
    if len(source_overlaps) > 10:
        print(f"    ... and {len(source_overlaps) - 10} more")

    print(f"\n--- GRAPH INSIGHTS: GAPS ---")
    print(f"[7] Agent blindspots (>7 days inactive): {len(agent_blindspots)}")
    for a, days in agent_blindspots:
        print(f"    - {a}: {days} days since last update")

    print(f"\n[8] Tag islands (only 1 occurrence): {len(tag_islands)}")
    for tag, _ in tag_islands[:10]:
        print(f"    - #{tag}")
    if len(tag_islands) > 10:
        print(f"    ... and {len(tag_islands) - 10} more")

    print(f"\n[9] Undigested sources (summary not linked from Knowledge/Entities): {len(undigested_sources)}")
    for p in undigested_sources[:10]:
        print(f"    - {p}")

    print(f"\n[10] Stale tasks (>14 days): {len(stale_tasks)}")
    for p, age in stale_tasks[:10]:
        print(f"    - {p} ({age} days)")

    print(f"\n[11] Frontmatter issues: {len(missing_frontmatter) + len(incomplete_frontmatter)}")
    for p in missing_frontmatter[:5]:
        print(f"    - {p}: missing frontmatter")
    for p, fields in incomplete_frontmatter[:5]:
        print(f"    - {p}: missing {', '.join(fields)}")

    print(f"\n[12] Malformed audit files: {len(malformed_audits)}")
    for msg in malformed_audits:
        print(f"    - {msg}")

    print(f"\n[13] Malformed log files: {len(malformed_logs)}")
    for msg in malformed_logs:
        print(f"    - {msg}")

    print("\n" + "=" * 70)
    # Tag islands in small vaults are expected; treat as insight rather than issue
    penalized_tag_islands = len(tag_islands) if total_pages >= 30 else 0
    total_issues = (
        len(dead_links) + len(orphans) + len(frequent_missing) +
        len(source_overlaps) + len(agent_blindspots) + penalized_tag_islands +
        len(undigested_sources) + len(stale_tasks) +
        len(missing_frontmatter) + len(incomplete_frontmatter) +
        len(malformed_audits) + len(malformed_logs) + len(empty_dirs) +
        len(oversized_files)
    )
    print(f"Total issues found: {total_issues}")
    if total_issues == 0:
        print("Vault is healthy. Good job, agents.")
    else:
        print("Please fix the reported issues.")

    return total_issues


if __name__ == "__main__":
    issues = lint()
    sys.exit(1 if issues > 0 else 0)
