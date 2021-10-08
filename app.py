import uvicorn
from fastapi import FastAPI, UploadFile, File  # , Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable, AuthError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime
from uuid import uuid4
import shutil
from pathlib import Path
import os

# from fastapi.responses import JSONResponse
# return JSONResponse(status_code=status.HTTP_201_CREATED, content={...})

# from flaskwebgui import FlaskUI

from utils.models import DBConnectionModel, MedicalRecordModel, FileModel, IDOnlyModel
from utils.queries import query_add_medical_record, query_add_file, query_update_medical_record, \
    query_delete_medical_record, query_delete_file, query_node_contained_files_uuids, \
    query_get_medical_records, query_get_contained_files, query_add_definitions, \
    query_mr_nodes_contained_files_uuids
from utils.drive import upload_file, delete_uploaded_file
from utils.useful import extract_items_from_pdf_and_upload_them, extract_items_from_excel_and_upload_them, delete_dir_contents
from utils.converters import convert_docx_to_pdf

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GRAPH DB CONNECTION
session = None
current_db_connection: DBConnectionModel = None

# GOOGLE DRIVE CONNECTION
drive = None


def connect_to_graph_db(db_connection):
    global session

    graph_db = GraphDatabase.driver(
        # "bolt://54.243.4.93:7687",
        "neo4j+s://57bb6776.databases.neo4j.io",
        auth=basic_auth("neo4j", db_connection.password)
    )

    # graph_db = GraphDatabase.driver(
    #     "neo4j://localhost:7687",
    #     auth=(db_connection.username, db_connection.password)
    # )
    session = graph_db.session()


def connect_to_google_drive():
    global drive
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)


@app.get("/")
def root():
    return {"statusCode": 200, "message": "Graph App Running Succesfully"}


@app.post("/establish-connections")
def establish_connections(db_connection: DBConnectionModel):
    global current_db_connection
    current_db_connection = db_connection

    try:
        connect_to_graph_db(db_connection)
        connect_to_google_drive()
        return {"statusCode": "200", "message": "Connections Established Successfully"}
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    # return {"statusCode": "400", "message": "Couldn't Establish Connection"}
    # return {"statusCode": "200", "message": "Connection Already Established"}
    # return {"statusCode": "500", "message": "Internal Server Error"}


@app.get("/medical-record")
async def get_medical_recoreds():
    try:
        res_list = query_get_medical_records(session)
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "Medical Records Resolved Successfully", "resList": res_list}


@app.post("/get-contained-files")
async def get_contained_files(obj: IDOnlyModel):
    try:
        res_list = query_get_contained_files(session, obj)
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "Contained Files List Resolved Successfully", "resList": res_list}


@app.post("/medical-record")
async def create_medical_record(mr: MedicalRecordModel):
    mr.uuid = str(uuid4())
    mr.created_at = str(datetime.now()).split(".")[0][:-3]

    try:
        query_add_medical_record(session, mr)
    except (ServiceUnavailable, AuthError) as e:
        return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
    except Exception as e:
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "Medical Record Added Successfully", "medicalRecord": mr}


@app.post("/file")
async def add_file(file: FileModel):
    global session, drive

    try:
        file_local_path = file.path

        file.uuid, file.name, file.path = upload_file(drive, file.path)
        query_add_file(session, file)
        print(file.format)
        if(file.type == "composed"):
            if(file.format == "PDF"):
                extract_items_from_pdf_and_upload_them(
                    session, drive, file, file_local_path)
            elif(file.format == "MS_DOC"):
                # TODO: CONVERT DOC TO PDF, EXTRACT ATTACHEMENTS AND UPLOAD THEM
                pass
            elif(file.format == "MS_DOCX"):
                converted_file_path = convert_docx_to_pdf(file_local_path)
                extract_items_from_pdf_and_upload_them(
                    session, drive, file, converted_file_path)
            elif(file.format == "MS_PPT"):
                # TODO:  CONVERT PPT TO PDF, EXTRACT ATTACHEMENTS AND UPLOAD THEM
                pass
            elif(file.format == "MS_PPTX"):
                # TODO: CONVERT PPTX TO PDF, EXTRACT ATTACHEMENTS AND UPLOAD THEM
                pass
            elif(file.format == "MS_XLS"):
                # TODO: CONVERT XLS TO PDF, EXTRACT ATTACHEMENTS AND UPLOAD THEM
                pass
            elif(file.format == "MS_XLSX"):
                extract_items_from_excel_and_upload_them(
                    session, drive, file, file_local_path)
        else:
            if(file.format == "TXT"):
                with open(file_local_path) as f:
                    query_add_definitions(session, file.uuid, f.read())

    except AttributeError as e:
        print(type(e), e)
        return {"statusCode": "400", "message": "Connection Must Be Established First"}
    except (ServiceUnavailable, AuthError) as e:
        print(type(e), e)
        return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "File Added Successfully", "file": file}


@app.post("/upload-file")
async def upload_local_file(file: UploadFile = File(...)):
    Path("assets/uploaded").mkdir(parents=True, exist_ok=True)
    with open(f"assets/uploaded/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "statusCode": 200,
        "message": f"{file.filename} Uploaded"
        # "file": [file.filename, file.content_type]
    }


@app.patch("/medical-record")
async def update_medical_record(mr: MedicalRecordModel):
    try:
        query_update_medical_record(session, mr)
    except (ServiceUnavailable, AuthError) as e:
        return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
    except Exception as e:
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "Medical Record Updated Successfully", "medicalRecord": mr}


# TODO: IMPLEMENT UPDATING FILE NAME AT LEAST, IT IS MUCH EASIER THAN THE OTHERS
# @app.patch("/file")
# def update_file(file: FileModel):
#     try:
#         query_update_file(session, file)
#     except AttributeError as e:
#         return {"statusCode": "400", "message": "Connection Must Be Established First"}
#     except (ServiceUnavailable, AuthError) as e:
#         return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
#     except Exception as e:
#         return {"statusCode": "500", "message": "Internal Server Error"}

#     return {"statusCode": "200", "message": "File Updated Successfully", "file": file}


@app.delete("/medical-record")
async def delete_medical_record(delNode: IDOnlyModel):
    try:
        for file_uuid in query_mr_nodes_contained_files_uuids(session, delNode.uuid):
            delete_uploaded_file(drive, file_uuid)

        query_delete_medical_record(session, delNode.uuid)
    except (ServiceUnavailable, AuthError) as e:
        return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "Medical Record Deleted Successfully", "delNode": delNode}


@app.delete("/file")
async def delete_file(delNode: IDOnlyModel):
    try:
        # print("BR0X01")
        # print(delNode)

        for file_uuid in query_node_contained_files_uuids(session, delNode.uuid):
            delete_uploaded_file(drive, file_uuid)
            # print("BR0X02")
            # print(file_uuid)

        delete_uploaded_file(drive, delNode.uuid)
        query_delete_file(session, delNode)
    except AttributeError as e:
        print(type(e), e)
        return {"statusCode": "400", "message": "Connection Must Be Established First"}
    except (ServiceUnavailable, AuthError) as e:
        print(type(e), e)
        return {"statusCode": "400", "message": "Auth Error, Most Likely Because of Invalid Connection Credentials"}
    except Exception as e:
        print(type(e), e)
        return {"statusCode": "500", "message": "Internal Server Error"}

    return {"statusCode": "200", "message": "File Deleted Successfully", "delNode": delNode}


# def main():
#     uvicorn.run(
#         "app:app",
#         # host="0.0.0.0",
#         port=8000,
#         debug=True,
#         # reload=True
#     )

if __name__ == "__main__":
    if(Path("./assets/extracted").exists()):
        delete_dir_contents("./assets/extracted")
    if(Path("./assets/uploaded").exists()):
        delete_dir_contents("./assets/uploaded")

    # uvicorn.run(
    #     app,
    #     # host="0.0.0.0",
    #     port=8000,
    # )

    # main()

    # ui.run(
    #     # "app:app",
    #     # host="0.0.0.0",
    #     # port=8000,
    #     # debug=True,
    #     # reload=True
    # )

    # FlaskUI(
    #     app,
    #     start_server='fastapi',
    #     browser_path="C:/Program Files/Google/Chrome/Application/Chrome.exe"
    # ).run()

    uvicorn.run(
        "app:app",
        # host="0.0.0.0",
        port=8000,
        debug=True,
        # reload=True
    )
