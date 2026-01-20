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
    
    # RGBAモードに変換（透過処理のため）
    img_rgba = cropped.convert('RGBA')
    
    # 暗いオーバーレイを追加（40%の黒）
    overlay = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 102))  # alpha=102は約40%
    img_with_overlay = Image.alpha_composite(img_rgba, overlay)
    
    # 描画用オブジェクトを作成
    draw = ImageDraw.Draw(img_with_overlay, 'RGBA')
    
    # 再生ボタンの中心位置
    center_x = target_width // 2
    center_y = target_height // 2
    
    # 外側の円の影（黒、半透明）
    circle_radius = 80
    shadow_offset = 8
    draw.ellipse(
        [center_x - circle_radius + shadow_offset, center_y - circle_radius + shadow_offset,
         center_x + circle_radius + shadow_offset, center_y + circle_radius + shadow_offset],
        fill=(0, 0, 0, 100)  # 黒い影
    )
    
    # 外側の円（白、不透明）
    draw.ellipse(
        [center_x - circle_radius, center_y - circle_radius,
         center_x + circle_radius, center_y + circle_radius],
        fill=(255, 255, 255, 255),  # 完全に白、不透明
        outline=(240, 240, 240, 255),
        width=4
    )
    
    # 再生ボタンの三角形（右向き、黒）
    triangle_size = 35
    # 三角形を少し右にオフセット（視覚的に中央に見えるように）
    offset_x = 8
    triangle = [
        (center_x - triangle_size//2 + offset_x, center_y - triangle_size),  # 上
        (center_x - triangle_size//2 + offset_x, center_y + triangle_size),  # 下
        (center_x + triangle_size + offset_x, center_y)  # 右
    ]
    draw.polygon(triangle, fill=(30, 30, 30, 255))  # ほぼ黒
    
    # RGBに変換して保存
    final_img = img_with_overlay.convert('RGB')
    final_img.save(output_file, 'PNG', quality=95)
    print(f"✅ 再生ボタン付きカードを生成: {output_file}")

if __name__ == "__main__":
    create_linkcard_image('card_image.jpg', 'card_image_v2.png', offset_y=50)
