import os
import re


def findAllFile(x):
    base=os.getcwd()
    for root, dirs, files in os.walk(base):
        for f in files:
            #if f.startswith(x):
            if f.endswith(x):
                fullname=os.path.join(root, f)
                yield fullname


def rewrite(step_list,filein,fileout):
    countdown=0
    for count, line in enumerate(filein.readlines(), start=1):
        if count==1:
            global num_atom
            num_atom=float(line)
        elif "i =" in line:
            num_step_read=str.split(line)[2].replace(',','') #”i =   18，“like, after spliting remove ","
            if num_step_read in step_list:
                countdown+=num_atom+2
        if countdown!=0:#because the last line is a blank line
            countdown-=1
        elif countdown==0:
            fileout.write(line)
    fileout.close()


def rewrite_all(dirname):
    #current directory
    filerefer='exclude_step_num.txt'
    if os.path.exists(filerefer)==True:
        #exclude process
        fin0=open(filerefer,'r')
        step_list=str.split(fin0.readline())
        fin0.seek(0)
    else:
        manual_input=input("input excluding step number, sep with ','")
        step_list=re.split('[, ]',manual_input)
    for path in findAllFile('xyz'):
        fin=os.path.basename(path)
        if os.path.dirname(path)==dirname:
            if 'new' in fin:#prevent self-circulation
                continue
            if 'pos' in fin:
                global fin1,fout1
                fin1=open(fin,'r')
                fout1=open('new'+fin,'w')
                rewrite(step_list,fin1,fout1)
                print("pos outfile=",'new'+fin)
            elif 'frc' in fin:
                global fin2,fout2
                fin2=open(fin,'r')
                fout2=open('new'+fin,'w')
                rewrite(step_list,fin2,fout2)
                print("frc outfile=",'new'+fin)
    print("atom number=",int(num_atom))


def collect():
    exc_dir=input("do you want to exclude some directories (dirname sep with ','/n)")
    if exc_dir=='n':
        pass
    else:
        exc_dir_list=re.split('[, ]',exc_dir)

    err_kw="SCF run NOT converged"
    pro_kw="PROGRAM PROCESS ID"
    step_kw="STEP NUMBER"

    distinguish=input("do you want to specify your keyword (y/n)"+'\n'+"if not, keyword will be set to 'SCF run NOT converged'")
    if distinguish=='y':
        err_kw=input('input your keyword:')

    for ii in findAllFile('out'):
        dirname=os.path.dirname(ii)
        if os.path.split(dirname)[-1] in exc_dir_list:
            continue
        os.chdir(dirname)
        num_pro_kw=[]
        num_err_kw=[]
        num_step_kw=[[] for i in range(2)]
        fin=open(ii,'r')
        for count, line in enumerate(fin.readlines(), start=1):
            if pro_kw in line:
                num_pro_kw.append(count)
        fin.seek(0)
        if len(num_pro_kw)==0:
            continue
        print("------Right file for input:", ii)
        print(' program number=',len(num_pro_kw))
        tick=0
        for count, line in enumerate(fin.readlines(), start=1):
            if count>=num_pro_kw[-1]:#only last program
                if err_kw in line:
                    tick=1#use tick to check next one "STEP" line
                    num_err_kw.append(count)
                elif step_kw in line and tick==1:
                    num_step_kw[0].append(count)
                    steplabel=str.split(line)[3]
                    num_step_kw[1].append(steplabel)
                    tick=0
        if len(num_err_kw)==len(num_step_kw[0])+1:#because ".out" doesn't have a "STEP NUMBER=0"
            num_step_kw[1].insert(0,'0')
        print(' step number=',len(num_step_kw[0]))
        print(' step label=',num_step_kw[1])

        fout=open('exclude_step_num.txt','w')
        outline=' '.join(num_step_kw[1])
        fout.write(outline)
        fout.close()
        rewrite_all(dirname)
    print('------finished')


collect()
