"""リンクカード用の画像に再生ボタンと暗いオーバーレイを追加"""
from PIL import Image, ImageDraw

def create_linkcard_image(input_file, output_file, target_width=1200, target_height=630, offset_y=50):
    """
    リンクカード用画像を生成（再生ボタン付き）
    
    Args:
        input_file: 入力画像ファイル
        output_file: 出力画像ファイル
        target_width: 目標幅
        target_height: 目標高さ
        offset_y: 切り取り開始位置のオフセット
    """
    # 元画像を読み込み
    img = Image.open(input_file)
    print(f"元画像サイズ: {img.width}x{img.height}")
    
    # 横幅を1200pxに合わせて拡大・縮小
    ratio = target_width / img.width
    new_height = int(img.height * ratio)
    resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
    print(f"リサイズ後: {target_width}x{new_height}")
    
    # 指定位置から切り取り
    if new_height >= target_height + offset_y:
        cropped = resized.crop((0, offset_y, target_width, target_height + offset_y))
        print(f"切り取り: Y={offset_y}から{target_height + offset_y}")
    else:
        cropped = Image.new('RGB', (target_width, target_height), (255, 255, 255))
        cropped.paste(resized, (0, 0))
    
    # RGBAモードに変換
    img_rgba = cropped.convert('RGBA')
    
    # オーバーレイなし、画像そのままを使用
    img_with_overlay = img_rgba
    print("✅ オーバーレイなし（元画像そのまま）")
    
    # RGBに変換して保存
    final_img = img_with_overlay.convert('RGB')
    final_img.save(output_file, 'PNG', quality=95)
    print(f"✅ 再生ボタン付きカードを生成: {output_file}")

if __name__ == "__main__":
    create_linkcard_image('card_image.jpg', 'card_image_v2.png', offset_y=50)
