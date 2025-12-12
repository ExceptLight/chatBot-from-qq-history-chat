# DigitFriend
---
> 上传QQ聊天记录，生成朋友的虚拟聊天
---

## 📃📃 TODO
 - [ ] 完善人物摘要的提取 
 - [ ] 使用RAG实现记忆能力

---
## 📓📓 项目简介

安装相关环境
**DigitFriend**让您可以通过上传的聊天记录，生成对应人物的数字人，随时随地进行聊天.

---

## 🌲🌲 项目目录结构
```
DigitFriend
├─.vscode
├─abstract
├─history
├─parse_history
├─scripts
│ ├─extract_persona.py
│ └─parse_history.py
├─main.py
└─README.md
```
---

## 🚀🚀 快速开始

### 环境准备
```bash 
conda create -n chatBotFromQQ python=3.11
conda activate chatBotFromQQ
pip instlal -r requirements.txt
```

### 运行项目

**1. 预处理聊天记录**
```bash
conda activate chatBotFromQQ
python scripts/parse_history.py -f "/path/to/your/file" -o "/path/to/your/output/dir"
```

**2. 使用大模型创建人物摘要**
```bash
python scripts/extract_persona.py -f "/path/to/your/file.json" -o "path/to/output" -t "your/target" --model "your/model" --api-key "your/key" --base-url "your/url" --chunk-size 30
```
---