# Pydio Cells アップロード（WebDAV）— 現行仕様

| 項目 | 値 |
|------|-----|
| 状態 | **現行仕様**（[#51](https://github.com/b4moss/necromancer/pull/51) → `develop` マージ済み。[#48](https://github.com/b4moss/necromancer/issues/48) クローズ） |
| `provider` | `cells`（セクション名も `cells`） |
| 転送 | Cells WebDAV（`/dav/`）+ curl + Basic |
| テスト仕様 | [plan_cells.md](../test/plan_cells.md) |
| 近傍 plans | [plan_additional_cloud_services.md](../plans/plan_additional_cloud_services.md)（Dropbox / GDrive・OAuth。本仕様とは別） |

本ファイルは実装済み機能の仕様正本（plans → specs）。設定の利用者向け説明は [setup_config（ja）](../../ja/setup_config.md) / [setup_config（en）](../../en/setup_config.md)。例示は `app/config/upload.example.json`。

----

## 1. 目的・範囲

スキャン成果物のアップロード先として **Pydio Cells** を使える。既存 Nextcloud と同契約のアダプターで、`upload.json` の `provider` 切り替えだけで利用する。

### 入っているもの

| 項目 | 内容 |
|------|------|
| 転送方式 | Cells **WebDAV**（`/dav/`） |
| 実装 | `app/lib/cells.py`（Nextcloud ドライバを別モジュール展開）+ `upload_adapter.CellsUploader` |
| 認証 | **Basic**（username + password。PAT を password に載せてよい） |
| 設定キー | `endpoint` / `username` / `password` / `upload_folder` / `delete_after_upload` |
| endpoint | workspace 込み（例: `https://<host>/dav/<workspace-slug>/`）。末尾 `/` |
| 公開契約 | `upload_directory` / `upload_file` / `upload_pdf` のみ |

### 入っていないもの（スコープ外）

- REST `/a/`
- S3 互換 API
- OAuth2 / OIDC
- Dropbox / Google Drive（#14 / #12）
- アップロード契約の拡張（一覧・削除・共有リンク等）

----

## 2. 設定

```json
{
  "provider": "cells",
  "cells": {
    "endpoint": "https://file.b4m.jp/dav/<workspace-slug>/",
    "username": "your_username",
    "password": "your_password_or_pat",
    "upload_folder": "Scans/",
    "delete_after_upload": true
  }
}
```

- `workspace` 独立キーは設けない（endpoint に含める）
- `upload.json` は gitignore（認証情報をリポジトリに入れない）
- 未知の `provider` は従来どおり Nextcloud へフォールバックする。`cells` は未知扱いにしない

----

## 3. 実装パス（参照）

| パス | 役割 |
|------|------|
| `app/lib/cells.py` | WebDAV（curl）: 設定読込、接続確認、MKCOL、PUT、directory / pdf |
| `app/lib/upload_adapter.py` | `CellsUploader` / `get_uploader_from_config()` の `cells` 分岐 |
| `app/config/upload.example.json` | `cells` セクション例 |
| `tests/test_cells.py` / `tests/test_upload_adapter.py` | curl モック中心 |

MKCOL の「既存ディレクトリ」成功扱いは Cells 実情に合わせる（初期: 201、既存相当として 405 / 409）。

----

## 4. 受け入れ条件（達成済み）

- [x] `provider: "cells"` で Cells WebDAV へアップロードできる
- [x] `cells` セクションに `endpoint` / `username` / `password` / `upload_folder` / `delete_after_upload` がある
- [x] `endpoint` は workspace 込み `/dav/...` を前提とする
- [x] 認証は Basic（PAT を password に載せてよい）
- [x] 公開 API は `upload_directory` / `upload_file` / `upload_pdf` のみ
- [x] REST `/a/`・S3・OAuth は実装しない
- [x] `docs/` 配下にテスト仕様があり、モック pytest が CI で緑
- [x] 既存 nextcloud 経路が回帰しない
- [x] **`file.b4m.jp` でのスモーク成功**
- [x] setup_config / example / plans→specs が現行を指す

----

以上
