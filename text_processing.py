#! python3
# -*- encoding: utf-8 -*-
###############################################################
#          @File    :   utils.py
#          @Time    :   2022/01/25 15:47:52
#          @Author  :   heng
#          @Version :   1.0
#          @Contact :   gaohengde@baidu.com
#          @Copyright (c) 2021 Baidu.com, Inc. All Rights Reserved
###############################################################
"""
@comment:文本处理中常用的辅助函数
"""
import logging
import re
import jieba
import os
import sys
import unicodedata
import zhconv
from . import file_processing as fp_heng


class Words(object):
    """跟词或字符相关的辅助函数"""
    def __init__(self):
        self.words = None
    
    def _is_whitespace(char):
        """Checks whether `char` is a whitespace character."""
        # \t, \n, and \r are technically control characters but we treat them
        # as whitespace since they are generally considered as such.
        if char == " " or char == "\t" or char == "\n" or char == "\r":
            return True
        cat = unicodedata.category(char)
        if cat == "Zs":
            return True
        return False

    def _is_punctuation(char):
        """Checks whether `char` is a punctuation character."""
        cp = ord(char)
        # We treat all non-letter/number ASCII as punctuation.
        # Characters such as "^", "$", and "`" are not in the Unicode
        # Punctuation class but we treat them as punctuation anyways, for
        # consistency.
        if (cp >= 33 and cp <= 47) or (cp >= 58 and cp <= 64) or (cp >= 91 and cp <= 96) or (cp >= 123 and cp <= 126):
            return True
        cat = unicodedata.category(char)
        if cat.startswith("P"):
            return True
        return False

class Sentence(object):
    """跟句相关的辅助函数"""
    def __init__(self, stopwords_file=""):
        self.stopwords_file = stopwords_file
        self.Words = Words()
        self.load_dicts()

    def load_dicts(self):
        """加载停用词"""
        if self.stopwords_file != "":
            self.stopwords = fp_heng.load_to_set(self.stopwords_file)
        else:
            self.stopwords = set()

    def pre_sentence(self, sentence,
                    replace_num=True,
                    quan_2_ban=True,
                    replace_punc=True,
                    convert_fan_jian=True,
                    remove_whitespace=True,
                    to_lower=True,
                    remove_stopwords=False,
                    ):
        """
        句子预处理
        param:
            replace_num:数字替换<num>,
            covert_fan_jian:繁简转换,
            quan_2_ban:全角半角转换,
            to_lower:大小写转换,
            replace_punc:替换标点为空格,
            remove_whitespace:去除空白符
            remove_stopwords:去除停用词
        """
        if replace_num:
            sentence = re.sub("[0-9]+", "<num>", sentence)
        if quan_2_ban:
            sentence = self.quan_to_ban(sentence)
        if replace_punc:
            sentence = self.replace_punc_to_blank(sentence)
        if convert_fan_jian:
            sentence = zhconv.convert(sentence, "zh-cn")
        if to_lower:
            sentence = sentence.lower()
        if remove_whitespace:
            sentence = "".join([i for i in sentence if not self.Words._is_whitespace(i)])
        if remove_stopwords:
            if len(self.stopwords) == 0:
                return sentence
            sentence = " ".join([word for word in jieba.cut(sentence) if word not in self.stopwords])
        return sentence
    
    def replace_punc_to_blank(self, sentence):
        """将句中的标点替换为空格"""
        temp = ""
        for i in sentence:
            if not self.Words._is_punctuation(i):
                temp += i
        return temp

    def quan_to_ban(self, sentence):
        """字符串全角转半角"""
        def _quan_2_ban_(uchar):
            """单个字符 全角转半角"""
            inside_code = ord(uchar)
            if inside_code == 0x3000:
                inside_code = 0x0020
            else:
                inside_code -= 0xfee0
            if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
                return uchar
            return chr(inside_code)
        return "".join([_quan_2_ban_(uchar) for uchar in sentence])


class Paragraph(object):
    """跟段落相关的辅助函数
    param:
        base_path:文本所在路径"""
    def __init__(self, base_path=""):
        self.base_path = base_path
    
    def split_content_by_max(self, content, max_length, min_length=20):
        """按照max_len将过检文本切割, 最后一段如果小于min_length则抛去
        param:
            file_in:待分割文本文件或列表，一行为一个待分割长文本
            max_length:每行的最大字数
            min_length:每行的最小字数
        return: 分割后的子片段"""
        len_ = len(content)
        if len_ < min_length: return []
        if len_ <= max_length: return [content]

        split_sent = []
        bound = range(0, len_ + 1, max_length)  # 这里如果len不加1则取不到最后一个字符
        for idx, i in enumerate(bound):
            if idx == 0: continue
            sub_sent = content[bound[idx - 1]:bound[idx]]
            split_sent.append(sub_sent)
        if len(content[bound[idx]:len_]) > min_length:
            split_sent.append(content[bound[idx]:len_])
        
        return split_sent

    def process(self):
        "按结尾标点分割文本"
        with open(self.file_in, encoding='utf-8') as fin:
            for line in fin:
                line = line.strip("\n")
                for sent in re.split("[。？！……]", line):
                    self.sentence_all.add(sent)
                
        with open(self.file_out, 'w', encoding='utf-8') as fout:
            for line in self.sentence_all:
                if len(line) > 5:
                    fout.write(f"{line}\n")
        print(f"len sentence in {len(self.sentence_all)}")

