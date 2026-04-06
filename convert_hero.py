#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  Hero 幻燈片 — JPG → WebP 轉換

  把 images/hero/ 裡的 JPG 轉成 WebP
  
  建議參數（已設定好）：
    寬度 1920px — 涵蓋 99% 螢幕，Full HD 滿版不會糊
    Quality 85  — 攝影作品用，肉眼看不出與原圖差異
                  比 82 稍高，因為 hero 是首頁門面要好看
                  檔案大約 200-400KB（原圖 3-8MB）

  用法：
    cd dolce_dynamic_test
    python convert_hero.py
    
  需要：pip install Pillow
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import glob

try:
    from PIL import Image, ImageOps
except ImportError:
    print("❌ 請先安裝 Pillow：pip install Pillow")
    sys.exit(1)

# ── 設定 ──
HERO_DIR  = os.path.join('.', 'images', 'hero')
MAX_WIDTH = 1920    # 幻燈片最大寬度（px）
QUALITY   = 85      # WebP 品質（85 = 攝影首頁推薦）


def convert(src_path):
    basename = os.path.splitext(os.path.basename(src_path))[0]
    dst_path = os.path.join(HERO_DIR, basename + '.webp')

    if os.path.exists(dst_path):
        src_kb = os.path.getsize(src_path) // 1024
        dst_kb = os.path.getsize(dst_path) // 1024
        print(f"  ⏭ {basename}.webp 已存在（{dst_kb}KB），跳過")
        return 0

    try:
        with Image.open(src_path) as img:
            # 處理 EXIF 旋轉
            try:
                img = ImageOps.exif_transpose(img)
            except:
                pass

            w, h = img.size

            # 等比縮放到 MAX_WIDTH
            if w > MAX_WIDTH:
                new_h = int(h * MAX_WIDTH / w)
                img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

            img.save(dst_path, 'WEBP', quality=QUALITY, method=4)

            src_kb = os.path.getsize(src_path) // 1024
            dst_kb = os.path.getsize(dst_path) // 1024
            ratio = dst_kb / src_kb * 100

            print(f"  ✓ {basename}")
            print(f"    {w}×{h} → {img.size[0]}×{img.size[1]}")
            print(f"    {src_kb:,}KB → {dst_kb:,}KB（{ratio:.0f}%，省 {(src_kb-dst_kb):,}KB）")
            return src_kb - dst_kb

    except Exception as e:
        print(f"  ✗ {basename}: {e}")
        return 0


def main():
    if not os.path.isdir(HERO_DIR):
        print(f"❌ 找不到 {HERO_DIR}，請在 repo 根目錄執行")
        sys.exit(1)

    # 找所有 JPG（不含已轉好的 WebP）
    jpgs = sorted(
        glob.glob(os.path.join(HERO_DIR, '*.JPG')) +
        glob.glob(os.path.join(HERO_DIR, '*.jpg')) +
        glob.glob(os.path.join(HERO_DIR, '*.jpeg')) +
        glob.glob(os.path.join(HERO_DIR, '*.JPEG'))
    )

    if not jpgs:
        print(f"⚠ {HERO_DIR} 裡沒有 JPG 檔案")
        print(f"  請先把要當幻燈片的照片複製到 {HERO_DIR}/")
        sys.exit(0)

    print("═" * 50)
    print("  Hero 幻燈片 — WebP 轉換")
    print(f"  寬度: {MAX_WIDTH}px  |  Quality: {QUALITY}")
    print("═" * 50)
    print(f"\n  找到 {len(jpgs)} 張 JPG：\n")

    total_saved = 0
    converted = 0

    for jpg in jpgs:
        saved = convert(jpg)
        if saved > 0:
            total_saved += saved
            converted += 1
        print()

    print("═" * 50)
    print(f"  ✅ 完成！ 轉換: {converted} 張  |  節省: {total_saved:,}KB（{total_saved/1024:.1f}MB）")
    print("═" * 50)
    print()

    # 列出最終 hero 資料夾內容
    webps = sorted(glob.glob(os.path.join(HERO_DIR, '*.webp')))
    if webps:
        print("  📂 images/hero/ 內容：")
        for wp in webps:
            kb = os.path.getsize(wp) // 1024
            print(f"     {os.path.basename(wp):40s} {kb:>5,}KB")


if __name__ == '__main__':
    main()
