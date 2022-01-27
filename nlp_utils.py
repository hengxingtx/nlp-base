#! python3
# -*- encoding: utf-8 -*-
#############################
#@File    :   nlp_utils.py
#@Time    :   2022/01/27 17:13:57
#@Author  :   heng 
#@Version :   1.0
#@Contact :   hengsblog@163.com
#@Comment :   NLP中的常用预处理操作
#############################

import subprocess
import logging
import sys

def get_file_len(file_in):
    "通过wc指令获取文件行数"
    result = subprocess.run(["wc", "-l", file_in], capture_output=True)
    return result.stdout.strip().split()[0]


def split_by_file_num(file_in, n, need_remaining=False):
    "按照文件数分割大文件为小文件"
    "param:"
    "file_in:输入的大文件"
    "n:分割为n个小文件"
    "need_remaining:末尾不足平均行数的文本是否存为第n+1个文件"
    n = int(n)
    if file_in.startswith("."):
        prefix = "."+"".join(file_in.split(".")[:-1])
    else:
        prefix = "".join(file_in.split(".")[:-1])
    print("file prefix is ", prefix)
    len_file = int(get_file_len(file_in))
    each_file_len = len_file // n  # 每个文件行数
    idx = 0
    all_text, sub_text = [], []
    with open(file_in, encoding='utf-8') as fin:
        for line_num, line_text in enumerate(fin):
            sub_text.append(line_text)
            if line_num == each_file_len * (idx + 1):
                idx += 1
                all_text.append(sub_text)
                sub_text = []
                logging.warning(f"file {idx} append success")
                
        if need_remaining:
            all_text.append(sub_text)  # 多余的不足平均行数的文本
            logging.warning(f"file {idx} append success")

    for idx, text in enumerate(all_text):
        write_file = f"{prefix}_{idx+1}.txt"
        with open(write_file, 'w', encoding='utf-8') as fout:
            for i in text:
                fout.write(i)


def main():
    "main"
    file_in, n = sys.argv[1], sys.argv[2]
    split_by_file_num(file_in, n)

if __name__ == "__main__":
    main()