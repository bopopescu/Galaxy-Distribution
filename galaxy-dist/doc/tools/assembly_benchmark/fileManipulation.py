
#!/usr/bin/python
import os

def seperateRefereceFile(ref):
    return 'empty file'

def mergeGeneFiles(genelist):
    result = open('result.gff', 'w')
    first = True
    for genefile in genelist:
        print genefile
        if first:
            #result.write(open(genefile).readlines())
            first = False
        else:
            result.write(open(genefile).readlines()[3:])
    result.close()
    
    return os.path.abspath(result)