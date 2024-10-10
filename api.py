import os
import json
import copy

from loguru import logger

from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.pipe.OCRPipe import OCRPipe
from magic_pdf.pipe.TXTPipe import TXTPipe
from magic_pdf.dict2md.ocr_mkcontent import ocr_mk_mm_markdown_with_para_and_pagination
from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
import magic_pdf.model as model_config
from fastapi import FastAPI, File, Response, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from zip import export_zip
model_config.__use_inside_model__ = True

 

def json_md_dump(
        pipe,
        md_writer,
        pdf_name,
        content_list,
        md_content,
        md_pages
):
    # 写入模型结果到 model.json
    orig_model_list = copy.deepcopy(pipe.model_list)
    md_writer.write(
        content=json.dumps(orig_model_list, ensure_ascii=False, indent=4),
        path=f"model.json"
    )

    # 写入中间结果到 middle.json
    md_writer.write(
        content=json.dumps(pipe.pdf_mid_data, ensure_ascii=False, indent=4),
        path=f"middle.json"
    )

    # text文本结果写入到 conent_list.json
    md_writer.write(
        content=json.dumps(content_list, ensure_ascii=False, indent=4),
        path=f"content_list.json"
    )

    # 遍历content_list
    for item in md_pages:
        # page_no
        # md_content
        md_writer.write(
        content=item['md_content'],
        path=f"{item['page_no']}.md"
    )


    md_writer.write(
        content=md_content,
        path=f"content.md"
    )


def pdf_parse_main(
        pdf_path: str,
        parse_method: str = 'auto',
        model_json_path: str = None,
        is_json_md_dump: bool = True,
        output_dir: str = None,
        pdf_name: str = None
):
    """
    执行从 pdf 转换到 json、md 的过程，输出 md 和 json 文件到 pdf 文件所在的目录

    :param pdf_path: .pdf 文件的路径，可以是相对路径，也可以是绝对路径
    :param parse_method: 解析方法， 共 auto、ocr、txt 三种，默认 auto，如果效果不好，可以尝试 ocr
    :param model_json_path: 已经存在的模型数据文件，如果为空则使用内置模型，pdf 和 model_json 务必对应
    :param is_json_md_dump: 是否将解析后的数据写入到 .json 和 .md 文件中，默认 True，会将不同阶段的数据写入到不同的 .json 文件中（共3个.json文件），md内容会保存到 .md 文件中
    :param output_dir: 输出结果的目录地址，会生成一个以 pdf 文件名命名的文件夹并保存所有结果
    """
    try:
        if not pdf_name:
            pdf_name =  os.path.basename(pdf_path).split(".")[0]
        pdf_path_parent = os.path.dirname(pdf_path)

        if output_dir:
            output_path = os.path.join(output_dir, pdf_name)
        else:
            output_path = os.path.join(pdf_path_parent, pdf_name)

        output_image_path = os.path.join(output_path, 'images')

        # 获取图片的父路径，为的是以相对路径保存到 .md 和 conent_list.json 文件中
        image_path_parent = os.path.basename(output_image_path)

        pdf_bytes = open(pdf_path, "rb").read()  # 读取 pdf 文件的二进制数据

        if model_json_path:
            # 读取已经被模型解析后的pdf文件的 json 原始数据，list 类型
            model_json = json.loads(open(model_json_path, "r", encoding="utf-8").read())
        else:
            model_json = []

        # 执行解析步骤
        # image_writer = DiskReaderWriter(output_image_path)
        image_writer, md_writer = DiskReaderWriter(output_image_path), DiskReaderWriter(output_path)

        # 选择解析方式
        # jso_useful_key = {"_pdf_type": "", "model_list": model_json}
        # pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        if parse_method == "auto":
            jso_useful_key = {"_pdf_type": "", "model_list": model_json}
            pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        elif parse_method == "txt":
            pipe = TXTPipe(pdf_bytes, model_json, image_writer)
        elif parse_method == "ocr":
            pipe = OCRPipe(pdf_bytes, model_json, image_writer)
        else:
            logger.error("unknown parse method, only auto, ocr, txt allowed")
            exit(1)

        # 执行分类
        pipe.pipe_classify()

        # 如果没有传入模型数据，则使用内置模型解析
        if not model_json:
            if model_config.__use_inside_model__:
                pipe.pipe_analyze()  # 解析
            else:
                logger.error("need model list input")
                exit(1)

        # 执行解析
        pipe.pipe_parse()
        # 保存 text 和 md 格式的结果
        content_list = pipe.pipe_mk_uni_format(image_path_parent, drop_mode="none")
        md_content = pipe.pipe_mk_markdown(image_path_parent, drop_mode="none")

        # 获得分页信息
        pdf_info_list = pipe.pdf_mid_data["pdf_info"]
        md_pages = ocr_mk_mm_markdown_with_para_and_pagination(pdf_info_list,image_path_parent)


        if is_json_md_dump:
            json_md_dump(pipe, md_writer, pdf_name, content_list, md_content,md_pages)


    except Exception as e:
        logger.exception(e)



from fastapi.middleware.cors import CORSMiddleware

# 定义文件保存路径

# 获取当前脚本的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义文件保存路径
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "uploads")
output = "output"
OUTPUT_DIRECTORY = os.path.join(UPLOAD_DIRECTORY, output)

# 确保保存目录存在
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)



 

import uvicorn
import os
import asyncio
import uuid
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi.staticfiles import StaticFiles


# 任务队列和状态管理
task_queue = asyncio.Queue()
task_status = {}
app = FastAPI()
executor = ThreadPoolExecutor(max_workers=1)

def pdf_parse_worker(task_id, file_location, parse_method, is_json_md_dump):
    try:
        task_status[task_id] = "processing"
        # 假设调用 pdf_parse_main
        pdf_parse_main(file_location, parse_method=parse_method, 
                       pdf_name=task_id,
                       is_json_md_dump=is_json_md_dump, output_dir=OUTPUT_DIRECTORY)
        task_status[task_id] = "done"
    except Exception as e:
        task_status[task_id] = f"处理失败: {str(e)}"

async def queue_worker():
    while True:
        task_id, file_location, parse_method, is_json_md_dump = await task_queue.get()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, pdf_parse_worker, task_id, file_location, parse_method, is_json_md_dump)
        task_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(queue_worker())
    yield
    # clean up worker
app = FastAPI(lifespan=lifespan)


# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，可以根据需要修改
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],   # 允许所有请求头
)




@app.post("/")
async def upload_pdf(
    file: UploadFile = File(...),
    parse_method: str = Form(...),
    is_json_md_dump: bool = Form(...)
):
    task_id = str(uuid.uuid4())
    file_name = task_id+".pdf";
    file_location = os.path.join(UPLOAD_DIRECTORY, task_id+".pdf")

    with open(file_location, "wb") as file_object:
        file_object.write(await file.read())

    await task_queue.put((task_id, file_location, parse_method, is_json_md_dump))
    task_status[task_id] = "pending"

    result = {
        "task_id": task_id,
        "file_name":file.filename,
        "pdf_url":f"/file/{file_name}",
        "md_url":f"/file/{output}/{task_id}/content.md",
        "images":f"/file/{output}/{task_id}",
        "model_json":f"/file/{output}/{task_id}/model.json",
        "middle_json":f"/file/{output}/{task_id}/middle.json",
        "content_list_json":f"/file/{output}/{task_id}/content_list.json",
        "message": "任务已提交"
    }

    return JSONResponse(content=result)

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    status = task_status.get(task_id, "处理失败:任务 ID 不存在")
    return JSONResponse(content={"task_id": task_id, "status": status})


@app.get("/pack/{task_id}")
async def pack(task_id: str):
    md_path = os.path.join(OUTPUT_DIRECTORY, task_id, "content.md")
    zip_file = export_zip(md_path)
    # 导出下载文件
    return FileResponse(zip_file, filename=f"{task_id}.zip")


@app.get("/")
async def index():
    return {"message": "欢迎使用 PDF 解析服务"}

app.mount("/file", StaticFiles(directory="uploads"), name="uploads")
   
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)