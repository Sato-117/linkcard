import asyncio
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from linkcard_generator import LinkCardGenerator
from PIL import Image, ImageTk

class LinkCardGUI:
    """リンクカード生成ツールのGUIアプリケーション"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("リンクカードジェネレーター")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        self.generator = LinkCardGenerator()
        self.preview_image = None
        
        self._create_widgets()
        
    def _create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL入力
        ttk.Label(main_frame, text="URL:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 出力ファイル名
        ttk.Label(main_frame, text="出力ファイル名:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.output_var = tk.StringVar(value="linkcard.png")
        output_entry = ttk.Entry(file_frame, textvariable=self.output_var, width=45)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(file_frame, text="参照...", command=self._browse_output)
        browse_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # オプション
        ttk.Label(main_frame, text="オプション:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        self.html_var = tk.BooleanVar(value=True)
        html_check = ttk.Checkbutton(
            main_frame, 
            text="HTMLファイルも生成する", 
            variable=self.html_var
        )
        html_check.grid(row=5, column=0, sticky=tk.W, pady=(0, 20))
        
        # 生成ボタン
        self.generate_btn = ttk.Button(
            main_frame, 
            text="🎨 リンクカードを生成", 
            command=self._generate_card,
            style='Accent.TButton'
        )
        self.generate_btn.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 進捗表示
        self.progress = ttk.Progressbar(
            main_frame, 
            mode='indeterminate', 
            length=300
        )
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ステータスラベル
        self.status_var = tk.StringVar(value="URLを入力して生成ボタンをクリックしてください")
        status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            foreground="gray",
            wraplength=600
        )
        status_label.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # プレビューフレーム
        preview_frame = ttk.LabelFrame(main_frame, text="プレビュー", padding="10")
        preview_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.preview_label = ttk.Label(preview_frame, text="生成後にプレビューが表示されます")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
    def _browse_output(self):
        """出力ファイル選択ダイアログ"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG画像", "*.png"), ("すべてのファイル", "*.*")],
            initialfile=self.output_var.get()
        )
        if filename:
            self.output_var.set(filename)
    
    def _generate_card(self):
        """リンクカード生成（非同期）"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("入力エラー", "URLを入力してください")
            return
        
        if not url.startswith(('http://', 'https://')):
            messagebox.showwarning("入力エラー", "有効なURL（http://またはhttps://）を入力してください")
            return
        
        output_path = self.output_var.get().strip()
        if not output_path:
            messagebox.showwarning("入力エラー", "出力ファイル名を入力してください")
            return
        
        # ボタン無効化、進捗開始
        self.generate_btn.config(state='disabled')
        self.progress.start(10)
        self.status_var.set("🔍 メタデータを取得中...")
        
        # 別スレッドで実行
        thread = threading.Thread(
            target=self._run_generation,
            args=(url, output_path, self.html_var.get()),
            daemon=True
        )
        thread.start()
    
    def _run_generation(self, url: str, output_path: str, generate_html: bool):
        """生成処理を実行（別スレッド）"""
        try:
            # asyncioイベントループを新規作成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 生成実行
            loop.run_until_complete(
                self.generator.generate(url, output_path, generate_html)
            )
            
            loop.close()
            
            # 成功時の処理（メインスレッドで実行）
            self.root.after(0, self._on_generation_success, output_path)
            
        except Exception as e:
            # エラー時の処理（メインスレッドで実行）
            self.root.after(0, self._on_generation_error, str(e))
    
    def _on_generation_success(self, output_path: str):
        """生成成功時の処理"""
        self.progress.stop()
        self.generate_btn.config(state='normal')
        self.status_var.set(f"✅ 生成完了！ファイル: {output_path}")
        
        # プレビュー表示
        try:
            img = Image.open(output_path)
            # サイズを調整（600px幅に収める）
            img.thumbnail((600, 315), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 参照を保持
            
        except Exception as e:
            self.preview_label.config(text=f"プレビュー表示エラー: {e}")
        
        # 成功メッセージ
        messagebox.showinfo(
            "生成完了",
            f"リンクカードを生成しました！\n\n"
            f"📁 画像: {output_path}\n"
            f"{'📄 HTML: ' + output_path.replace('.png', '.html') if self.html_var.get() else ''}\n\n"
            f"WebサーバーにアップロードしてXに投稿してください。"
        )
    
    def _on_generation_error(self, error_message: str):
        """生成エラー時の処理"""
        self.progress.stop()
        self.generate_btn.config(state='normal')
        self.status_var.set("❌ エラーが発生しました")
        
        messagebox.showerror(
            "生成エラー",
            f"リンクカードの生成に失敗しました。\n\n"
            f"エラー内容:\n{error_message}"
        )


def main():
    """メイン関数"""
    root = tk.Tk()
    app = LinkCardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
