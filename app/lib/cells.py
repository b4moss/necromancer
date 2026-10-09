import json
import os
import subprocess
from pathlib import Path

# MKCOL success: created, or already-exists equivalents observed on WebDAV / Cells.
_MKCOL_SUCCESS_STATUSES = {201, 405, 409}


def load_cells_config(config_path: str = str(Path(__file__).resolve().parent.parent / "config" / "upload.json")):
    """
    Load Pydio Cells configuration from upload.json.
    Expected structure:
    {
      "provider": "cells",
      "cells": {
        "endpoint": "https://host/dav/workspace/",
        "username": "...",
        "password": "...",
        "upload_folder": "Scans/",
        "delete_after_upload": true
      }
    }
    Returns the "cells" section as a flat dict.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cells_cfg = raw.get("cells")
    if not isinstance(cells_cfg, dict):
        raise ValueError("Invalid 'cells' section in upload.json")

    return cells_cfg


def test_cells_connection() -> bool:
    """
    Lightweight connectivity test to the configured Cells WebDAV endpoint (HEAD).
    """
    try:
        config = load_cells_config()

        endpoint = config.get("endpoint")
        if not endpoint:
            print("Cells endpoint is not configured.")
            return False

        curl_cmd = (
            f"curl -i -I "
            f"-u '{config['username']}:{config['password']}' "
            f"-k '{endpoint}'"
        )
        safe_cmd = curl_cmd.replace(
            f"{config['username']}:{config['password']}",
            "USERNAME:PASSWORD",
        )
        print(f"Testing Cells connectivity with command: {safe_cmd}")

        result = subprocess.run(
            curl_cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        print("\n===== Cells connectivity check output =====")
        print("stdout:")
        print(result.stdout)
        print("\nstderr:")
        print(result.stderr)
        print("===== end of output =====\n")

        response_lines = result.stdout.strip().split("\n")
        status_line = next((line for line in response_lines if line.startswith("HTTP/")), None)

        if not status_line:
            print("Could not find HTTP status line for connectivity check")
            return False

        print(f"Connectivity response: {status_line}")
        parts = status_line.split()
        if len(parts) < 2:
            print(f"Invalid HTTP status line: {status_line}")
            return False

        try:
            status_code = int(parts[1])
        except ValueError:
            print(f"Failed to parse HTTP status code: {status_line}")
            return False

        if 200 <= status_code < 400:
            print(f"Cells connectivity OK (status={status_code})")
            return True

        print(f"Cells connectivity NG (status={status_code})")
        return False
    except Exception as e:
        print(f"Error while testing Cells connectivity: {e}")
        return False


def create_remote_directory(remote_dir: str) -> bool:
    """
    Create a directory on Cells via WebDAV MKCOL.
    Treats already-exists responses as success (201 / 405 / 409; adjust if Cells differs).
    """
    try:
        config = load_cells_config()

        remote_url = f"{config['endpoint']}{remote_dir.rstrip('/')}/"

        curl_cmd = (
            f"curl -v -i "
            f"-X MKCOL "
            f"-u '{config['username']}:{config['password']}' "
            f"-k '{remote_url}'"
        )

        safe_cmd = curl_cmd.replace(
            f"{config['username']}:{config['password']}",
            "USERNAME:PASSWORD",
        )
        print(f"Create remote directory command: {safe_cmd}")

        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

        print("\n===== MKCOL output =====")
        print("stdout:")
        print(result.stdout)
        print("\nstderr:")
        print(result.stderr)
        print("===== end of output =====\n")

        response_lines = result.stdout.strip().split("\n")
        status_line = next((line for line in response_lines if line.startswith("HTTP/")), None)

        if not status_line:
            print("Could not find HTTP status line for MKCOL")
            return False

        print(f"MKCOL response: {status_line}")
        parts = status_line.split()
        if len(parts) < 2:
            print(f"Invalid MKCOL status line: {status_line}")
            return False

        try:
            status_code = int(parts[1])
        except ValueError:
            print(f"Failed to parse MKCOL status code: {status_line}")
            return False

        if status_code == 201:
            print(f"Successfully created remote directory: {remote_dir}")
            return True
        if status_code in _MKCOL_SUCCESS_STATUSES:
            print(
                f"Remote directory already exists or accepted "
                f"(status={status_code}, treated as success): {remote_dir}"
            )
            return True

        print(f"MKCOL failed (status code: {status_code})")
        return False

    except Exception as e:
        print(f"Error while creating remote directory: {e}")
        return False


def upload_file_to_cells(file_path: str, remote_path: str = None):
    """
    Upload a single file to Cells via WebDAV PUT.
    """
    try:
        config = load_cells_config()

        if not os.path.exists(file_path):
            print(f"Error: file '{file_path}' not found")
            return False

        if remote_path is None:
            filename = os.path.basename(file_path)
            remote_path = f"{config['upload_folder']}{filename}"

        remote_url = f"{config['endpoint']}{remote_path}"

        print("Uploading to Cells:")
        print(f"- local file: {file_path}")
        print(f"- remote URL: {remote_url}")
        print(f"- remote folder: {config['upload_folder']}")

        curl_cmd = (
            f"curl -v -i "
            f"-X PUT "
            f"-u '{config['username']}:{config['password']}' "
            f"--upload-file '{file_path}' "
            f"-k '{remote_url}'"
        )

        safe_cmd = curl_cmd.replace(
            f"{config['username']}:{config['password']}",
            "USERNAME:PASSWORD",
        )
        print(f"Executing command: {safe_cmd}")

        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

        print("\n===== CURL output =====")
        print("stdout:")
        print(result.stdout)
        print("\nstderr:")
        print(result.stderr)
        print("===== end of output =====\n")

        response_lines = result.stdout.strip().split("\n")
        status_line = next((line for line in response_lines if line.startswith("HTTP/")), None)

        if status_line:
            print(f"Server response: {status_line}")
            status_parts = status_line.split()
            if len(status_parts) >= 2:
                try:
                    status_code = int(status_parts[1])
                    if 200 <= status_code < 300:
                        print(f"Upload succeeded: {remote_path} (status={status_code})")
                        return True
                    print(f"Upload failed: server returned error (status={status_code})")
                    return False
                except ValueError:
                    print(f"Failed to parse HTTP status code: {status_line}")
                    return False
            print(f"Invalid HTTP status line format: {status_line}")
            return False

        if result.returncode == 0:
            if "100.0%" in result.stderr:
                print("Upload succeeded (status unknown, but transfer completed).")
                return True
            print("Upload result unknown (no status and transfer not confirmed).")
            return False

        print(f"curl command failed (return code: {result.returncode})")
        return False

    except Exception as e:
        print(f"Error while uploading to Cells: {e}")
        import traceback

        traceback.print_exc()
        return False


def upload_directory_to_cells(dir_path: str, delete_after_upload: bool = None):
    """
    Upload all files in a directory to Cells.
    """
    try:
        config = load_cells_config()

        if not os.path.isdir(dir_path):
            print(f"Error: directory '{dir_path}' not found")
            return False

        if delete_after_upload is None:
            delete_after_upload = config.get("delete_after_upload", False)

        dir_name = os.path.basename(os.path.normpath(dir_path))
        remote_dir = f"{config['upload_folder']}{dir_name}/"

        print(f"Remote directory: {remote_dir}")

        if not create_remote_directory(remote_dir):
            print(f"Error: failed to create remote directory '{remote_dir}'")
            return False

        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

        if not files:
            print(f"Warning: directory '{dir_path}' has no files")
            return False

        upload_success = True
        uploaded_files = []

        for filename in files:
            file_path = os.path.join(dir_path, filename)
            remote_path = f"{remote_dir}{filename}"

            success = upload_file_to_cells(file_path, remote_path)

            if success:
                uploaded_files.append(file_path)
            else:
                upload_success = False

        if upload_success and delete_after_upload and uploaded_files:
            print("Deleting successfully uploaded files...")
            for file_path in uploaded_files:
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error while deleting file: {e}")

            if not os.listdir(dir_path):
                try:
                    os.rmdir(dir_path)
                    print(f"Deleted empty directory: {dir_path}")
                except Exception as e:
                    print(f"Error while deleting directory: {e}")

        return upload_success

    except Exception as e:
        print(f"Error while uploading directory to Cells: {e}")
        return False


def upload_pdf_to_cells(pdf_path: str, delete_after_upload: bool = None):
    """
    Upload a single PDF file to Cells.
    """
    try:
        config = load_cells_config()

        if not os.path.isfile(pdf_path):
            print(f"Error: PDF file '{pdf_path}' not found")
            return False

        if delete_after_upload is None:
            delete_after_upload = config.get("delete_after_upload", False)

        pdf_filename = os.path.basename(pdf_path)
        remote_path = f"{config['upload_folder']}{pdf_filename}"
        success = upload_file_to_cells(pdf_path, remote_path)

        if success and delete_after_upload:
            try:
                os.remove(pdf_path)
                print(f"Deleted local PDF: {pdf_path}")
            except Exception as e:
                print(f"Error while deleting local PDF: {e}")

        return success

    except Exception as e:
        print(f"Error while uploading PDF to Cells: {e}")
        return False
