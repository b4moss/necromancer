# b4m-necromancer - revive your old scanner with Raspberry Pi ZERO 2

[![CI](https://github.com/b4m-oss/necromancer/actions/workflows/ci.yml/badge.svg)](https://github.com/b4m-oss/necromancer/actions/workflows/ci.yml)

[English](./README.md)

このシステムは、テンキーパッドからの入力によってドキュメントスキャンを自動実行するためのソリューションです。
テンキーの数字を押してEnterを押すだけで、異なるモードでのスキャンが可能です。

## モチベーション

メーカーサポートの切れたスキャナを、OSSの力を使って蘇らせる。

開発者は、FujitsuのiX500を使っていましたが、ある時、iOSアプリのサポートが打ち切られました。
どうしてもWiFi下でリモートにファイルをアップデートしたかったため、様々な方策を考えました。
結果、SANEというライブラリを見つけ、これをRaspberry Pi ZERO 2で動かすことを思いついたのです。

## 何ができますか？

- サポートの切れたスキャナを継続して使用することができます
- 自動でクラウドサービスにスキャンした内容をアップロードすることができます
- 細かな設定を自分でプリセットとして用意することができます
- テンキー入力から操作を実行できます

## 必要なハードウェア

- Raspberry Pi Zero 2W（または他のRaspberry Pi）
- ScanSnap iX500スキャナー（または他のSANE対応スキャナー）
- テンキーパッド（USBまたはBluetooth接続）

## 機能

- テンキーパッドからの入力を監視
- 数字キーごとに異なるスキャンモードを実行（diary、receipt、flyer）
- スキャンした文書をNextcloudに自動アップロード
- システム起動時に自動的にサービス開始
- ログ出力による動作記録


## インストール方法

### 自動インストール

Raspberry Pi 上でリポジトリをクローンし、ルートのインストーラを実行します（内部で `app/install.sh` に委譲します）。

**推奨**（リリースタグ `v0.3.0` 公開後）:

```bash
git clone --branch v0.3.0 https://github.com/b4m-oss/necromancer.git ~/necromancer
cd ~/necromancer && ./install.sh
```

タグがまだ無い場合は、開発ブランチを使ってください:

```bash
git clone --branch dev-v0.3.0 https://github.com/b4m-oss/necromancer.git ~/necromancer
# または: --branch main
cd ~/necromancer && ./install.sh
```

