import os
import json
import argparse
from openai import OpenAI


def main():
    parser = argparse.ArgumentParser(description="Chunked persona extractor (chunk -> summarize -> merge).")
    parser.add_argument("-f", "--input-file", dest="input_file", required=True, help="Path to input JSON list file.")
    parser.add_argument("-o", "--output-dir", dest="output_dir", default="./abstract", help="Output directory.")
    parser.add_argument("-t", "--target", dest="target", required=True, help="Target senderName to analyze.")
    parser.add_argument("--base-url", dest="base_url", default="http://127.0.0.1:11434/v1", help="OpenAI base URL (proxy).")
    parser.add_argument("--api-key", dest="api_key", default=None, help="API key (or use APIKEY env).")
    parser.add_argument("--model", dest="model", required=True, help="Model to use.")
    parser.add_argument("--chunk-size", dest="chunk_size", type=int, default=1000, help="Messages per chunk.")
    parser.add_argument("--min-messages", dest="min_messages", type=int, default=5, help="Minimum messages required.")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("APIKEY", "")
    client = OpenAI(base_url=args.base_url, api_key=api_key)

    with open(args.input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    target = args.target
    uid = None
    all_names = set()
    for msg in messages:
        all_names.add(msg['senderName'])
        all_names.add(msg['receiverName'])
        if msg['senderName'] == target:
            uid = msg['senderUid']
            break
        if msg['receiverName'] == target:
            uid = msg['receiverUid']
            break
    if uid is None:
        print(f'聊天记录不包含目标人物！！可选的人物有({all_names})')
        return

    chunk_size = args.chunk_size
    chunks = [messages[i:i+chunk_size] for i in range(0, len(messages), chunk_size)]

    # prompt templates
    system_prompt_chunk = """
        【角色设定】
        你是一位专业的对话行为分析师，擅长从人际交流文本中提取人物特征。你具备心理学、语言学和社交行为分析的专业知识。

        【核心能力】
        1. 文本特征提取：能从对话中识别独特的语言模式和表达习惯
        2. 行为模式分析：能基于对话序列推断人物的互动偏好和社交风格
        3. 语境敏感分析：能理解不同对话场景对说话方式的影响
        4. 客观推断：基于文本证据进行分析，避免无依据的主观猜测
    """

    user_content_template = """
            请基于以下聊天记录，**分析人物""" + target + """"的对话特征**。
            在对话中出现的主体有 ` {} `，但是记得只分析**人物"""+ target +"""**
            【聊天记录】：
            {}

            【分析重点选择】：
              A. 语言风格：用词习惯、句式结构、常用表达等
              B. 情感倾向：常见情绪表达、情感变化模式等
              C. 交流方式：信息传递风格、回应习惯、互动频率等
              D. 社交特征：对话中的角色定位、关系处理方式等
        
            【输出详细程度】：
              只输出核心发现
        
            【其他要求】
                1. 只分析目标人物的发言，忽略对其他人的分析
                2. 基于文本证据进行分析，避免无依据的推断
                3. 明确区分观察事实与合理推断
            """

    print(user_content_template)

    chunk_summaries = []
    for idx, chunk in enumerate(chunks, start=1):
        print(f"正在处理 chunk {idx}/{len(chunks)}，消息数：{len(chunk)}")
        # 如果chunk中不包含目标人物，跳过
        if all(msg['senderName'] != target for msg in chunk):
            print(f"跳过 chunk {idx}，不包含目标人物 {target}。")
            continue
        user_content = user_content_template.format(json.dumps(list(all_names)), json.dumps(chunk, ensure_ascii=False))
        # print(user_content)
        # user_content = "下面是聊天记录：\n\n，**你需要从中分析的目标人物是{}，需要生成其摘要**,不要分析其他人".format(target) + json.dumps(chunk, ensure_ascii=False)
        try:
            resp = client.chat.completions.create(
                model=args.model,
                messages=[
                    {"role": "system", "content": system_prompt_chunk},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=5000,
                temperature=0.2,
                top_p=0.1
            )
            # print(resp)
            text = resp.choices[0].message.content
            dir = os.path.join(args.output_dir, uid)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(os.path.join(dir, f"chunk_{idx}_summary.txt"), "w+", encoding="utf-8") as f:
                f.write(text)    
            print(text)
            if text:
                chunk_summaries.append(text)
            else:
                chunk_summaries.append(f"(chunk {idx} 无摘要或模型返回为空)")
        except Exception as e:
            print(f"调用模型失败（chunk {idx}）：{e}")
            chunk_summaries.append(f"(chunk {idx} 调用失败：{e})")

    # 合并所有 chunk 的摘要为最终摘要
    system_prompt_merge = (
        "你是一个负责把多条短摘要合并为最终人物简介的助手。"
        "下面给出若干 chunk 摘要，请将它们合成为一段关于目标人物的中文最终摘要，用于下游对话模型模仿目标说话方式。"
        "要求：按方面总结目标人物的特点，一定要全面且真实。"
    )
    merge_input = "以下为各 chunk 的摘要（按顺序），**你需要分析的目标人物是{}**,不要分析其他人：\n\n".format(target) + "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(chunk_summaries))

    try:
        resp2 = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": system_prompt_merge},
                {"role": "user", "content": merge_input}
            ],
            max_tokens=800,
            temperature=0.3
        )
        final_summary = resp2.choices[0].message.content
    except Exception as e:
        print(f"合并调用失败：{e}")
        final_summary = "\n".join(chunk_summaries)

    # write output
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, f"{uid}_persona.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_summary)

    print("完成，输出已写入：", out_path)

if __name__ == "__main__":
    main()