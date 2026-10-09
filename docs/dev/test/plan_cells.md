# Pydio Cells WebDAV ドライバー — テスト仕様

関連 plans: [plan_pydio_cells.md](../plans/plan_pydio_cells.md) / Issue [#48](https://github.com/b4moss/necromancer/issues/48)

`provider: "cells"` のとき、既存 Nextcloud と同契約で Cells WebDAV（`/dav/` + curl + Basic）へアップロードする。

氷山パターン: CI は curl モック。実機 `file.b4m.jp` スモークは Acceptance（手動可）。

----

## `load_cells_config`

- `upload.json` を読み、`cells` セクションを dict で返す。
- セクションが無い／dict でない場合は `ValueError`。

### テスト：正常系

- `provider="cells"` と妥当な `cells` セクションから endpoint / upload_folder 等が読める。

### テスト: 異常系

- `cells` が無い、または非 dict のとき `ValueError`。

----

## `create_remote_directory`（Cells）

- `endpoint + remote_dir` に対し `MKCOL`（curl）。
- 作成成功と「既に存在」を成功とみなす。成功ステータスは **Cells の実情に合わせてよい**（初期: 201、既存相当として 405 / 409）。

### テスト：正常系

- HTTP 201 → True
- HTTP 405 → True（既存）
- HTTP 409 → True（既存・Cells 向け）

### テスト: 異常系

- ステータス行が無い → False
- 明らかに失敗する 4xx/5xx（例: 401 / 500）→ False

----

## `upload_file_to_cells`

- ローカルファイル存在確認。
- `remote_path` 省略時は `upload_folder + ファイル名`。
- `PUT`（curl）。2xx で True。ステータス無し時は nextcloud と同様に returncode + `100.0%` フォールバック。

### テスト：正常系

- ファイルあり・HTTP 201 → True
- `remote_path=None` で upload_folder が使われる

### テスト: 異常系

- ローカル欠落 → False
- HTTP 4xx/5xx → False

----

## `upload_directory_to_cells`

- ディレクトリ名をサフィックスに `upload_folder` 下へ MKCOL 後、全ファイルを PUT。
- `delete_after_upload` は設定または引数。

### テスト：正常系

- 複数ファイルがアップロードされる（内部関数モック）

### テスト: 異常系

- リモート dir 作成失敗 → False
- 空ディレクトリ → False

----

## `upload_pdf_to_cells`

- PDF を `upload_folder + ファイル名` で PUT。成功時 `delete_after_upload` ならローカル削除。

### テスト：正常系

- 成功 → True
- `delete_after_upload=True` でローカル削除

### テスト: 異常系

- ファイル欠落 → False

----

## `test_cells_connection`

- endpoint へ HEAD。2xx〜3xx を OK。

### テスト：正常系

- HTTP 200 → True

### テスト: 異常系

- HTTP 500 → False
- ステータス行無し → False

----

## `get_uploader_from_config`（cells）

- `provider="cells"` のとき CellsUploader を返す。
- 未知 provider は従来どおり Nextcloud フォールバック（`cells` は未知にしない）。

### テスト：正常系

- `provider="cells"` → CellsUploader

### テスト: 異常系

- `provider="dropbox"` → NextcloudUploader + 警告（既存契約）

----

## 手動スモーク（Acceptance）

対象: **`file.b4m.jp`**

1. `upload.json` に `provider: "cells"` と workspace 込み endpoint（例: `https://file.b4m.jp/dav/<workspace>/`）を設定
2. 接続確認（HEAD）が成功する
3. 小さなファイルまたはディレクトリのアップロード（PUT / MKCOL）が成功する
4. 認証情報はリポジトリに入れない

認証情報が無い環境ではスモークはブロッカーとし、モック pytest のみで CI を進める。

----

以上
