#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')
import os, sys, time, numpy as np, matplotlib.pyplot as plt 

# validate input
usage = 'Usage: %s path to QUAST report.txt file' % sys.argv[0]
global stat, title, header, plotPrefix, colorSet


class switch(object):
    	value = None
    	def __new__(class_, value):
        	class_.value = value
        	return True

def case(arg):	
	if (switch.value.find(arg) != -1): return True
    	return False

def makeStaticPlot(input, y_label, plotTitle, nr):
	fig = plt.figure()
        x = []
        y = []
        for i in range(len(header)-1,0,-1):
                x.append(header[i])
	if ('GC%' in y_label) | ('N per' in y_label):
	        for i in range(len(input)-1,(len(input)-len(header)),-1):
        	        y.append(float(input[i]))
	else:
		for i in range(len(input)-1,(len(input)-len(header)),-1):
                        y.append(int(input[i]))

        x_pos = np.arange(len(x))
	ax = plt.subplot(311)
        for i in range(0,len(x)):
                #plt.bar(x_pos[i], y[i], color=colorSet[i], align='center')
        	#plt.text(x_pos[i], y[i]/2., str(y[i]), rotation=90., ha="center", va="center", bbox=dict(boxstyle="square",color=colorSet[i], alpha=0.5))
		ax.bar(x_pos[i], y[i], align='center', color=colorSet[i], label=str(y[i]))
	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width * 0.5, box.height])
	plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	plt.xticks(x_pos, x, rotation=80)
        plt.ylabel(y_label)
        plt.title(plotTitle)
       	#fig.tight_layout()
        plt.savefig(os.getcwd().split("galaxy-dist")[0]+"galaxy-dist/"+plotPrefix+str(nr)+'.jpeg')
	nr += 1
	plt.close()

def createTable(stat):
	tblHeader = True
	table = ['<TABLE BORDER="0">']
	first = True
	plotnr = 0;
	for line in stat:
		table.append('<TR>')
		elements = line.split()
		if not tblHeader:
			plotnr += 1
			info = "<TD><A HREF=\"javascript:toggleImg(\'plot"+str(plotnr)+"\');\"></TD>"
			for i in range(0,len(elements)-len(header)+1):
				info = info[0:-5]+elements[i]+" </TD>"
			table.append(info[0:-5]+'</A></TD>\n')
			
			for i in range(len(elements)-1,(len(elements)-len(header)),-1):
                        	table.append('<TD>'+elements[i]+'</TD>')
		else:
			tblHeader = False
			table.append('<TD>'+elements[0]+'</TD>')
			for i in range(len(elements)-1,0,-1):
				table.append('<TD>'+elements[i]+'</TD>')

		table.append('</TR>\n')
	table.append('</TABLE>')
	return ''.join(table)  

def createStyleSheet():
	css = open('plot_stylesheet.css', 'w')

	#Hide all pictures
	hideall = "#plot1 {\n \
	    display:none;}\n"

	#Default body style
	bodyStyle = "body {\n \
	    background-color=grey;}\n"

	#Write to css-file
	write(bodyStyle)
	write(hideall)

	css.close()

def getScript():
	script = "function toggleImg(id){ \n \
		var img = document.getElementById(id);\n \
	        img.style.display = (img.style.display=='none' ? 'block' : 'none');}"
	return script

def createHtml(nr, table):
	html = open('plot.html', 'w')
	content = "<!DOCTYPE html>\n<HTML><HEAD>\n \
		<SCRIPT type=\"text/javascript\">"+getScript()+"</SCRIPT> \
	    	<H3>"+title+"</H3></HEAD>\n<BODY>"
	content +="<P>"+table+"</BR>"
	
	for i in range(1,nr):
    		content += "<img style=\"display:none;\" id=\"plot"+str(i)+"\" src=\""
		content += plotPrefix+str(i)+".jpeg\" alt=\"Plot "+str(i)+"\"/>\n"
	content += "</BODY></HTML>"
	html.write(content)
	#print content
	html.close()

def getPrefix():
	#make a new folder 
	datetime = time.strftime("%d%m%Y-%H%M%S")
	os.mkdir(os.getcwd().split("galaxy-dist")[0]+"galaxy-dist/static/plots/"+datetime)
	prefix = "/static/plots/"+datetime+"/plot"
	return prefix

def getColorSet():
	color = ['red', 'blue', 'green', 'yellow', 'pink', 'purple', 'grey', 'orange', 'indigo', 'fuchshia']
	return color

if __name__ == '__main__':
	try:
		filename = sys.argv[1]
	except:
		print usage; sys.exit(1)

	# open stat-file from QUAST
	try:

		f = open(filename, 'r')
		#grab the headers
		title = f.readline();f.readline()
		stat = []; stat.append(f.readline())
		header = stat[0].split()
		plotPrefix = getPrefix()
		colorSet = getColorSet()
		nr = 1
		for word in f.readlines():#[3:max(enumerate(open(filename)))[0]+1]:
			stat.append(word)
			wordArray = word.split()
			while switch(word):
				if case('# contigs (>= 0 bp)'):
					makeStaticPlot(wordArray, 'Contigs (>= 0 bp)', 'Contigs larger than 0bp', nr)
					nr += 1
					break
				if case('# contigs (>= 1000 bp)'):
                                       	makeStaticPlot(wordArray, 'Contigs (>= 1000 bp)', 'Contigs larger than 1000bp', nr)
                                        nr += 1 
                                        break
				if case('Total length (>= 0 bp)'):
                                       	makeStaticPlot(wordArray, 'Total length (>= 0 bp)', 'Total length larger than 0bp', nr)
                                        nr += 1
                                        break
				if case('Total length (>= 1000 bp)'):
                                        makeStaticPlot(wordArray, 'Total length (>= 1000 bp)', 'Total length larger than 1000bp', nr)
                                        nr += 1
					break
				if case('# contigs'):
					makeStaticPlot(wordArray, 'Number of contigs', 'Total number of contigs', nr)
                                        nr += 1
                                        break
				if case('Total length'):
					makeStaticPlot(wordArray, 'Total length', 'Total length', nr)
                                        nr += 1
                                        break
				if case('Largest contig'):
                                        makeStaticPlot(wordArray, 'Largest contig', 'Largest contig', nr)
                                        nr += 1
                                        break
				if case('GC (%)'):
                                        makeStaticPlot(wordArray, 'GC%', 'GC %', nr)
                                        nr += 1
                                        break
				if case('N50'):
                                        makeStaticPlot(wordArray, 'N50', 'N50', nr)
                                        nr += 1
                                        break
				if case('N75'):
                                        makeStaticPlot(wordArray, 'N75', 'N75', nr)
                                        nr += 1
                                        break
				if case('L50'):
					makeStaticPlot(wordArray, 'L50', 'L50', nr)
                                        nr += 1
                                        break
				if case('L75'):
                                        makeStaticPlot(wordArray, 'L75', 'L75', nr)
                                        nr += 1
                                        break
				if case('# N\'s per 100 kbp'):
                                        makeStaticPlot(wordArray, 'N per 100kbp', 'Number of N\'s per 100 kbp', nr)
                                        nr += 1
                                        break
				break
		f.close()
		createHtml(nr, createTable(stat))
	except:
		print "Unexpected error:", sys.exc_info()[0]
		raise