#!/usr/bin/env python
import json

def assessOutput(quastfile):	
	#Assemblies
	assembly = {}

	with open(quastfile) as data_file:
		data = json.load(data_file)
		report = data['report']

	ddl = []
	for line in report:
		title = line[0]
		for field in line[1]:
			ddl.append(field['metricName']) 
	result = '\n'+createddl(ddl)
	return result

def createddl(option):
	ddl1 = '<select id="ddl1">\n'
	ddl2 = '<select id="ddl2">\n'
	ddl3 = '<select id="ddl3">\n'
        ddlAll = '  <option value="">--- Select ---</option>\n'
	for opt in option:
		ddlAll += '  <option value="'+opt+'">'+opt+'</option>\n'
	ddlAll += '</select>\n'
	ddl1 += ddlAll
	ddl2 += ddlAll
	ddl3 += ddlAll
	ddl1 += '<button name="btn1" type="button" onClick="javascript:drawColumnChart();">Create bar chart</button><br>\n'
	ddl3 += '<button name="btn2" type="button" onClick="javascript:drawScatterPlot();">Create scatter plot</button><br>\n'
	return ddl1 + ddl2 + ddl3 + '<!--Div that will hold the chart-->\n \
	<a id="hideplot" href="javascript:toggleImg()" style="display:none"><b>Hide plot</b></a>\n \
	<div id="chart_div" style="display:none"></div>\n'

def getScript():
	return '<script type="text/javascript" src="https://www.google.com/jsapi"></script>\n \
	<script type="text/javascript">google.load(\'visualization\', \'1.0\', {\'packages\':[\'corechart\']});</script>\n \
	<script type="text/javascript" src="report_html_aux/scripts/draw_custom_plot.js"></script>\n'