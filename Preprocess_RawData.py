import codecs
import os
import re

import javalang

from CodeAbstract.CA_Recoder import generate_classcontent
from CodeAbstract.CA_SequenceR import run_SequenceR_abs
from CodeAbstract.CA_src2abs import run_src2abs
from Utils.CA_Utils import remove_comments
from Utils.IOHelper import readF2L, writeL2F


"""
ids_f: a list of bug-fix ids
input_dir: raw data dir 
output_dir: where you want to output the processed code of SequenceR
tmp_dir: when building a SequenceR-type context, you need a directory to restore temp files
"""
def preprocess_SequenceR_fromRaw(ids_f,input_dir,output_dir,tmp_dir):
    ids=readF2L(ids_f)
    def build(src_f, tgt_f, error_f, correct_f, ids):
        buggy_codes = []
        fix_codes = []
        error_ids = []
        correct_ids=[]
        ind=1
        newline_count=0
        in_count=0
        bug_1=0
        for id in ids:
            buginfo={"_id":id}
            buginfo["buggy_code"]=codecs.open(input_dir+"/buggy_methods/"+id+'.txt','r',encoding='utf8').read().strip()
            id_metas=codecs.open(input_dir+"/metas/"+id+'.txt','r',encoding='utf8').read().strip()
            buginfo["err_pos"]=int(str(id_metas.split("<sep>")[2])[1:-1].split(":")[0])
            tmp_f=tmp_dir+id+'.txt'
            fix_code=codecs.open(input_dir+'/fix_lines/'+id+'.txt').read().strip()


            buggy_code,hitflag=run_SequenceR_abs(input_dir+"/buggy_classes_java/"+id+'.txt',tmp_f,buginfo,max_length=1000)
            print("hitflag",hitflag)
            if len(buggy_code.strip())<=1:
                    hitflag=0
            if hitflag==1:
                    try:
                        toked_fix = javalang.tokenizer.tokenize(fix_code)
                        toked_fix = ' '.join([tok.value for tok in toked_fix])
                    except:
                        toked_fix = re.split(r"([.,!?;(){}])", fix_code)
                        toked_fix = ' '.join(toked_fix)
                    try:
                        toked_bug=javalang.tokenizer.tokenize(buggy_code)
                        toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >','<START_BUG>').replace('< END_BUG >','<END_BUG>')
                    except:
                        toked_bug = re.split(r"([.,!?;(){}])", buggy_code)
                        toked_bug = ' '.join(toked_bug).replace('< START_BUG >','<START_BUG>').replace('< END_BUG >','<END_BUG>')
                    bug_count=toked_bug.count('<START_BUG>'
                    )
                    if not bug_count==1:
                        bug_1+=1
                        error_ids.append(buginfo['_id'])
                    else:
                        buggy_codes.append(toked_bug)
                        fix_codes.append(toked_fix)
                        if '\n' in toked_bug:
                            newline_count+=1
                            print("newline_count",newline_count)
                        #print(toked_bug)
                        #print(toked_fix)
                        correct_ids.append(buginfo['_id'])
                        in_count+=1
            elif hitflag==0:
                #as a substitude-schema, generating method-level context

                buggy_method=readF2L(input_dir+'/buggy_methods/'+id+'.txt')
                buggy_line_id=codecs.open(input_dir+'/metas/'+id+'.txt').read().strip().split("<sep>")[2]
                buggy_line_id=int(buggy_line_id[1:-1].split(":")[0])
                buggy_method[buggy_line_id]="<START_BUG> "+buggy_method[buggy_line_id]+" <END_BUG>"
                buggy_code=' '.join(buggy_method)
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
                bug_count = toked_bug.count('<START_BUG>'
                                            )
                if not bug_count == 1:
                    bug_1 += 1
                    error_ids.append(buginfo['_id'])
                else:
                    buggy_codes.append(toked_bug)
                    fix_codes.append(toked_fix)
                    if '\n' in toked_bug:
                        newline_count += 1
                        print("newline_count", newline_count)
                    # print(toked_bug)
                    # print(toked_fix)
                    correct_ids.append(buginfo['_id'])
                    in_count += 1

            elif hitflag==2:
                    print(tmp_f)
                    error_ids.append(buginfo['_id'])
            else:
                    error_ids.append(buginfo['_id'])
            print(ind,"in:",in_count,"bug >1",bug_1)
            print("newline_count", newline_count)
            ind+=1
        assert len(buggy_codes)==len(fix_codes)
            #buggy_codes,fix_codes,correct_ids=shuffle(buggy_codes,fix_codes,correct_ids)
        assert len(buggy_codes) == len(fix_codes)
        print(len(buggy_codes),len(fix_codes))
        print("newline_count", newline_count)
        writeL2F(buggy_codes,src_f)
        writeL2F(fix_codes,tgt_f)
        writeL2F(error_ids,error_f)
        writeL2F(correct_ids, correct_f)
        #build(output_dir+"trn.buggy",output_dir+"trn.fix",output_dir+"trn.fids",output_dir+"trn.sids",ids)
    build(output_dir+".buggy",output_dir+".fix",output_dir+".fids",output_dir+".sids",ids)
#preprocess_SequenceR_fromRaw("/home/zhongwenkang/NPR4J_new_test/new_test/test.ids","/home/zhongwenkang/NPR4J_new_test/new_test",
                             #"/home/zhongwenkang/NPR4J_processed/SequenceR/test","/home/zhongwenkang/NPR4J_processed/SequenceR/temp")
"""
ids_f: a list of bug-fix ids
input_dir: raw data dir 
output_dir: where you want to output the processed code of SequenceR
tmp_dir: when building a SequenceR-type context, you need a directory to restore temp files
idiom_path: tokens that will not be abstracted , eg_path: CodeAbstract/CA_Resource/Idioms.2w
mode: when you are preparing test or valid data, using mode 'test'
"""
def preprocess_Tufano_fromRaw(ids_f,input_dir,output_dir,idom_path,temp_dir,mode,max_length=1000):
    ids=readF2L(ids_f)
    buggy_codes = []
    fix_codes = []
    success_ids = []
    fail_ids = []
    ind=0
    for id in ids:
        out_a = temp_dir + "/" + id + "_buggy.txt.abs"
        out_b = temp_dir + "/" + id + "_fix.txt.abs"
        if os.path.exists(out_a) and os.path.exists(out_b):
            print("abstraction file already exists ")
            try:
                buggy_code=codecs.open(out_a,'r',encoding='utf8').read()
                fix_code=codecs.open(out_b,'r',encoding='utf8').read()
                if buggy_code!=fix_code and 1<=len(buggy_code.split())<=max_length :
                    print('added')
                    buggy_codes.append(buggy_code)
                    fix_codes.append(fix_code)
                    success_ids.append(id)
            except:
                fail_ids.append(id)
        else:
            print("generating abstraction")
            buggy_f = input_dir + '/buggy_methods/' + id + ".txt"
            fix_f = input_dir + '/fix_methods/' + id + ".txt"

            if mode=="test":
                run_src2abs("method",buggy_f,"",out_a,"",idom_path,mode='single')
                run_src2abs("method", fix_f, "", out_b, "", idom_path, mode='single')
            else:
                run_src2abs("method",buggy_f,fix_f,out_a,out_b,idom_path)
            if os.path.exists(out_a) and os.path.exists(out_b):
                try:
                    buggy_code = codecs.open(out_a, 'r', encoding='utf8').read()
                    fix_code = codecs.open(out_b, 'r', encoding='utf8').read()
                    if buggy_code != fix_code and 1<=len(buggy_code.split()) <= max_length:
                        buggy_codes.append(buggy_code)
                        fix_codes.append(fix_code)
                        success_ids.append(id)
                except:
                    fail_ids.append(id)
        print(ind)
        ind+=1

    writeL2F(buggy_codes,output_dir+"/"+mode+".buggy")
    writeL2F(fix_codes, output_dir + "/" + mode + ".fix")
    writeL2F(success_ids, output_dir + "/" + mode + ".sids")
    writeL2F(fail_ids, output_dir + "/" + mode + ".fids")
#peprocess_Tufano_fromRaw(r"/home/zhongwenkang/ML/test/success.ids", "/home/zhongwenkang/ML/test",
#                              "/home/zhongwenkang/ML_Processed/Tufano",
#                              r"/home/zhongwenkang/ML_Processed/Tufano/idioms.txt",
#                              "/home/zhongwenkang/ML_Processed/Tufano/temp", "test")
#preprocess_Tufano_fromRaw(r"/home/zhongwenkang/ML/train/success.ids","/home/zhongwenkang/ML/train","/home/zhongwenkang/ML_Processed/Tufano",
#                          r"/home/zhongwenkang/ML_Processed/Tufano/idioms.txt","/home/zhongwenkang/ML_Processed/Tufano/temp","train")
#preprocess_Tufano_fromRaw(r"/home/zhongwenkang/ML/valid/success.ids","/home/zhongwenkang/ML/valid","/home/zhongwenkang/ML_Processed/Tufano",
#                          r"/home/zhongwenkang/ML_Processed/Tufano/idioms.txt","/home/zhongwenkang/ML_Processed/Tufano/temp","valid")

"""
ids_f: a list of bug-fix ids
input_dir: raw data dir 
output_preix: where you want to output the processed code of RewardRepair
tmp_dir: when building a SequenceR-type context, you need a directory to restore temp files
idiom_path: tokens that will not be abstracted , eg_path: CodeAbstract/CA_Resource/Idioms.2w
mode: when you are preparing test or valid data, using mode 'test'
"""
def preprocess_RewardRepair_fromRaw(ids_f,input_dir,output_prefix,tmp_dir):
    ids=readF2L(ids_f)
    bug_fix=[]
    error_ids = []
    correct_ids = []

    bug_fix.append("bugid"+'\t'+"buggy"+'\t'+"patch")
    for idx,id in enumerate(ids):
        buginfo = {"_id": id}
        buginfo["buggy_code"] = codecs.open(input_dir + "/buggy_methods/" + id + '.txt', 'r',
                                            encoding='utf8').read().strip()
        id_metas = codecs.open(input_dir + "/metas/" + id + '.txt', 'r', encoding='utf8').read().strip()
        buginfo["err_pos"] = int(str(id_metas.split("<sep>")[2])[1:-1].split(":")[0])
        tmp_f = tmp_dir + id + '.txt'
        fix_code = codecs.open(input_dir + '/fix_lines/' + id + '.txt').read().strip().replace('\t','')

        buggy_code, hitflag = run_SequenceR_abs(input_dir + "/buggy_classes/" + id + '.txt', tmp_f, buginfo,
                                                max_length=1000)

        if len(buggy_code.strip()) <= 1:
            hitflag = 0

        if hitflag == 1:
            buggy_context=buggy_code.replace("<START_BUG>","").replace("<END_BUG>","").replace('\t','')
            buggy_line=codecs.open(input_dir + '/buggy_lines/' + id + '.txt').read().strip().replace('\t','')

            buggy_src="buggy: "+buggy_line+" context: "+buggy_context
            bug_fix.append(buginfo['_id']+'\t'+buggy_src+'\t'+fix_code)
            correct_ids.append(buginfo['_id'])
            print("Total,Success: ",idx, len(correct_ids))
        elif hitflag == 0:
            buggy_method=codecs.open(input_dir + '/buggy_methods/' + id + '.txt').read().strip().replace('\t','')
            buggy_src="buggy: "+buggy_line+" context: "+buggy_method
            bug_fix.append(buginfo['_id']+'\t'+buggy_src+'\t'+fix_code)
            correct_ids.append(buginfo['_id'])
            print("Total,Success: ",idx, len(correct_ids))
        elif hitflag == 2:
            error_ids.append(buginfo['_id'])
        else:
            error_ids.append(buginfo['_id'])
        assert len(correct_ids)==len(correct_ids)
        writeL2F(bug_fix,output_prefix+'.bug-fix.csv')
        writeL2F(error_ids,output_prefix+'.fids')
        writeL2F(correct_ids, output_prefix+'.ids')
#preprocess_RewardRepair_fromRaw("/home/zhongwenkang/RawData/Train/trn.ids","/home/zhongwenkang/RawData/Train",
                                #"/home/zhongwenkang/NPR4J_Data/RewardRepair/trn","/home/zhongwenkang/NPR4J_Data/SequenceR/temp_files/")

def preprocess_CodeBertFT_fromRaw(ids_f,input_dir,output_prefix):
    ids=readF2L(ids_f)
    buggy_lines=[]
    fix_lines=[]
    for idx,id in enumerate(ids):
        buggy_line=codecs.open(input_dir+'/buggy_lines/'+id+'.txt','r',encoding='utf8').read().strip()
        fix_line=codecs.open(input_dir+'/fix_lines/'+id+'.txt','r',encoding='utf8').read().strip()
        buggy_lines.append(buggy_line)
        fix_lines.append(fix_line)
    writeL2F(buggy_lines,output_prefix+'.buggy')
    writeL2F(fix_lines,output_prefix+'.fix')
def preprocess_CodeBertFT_fromRaw_methodLevel(ids_f,input_dir,output_prefix):
    ids=readF2L(ids_f)
    print(len(ids))
    buggy_methods=[]
    fix_methods=[]
    for idx,id in enumerate(ids):
        buggy_method=codecs.open(input_dir+'/buggy_methods/'+id+'.txt','r',encoding='utf8').read().strip()
        buggy_method=remove_comments(buggy_method)
        buggy_method=buggy_method.replace('\r\n','').replace('\n','').replace('\t','')
        fix_line=codecs.open(input_dir+'/fix_methods/'+id+'.txt','r',encoding='utf8').read().strip()
        fix_line=remove_comments(fix_line)
        fix_line=fix_line.replace('\r\n','').replace('\n','').replace('\t','')
        buggy_methods.append(buggy_method)
        fix_methods.append(fix_line)
        print(idx)
    writeL2F(buggy_methods,output_prefix+'.buggy')
    writeL2F(fix_methods,output_prefix+'.fix')
#preprocess_CodeBertFT_fromRaw("/home/zhongwenkang/RawData/Valid/valid.ids","/home/zhongwenkang/RawData/Valid",
#                              "/home/zhongwenkang/NPR4J_Data/CodeBertFT/val")
#preprocess_CodeBertFT_fromRaw_methodLevel("/home/zhongwenkang/ML/train/success.ids","/home/zhongwenkang/ML/train",
#                              "/home/zhongwenkang/ML_Processed/CodeBERT/train")
#preprocess_CodeBertFT_fromRaw_methodLevel("/home/zhongwenkang/ML/valid/success.ids","/home/zhongwenkang/ML/valid",
#                              "/home/zhongwenkang/ML_Processed/CodeBERT/valid")

def preprocess_Recoder_fromRaw(mode,ids_f,input_dir,output_dir):
    ids=readF2L(ids_f)
    if mode=="test":
        fail_ids=[]

        for idx,id in enumerate(ids):
            if not os.path.exists(os.path.join(output_dir,id+'.json')):
                print(idx)
                try:
                    meta_info=codecs.open(os.path.join(input_dir,"metas",id+".txt")).read().strip()
                    filename=meta_info.split("<sep>")[-1].split('@')[0].split("\\")[-1]
                    generate_classcontent(os.path.join(input_dir,"buggy_classes",id+".txt"),os.path.join(output_dir,id+'.json')
                                          ,filename)
                except:
                    fail_ids.append(id)
        print(len(fail_ids))
        writeL2F(fail_ids,output_dir+'/fail.ids')


preprocess_Recoder_fromRaw("test","/home/zhongwenkang/NPR4J_new_test/new_test/test.ids","/home/zhongwenkang/NPR4J_new_test/new_test",
                           "/home/zhongwenkang/NPR4J_processed/Recoder")