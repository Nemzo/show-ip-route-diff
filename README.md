# show-ip-route-diff (SirDiff)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A smart, CLI-based `show ip route` diff tool designed specifically for network engineers.  

When comparing routing tables, standard diff tools often flag "uptime changes" (e.g., `00:15:33` to `00:15:38`) as differences, burying actual topological changes. **SirDiff** automatically ignores these time-based fluctuations, translates IP addresses into readable hostnames, and highlights exactly what changed.  
## ✨ Features / 特徴

- **🕒 Uptime Masking / 経過時間の自動スキップ**: Automatically ignores routing uptime changes. / `00:12:34` や `1w2d` といった時刻の変動を差分から自動的に除外します。
- **🏷️ Hostname Translation / ホスト名への自動変換**: Converts raw IP addresses into intuitive hostnames based on `hosts.json`. / 無機質なIPアドレスを直感的なホスト名（例: `192.168.1.1[Core-SW-A]`）に変換して比較します。
- **✂️ Smart Abbreviations / インターフェース名の短縮**: Shortens verbose interface names (e.g., `GigabitEthernet` -> `GE`) for better readability. / 視認性を高めるための自動フォーマットを行います。
- **👀 Multiple Display Modes / 多彩な表示モード**: 
  - Side-by-Side (Default) / 左右分割表示（デフォルト）
  - Unified vertical format (`-u`) / 上下分割のUnifiedフォーマット
  - Diff-only extraction (`-d`) / 差分行のみ抽出
  - Inline character-level highlighting (`-i`) / 変更された文字（単語）のみ色付け
- **📊 Markdown Support / Markdown出力対応**: Generates Markdown-formatted tables/diffs ready for your Wiki or Jira. / WikiやJiraにそのまま貼り付けられるMarkdown形式での出力に対応しています。
## 🚀 Installation / インストール

Requires Python 3.x. No additional packages needed (standard libraries only)

```bash
# 1. Clone the repository / リポジトリをクローン
git clone https://github.com/[YourUsername]/show-ip-route-diff.git
cd show-ip-route-diff
```

## ⚙️ Configuration

Create a `hosts.json` file in the script directory to map IP addresses to hostnames.
```
{
    "192.168.1.1": "Cisco-Core-A",
    "10.0.0.254": "L3-Switch",
    "172.16.0.1": "FW"
}
```
## 📖 Usage
### Basic Command
```
sirdiff <Old_File> <New_File>
```
## 💡 Examples
1. **Show only the routes that actually changed**
    ```
    sirdiff route_old.txt route_new.txt -d
    ```
    
2. **Highlight exact character changes**
    ```
    sirdiff route_old.txt route_new.txt -d -i
    ```
    
3. **Filter by a specific subnet or hostname**
    ```
    sirdiff route_old.txt route_new.txt -g "10.20."
    ```
    
4. **Save the result as plain text**
    ```
    sirdiff route_old.txt route_new.txt -o diff_result.txt
    ```
    
5. **Export a Markdown table**
    ```
    sirdiff route_old.txt route_new.txt -d --md -o report.md
    ```
## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📝 License
This project is licensed under the **MIT License**.