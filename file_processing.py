#! python3
# -*- encoding: utf-8 -*-
###############################################################
#          @File    :   file_processing.py
#          @Time    :   2022/01/28 11:08:47
#          @Author  :   heng
#          @Version :   1.0
#          @Contact :   gaohengde@baidu.com
#          @Copyright (c) 2021 Baidu.com, Inc. All Rights Reserved
###############################################################
"""
@comment:文件相关操作
"""

import subprocess
import logging
import sys
import numpy as np
import os
import jieba
import sklearn.model_selection as s_m
from . import text_processing as tp_heng


def load_to_list(file_input):
    """读取文件，不做任何处理"""
    with open(file_input, encoding="utf-8", errors="ignore") as fin:
        content = [line.strip() for line in fin]
        return content


def load_to_set(file_input):
    """读取文件，返回set"""
    with open(file_input, encoding="utf-8", errors="ignore") as fin:
        return set([i.strip() for i in fin])


def load_idf(file_input):
    """读取idf词典"""
    words_idf = {}
    with open(file_input, encoding='utf-8', errors="ignore") as fin:
        for i in fin:
            word, idf = i.strip().split()
            words_idf[word] = float(idf)
    return words_idf

def load_word2vec(vec_file, word_dim):
    "读取词向量文件"
    "param:vec_file:词向量文件路径"
    "word_dim:向量维度"
    "return:词与array类型向量的字典"
    word2vec = {}
    with open(vec_file, encoding='utf-8', errors="ignore") as fin:
        fin.readline()
        for i in fin:
            line = i.strip().split(" ",1)
            if len(line) != 2:
                logging.error("vec file maybe err, please check!")
                continue
            word, vec = line[0], line[1]
            try:
                word2vec[word] = np.array([float(i) for i in vec.split()]).reshape(1, word_dim)
            except Exception as e:
                raise ValueError("vec size is not equal %s, error is %s"%(word_dim,e))
    return word2vec


def get_file_len(file_in):
    "通过wc指令获取文件行数"
    result = subprocess.run(["wc", "-l", file_in], capture_output=True)
    return int(result.stdout.strip().split()[0])


def split_by_file_num(file_in, num=10, line_num="100", mem="5k", method="num", need_remaining=False):
    "按照文件数分割大文件为小文件"
    "param:"
    "file_in:输入的大文件"
    "n:分割为n个小文件"
    "each_file_num:按照行数分割时，每个文件的行数"
    "need_remaining:末尾不足平均行数的文本是否存为第n+1个文件"
    "method:分割方式"
    "       --num:按照文件个数分割--mem:按照文件大小分割--line_no:按照行数分割"

    "注意:"
    "这里把输出的文件直接放在原路径下，文件名和原文件名相同并加后缀。"
    "如果要改输出可以自己改改代码或者提issue我有时间改改"
    "按照num分割文件速度比较慢,后面有时间优化下速度"
    try:
        n = int(num)
        line_num = str(int(line_num))
    except Exception as e:
        raise ValueError(f"n or line_num must be a number, please check it!")

    if file_in.startswith("."):
        prefix = "."+"".join(file_in.split(".")[:-1])
    else:
        prefix = "".join(file_in.split(".")[:-1])

    logging.info("file prefix is ", prefix)
    
    len_file = get_file_len(file_in)

    if method == "line_num":  # 按照行数进行分割,这里使用shell的split函数，分割后的文件会以双字母结尾
        subprocess.run(["split", "-l", line_num, file_in, prefix], capture_output=True)
    elif method == "mem":  # 按照大小切割,这里使用shell的split函数，分割后的文件会以双字母结尾
        subprocess.run(["split", "-b", mem, file_in, prefix], capture_output=True)
    elif method == "num":  # 按照文件个数进行分割
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
    else:
        raise ValueError("please input right method one of num,line_num,mem")


def merge_and_write(base_dir, write_path, is_dfs=False):
    """将一个文件夹下的多个文件写入一个文件
    param:
        base_dir:原文件路径
        write_dir:写入文件路径
        if_dfs:是否递归写入
               true:将文件夹内所有文件夹下的文件全部写入
               false:只写入该文件夹下的文件，不写子文件夹下的文件
    return:
        None"""
    with open(write_path, 'w', encoding='utf-8') as fout:
        for dirpath, dirname, filenames in os.walk(base_dir):
            for sub_file in filenames:
                file_path = os.path.join(dirpath, sub_file)
                for i in load_to_list(file_path):
                    fout.write(f"{i}\n")
                logging.info(f"writing file {file_path} success!!!")
            if is_dfs:
                break


def split_by_max_length(file_in, file_out, max_length, min_length=20):
    """按照句子长度分割文本
    param:
        file_in:待分割文本文件，一行为一个待分割长文本
        max_length:每行的最大字数
        file_out:分割后的文件写入路径
    return:
        分割后的文本"""
    count = 0
    with open(file_out, 'w', encoding='utf-8') as fout:
        with open(file_in, encoding='utf-8') as fin:
            for i in fin:
                line = i.strip("\n")
                for sent in tp_heng.Paragraph().split_content_by_max(line, max_length, min_length):
                    count += 1
                    fout.write(f"{sent}\n")
    logging.info(f"write file success contains {count} line")


def split_train_test_dev(data_or_file, test_size=0.2, dev_size=0.1, shuffle=False):
    """划分训练测试和验证集
    param:
        data_or_file:输入列表或者文件路径
        test_size:测试集占比
        dev_size:验证集占比(这里是基于训练集的二次划分)"""
    if isinstance(data_or_file, list):
        all_data = data_or_file
    elif os.path.isfile(data_or_file):
        all_data = load_to_list(data_or_file)
    else:
        raise ValueError("please input list for file path")
    train, test = s_m.train_test_split(all_data, test_size=test_size, shuffle=shuffle)
    train, dev = s_m.train_test_split(train, test_size=dev_size)
    return train, test, dev


def write_list(input, file_out):
    "将列表写入文件"
    with open(file_out, 'w', encoding='utf-8') as fout:
        for i in input:
            fout.write(f"{i}\n")

def main():
    "main"
    file_in, n = sys.argv[1], sys.argv[2]
    split_by_file_num(file_in, n, method="num")

if __name__ == "__main__":
    main()