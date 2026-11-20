from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]

def test_six_layout_families_exist():
    layouts = list((ROOT / "templates/layouts").iterdir())
    assert len([p for p in layouts if p.is_dir()]) >= 6

def test_categories_map_to_different_layouts():
    cats = {}
    for p in (ROOT / "templates/categories").glob("*.json"):
        data = json.loads(p.read_text())
        cats[data["category"]] = data["layoutFamily"]
    assert len(set(cats.values())) >= 6
