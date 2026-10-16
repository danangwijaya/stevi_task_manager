import re
import urllib.request
import json
import sys

GDOC_URL = "https://docs.google.com/document/d/1hbHWoxLoZ9nuNIvHMDXcL-tcW72wY86BW8QEkGTbBkc/export?format=txt"

def fetch_gdoc_text():
    req = urllib.request.Request(
        GDOC_URL,
        headers={"User-Agent": "Mozilla/5.0 (GeoAI Issue Monitor)"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode("utf-8")

def parse_issues(text):
    # Remove BOM if present
    text = text.lstrip("\ufeff")
    lines = text.splitlines()

    issues = []
    current_issue = None

    header_pattern = re.compile(r"^\s*(\d+)[\.\)]\s*(.*)", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = header_pattern.match(stripped)
        if match:
            if current_issue:
                issues.append(current_issue)
            
            num = match.group(1)
            raw_title = match.group(2).strip()
            is_solved = "SOLVED" in raw_title.upper() or "SOLVE" in raw_title.upper()
            title_clean = re.sub(r"\bSOLVED\b|\bSOLVE\b", "", raw_title, flags=re.IGNORECASE).strip()

            current_issue = {
                "number": int(num),
                "title": title_clean or f"Issue {num}",
                "raw_header": stripped,
                "is_solved": is_solved,
                "grid": None,
                "kendala": [],
                "jawab": [],
                "current_section": "kendala"
            }
            continue

        if current_issue:
            upper_line = stripped.upper()
            if "SOLVED" in upper_line:
                current_issue["is_solved"] = True

            grid_match = re.search(r"grid[\s_:]+([A-Za-z0-9_]+)", stripped, re.IGNORECASE)
            if grid_match and not current_issue["grid"]:
                current_issue["grid"] = grid_match.group(1)

            if upper_line.startswith("JAWAB:") or upper_line.startswith("SOLVING:"):
                current_issue["current_section"] = "jawab"
                current_issue["jawab"].append(stripped)
            elif current_issue["current_section"] == "jawab":
                current_issue["jawab"].append(stripped)
            else:
                current_issue["kendala"].append(stripped)

    if current_issue:
        issues.append(current_issue)

    return issues

def check_all_issues():
    print(f"📥 Mengambil data keluhan dari Google Docs...")
    try:
        raw_text = fetch_gdoc_text()
    except Exception as e:
        print(f"❌ Gagal mengambil Google Docs: {e}")
        return

    issues = parse_issues(raw_text)
    total = len(issues)
    solved = sum(1 for i in issues if i["is_solved"])
    pending = [i for i in issues if not i["is_solved"]]

    print(f"\n📊 RANGKUMAN KELUHAN MAPPER:")
    print(f"   • Total Keluhan Tercatat: {total}")
    print(f"   • Sudah Selesai (SOLVED): {solved}")
    print(f"   • Belum Selesai (PENDING): {len(pending)}\n")

    if pending:
        print(f"⚠️ DAFTAR KELUHAN YANG BELUM 'SOLVED' ({len(pending)} item):")
        for p in pending:
            kendala_txt = "\n       ".join(p["kendala"])
            print(f"\n   [{p['number']}] {p['title']} (Grid: {p['grid'] or 'N/A'})")
            if kendala_txt:
                print(f"       {kendala_txt}")
    else:
        print("🎉 SEMUA KELUHAN SUDAH BERSTATUS 'SOLVED'!")

if __name__ == "__main__":
    check_all_issues()
