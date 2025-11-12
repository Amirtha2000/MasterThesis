#!/usr/bin/env python3
"""
batch_strip_and_remove_materials.py
One-file utility to remove faces using specific material names from many OBJ files.
It contains both the single-file stripper and a batch driver.

Examples:
  # Process all in a folder, write to "cleaned", remove LayerSurface, compact, recurse
  python batch_strip_and_remove_materials.py batch --input-dir ./objs --output-dir ./cleaned --remove LayerSurface --compact --recursive

  # Process a single file
  python batch_strip_and_remove_materials.py single --input ./in.obj --output ./out.obj --remove LayerSurface --compact
"""

import argparse
import sys
from pathlib import Path
import re

FACE_RE = re.compile(r'^f\s+(.+)$', re.IGNORECASE)
USEMTL_RE = re.compile(r'^usemtl\s+(.+)$', re.IGNORECASE)

def parse_face_tokens(face_payload):
    verts = []
    for part in face_payload.strip().split():
        comps = part.split('/')
        v = int(comps[0]) if comps[0] not in ('', None) else None
        vt = int(comps[1]) if len(comps) >= 2 and comps[1] not in ('', None) else None
        vn = int(comps[2]) if len(comps) >= 3 and comps[2] not in ('', None) else None
        verts.append((v, vt, vn))
    return verts

def rebuild_face_tokens(verts):
    parts = []
    for v, vt, vn in verts:
        if vt is None and vn is None:
            parts.append(f"{v}")
        elif vt is not None and vn is None:
            parts.append(f"{v}/{vt}")
        elif vt is None and vn is not None:
            parts.append(f"{v}//{vn}")
        else:
            parts.append(f"{v}/{vt}/{vn}")
    return "f " + " ".join(parts)

def scan_negative_indices(lines):
    for line in lines:
        m = FACE_RE.match(line)
        if not m:
            continue
        payload = m.group(1)
        for part in payload.split():
            v = part.split('/')[0]
            try:
                if int(v) < 0:
                    return True
            except Exception:
                pass
    return False

def strip_obj_material(input_path, output_path, remove_materials, case_sensitive=False, compact=False):
    remove_set = set(remove_materials if case_sensitive else [s.lower() for s in remove_materials])

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    current_mtl = None
    kept_lines = []
    removed_faces = 0
    kept_faces = 0

    do_compact = compact and not scan_negative_indices(lines)
    used_v = set()
    used_vt = set()
    used_vn = set()

    def is_remove_material(name):
        if name is None:
            return False
        return (name if case_sensitive else name.lower()) in remove_set

    for line in lines:
        um = USEMTL_RE.match(line)
        if um:
            current_mtl = um.group(1).strip()
            kept_lines.append(line)
            continue

        fm = FACE_RE.match(line)
        if fm:
            if is_remove_material(current_mtl):
                removed_faces += 1
                continue
            else:
                kept_faces += 1
                if do_compact:
                    verts = parse_face_tokens(fm.group(1))
                    for v, vt, vn in verts:
                        if v is not None and v > 0:
                            used_v.add(v)
                        if vt is not None and vt > 0:
                            used_vt.add(vt)
                        if vn is not None and vn > 0:
                            used_vn.add(vn)
                    kept_lines.append(("__FACE__", verts))
                else:
                    kept_lines.append(line)
            continue

        kept_lines.append(line)

    if not do_compact:
        with open(output_path, "w", encoding="utf-8") as out:
            for item in kept_lines:
                if isinstance(item, tuple) and item and item[0] == "__FACE__":
                    out.write(rebuild_face_tokens(item[1]) + "\n")
                else:
                    out.write(item)
        return {"removed_faces": removed_faces, "kept_faces": kept_faces, "compaction": False}

    v_lines = []
    vt_lines = []
    vn_lines = []
    other_lines = []

    for item in kept_lines:
        if isinstance(item, str):
            if item.startswith('v '):
                v_lines.append(item)
            elif item.startswith('vt '):
                vt_lines.append(item)
            elif item.startswith('vn '):
                vn_lines.append(item)
            else:
                other_lines.append(item)
        else:
            other_lines.append(item)

    def build_remap(used_set, total_count):
        used_sorted = sorted([i for i in used_set if 1 <= i <= total_count])
        remap = {}
        for new_idx, old_idx in enumerate(used_sorted, start=1):
            remap[old_idx] = new_idx
        return remap, used_sorted

    v_remap, used_v_sorted = build_remap(used_v, len(v_lines))
    vt_remap, used_vt_sorted = build_remap(used_vt, len(vt_lines))
    vn_remap, used_vn_sorted = build_remap(used_vn, len(vn_lines))

    new_v_lines = [v_lines[i-1] for i in used_v_sorted]
    new_vt_lines = [vt_lines[i-1] for i in used_vt_sorted]
    new_vn_lines = [vn_lines[i-1] for i in used_vn_sorted]

    with open(output_path, "w", encoding="utf-8") as out:
        emitted_v = emitted_vt = emitted_vn = False
        for item in kept_lines:
            if isinstance(item, str):
                if item.startswith('v '):
                    if not emitted_v:
                        for ln in new_v_lines:
                            out.write(ln)
                        emitted_v = True
                    continue
                elif item.startswith('vt '):
                    if not emitted_vt:
                        for ln in new_vt_lines:
                            out.write(ln)
                        emitted_vt = True
                    continue
                elif item.startswith('vn '):
                    if not emitted_vn:
                        for ln in new_vn_lines:
                            out.write(ln)
                        emitted_vn = True
                    continue
                else:
                    out.write(item)
            else:
                _, verts = item
                remapped = []
                for v, vt, vn in verts:
                    rv = v_remap.get(v, None) if (v is not None and v > 0) else v
                    rvt = vt_remap.get(vt, None) if (vt is not None and vt > 0) else vt
                    rvn = vn_remap.get(vn, None) if (vn is not None and vn > 0) else vn
                    if rv is None:
                        remapped = None
                        break
                    remapped.append((rv, rvt, rvn))
                if remapped is not None:
                    out.write(rebuild_face_tokens(remapped) + "\n")

    return {
        "removed_faces": removed_faces,
        "kept_faces": kept_faces,
        "compaction": True,
        "vertices_kept": len(new_v_lines),
        "uvs_kept": len(new_vt_lines),
        "normals_kept": len(new_vn_lines),
    }

def run_single(args):
    stats = strip_obj_material(
        input_path=args.input,
        output_path=args.output,
        remove_materials=args.remove,
        case_sensitive=args.case_sensitive,
        compact=args.compact,
    )
    print(f"Removed faces: {stats['removed_faces']}")
    print(f"Kept faces:    {stats['kept_faces']}")
    print(f"Compaction:    {'enabled' if stats['compaction'] else 'disabled'}")
    if stats['compaction']:
        print(f"Vertices kept: {stats['vertices_kept']}")
        print(f"UVs kept:      {stats['uvs_kept']}")
        print(f"Normals kept:  {stats['normals_kept']}")

def run_batch(args):
    in_dir = Path(args.input_dir).expanduser().resolve()
    if not in_dir.is_dir():
        print(f"[ERROR] Input directory not found: {in_dir}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*.obj" if args.recursive else "*.obj"
    files = sorted(in_dir.glob(pattern))

    if not files:
        print("[INFO] No .obj files found.")
        return

    total = len(files)
    ok = 0
    skipped = 0
    failed = 0

    for i, f in enumerate(files, 1):
        rel = f.relative_to(in_dir)
        if out_dir:
            out_path = (out_dir / rel).with_suffix(".obj")
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_path = f.with_name(f.stem + args.suffix + ".obj")

        if out_path.exists() and not args.overwrite:
            print(f"[SKIP] ({i}/{total}) {rel} -> {out_path} (exists)")
            skipped += 1
            continue

        try:
            stats = strip_obj_material(
                input_path=str(f),
                output_path=str(out_path),
                remove_materials=args.remove,
                case_sensitive=args.case_sensitive,
                compact=args.compact,
            )
            print(f"[ OK ] ({i}/{total}) {rel} -> {out_path.name} | removed={stats['removed_faces']} kept={stats['kept_faces']} compact={'y' if stats['compaction'] else 'n'}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] ({i}/{total}) {rel} -> {e}", file=sys.stderr)
            failed += 1

    print("\n=== Summary ===")
    print(f"Found:    {total}")
    print(f"Success:  {ok}")
    print(f"Skipped:  {skipped}")
    print(f"Failed:   {failed}")

def main():
    ap = argparse.ArgumentParser(description="Remove faces using specified materials from OBJ files (single or batch).")
    sub = ap.add_subparsers(dest="mode")

    single = sub.add_parser("single", help="Process a single input/output pair")
    single.add_argument("--input", required=True, help="Path to input OBJ")
    single.add_argument("--output", required=True, help="Path to output OBJ")
    single.add_argument("--remove", nargs="+", required=True, help="Material name(s) to remove")
    single.add_argument("--case-sensitive", action="store_true", help="Case-sensitive material matching")
    single.add_argument("--compact", action="store_true", help="Drop unused vertices/UVs/normals and reindex faces (positive indices only)")
    single.set_defaults(func=run_single)

    batch = sub.add_parser("batch", help="Process all OBJ files in a folder")
    batch.add_argument("--input-dir", required=True, help="Directory containing .obj files")
    batch.add_argument("--output-dir", help="Directory to write cleaned .obj files (defaults to input-dir)")
    batch.add_argument("--remove", nargs="+", required=True, help="Material name(s) to remove")
    batch.add_argument("--suffix", default="_stripped", help="Suffix appended to filename if output-dir not set (e.g., _nosheet)")
    batch.add_argument("--compact", action="store_true", help="Enable compaction/reindexing")
    batch.add_argument("--case-sensitive", action="store_true", help="Case-sensitive material matching")
    batch.add_argument("--recursive", action="store_true", help="Recurse into subdirectories to find .obj files")
    batch.add_argument("--overwrite", action="store_true", help="Allow overwriting existing outputs")
    batch.set_defaults(func=run_batch)

    args = ap.parse_args()
    if args.mode is None:
        ap.print_help()
        sys.exit(2)
    args.func(args)

if __name__ == "__main__":
    main()
