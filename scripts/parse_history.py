import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Digit Friend Application")
    parser.add_argument("-f", "--history-chat-file", type=str, required=True, help="path to history json")
    parser.add_argument("-o", "--output-dir", type=str, default="./parse_history", help="output directory")


    args = parser.parse_args()

    history = json.load(open(args.history_chat_file, "r", encoding="utf-8"))
    target_uid = "_".join(args.history_chat_file.split('_')[1:3])
    senders = [{"name": senderInfo['name'],
                "uid" : senderInfo['uid']} for senderInfo in history['statistics']['senders']]

    print(f"正在提取{senders[0]['name']}和{senders[0]['name']}的聊天记录...")
    messages = [{
        "senderUid":line['sender']['uid'],
        "senderName":line['sender']['name'],
        "content":line['content']['text'],
        "receiverUid":senders[0]['uid'] if line['sender']['uid'] == senders[1]['uid'] else senders[1]['uid'],
        "receiverName":senders[0]['name'] if line['sender']['uid'] == senders[1]['uid'] else senders[1]['name'],
        "timestamp":line["timestamp"]
    } for line in history['messages'] if line['sender']['name'] != '0']
    print(f"提取出 {len(messages)} 条有效的聊天记录")
    output_path = '{}/{}.json'.format(args.output_dir, target_uid)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)
    print("处理后的聊天记录已保存至:", output_path)


if __name__ == "__main__":
    main()