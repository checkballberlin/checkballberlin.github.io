#!/usr/bin/env python3
"""Export the Checkball feed for the open web version.

Input:  a dump of the app database as the Checkball agent writes it with
        ArtifactData (list/get with out_dir): DUMP/items/<id>.json and DUMP/meta/agent.json
Output: data/items.json and data/meta.json next to index.html

Public rule: an entry goes into the open web version only if it has a public source
(sourceUrl or regUrl) or is released with "public": true in the database. Internal BBV plans
stay out until they are released.

Usage: python3 tools/export_data.py DUMP_DIR [SITE_DIR]
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import calendar_ics  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
DUMP = pathlib.Path(sys.argv[1])
SITE = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent.parent
TYPES = {"news", "turnier", "gym", "event"}


def is_public(item):
    if item.get("public") is True:
        return True
    if item.get("public") is False:
        return False
    return any(isinstance(item.get(k), str) and item[k].startswith("https://") for k in ("sourceUrl", "regUrl"))


def main():
    files = sorted((DUMP / "items").glob("*.json"))
    if not files:
        sys.exit(f"Keine Einträge in {DUMP / 'items'} gefunden")
    items, held_back = [], []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("type") not in TYPES or not data.get("title"):
            continue
        item = {"id": f.stem, **{k: v for k, v in data.items() if k != "id"}}
        (items if is_public(item) else held_back).append(item)

    now = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")
    out = SITE / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "items.json").write_text(
        json.dumps({"generatedAt": now, "items": items}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    meta_file = DUMP / "meta" / "agent.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    if not isinstance(meta, dict):
        meta = {}
    stats = meta.get("stats") if isinstance(meta.get("stats"), dict) else {}
    meta["stats"] = {**stats, "items": len(items)}
    meta["exportedAt"] = now
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    try:
        cal = calendar_ics.write_all(items, out)
        print(f"Kalender: {cal[0]} Turniere, {cal[1]} Open Gyms, {cal[2]} gesamt")
    except Exception as e:  # Kalender darf den Export nie blockieren
        print(f"Kalender nicht erzeugt: {e}")

    print(f"{len(items)} öffentliche Einträge exportiert, {len(held_back)} zurückgehalten"
          + (": " + ", ".join(i["id"] for i in held_back) if held_back else ""))


if __name__ == "__main__":
    main()
