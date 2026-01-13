FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码（.dockerignore 会排除 config.yaml 和 data/）
COPY . .

# 复制配置文件模板（仅作为参考）
COPY config.yaml.example ./config.yaml.example

# 暴露端口
EXPOSE 8888

# 启动应用
CMD ["python", "app.py"]
