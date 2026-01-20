"""画像を上部基準でリンクカードサイズにリサイズ"""
from PIL import Image

def resize_top_aligned(input_file, output_file, target_width=1200, target_height=630, offset_y=0):
    """
    画像を上部基準でリサイズ（アスペクト比保持）
    
    Args:
        input_file: 入力画像ファイル
        output_file: 出力画像ファイル
        target_width: 目標幅
        target_height: 目標高さ
        offset_y: 切り取り開始位置のオフセット（ピクセル）正の数で下にずれる
    """
    # 元画像を読み込み
    img = Image.open(input_file)
    original_size = img.size
    print(f"元画像サイズ: {img.width}x{img.height}")
    
    # 横幅を1200pxに合わせて拡大・縮小
    ratio = target_width / img.width
    new_height = int(img.height * ratio)
    
    resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
    print(f"リサイズ後: {target_width}x{new_height}")
    
    # 高さが630px以上なら指定位置から切り取り
    if new_height >= target_height + offset_y:
        final = resized.crop((0, offset_y, target_width, target_height + offset_y))
        print(f"切り取り: Y={offset_y}から{target_height + offset_y} ({target_width}x{target_height})")
    else:
        # 高さが足りない場合は白背景で埋める（通常は起こらない）
        final = Image.new('RGB', (target_width, target_height), (255, 255, 255))
        final.paste(resized, (0, 0))
        print(f"白背景で埋めました: {target_width}x{target_height}")
    
    # 保存
    final.save(output_file, 'PNG', quality=95)
    print(f"✅ 保存完了: {output_file}")

if __name__ == "__main__":
    # 50ピクセル下にずらす（顔がより中央に来るように調整）
    resize_top_aligned('card_image.jpg', 'card_image_v2.png', offset_y=50)
