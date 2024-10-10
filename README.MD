

<div align="center" xmlns="http://www.w3.org/1999/html">
<!-- logo -->
<p align="center">
  <img src="doc/mineru.png" width="300px" style="vertical-align:middle;">
</p> 
<!-- hot link --> 
<p align="center">
<a href="https://github.com/opendatalab/PDF-Extract-Kit">PDF-Extract-Kit: High-Quality PDF Extraction Toolkit</a>🔥🔥🔥
</p>
</div>

## 项目简介
MinerU是一款开源的高质量PDF解析工具，基于深度学习技术，可自动提取PDF文档中的文字、表格、图片、公式等内容，并提供丰富的分析、统计、搜索等功能。
本项目为其提供一个简化版本的WebUI，方便用户上传PDF文件，并实时展示提取结果。

![页面截图](doc/preview.png)


## 更新日志
### 2022.03.15
- 支持API接口 👏👏👏👏
- 接口支持异步处理，并发处理🔥🔥🔥🔥

## 1. 第一次运行前的配置
在仓库根目录可以获得 [magic-pdf.template.json](doc/magic-pdf.template.json) 配置模版文件
> ❗️务必执行以下命令将配置文件拷贝到【用户目录】下，否则程序将无法运行
>  
> windows用户目录为 "C:\Users\用户名"
```powershell
(New-Object System.Net.WebClient).DownloadFile('https://gitee.com/myhloli/MinerU/raw/master/magic-pdf.template.json', 'magic-pdf.template.json')
cp magic-pdf.template.json ~/magic-pdf.json
```

在用户目录中找到magic-pdf.json文件并配置"models-dir"为[5. 下载模型](#5-下载模型)中下载的模型权重文件所在目录
> ❗️务必正确配置模型权重文件所在目录的【绝对路径】，否则会因为找不到模型文件而导致程序无法运行
> 
> windows系统中此路径应包含盘符，且需把路径中所有的`"\"`替换为`"/"`,否则会因为转义原因导致json文件语法错误。
> 
> 例如：模型放在D盘根目录的models目录，则model-dir的值应为"D:/models"
```json
{
  "models-dir": "/tmp/models"
}
```


## 2. 测试CUDA加速
如果您的显卡显存大于等于8G，可以进行以下流程，测试CUDA解析加速效果

**1.覆盖安装支持cuda的torch和torchvision**
```bash
pip install --force-reinstall torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cu118
```
> ❗️务必在命令中指定以下版本
> ```bash
> torch==2.3.1 torchvision==0.18.1 
> ```
> 这是我们支持的最高版本，如果不指定版本会自动安装更高版本导致程序无法运行

**2.修改【用户目录】中配置文件magic-pdf.json中"device-mode"的值**
```json
{
  "device-mode":"cuda"
}
```

> 提示：CUDA加速是否生效可以根据log中输出的各个阶段cost耗时来简单判断，通常情况下，`layout detection cost` 和 `mfr time` 应提速10倍以上。


## 案例PDF可以选择 `examples/small_ocr.pdf`

## 如何下载模型权重文件

详细参考 [如何下载模型文件](https://github.com/opendatalab/MinerU/blob/master/docs/how_to_download_models_zh_cn.md)
> ❗️模型下载后请务必检查模型文件是否下载完整
> 
> 请检查目录下的模型文件大小与网页上描述是否一致，如果可以的话，最好通过sha256校验模型是否下载完整
> 下载完成后，建议放入目录`models`，并且修改配置文件`magic-pdf.json`中的`models-dir`为模型文件所在目录的绝对路径。

## 启动项目
```bash
conda create -n MinerU python=3.10
conda activate MinerU
pip install -U magic-pdf[full] --extra-index-url https://wheels.myhloli.com -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt
python webui.py
```

> 启动成功后，浏览器打开 http://localhost:7860/ 即可访问项目主页。

## TODO：
- [ ] 支持进度查看
- [ ] 支持多文件上传，批处理