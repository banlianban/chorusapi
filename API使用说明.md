# Chorus API 使用说明文档

## 概述

Chorus API 是一个基于 FastAPI 构建的强大服务，用于从音频文件中自动提取音乐副歌部分。该 API 使用 [pychorus](https://github.com/vivjay30/pychorus) 库来实现智能的副歌检测和提取功能。

## 主要特性

- 🎵 **智能副歌提取**: 自动检测并提取音频文件中最可能的副歌部分
- 🚀 **高性能**: 基于 FastAPI 框架，支持异步处理
- 📁 **多格式支持**: 支持 MP3、WAV、M4A、FLAC、AAC、OGG 等音频格式
- ⚡ **异步处理**: 非阻塞文件处理，提供更好的性能
- 🔧 **可配置**: 支持自定义时长、质量设置和文件处理参数
- 📊 **健康监控**: 内置健康检查端点
- 🗂️ **文件管理**: 自动清理和临时文件处理
- 📚 **自动文档**: 交互式 API 文档，支持 Swagger UI 和 ReDoc

## 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器

### 安装步骤

1. **克隆仓库**:
   ```bash
   git clone <repository-url>
   cd chorus-api
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量** (可选):
   ```bash
   cp env.example .env
   # 编辑 .env 文件设置您的偏好配置
   ```

4. **启动服务**:
   ```bash
   python main.py
   ```
   
   或使用 uvicorn 直接启动:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

API 将在 `http://localhost:8000` 上运行

## API 端点文档

### 交互式文档

服务运行后，您可以访问以下地址查看交互式 API 文档：
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 端点列表

#### 1. 健康检查

```http
GET /
GET /health
```

**描述**: 返回 API 状态和版本信息

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "running"
}
```

#### 2. 提取副歌

```http
POST /extract-chorus
```

**描述**: 从上传的音频文件中提取副歌部分

**请求参数**:
- `file` (multipart/form-data, 必需): 要处理的音频文件
- `duration` (form data, 可选): 要提取的副歌时长（10-120秒，默认30秒）
- `quality` (form data, 可选): 质量设置 - "low"、"medium"、"high"（默认"high"）

**响应示例**:
```json
{
  "success": true,
  "chorus_start_sec": 45.2,
  "output_file_path": "outputs/abc123_chorus.wav",
  "message": "Chorus extracted successfully",
  "file_id": "abc123"
}
```

**错误响应**:
```json
{
  "detail": "Invalid file type. Supported formats: mp3, wav, m4a, flac"
}
```

#### 3. 下载副歌文件

```http
GET /download/{file_id}
```

**描述**: 使用从 extract-chorus 端点返回的 file_id 下载提取的副歌文件

**路径参数**:
- `file_id` (string, 必需): 从 extract-chorus 端点返回的文件 ID

**响应**: 返回 WAV 格式的副歌音频文件

#### 4. 清理文件

```http
DELETE /cleanup/{file_id}
```

**描述**: 清理与特定 file_id 关联的临时文件

**路径参数**:
- `file_id` (string, 必需): 要清理的文件 ID

**响应示例**:
```json
{
  "message": "Files cleaned up successfully",
  "file_id": "abc123"
}
```

#### 5. 获取支持的格式

```http
GET /supported-formats
```

**描述**: 返回支持的音频格式和限制信息

**响应示例**:
```json
{
  "supported_formats": [".mp3", ".wav", ".m4a", ".flac"],
  "max_file_size": "50MB",
  "max_duration": "120 seconds"
}
```

## 使用示例

### Python 示例

```python
import requests

# 从音频文件提取副歌
url = "http://localhost:8000/extract-chorus"
files = {"file": open("song.mp3", "rb")}
data = {"duration": 40, "quality": "high"}

response = requests.post(url, files=files, data=data)
result = response.json()

if result["success"]:
    print(f"副歌开始时间: {result['chorus_start_sec']} 秒")
    
    # 下载提取的副歌
    download_url = f"http://localhost:8000/download/{result['file_id']}"
    chorus_file = requests.get(download_url)
    
    with open("extracted_chorus.wav", "wb") as f:
        f.write(chorus_file.content)
```

### cURL 示例

```bash
# 提取副歌
curl -X POST "http://localhost:8000/extract-chorus" \
  -F "file=@song.mp3" \
  -F "duration=30" \
  -F "quality=high"

# 下载提取的副歌
curl -X GET "http://localhost:8000/download/{file_id}" \
  -o "chorus.wav"
```

### JavaScript 示例

```javascript
const formData = new FormData();
formData.append('file', audioFile);
formData.append('duration', '30');
formData.append('quality', 'high');

fetch('http://localhost:8000/extract-chorus', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(`副歌开始时间: ${data.chorus_start_sec} 秒`);
    // 下载文件
    window.open(`http://localhost:8000/download/${data.file_id}`);
  }
});
```

## 配置选项

API 支持通过环境变量进行配置：

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务器主机地址 |
| `PORT` | `8000` | 服务器端口 |
| `DEBUG` | `false` | 调试模式 |
| `MAX_FILE_SIZE` | `52428800` | 最大文件大小（字节，50MB） |
| `MIN_DURATION` | `10` | 最小副歌时长（秒） |
| `MAX_DURATION` | `120` | 最大副歌时长（秒） |
| `DEFAULT_DURATION` | `30` | 默认副歌时长（秒） |
| `FILE_RETENTION_HOURS` | `24` | 文件保留时间（小时） |

## 支持的音频格式

- **MP3** (.mp3)
- **WAV** (.wav)
- **M4A** (.m4a)
- **FLAC** (.flac)
- **AAC** (.aac)
- **OGG** (.ogg)

## 质量设置

- **Low**: 快速处理，较低精度（22.05kHz, 16-bit）
- **Medium**: 平衡处理（44.1kHz, 16-bit）
- **High**: 较慢处理，高精度（44.1kHz, 24-bit）

## 错误处理

API 返回适当的 HTTP 状态码和错误信息：

- `400 Bad Request`: 无效文件格式、时长超出范围或缺少参数
- `404 Not Found`: 下载时文件未找到
- `500 Internal Server Error`: 处理错误或服务器问题

**常见错误信息**:
- `"Invalid file type. Supported formats: mp3, wav, m4a, flac"`
- `"Duration must be between 10 and 120 seconds"`
- `"File not found. It may have expired or been deleted."`
- `"Failed to extract chorus from audio file"`

## 文件管理

- 上传的文件存储在 `uploads/` 目录
- 提取的副歌文件存储在 `outputs/` 目录
- 临时文件存储在 `temp/` 目录
- 文件在 24 小时后自动清理（可配置）
- 可通过 `/cleanup/{file_id}` 端点手动清理

## 开发指南

### 项目结构

```
chorus-api/
├── main.py                 # FastAPI 应用程序
├── requirements.txt        # Python 依赖
├── env.example            # 环境变量模板
├── README.md              # 项目说明
├── config/
│   ├── __init__.py
│   └── settings.py        # 配置设置
└── utils/
    ├── __init__.py
    ├── audio_processor.py # 音频处理工具
    └── file_manager.py    # 文件管理工具
```

### 开发环境运行

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行并自动重载
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 测试

```bash
# 测试健康检查端点
curl http://localhost:8000/health

# 测试副歌提取
curl -X POST "http://localhost:8000/extract-chorus" \
  -F "file=@test_audio.mp3" \
  -F "duration=30"
```

## 依赖库

- **FastAPI**: 构建 API 的现代 Web 框架
- **pychorus**: 副歌提取的核心库
- **librosa**: 音频分析库
- **soundfile**: 音频文件 I/O
- **uvicorn**: ASGI 服务器
- **aiofiles**: 异步文件操作

## 最佳实践

1. **文件大小**: 建议上传文件大小不超过 50MB
2. **音频质量**: 使用高质量音频文件可获得更好的副歌检测效果
3. **时长设置**: 根据歌曲长度合理设置副歌提取时长
4. **文件清理**: 及时清理不需要的文件以节省存储空间
5. **错误处理**: 始终检查 API 响应中的 `success` 字段
6. **超时设置**: 对于大文件，设置适当的请求超时时间

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件格式是否支持
   - 确认文件大小未超过限制
   - 验证网络连接

2. **副歌提取失败**
   - 确认音频文件未损坏
   - 尝试不同的质量设置
   - 检查音频文件是否包含明显的副歌部分

3. **下载失败**
   - 确认 file_id 正确
   - 检查文件是否已过期被清理
   - 验证网络连接

### 日志查看

API 会记录详细的处理日志，包括：
- 文件上传和保存
- 音频处理过程
- 错误和异常信息
- 文件清理操作

## 许可证

本项目基于 [pychorus](https://github.com/vivjay30/pychorus) 库构建。请参考原始库的许可证了解使用条款。

## 支持

如遇到问题或需要帮助：

1. 查看 API 文档：`/docs` 或 `/redoc`
2. 检查响应中的错误信息
3. 查看服务器日志获取详细错误信息
4. 确认音频文件格式支持且未超过大小限制

## 更新日志

### v1.0.0
- 初始版本发布
- 支持多种音频格式
- 提供完整的 REST API
- 支持异步处理
- 包含文件管理和清理功能

