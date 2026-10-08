# Pydio Cells ドライバー追加（WebDAV）

| 項目 | 値 |
|------|-----|
| 状態 | **仕様詳細**（方針確定済み。実装前） |
| マイルストーン | **未定**（ただし他 Issue より優先） |
| 関連 Issue | [#48](https://github.com/b4moss/necromancer/issues/48) |
| PR ベース | `develop` |
| 開発方針 | [b4moss/charter](https://github.com/b4moss/charter)（本リポジトリ `docs/override-charter.md` は現状設定なし → 憲章どおり） |
| 近傍 plans | [plan_additional_cloud_services.md](./plan_additional_cloud_services.md)（Dropbox / GDrive・OAuth。本計画とは別） |

**Acceptance Criteria の正本は本ファイル。** Issue #48 本文には AC 全文を書かない（リンクのみ）。

**いまやらないこと:** 実装コード・テストコード（本 PR は docs のみ）。実装は本 plans が `develop` に載ったあと、テスト仕様（`docs/dev/test/` 等の `docs/` 配下）→ TDD。

----

## 1. 目的・範囲

### 目的

スキャン成果物のアップロード先として **Pydio Cells** を追加する。既存 Nextcloud と同契約のアダプター（WebDAV + curl + Basic）で、`upload.json` の `provider` 切り替えだけで使えるようにする。

### 入れる

| 項目 | 内容 |
|------|------|
| 転送方式 | Cells **WebDAV**（`/dav/`） |
| 実装ベース | 既存 Nextcloud driver（WebDAV + curl）を **別モジュール展開**。問題があれば別案を検討 |
| 認証 | **Basic**（username + password。PAT を password に載せてよい） |
| `provider` | **`cells`**（セクション名も `cells`） |
| 設定キー | `endpoint` / `username` / `password` / `upload_folder` / `delete_after_upload` |
| endpoint | workspace 込み（例: `https://<host>/dav/<workspace-slug>/`） |
| 公開契約 | `upload_directory` / `upload_file` / `upload_pdf` のみ |
| 実機受け入れ | **`file.b4m.jp` でのスモーク成功** |

### 入れない

- REST `/a/`
- S3 互換 API
- OAuth2 / OIDC
- Dropbox / Google Drive（#14 / #12）
- アップロード契約の拡張（一覧・削除・共有リンク等）

----

## 2. 設定（確定）

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
- `upload.json` は既存どおり gitignore（認証情報をリポジトリに入れない）

----

## 3. 実装寄せ方

### 対象パス（現行）

- `app/lib/nextcloud.py` — 雛形（MKCOL / PUT / HEAD + curl）
- `app/lib/upload_adapter.py` — `get_uploader_from_config()` に `cells` 分岐
- `app/config/upload.example.json` — `cells` 例を追加（実装時）
- `tests/test_nextcloud.py` / `tests/test_upload_adapter.py` — モック方針の参考

### 方針

1. **別モジュール**（例: `app/lib/cells.py`）に Nextcloud 相当の関数群を展開する
2. `CellsUploader` を adapter から返す（契約は `upload_directory` / `upload_file` / `upload_pdf`）
3. 未知 provider の Nextcloud フォールバックは維持。`cells` は未知にしない
4. **MKCOL「既存ディレクトリ」** の成功扱いステータスは **Cells の実情に合わせて変更してよい**（Nextcloud の 405 固定にしない）
5. 共通 WebDAV 抽出は初手ではやらない

### 推奨実装順

1. 設定読込 + adapter の `cells` 分岐
2. Cells WebDAV モジュール（MKCOL / PUT / 接続確認）
3. `upload.example.json` 例示
4. モック pytest + 回帰（nextcloud）
5. `file.b4m.jp` スモーク

----

## 4. テスト方針

- charter 氷山: CI は curl モック中心（現行 nextcloud と同様）
- テスト仕様は **`docs/` 配下**（例: `docs/dev/test/`。develop 既存配置に合わせる）
- 実 HTTP 結合は CI 必須にしない
- **Acceptance:** `file.b4m.jp` スモーク成功（手動可。手順はテスト仕様または PR に残す）

----

## 5. 進め方（charter）

1. ~~plans に載せる~~（本ファイル）
2. テスト仕様を `docs/` 配下に書く
3. TDD（Red → Green → Refactor）。実装 PR → **`develop`**
4. マージ後: plans → specs（setup_config 等）。実装 Agent は `plans` / `roadmap` / `wishlist` / `specs` を触らない

実装 Agent が触ってよいもの: コード + 当該テスト仕様（`docs/` 配下の tests）+ 必要なら `docs-agent-note/`。

----

## 6. 受け入れ条件（AC・正本）

- [ ] `provider: "cells"` で Cells WebDAV へアップロードできる
- [ ] `cells` セクションに `endpoint` / `username` / `password` / `upload_folder` / `delete_after_upload` がある
- [ ] `endpoint` は workspace 込み `/dav/...` を前提とする
- [ ] 認証は Basic（PAT を password に載せてよい）
- [ ] 公開 API は `upload_directory` / `upload_file` / `upload_pdf` のみ
- [ ] REST `/a/`・S3・OAuth は実装しない
- [ ] `docs/` 配下にテスト仕様があり、モック pytest が CI で緑
- [ ] 既存 nextcloud 経路が回帰しない
- [ ] **`file.b4m.jp` でのスモーク成功**
- [ ] （マージ後・PO）setup_config / example / plans→specs が現行を指す

----

## 7. リスク

| リスク | 緩和 |
|--------|------|
| MKCOL ステータス差 | Cells 実情に合わせて変更可。`file.b4m.jp` で確認 |
| 別モジュールの重複 | まず展開。問題があれば別案 |
| Dropbox/GDrive plans との混線 | 本ファイルに分離。OAuth 計画と混ぜない |

----

以上
