import fitz
from pathlib import Path
import shutil
from threading import Thread
from time import sleep
# from typing import Union

import uuid as unqId
from .models import FileModel, ExcelNodeModel
from .queries import query_add_file, query_add_definitions, query_add_excel_node
from .drive import upload_file

import pandas as pd
import matplotlib.pyplot as plt


def delete_dir_contents(dir_path: str):
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print(e)
        print("Error: %s - %s." % (e.filename, e.strerror))


def schedule_delete_dir_contents(dir_path: str):
    sleep(600)  # 10 minutes

    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print(e)
        print("Error: %s - %s." % (e.filename, e.strerror))
        # Thread(target=lambda: delete_container_path(container_path)).start()
        schedule_delete_dir_contents(dir_path)


# Union[FileModel, dict]
def extract_items_from_pdf_and_upload_them(session, drive, composed_file: FileModel, file_local_path: str):
    file = fitz.open(file_local_path)

    container_path = f"assets/extracted/{composed_file.uuid}"
    Path(container_path).mkdir(parents=True, exist_ok=True)
    nb_exceptions = 0

    for page_nb, page in enumerate(file.pages(), start=1):
        text = page.getText()

        txt_file_name = f"SN{page_nb}.txt"
        txt_file_path = f'assets/extracted/{composed_file.uuid}/{txt_file_name}'
        txt = open(txt_file_path, 'a')

        try:
            txt.writelines(text)
            txt.close()
            _uuid, _name, _path = upload_file(drive, txt_file_path)
            fileObj = FileModel(uuid=_uuid, parent_uuid=composed_file.uuid,
                                name=_name, format="TXT", type="simple", path=_path)
            query_add_file(session, fileObj, fromComposedFile=True)
            query_add_definitions(session, _uuid, text)
        except Exception as e:
            print(type(e), e)
            nb_exceptions += 1
            print(f"EXCEPTION {nb_exceptions} OCCURED.")

        for img_nb, img in enumerate(page.getImageList(), start=1):
            xref = img[0]
            pix = fitz.Pixmap(file, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            img_file_name = f"SN{page_nb} Img{img_nb}.png"
            img_file_path = f"assets/extracted/{composed_file.uuid}/{img_file_name}"

            try:
                pix.writePNG(img_file_path)
                _uuid, _name, _path = upload_file(drive, img_file_path)
                query_add_file(session, FileModel(uuid=_uuid, parent_uuid=composed_file.uuid,
                                                  name=_name, format="IMG",
                                                  type="simple", path=_path), fromComposedFile=True)
            except Exception as e:
                print(e)

    Thread(target=lambda: schedule_delete_dir_contents(container_path)).start()


def calculate(list):
    return {
        "Max": max(list),
        "Min": min(list),
        "Avg": round(sum(list/len(list)), 3)
    }


def add_max_min_avg_nodes(session, composed_file, list, colName):
    MMA = calculate(list[colName])
    for val in MMA:
        query_add_excel_node(session, ExcelNodeModel(parent_uuid=composed_file.uuid,
                                                     name=f'{val}{colName}', value=MMA[val]),
                                                     relation_name=f'{val.upper()}_{colName.upper()}')


def extract_items_from_excel_and_upload_them(session, drive, composed_file: FileModel, file_local_path: str):
    ExcelTemplates = [
        ['Date', 'Systolic', 'Diastolic', 'Location'],
        ['Date', 'Temperature', 'Location']
    ]

    excel_file = pd.ExcelFile(file_local_path).parse()

    if list(excel_file) in ExcelTemplates:

        plt.figure(figsize=(30, 15))
        plt.xlabel('Date')

        template = ExcelTemplates.index(list(excel_file))
        y, y1 = ExcelTemplates[template][1], ExcelTemplates[template][2]

        ax1 = excel_file[y].plot(color='blue', grid=True)
        ax1.legend(loc=1)

        if template == 0:
            ax2 = excel_file[y1].plot(color='red', grid=True, secondary_y=True)
            ax2.legend(loc=2)

        graphPath = f'assets/uploaded/{str(unqId.uuid4().node)}.png'
        plt.savefig(graphPath)
        _uuid, _name, _path = upload_file(drive, graphPath)

        query_add_file(session, FileModel(uuid=_uuid, parent_uuid=composed_file.uuid,
                                          name=_name, format="GRAPH",
                                          type="simple", path=_path), fromComposedFile=True)

        add_max_min_avg_nodes(session, composed_file, excel_file, y)

        if template == 0:
            add_max_min_avg_nodes(session, composed_file, excel_file, y1)
