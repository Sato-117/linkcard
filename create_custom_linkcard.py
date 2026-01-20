"""カスタム画像を使ったリンクカード生成スクリプト（URL非表示版）"""

def create_custom_linkcard(
    image_filename: str,
    redirect_url: str,
    title: str,
    description: str,
    display_url: str = None,
    output_html: str = "linkcard.html",
    base_url: str = ""
):
    """
    カスタム画像を使用したリンクカードHTMLを生成
    
    Args:
        image_filename: 使用する画像ファイル名（例: card_image.jpg）
        redirect_url: 実際のリダイレクト先URL（非表示）
        title: OGPタイトル
        description: OGP説明文
        display_url: OGPに表示するURL（Noneの場合は非表示）
        output_html: 出力HTMLファイル名
        base_url: GitHub PagesのベースURL
    """
    
    # 画像URLを絶対URLに変換
    if base_url:
        image_url = f"{base_url.rstrip('/')}/{image_filename}"
    else:
        image_url = image_filename
    
    # 表示用URLの設定
    if display_url is None:
        display_url = base_url if base_url else "https://example.com"
    
    # Base64エンコードでリダイレクトURLを隠す
    import base64
    encoded_url = base64.b64encode(redirect_url.encode()).decode()
    
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="配信先：vv_ga07">
    <meta property="og:title" content="{_escape_html(title)}">
    <meta property="og:description" content="{_escape_html(description)}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:type" content="image/png">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{_escape_html(title)}">
    <meta name="twitter:description" content="{_escape_html(description)}">
    <meta name="twitter:image" content="{image_url}">
    <meta name="twitter:image:alt" content="{_escape_html(title)}">>
    <meta name="twitter:image:alt" content="{_escape_html(title)}">
    
    <title>{_escape_html(title)}</title>
    
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
    </style>
    
    <script>
        // Base64デコードしてリダイレクト
        window.onload = function() {{
            setTimeout(function() {{
                var encodedUrl = "{encoded_url}";
                var decodedUrl = atob(encodedUrl);
                window.location.href = decodedUrl;
            }}, 3000);
        }};
    </script>
</head>
<body>
    <div class="container">
        <h1>リダイレクト中...</h1>
        <p class="redirect-message">3秒後にページに移動します。</p>
    </div>
</body>
</html>"""
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ カスタムリンクカードを生成しました: {output_html}")
    print(f"📷 画像: {image_filename}")
    print(f"🔒 リダイレクト先: {redirect_url} (Base64エンコード済み)")
    print(f"📄 OGP表示URL: {display_url}")


def _escape_html(text: str) -> str:
    """HTMLエスケープ処理"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
               .replace('<', '&lt;')
               .replace('>', '&gt;')
               .replace('"', '&quot;')
               .replace("'", '&#39;'))


if __name__ == "__main__":
    import sys
    
    # 実行例
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python create_custom_linkcard.py <リダイレクト先URL>")
        print("")
        print("例:")
        print('  python create_custom_linkcard.py https://ad-nex.com/u/ai9fstn0aesb')
        sys.exit(1)
    
    redirect_url = sys.argv[1]
    
    # 設定
    create_custom_linkcard(
        image_filename="livecard.png",
        redirect_url=redirect_url,
        title="🔴6分前に配信を始めました：584人が視聴中",
        description="",
        display_url="https://vv-ga07.github.io/linkcard",
        output_html="linkcard.html",
        base_url="https://vv-ga07.github.io/linkcard"
    )
