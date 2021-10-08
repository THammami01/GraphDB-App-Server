from pathlib import Path


def upload_file(drive, file_path: str):
    # print("--01")
    file_name = Path(file_path).name
    # print("--02")
    curr_file = drive.CreateFile({'title': file_name, 'parents': [
        {'id': '1RrzH7xclxFdd25At-sQBbcp-tpv1edTu'}]})
        # 1SKsMBap6phtn14U3kkb2OYYnED8RwXEV
    # print("--03")
    curr_file.SetContentFile(file_path)
    # print("--04")
    curr_file.Upload()
    # print("--05")
    return curr_file["id"], file_name, curr_file["alternateLink"]


def delete_uploaded_file(drive, file_uuid: str):
    # print("-x01")
    file1 = drive.CreateFile({'id': file_uuid})
    # print("-x02")
    file1.Delete()
    # print("-x03")
