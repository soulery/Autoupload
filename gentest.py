#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      haow
#
# Created:     27/01/2014
# Copyright:   (c) haow 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import re
import sys
import urllib
import ast
from random import randint
from random import choice
from BeautifulSoup import BeautifulSoup as bs

def get_en_chr_list(content):
    en_list = []
    chr_list = []
    for line in content:
        chr_str = ""
        en_str = ""
        if len(line) > 2 and line[0] != "#":
            s = line.replace('\n','').replace('\r','')
            m = s.split("\t")
            s_new = []
            for i in m:
                if i != '':
                    s_new.append(i)

            if only_raw(s_new[1]):
                en_str = s_new[0]
                if len(s_new) == 3:
                    chr_str = s_new[2]
                else:
                    for i in range (2,len(s_new)):
                        if keep_property(s_new[i]):
                            chr_str = chr_str + s_new[i] + "."
                        else:
                            if has_en_string(s_new[i]):
                                trim_str = ""
                            else:
                                trim_str = trim_en_char(s_new[i])
                            chr_str = chr_str + trim_str + "."

            chr_str=re.sub(r'(!n\.)\w+','',chr_str)
            chr_str=chr_str.replace('..','.').replace('..','.').replace('..','.')
            if en_str != '':
                en_list.append(en_str)
            if chr_str != '':
                chr_list.append(chr_str)

    return en_list,chr_list

def only_raw(str):
    if re.search(r'^1',str): #only test unfamiliar words
        return True
    else:
        return False

def keep_property(str):
    if re.search(r'adj\.|v\.|vi\.|n\.|adv\.|vt\.', str):
        return True
    else:
        return False

def trim_en_char(str):
    str = re.sub(r'\w+','',str)
    return str

def has_en_string(str):
    if re.search(r'\w+',str):
        return True
    else:
        return False


def print_en_chr_line(en_list,chr_list,line_num):
    print en_list[line_num],chr_list[line_num].decode("utf8")

def check(string):
    string = string.replace("&#39","'").replace("&quot","")
    return string

def get_seq(ans):
    if ans == 'A':
        seq = 0
    elif ans == 'B':
        seq = 1
    elif ans == 'C':
        seq = 2
    elif ans == 'D':
        seq = 3
    elif ans == 'E':
        seq = 4
    return seq

def search_en_meaning(word,filename):
    print word
    url="http://services.aonaware.com/DictService/Default.aspx?action=define&dict=wn&query="+word
    try:
		obj=urllib.urlopen(url);
    except:
		pass
		return
    content=obj.read()
    soup = bs(content)
    for span in soup.findAll('pre'):
        meaning = span.text.replace('&quot;','')
        lines = re.split('\n',meaning)
        n = 0
        watch = False
        for i in lines:
            i = re.sub(r'^\s+','',i)
            if re.search(r'[0-9]:',i) and re.search(r'^[a-zA-Z]',i):
                watch = True
            if watch and re.search(r'[0-9]:',i) and re.search(r'^[0-9]',i):
                watch = False
            if watch:
                filename.write(i+'\n')
            n=n+1
    filename.write('\n')
    obj.close()


def search_en_google(word,filename):
    url="http://www.google.com/dictionary/json?callback=s&q="+word+"&sl=en&tl=zh&restrict=pr,de&client=te"
    try:
		obj=urllib.urlopen(url);
    except:
		pass
		return
    content=obj.read()
    obj.close()
    content=content[2:-10]
    dic=ast.literal_eval(content)
    if dic.has_key("webDefinitions"):
		webdef=dic["webDefinitions"]
		webdef=webdef[0]
		webdef=webdef["entries"]
		index=1
		index_list=["01","02"]
		for i in webdef:
			if index==3:
				break
			filename.write('\tExplanation'+str(index)+':\n')
			index+=1

			if i["type"]=="meaning":
				ans=i["terms"]
				op=ans[0]['text']
				split=op.split(';')
				filename.write('\t'+check(split[0].strip())+'\n')
				count=0
				for i in split:
					if count!=0:
						filename.write('\t\t'+check(i)+'\n')
					count+=1
    else:
		pass
    filename.write('\n')


def main():
    answer = ['A','B','C','D','E']
    question = """%s. What is the meaning of %s.

A. %s
B. %s
C. %s
D. %s
E. %s

Answer: %s

Correct answer explanation and reference.

"""
    file = open("C:\\Users\\administrator\\Downloads\\wordbook.txt","r")
    content = file.readlines()
    enl,chrl = get_en_chr_list(content)
    file.close()
    file = open("C:\\Users\\administrator\\Downloads\\wordquiz.txt","w+")
    #print_en_chr_line(enl,chrl,0)

    for i in range (0,len(enl)):
        quiz_list = []
        quiz_num = i + 1
        quiz_list.append(quiz_num)
        quiz_list.append(chrl[i]) #Answer from chrl
        ans = choice(answer)
        seq = get_seq(ans)
        temp_list = [None]*5
        for j in range (0,5):
            if j == seq:
                temp_list[j] = enl[i] #Correct Choice
            else:
                wrong_choice = choice(enl)
                while wrong_choice == enl[i] or wrong_choice in temp_list:
                    wrong_choice = choice(enl)
                temp_list[j] = wrong_choice
            quiz_list.append(temp_list[j])
        quiz_list.append(ans)
        quiz_body = question % (quiz_list[0],quiz_list[1],quiz_list[2],quiz_list[3],quiz_list[4],quiz_list[5],quiz_list[6],quiz_list[7])
        file.write(quiz_body)
        #search_en_google(enl[i],file)
        search_en_meaning(enl[i],file)

    for i in range (0,len(enl)):
        quiz_list = []
        quiz_num = i + len(enl) + 1
        quiz_list.append(quiz_num)
        quiz_list.append(enl[i]) #Answer from chrl
        ans = choice(answer)
        seq = get_seq(ans)
        temp_list = [None]*5
        for j in range (0,5):
            if j == seq:
                temp_list[j] = chrl[i] #Correct Choice
            else:
                wrong_choice = choice(chrl)
                while wrong_choice == chrl[i] or wrong_choice in temp_list:
                    wrong_choice = choice(chrl)
                temp_list[j] = wrong_choice
            quiz_list.append(temp_list[j])
        quiz_list.append(ans)
        quiz_body = question % (quiz_list[0],quiz_list[1],quiz_list[2],quiz_list[3],quiz_list[4],quiz_list[5],quiz_list[6],quiz_list[7])
        file.write(quiz_body)
        #search_en_google(enl[i],file)
        search_en_meaning(enl[i],file)

    file.close


if __name__ == '__main__':
    main()
