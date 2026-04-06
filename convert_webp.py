#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  Dolce far niente — WebP 轉換 + 尺寸更新  v3

  一次完成：
    1. 把 JPG 原圖轉成 WebP（gallery + thumbs + hero）
    2. 用實際 WebP 的真實寬高更新 JSON

  用法：
    cd dolce_dynamic_test
    python convert_webp.py

  需要：pip install Pillow
═══════════════════════════════════════════════════════════════
"""

import os, json, sys, glob

try:
    from PIL import Image, ImageOps
except ImportError:
    print("❌ 請先安裝 Pillow：pip install Pillow")
    sys.exit(1)

JSON_FILE = 'photos.json'
ROOT = '.'
stats = {'converted': 0, 'skipped': 0, 'saved_mb': 0, 'dims_fixed': 0}


def convert_image(src_path, dst_path, max_width, quality):
    if os.path.exists(dst_path):
        stats['skipped'] += 1
        return
    try:
        with Image.open(src_path) as img:
            try: img = ImageOps.exif_transpose(img)
            except: pass
            w, h = img.size
            if w > max_width:
                img = img.resize((max_width, int(h * max_width / w)), Image.LANCZOS)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            img.save(dst_path, 'WEBP', quality=quality, method=4)
            src_sz = os.path.getsize(src_path)
            dst_sz = os.path.getsize(dst_path)
            saved = (src_sz - dst_sz) / (1024 * 1024)
            stats['converted'] += 1
            stats['saved_mb'] += max(saved, 0)
            print(f"  ✓ {os.path.basename(dst_path):40s}  {src_sz//1024:>6d}KB → {dst_sz//1024:>4d}KB  ({saved:.1f}MB saved)")
    except Exception as e:
        print(f"  ✗ {src_path}: {e}")


def find_original(webp_path):
    base = os.path.splitext(webp_path)[0]
    for ext in ['.JPG', '.jpg', '.jpeg', '.JPEG', '.png', '.PNG']:
        candidate = base + ext
        if os.path.exists(candidate):
            return candidate
    return None


def fix_dimensions(photo):
    """讀取實際 WebP 檔案的寬高，更新 JSON 裡的 width/height"""
    src = photo.get('src', '')
    if not src:
        return
    path = os.path.join(ROOT, src)
    if not os.path.exists(path):
        return
    try:
        with Image.open(path) as img:
            w, h = img.size
            old_w = photo.get('width', 0)
            old_h = photo.get('height', 0)
            if old_w != w or old_h != h:
                photo['width'] = w
                photo['height'] = h
                stats['dims_fixed'] += 1
    except:
        pass


def main():
    json_path = os.path.join(ROOT, JSON_FILE)
    if not os.path.exists(json_path):
        print(f"❌ 找不到 {JSON_FILE}，請在 repo 根目錄執行")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    settings = data.get('settings', {})
    QUALITY   = settings.get('quality', 82)
    GALLERY_W = settings.get('gallery_max_w', 2400)
    HERO_W    = settings.get('hero_max_w', 1920)
    THUMB_W   = settings.get('thumb_max_w', 600)
    hero_list = data.get('hero', [])

    print("═" * 60)
    print(f"  Dolce far niente — WebP 轉換 + 尺寸更新  v3")
    print(f"  JSON: {JSON_FILE}")
    print(f"  Quality: {QUALITY}  |  Gallery: {GALLERY_W}px  |  Hero: {HERO_W}px  |  Thumb: {THUMB_W}px")
    print("═" * 60)

    # ══════════════════════════════════════
    #  STEP 1：轉換 WebP
    # ══════════════════════════════════════

    # ── Hero ──
    print(f"\n📷 Step 1 — 轉換 WebP")
    print(f"\n  Hero（{HERO_W}px）— {len(hero_list)} 張:")
    hero_dir = os.path.join(ROOT, 'images', 'hero')
    os.makedirs(hero_dir, exist_ok=True)

    for h in hero_list:
        dst_path = os.path.join(ROOT, h['src'])
        if os.path.exists(dst_path):
            stats['skipped'] += 1
            continue
        orig = find_original(dst_path)
        if not orig:
            basename_no_ext = os.path.splitext(os.path.basename(h['src']))[0]
            for j in glob.glob(os.path.join(hero_dir, '*')):
                if os.path.splitext(os.path.basename(j))[0] == basename_no_ext and not j.endswith('.webp'):
                    orig = j; break
        if orig:
            convert_image(orig, dst_path, HERO_W, QUALITY)
        else:
            print(f"  ⚠ 找不到原圖: {h['src']}")

    # ── Gallery + Thumbs ──
    all_photos = []
    def collect(obj):
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and 'src' in item:
                    all_photos.append(item)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('hero', 'settings'): continue
                collect(v)
    collect(data)

    print(f"\n  Gallery（{GALLERY_W}px）+ Thumb（{THUMB_W}px）— {len(all_photos)} 張:\n")

    for photo in all_photos:
        dst_path = os.path.join(ROOT, photo['src'])
        if not os.path.exists(dst_path):
            orig = find_original(dst_path)
            if orig: convert_image(orig, dst_path, GALLERY_W, QUALITY)
            else: print(f"  ⚠ 找不到原圖: {photo['src']}")
        else:
            stats['skipped'] += 1

        thumb_rel = photo.get('thumb', '')
        if thumb_rel:
            thumb_dst = os.path.join(ROOT, thumb_rel)
            if not os.path.exists(thumb_dst):
                thumb_orig = find_original(thumb_dst)
                if thumb_orig:
                    convert_image(thumb_orig, thumb_dst, THUMB_W, QUALITY)
                else:
                    gallery_orig = find_original(dst_path)
                    if gallery_orig:
                        print(f"  ⚠ thumb 原檔不存在，從原圖生成")
                        convert_image(gallery_orig, thumb_dst, THUMB_W, QUALITY)
            else:
                stats['skipped'] += 1

    print(f"\n  轉換: {stats['converted']}  跳過: {stats['skipped']}  節省: {stats['saved_mb']:.1f} MB")

    # ══════════════════════════════════════
    #  STEP 2：更新 JSON 尺寸
    # ══════════════════════════════════════

    print(f"\n📐 Step 2 — 更新 JSON 尺寸（從實際 WebP 讀取）\n")

    for photo in all_photos:
        fix_dimensions(photo)

    # Hero 也更新
    for h in hero_list:
        path = os.path.join(ROOT, h['src'])
        if os.path.exists(path):
            try:
                with Image.open(path) as img:
                    h['width'] = img.size[0]
                    h['height'] = img.size[1]
            except:
                pass

    # ── 寫回 JSON ──
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  尺寸更新: {stats['dims_fixed']} 張")
    print(f"  ✓ {JSON_FILE} 已儲存")

    # ── 完成 ──
    print("\n" + "═" * 60)
    print(f"  ✅ 全部完成！")
    print(f"     WebP 轉換: {stats['converted']} 張  |  節省: {stats['saved_mb']:.1f} MB")
    print(f"     尺寸更新: {stats['dims_fixed']} 張")
    print("═" * 60)
    print(f"\n📋 接下來：  git add . && git commit -m 'WebP update' && git push")


if __name__ == '__main__':
    main()
