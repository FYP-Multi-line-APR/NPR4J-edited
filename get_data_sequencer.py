import codecs
import os
import re
import subprocess

import javalang
from tqdm import tqdm

from CodeAbstract.CA_SequenceR import run_SequenceR_abs
# from CodeAbstract.CA_src2abs import run_src2abs
# from Utils.CA_Utils import remove_comments
from Utils.IOHelper import readF2L, writeL2F, readF2L_ori
# from Utils._tokenize import CoCoNut_tokenize

# BENCH="qbs_"

"""
ids_f: a list of bug-fix ids
input_dir: raw data dir 
output_dir: where you want to output the processed code of SequenceR
tmp_dir: when building a SequenceR-type context, you need a directory to restore temp files
"""
def preprocess_SequenceR_fromRaw(ids_f,input_dir,output_prefix,tmp_dir,BENCH="qbs_"):
    ids=readF2L(ids_f)

    def build(src_f, tgt_f, error_f, correct_f, ids):
        buggy_codes = []
        fix_codes = []
        error_ids = []
        correct_ids = []
        ind = 1
        in_count = 0

        small_fixes=[]
        for id in ids:
            print(id)
            buginfo = {"_id": id}
            try:
                buginfo["buggy_code"] = readF2L_ori(input_dir + "/buggy_methods/"+BENCH + id + '.txt')
            except Exception as e:
                print("Error:",e)
                continue
            buginfo["buggy_line"] = codecs.open(input_dir + "/buggy_lines/" +BENCH+ id + '.txt', 'r',
                                                encoding='utf8').read().strip()
            id_metas = codecs.open(input_dir + "/metas/" +BENCH+ id + '.txt', 'r', encoding='utf8').read().strip()
            buginfo["err_start"] = int(str(id_metas.split("<sep>")[2])[1:-1].split(":")[0])
            buginfo["err_end"] = int(str(id_metas.split("<sep>")[2])[1:-1].split(":")[1])

            tmp_f = tmp_dir +'/'+ id + '.txt'
            fix_code = codecs.open(input_dir + '/fix_lines/'+BENCH + id + '.txt').read().strip()

            buggy_code, hitflag = run_SequenceR_abs(input_dir + "/buggy_classes/" + id + '.txt', tmp_f, buginfo,max_length=1000)

            print("hitflag", hitflag)

            if hitflag == 1:
                try:
                    toked_fix = javalang.tokenizer.tokenize(fix_code)
                    toked_fix = ' '.join([tok.value for tok in toked_fix])
                except:
                    toked_fix = re.split(r"([.,!?;(){}])", fix_code)
                    toked_fix = ' '.join(toked_fix)

                try:
                    toked_bug = javalang.tokenizer.tokenize(buggy_code)
                    toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                                   '<START_BUG>').replace('< END_BUG >',
                                                                                                          '<END_BUG>')
                except:
                    toked_bug = re.split(r"([.,!?;(){}])", buggy_code)
                    toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace('< END_BUG >',
                                                                                                    '<END_BUG>')

                if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                    method = buginfo["buggy_code"]
                    err_end=int(buginfo["err_end"])
                    err_start=int(buginfo["err_start"])
                    err_end = min(len(method) - 1, err_end)
                    print("err_start",err_start,"err_end",err_end)
                    print(len(method))
                    error_line = "<START_BUG> " + buginfo["buggy_line"] + " <END_BUG>"
                    method = method[:err_start] + [error_line] + method[err_end:]
                    method=' '.join(method)
                    if not ("<START_BUG>" in method and "<END_BUG>" in method):
                        print("not contain flags")
                    else:
                        print("contain flags-------")
                    try:
                        toked_bug = javalang.tokenizer.tokenize(method)
                        toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                                       '<START_BUG>').replace(
                            '< END_BUG >', '<END_BUG>')
                        toked_buggyline=javalang.tokenizer.tokenize(buginfo["buggy_line"])
                        toked_buggyline=' '.join([tok.value for tok in toked_buggyline])
                        if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                            if toked_bug.count(toked_buggyline)==1:
                                toked_bug=toked_bug.replace(toked_buggyline,"<START_BUG> "+toked_buggyline+" <END_BUG>")
                            else:
                                buggy_code=buggy_code.replace('\t\n','').replace('\n','')
                                toked_bug = re.split(r"([.,!?;(){}])", buggy_code)
                                toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace(
                                    '< END_BUG >', '<END_BUG>')
                        else:
                            print("1 contain flags-------")
                    except:
                        buggy_code = buggy_code.replace('\t\n', '').replace('\n', '')
                        toked_bug = re.split(r"([.,!?;(){}])", buggy_code)
                        toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace(
                            '< END_BUG >', '<END_BUG>')

                toked_bug = toked_bug.replace("<START_BUG> <START_BUG>", "<START_BUG>").replace("<END_BUG> <END_BUG>",
                                                                                                "<END_BUG>")
                if len(toked_bug) > 10:
                    toked_bug = toked_bug.replace('\t\n', '').replace('\n', '')
                    buggy_codes.append(toked_bug)
                    if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                        print("not contain flags")
                    else:
                        print("final contain")
                    if toked_fix.strip()=="" or toked_fix.strip().isspace() or len(toked_fix)<1:
                        toked_fix = "<DELETE>"
                    toked_fix = toked_fix.replace('\t\n', ' ').replace('\n', ' ')
                    if len(toked_fix) < 2:
                        small_fixes.append(id + "<sep>" + toked_fix)
                    fix_codes.append(toked_fix)
                    correct_ids.append(buginfo['_id'])
                    in_count += 1
            elif hitflag == 2:
                error_ids.append(buginfo['_id'])
                print(tmp_f)
            else:
                try:
                    toked_fix = javalang.tokenizer.tokenize(fix_code)
                    toked_fix = ' '.join([tok.value for tok in toked_fix])
                except:
                    toked_fix = re.split(r"([.,!?;(){}])", fix_code)
                    toked_fix = ' '.join(toked_fix)
                try:
                    method = buginfo["buggy_code"]
                    err_end=int(buginfo["err_end"])
                    err_start=int(buginfo["err_start"])
                    err_end=min(len(method)-1,err_end)
                    error_line = "<START_BUG> " + buginfo["buggy_line"] + " <END_BUG>"
                    method = method[:err_start] + [error_line] + method[err_end:]
                    method=' '.join(method)
                    try:
                        toked_bug = javalang.tokenizer.tokenize(method)
                        toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                                       '<START_BUG>').replace(
                            '< END_BUG >', '<END_BUG>')
                        toked_buggyline=javalang.tokenizer.tokenize(buginfo["buggy_line"])
                        toked_buggyline=' '.join([tok.value for tok in toked_buggyline])
                        if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                            if toked_bug.count(toked_buggyline)==1:
                                toked_bug=toked_bug.replace(toked_buggyline,"<START_BUG> "+toked_buggyline+" <END_BUG>")
                            else:
                                method = method.replace('\t\n', ' ').replace('\n', ' ')

                                toked_bug = re.split(r"([.,!?;(){}])", method)
                                toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace(
                                    '< END_BUG >', '<END_BUG>')
                        else:
                            print("1 contain flags-------")
                    except:
                        method = method.replace('\t\n', ' ').replace('\n', ' ')
                        toked_bug = re.split(r"([.,!?;(){}])", method)
                        toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace(
                            '< END_BUG >', '<END_BUG>')


                    toked_bug=toked_bug.replace("<START_BUG> <START_BUG>","<START_BUG>").replace("<END_BUG> <END_BUG>","<END_BUG>")

                    if len(toked_bug)>10:
                        toked_bug = toked_bug.replace('\t\n', '').replace('\n', '')
                        buggy_codes.append(toked_bug)
                        if toked_fix.strip()=="" or toked_fix.strip().isspace() or len(toked_fix)<1:
                            toked_fix="<DELETE>"
                        toked_fix = toked_fix.replace('\t\n', ' ').replace('\n', ' ')
                        if len(toked_fix)<2:
                            small_fixes.append(id+"<sep>"+toked_fix)
                        fix_codes.append(toked_fix)

                        correct_ids.append(buginfo['_id'])
                        in_count += 1
                except:
                    continue
            print(ind, "correct:", len(correct_ids))
            print('='*20)
            ind += 1
        assert len(buggy_codes) == len(fix_codes)
        # buggy_codes,fix_codes,correct_ids=shuffle(buggy_codes,fix_codes,correct_ids)
        assert len(buggy_codes) == len(fix_codes)
        print(len(buggy_codes), len(fix_codes))
        #print(small_fixes)

        write_fail_indexs=[]

        with open("tmp.txt",'w',encoding='utf8')as f:
            for idx,line in enumerate(buggy_codes):
                try:
                    f.write(line+'\n')
                except:
                    write_fail_indexs.append(idx)
                    error_ids.append(correct_ids[idx])
            for idx,line in enumerate(fix_codes):
                try:
                    f.write(line+'\n')
                except:
                    write_fail_indexs.append(idx)
                    error_ids.append(correct_ids[idx])
            f.close()

        with open(src_f,'w',encoding='utf8')as f:
            for idx,line in enumerate(buggy_codes):
                if not idx  in write_fail_indexs:
                    f.write(line+'\n')
            f.close()
        with open(tgt_f,'w',encoding='utf8')as f:
            for idx,line in enumerate(fix_codes):
                if not idx  in write_fail_indexs:
                    f.write(line+'\n')
            f.close()
        with open(error_f,'w',encoding='utf8')as f:
            for idx,line in enumerate(list(set(error_ids))):
                f.write(line+'\n')
            f.close()
        with open(correct_f,'w',encoding='utf8')as f:
            for idx,line in enumerate(correct_ids):
                if not idx  in write_fail_indexs:
                    f.write(line+'\n')
            f.close()
        #writeL2F(buggy_codes, src_f)
        #writeL2F(fix_codes, tgt_f)
        #writeL2F(error_ids, error_f)
        #writeL2F(correct_ids, correct_f)
        # build(output_dir+"trn.buggy",output_dir+"trn.fix",output_dir+"trn.fids",output_dir+"trn.sids",ids)
    build(output_prefix+".buggy",output_prefix+".fix",output_prefix+".fids",output_prefix+".sids",ids)
def Preprocess_PatchEdits_fromSequenceR(ids_f,SequenceR_buggy_f,SequenceR_fix_f,output_data_f,output_ids_f):
    SequenceR_buggys=readF2L(SequenceR_buggy_f)
    SequenceR_fixes=readF2L(SequenceR_fix_f)
    ids=readF2L(ids_f)
    count=0
    def deal_control_char(s):
        temp = re.sub('[\x00-\x09|\x0b-\x0c|\x0e-\x1f]', '', s)
        return temp
    for i, code in enumerate(tqdm(SequenceR_buggys)):
        if not ("<START_BUG>" in code and "<END_BUG>" in code):
            continue
        fix_code = SequenceR_fixes[i].strip()
        code = deal_control_char(code)
        fix_code = deal_control_char(fix_code)
        while '###' in code:
            code = code.replace('###', '')
        while '###' in fix_code:
            fix_code = fix_code.replace('###', '')
        temp = code
        code = code.strip().split()
        start_index = code.index("<START_BUG>")
        code.remove("<START_BUG>")
        end_index = code.index("<END_BUG>")
        code.remove("<END_BUG>")
        dataset = 'test'
        data = f"{dataset} ### {' '.join(code)} ### {start_index} {end_index} ### <s> {fix_code} </s>\n"
        if data.count('###') != 3:
            print(data.count('###'), '###' in data, temp)
            print(data)
        with open(output_data_f, 'a', encoding='utf8') as fp:
            fp.write(data)

        with open(output_ids_f, 'a', encoding='utf8') as fp:
            fp.write(ids[i]+'\n')
            count += 1
    print(count)



if __name__ == '__main__':
    # first step test data qbs
    preprocess_SequenceR_fromRaw(
    "/content/extracted_data/Evaluation/Benchmarks/qbs.ids",
    "/content/extracted_data/Evaluation/Benchmarks",
    "/content/RawData/test/test",
    "/content/RawData/test/temp",
    BENCH="qbs_"
    )


    # second step  test data qbs 
    Preprocess_PatchEdits_fromSequenceR(
    "/content/RawData/test/test.sids",
    "/content/RawData/test/test.buggy",
    "/content/RawData/test/test.fix",
    "/content/RawData/test/test.data",
    "/content/RawData/test/test.ids"
    )


    # first step train data qbs
    preprocess_SequenceR_fromRaw(
    "/content/extracted_data/Train/trn.ids",
    "/content/extracted_data/Train",
    "/content/RawData/train/train",
    "/content/RawData/train/temp",
    BENCH=""
    )

    # second step train data qbs
    Preprocess_PatchEdits_fromSequenceR(
    "/content/RawData/train/train.sids",
    "/content/RawData/train/train.buggy",
    "/content/RawData/train/train.fix",
    "/content/RawData/train/train.data",
    "/content/RawData/train/train.ids")

    # first step valid data qbs
    preprocess_SequenceR_fromRaw(
    "/content/extracted_data/Valid/valid.ids",
    "/content/extracted_data/Valid",
    "/content/RawData/valid/valid",
    "/content/RawData/valid/temp",
    BENCH=""
    )

    # second step valid data qbs
    Preprocess_PatchEdits_fromSequenceR(
    "/content/RawData/valid/valid.sids",
    "/content/RawData/valid/valid.buggy",
    "/content/RawData/valid/valid.fix",
    "/content/RawData/valid/valid.data",
    "/content/RawData/valid/valid.ids"
    )

