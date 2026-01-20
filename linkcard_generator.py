import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import io
import requests

class MetadataFetcher:
    """URLからメタデータを取得するクラス（OGPフォールバック対応）"""
    
    async def fetch(self, url: str) -> dict:
        """メタデータを取得"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(500)
                
                metadata = {
                    'title': await self._get_title(page, url),
                    'description': await self._get_description(page),
                    'image': await self._get_image(page, url),
                    'url': url
                }
                
                return metadata
                
            except Exception as e:
                print(f"エラー: {e}")
                return self._get_fallback_metadata(url)
            finally:
                await browser.close()
    
    async def _get_title(self, page, url: str) -> str:
        """タイトルを優先順位付きで取得"""
        selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'meta[property="og:site_name"]',
            'title',
            'h1'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    if 'meta' in selector:
                        content = await element.get_attribute('content')
                    else:
                        content = await element.inner_text()
                    
                    if content and content.strip():
                        return content.strip()
            except:
                continue
        
        # デフォルト: ドメイン名
        return urlparse(url).netloc
    
    async def _get_description(self, page) -> str:
        """説明文を優先順位付きで取得"""
        selectors = [
            'meta[property="og:description"]',
            'meta[name="twitter:description"]',
            'meta[name="description"]',
            'meta[itemprop="description"]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    content = await element.get_attribute('content')
                    if content and content.strip():
                        return content.strip()[:200]  # 最大200文字
            except:
                continue
        
        # フォールバック: 最初のpタグ
        try:
            p_element = await page.query_selector('p')
            if p_element:
                text = await p_element.inner_text()
                if text and text.strip():
                    return text.strip()[:200]
        except:
            pass
        
        return ""
    
    async def _get_image(self, page, url: str) -> str:
        """画像URLを優先順位付きで取得"""
        selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            'meta[itemprop="image"]',
            'link[rel="image_src"]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    if 'meta' in selector:
                        image_url = await element.get_attribute('content')
                    else:
                        image_url = await element.get_attribute('href')
                    
                    if image_url:
                        # 相対URLを絶対URLに変換
                        return urljoin(url, image_url)
            except:
                continue
        
        return None
    
    def _get_fallback_metadata(self, url: str) -> dict:
        """フォールバックメタデータ"""
        parsed = urlparse(url)
        return {
            'title': parsed.netloc,
            'description': '',
            'image': None,
            'url': url
        }


class CardGenerator:
    """リンクカード画像を生成するクラス（YouTubeサムネイル風）"""
    
    def __init__(self):
        self.width = 1200
        self.height = 630
        self.bg_color = (30, 30, 30)  # ダークグレー背景
        
    def generate(self, metadata: dict, output_path: str):
        """カード画像を生成（YouTubeサムネイル風）"""
        # キャンバス作成
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        
        # サムネイル画像を全面に配置
        if metadata['image']:
            try:
                thumb_img = self._download_image(metadata['image'])
                if thumb_img:
                    # 画像を1200x630にフィット（アスペクト比を保ちつつクロップ）
                    thumb_img = self._resize_and_crop(thumb_img, self.width, self.height)
                    img.paste(thumb_img, (0, 0))
            except Exception as e:
                print(f"画像の読み込みに失敗: {e}")
                # 背景色のまま
        
        # 半透明のグラデーションオーバーレイを作成（下部を暗く）
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # グラデーション（下部200pxを徐々に暗く）
        gradient_height = 300
        for y in range(gradient_height):
            alpha = int((y / gradient_height) * 180)  # 0→180の透明度
            overlay_draw.rectangle(
                [(0, self.height - gradient_height + y), (self.width, self.height - gradient_height + y + 1)],
                fill=(0, 0, 0, alpha)
            )
        
        # オーバーレイを合成
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        # テキストを描画
        draw = ImageDraw.Draw(img)
        
        # フォント設定
        try:
            title_font = ImageFont.truetype("msgothic.ttc", 56)
            desc_font = ImageFont.truetype("msgothic.ttc", 32)
            url_font = ImageFont.truetype("msgothic.ttc", 24)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            url_font = ImageFont.load_default()
        
        # テキストのパディング
        padding_x = 40
        text_width = self.width - (padding_x * 2)
        
        # タイトル（下部に配置）
        title = metadata['title']
        title_y = self.height - 220
        self._draw_wrapped_text(
            draw, title, (padding_x, title_y), text_width,
            title_font, (255, 255, 255), max_lines=2
        )
        
        # 説明文（タイトルの下）
        if metadata['description']:
            desc_y = self.height - 120
            self._draw_wrapped_text(
                draw, metadata['description'], (padding_x, desc_y), text_width,
                desc_font, (230, 230, 230), max_lines=2
            )
        
        # ドメイン名（右下）
        domain = urlparse(metadata['url']).netloc
        url_y = self.height - 40
        url_x = self.width - padding_x
        
        # テキストの幅を計算して右寄せ
        bbox = draw.textbbox((0, 0), domain, font=url_font)
        text_width = bbox[2] - bbox[0]
        draw.text((url_x - text_width, url_y), domain, font=url_font, fill=(200, 200, 200))
        
        # 保存
        img.save(output_path, 'PNG', quality=95)
        print(f"リンクカードを生成しました: {output_path}")
    
    def _download_image(self, url: str) -> Image.Image:
        """画像をダウンロード"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
        except:
            pass
        return None
    
    def _resize_and_crop(self, img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """画像をリサイズ＆クロップ（アスペクト比を保ちつつ全面に配置）"""
        # 元の画像のアスペクト比
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # 画像が横長：高さを合わせて、幅をクロップ
            new_height = target_height
            new_width = int(img.width * (target_height / img.height))
        else:
            # 画像が縦長：幅を合わせて、高さをクロップ
            new_width = target_width
            new_height = int(img.height * (target_width / img.width))
        
        # リサイズ
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 中央でクロップ
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img.crop((left, top, right, bottom))
    
    def _draw_wrapped_text(self, draw, text: str, position: tuple, max_width: int, 
                           font, color: tuple, max_lines: int = 3):
        """折り返しテキストを描画"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 最大行数で切り捨て
        lines = lines[:max_lines]
        if len(lines) == max_lines and len(text) > sum(len(l) for l in lines):
            lines[-1] = lines[-1][:50] + "..."
        
        # 描画
        y = position[1]
        for line in lines:
            draw.text((position[0], y), line, font=font, fill=color)
            bbox = draw.textbbox((0, 0), line, font=font)
            y += bbox[3] - bbox[1] + 10


class HTMLGenerator:
    """OGP対応HTMLファイルを生成するクラス"""
    
    def __init__(self, base_url: str = ""):
        """初期化
        
        Args:
            base_url: GitHub PagesのベースURL（例: https://username.github.io/linkcard）
        """
        self.base_url = base_url.rstrip('/')
    
    def generate(self, metadata: dict, image_filename: str, output_path: str = "linkcard.html"):
        """OGPタグ付きHTMLファイルを生成"""
        # 画像URLを絶対URLに変換
        if self.base_url:
            image_url = f"{self.base_url}/{image_filename}"
        else:
            image_url = image_filename
        
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{metadata['url']}">
    <meta property="og:title" content="{self._escape_html(metadata['title'])}">
    <meta property="og:description" content="{self._escape_html(metadata['description'])}">
    <meta property="og:image" content="{image_url}">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{metadata['url']}">
    <meta name="twitter:title" content="{self._escape_html(metadata['title'])}">
    <meta name="twitter:description" content="{self._escape_html(metadata['description'])}">
    <meta name="twitter:image" content="{image_url}">
    
    <title>{self._escape_html(metadata['title'])}</title>
    
    <!-- 自動リダイレクト（3秒後） -->
    <meta http-equiv="refresh" content="3;url={metadata['url']}">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 600px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .redirect-message {{
            color: #666;
            margin-bottom: 20px;
        }}
        a {{
            color: #1da1f2;
            text-decoration: none;
            font-weight: bold;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>リダイレクト中...</h1>
        <p class="redirect-message">3秒後に元のページに移動します。</p>
        <p>自動で移動しない場合は、<a href="{metadata['url']}">こちらをクリック</a>してください。</p>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTMLファイルを生成しました: {output_path}")
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ処理"""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))


class LinkCardGenerator:
    """リンクカード生成のメインクラス"""
    
    def __init__(self, base_url: str = ""):
        """初期化
        
        Args:
            base_url: GitHub PagesのベースURL（例: https://username.github.io/linkcard）
        """
        self.fetcher = MetadataFetcher()
        self.generator = CardGenerator()
        self.html_generator = HTMLGenerator(base_url)
    
    async def generate(self, url: str, output_path: str = "linkcard.png", generate_html: bool = False):
        """リンクカードを生成"""
        print(f"メタデータを取得中: {url}")
        metadata = await self.fetcher.fetch(url)
        
        print(f"タイトル: {metadata['title']}")
        print(f"説明: {metadata['description'][:50]}..." if metadata['description'] else "説明: なし")
        print(f"画像: {metadata['image']}" if metadata['image'] else "画像: なし")
        
        print("カード画像を生成中...")
        self.generator.generate(metadata, output_path)
        
        if generate_html:
            print("HTMLファイルを生成中...")
            # 画像ファイル名を取得（絶対URLに変換する必要がある場合は後で調整）
            image_filename = Path(output_path).name
            html_path = output_path.replace('.png', '.html')
            self.html_generator.generate(metadata, image_filename, html_path)
            print("\n📝 次のステップ:")
            print(f"1. {output_path} と {html_path} をWebサーバー（GitHub Pages等）にアップロード")
            print("2. アップロード先のHTMLファイルのURLをXに投稿")
            print("3. Xで自動的にリンクカードが表示されます")
            print(f"4. カードをクリックすると {url} に遷移します")


async def main():
    if len(sys.argv) < 2:
        print("使用方法: python linkcard_generator.py <URL> [-o 出力ファイル名] [--generate-html] [--base-url ベースURL]")
        print("例: python linkcard_generator.py https://example.com")
        print("例: python linkcard_generator.py https://example.com -o card.png")
        print("例: python linkcard_generator.py https://example.com --generate-html")
        print("例: python linkcard_generator.py https://example.com --generate-html --base-url https://username.github.io/linkcard")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = "linkcard.png"
    generate_html = False
    base_url = ""
    
    # オプション解析
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "-o" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--generate-html":
            generate_html = True
            i += 1
        elif sys.argv[i] == "--base-url" and i + 1 < len(sys.argv):
            base_url = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    generator = LinkCardGenerator(base_url)
    await generator.generate(url, output_path, generate_html)


if __name__ == "__main__":
    asyncio.run(main())
