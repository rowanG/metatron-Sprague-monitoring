from __future__ import division
import ConfigParser
import datetime
import time
import json
import redis
import math
import db
import pyodbc
import _mssql
from prettytable import PrettyTable
import cgi
import requests
import os, sys
import operator
from collections import OrderedDict
from flask import Flask,render_template,request,Response
import werkzeug.exceptions

Config = ConfigParser.ConfigParser()
Config.read('settings.ini')
user = Config.get('DatabaseConnection', 'user')
dsn = Config.get('DatabaseConnection', 'dsn')
password = Config.get('DatabaseConnection', 'password')
database = Config.get('DatabaseConnection', 'database')


class NotModified(werkzeug.exceptions.HTTPException):
    code = 304
    def get_response(self, environment):
        return Response('304 notmodified',status=304)

class NotFound(werkzeug.exceptions.HTTPException):
    code = 404
    def get_response(self, environment):
        return Response('404 not found',status=404)

def read_in_chunks(fp, chunk_size=1024):
    while True:
        data = fp.read(chunk_size)
        if not data:
            break
        yield data
    fp.close()


app=Flask(__name__)
@app.route('/', methods=['GET'])
def index():
    header = 'Index'
    urls = [
        {'url':'/files',                'name':'Generic Files'},
        {'url':'/dashboards',           'name':'Dashboards'},
    ]

    return render_template('index.html',urls=urls, header=header)


@app.route('/dashboards', methods=['GET'])
def dashboards():
    header = 'Dashboards'
    urls = [
        {'url':'/dashboard/EQL',         'name':'Equallogic Test Monitoring'},
        {'url':'/dashboard/PCB',         'name':'Components PCB'},
	{'url':'/dashboard/HEAD',	 'name':'Components HEAD'},
	{'url':'/dashboard/LOGISTICS',	 'name':'Logistics'}
    ]


    return render_template('index.html',urls=urls,header=header)


@app.route('/dashboard/LOGISTICS', methods=['GET'])
def dashboard_LOGISTICS():
    app.jinja_env.autoescape = False

    # start of tiles, atomic tile height, width and offsets between tiles
    # Note: these are percentages of the total width and height of the html body
    start_x = 3.5
    start_y = 10
    tile_width = 7.28
    tile_height = 13
    tile_offset_x = 1.54
    tile_offset_y = 1.5
    sync_x = 0
    sync_y = 0
    sync_offset_x = 0.0
    sync_offset_y = 0.0
    

    # return relative position in percentage from the internal tile positon
    def gety(y):
        return (start_y + y * tile_offset_y + y * tile_height)

    def getx(x):
        return (start_x + x * tile_offset_x + x * tile_width)

    def runCycle(result):
        for x in result:
            return str(x[0])

    def woOpenDef(result):
        return str(x[0][0])

    def openComponents(result):
	final = len(result)
	return final

    def shippedToday(result):
	return result[0][0]

    def dueTime(result):
	return result[0][1]

    def onHold(result):
        """
        Creates a table of the top 5 on hold workorders.
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Part', 'Qty'])
        t = 0
        currentPos = 0
        typeDict = {}
        resultEmpty = 0
        final = []
	#tempSplitList = []
        for x in result:
            tempSplitList = []
            noHead = False
            varTitle = x[0].split()
	    if 'HEAD' in varTitle:
	        pass
	    else:
		resultEmpty += 1
		part = str(x[0])
		amount = str(x[1])
		print part, amount
		table.add_row([part,amount])
        #, "bgcolor":"#FF7449"
    	if resultEmpty == 0:
       	    happyString = "0"
            tableShow = ""
        else:
            happyString = ""
            tableShow = table.get_html_string(attributes={"text-align":"left", "size":"100%", "class":"Onhold"})
        final.append(happyString)
        final.append(tableShow)
        return final



    def threeColumn(result):
        """
        Create a table with three columns
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Description', 'Shortage'], border=True)
        t = 0
        table.border == True
        for x in result:
            if t <= 2:
                table.add_row([x[1], x[7]])
                t += 1
            else:
                break
        #, "bgcolor":"#08D00C"
        return table.get_html_string(attributes={"table align":"left", "col width":"130", "td width":"100%", "size":"50px", "class":"InvShortage", "cellpadding":"5", "align":"center"})

    def DOA(result):
        """
        Create a table for the DOA's (not including HEAD)
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border=True)
        for x in result:
            if x[0] == 'HEAD':
                pass
            else:
                table.add_row([x[0], x[1], x[2]])
        print table.get_html_string(attributes={"size":"50px", "class":"DOA", "background-color":"green"})
        #"bgcolor":"#61ABFF"
        return table.get_html_string(attributes={"size":"10px", "class":"DOA", "cellpadding":"5"})

    def openQuotes(result):
	if len(result) != 0:
	    finalList = []
	    counter = 4
	    while counter >= 0:
	    	for x in result:
		    if counter >= 0:
	    	    	a = 'Q' + str(x[1])
 	    	    	finalList.append(a)
		    	counter -= 1
		    else:
		    	break
	
	    table = PrettyTable(['Quote Number:'], border= True)
	    for x in finalList:
	        table.add_row([x])
	    finale1 = table.get_html_string(attributes={"size":"10px", "class":"OpenQuotes", "border":"0"})
	    finale = ''
	else:
	    finale = '0'
	    finale1 = ''

	total = []
	total.append(finale1)
	total.append(finale)
	return total    


    def doaHead(result):
        """
        Create a table for HEAD DOA's
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border= True)
        for x in result:
            table.add_row([x[0], x[1], x[2]])
        return table.get_html_string(attributes={"size":"10px", "class":"DOAHead", "border":"1"})

    def repairedTodayNum(result):
        """
        Create one large number to be displayed as a count
        for the amount of S-numbers repaired today
        """
        return result[0][0]

    def woOverdueDisp(result):
        return result

    def openWO(result):
        return result[0][0]
        
    def runQuery(query):
        """
        Run a query from the database
        Parameter:
        query - Query to be ran
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        try:
            qr = c.execute(query)
            qry = c.fetchall()
        except Exception, e:
            qry = e
        return qry

    def funPic():
        pass

    def onFloor(result):
	a = []
	componentUsers = ['tom', 'marian', 'frans', 'beer', 'JiriM', 'johan', 'eric', 'manuela']
	final = 0
	for i in result:
	    a.append(str(i[0]))
	for x in a:
	    if x in componentUsers:
	        final += 1
	return final

    def SAvailability(result):
        shipped = result[0][0]
        onhold = result[0][1]

        percentWO = 100 / int(shipped)
        percentOnHold = percentWO * int(onhold)
        total = str(int(math.floor(100 - percentOnHold)))
    
        return total

    def connect(storedProcedure):
        """
        Run a stored procedure from the database
        Parameter:
        storedProcedure - name of Stored Procedure within the database
        Please keep an eye on the driver (SQL Server Native Client 11.0)
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        proc = str(storedProcedure)
        try:
            fuz = c.execute("exec %s" % proc)
            fuzzy = c.fetchall()
        except Exception, e:
            fuzzy = e
        return fuzzy

    # It's so hot, please, someone shoot me
    currentTime = datetime.datetime.now().strftime("%H:%M")
    if str(currentTime) == '17:00':
        funPic()
        print "It's five!"
    else:
        pass

    def repaired2Day(storedProcedure):
	return storedProcedure[0][0]

    def weekCalc():
        currentWeek = (datetime.date.today().isocalendar()[1])
        print "Week: %s " % currentWeek

        return currentWeek
    
    # Create a list of procedures to be carried out, these can be called upon .
    sAvail = "exec sp_com_part_availability @week='%s'" % weekCalc()
    woOverdue = "SELECT rp.received_wo 'WO in' FROM tbl_rmaproducts_generic AS rp, tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus WHERE rp.swapgroup_id NOT IN (5,8,13,12,17,18) AND rma.klant_id not in (178,179,213,306) AND rp.received_wo IS NOT NULL and part.category IN ('DRIVE', 'LOADER', 'LIBRARY') AND rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND part.category IN ('PCB', 'PSU', 'DECK') AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id NOT IN (447) AND dbo.GetWorkingDays(rma.receivedate,CONVERT(DATE, GETDATE())) <= 6"
    woOpen = "SELECT count(*) FROM tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus, tbl_rmaproducts_generic AS rp LEFT JOIN tbl_workorders w ON w.id = rp.received_wo LEFT JOIN tbl_loc_latest ll ON ll.workorder_id = w.id LEFT JOIN tbl_locations l ON l.id = ll.location_id WHERE rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id <> 306"
    repairedToday = "SELECT COUNT(*) AS 'Work orders closed today' FROM tbl_workorders AS wo WHERE CONVERT(DATE, wo.repairdate) = CONVERT(DATE, GETDATE())"
    sRepairedToday = "SELECT COUNT(*) FROM tbl_component_location AS cl JOIN tbl_component AS co ON cl.component_id = co.id WHERE CONVERT(DATE, cl.entrancetime) = CONVERT(DATE, GETDATE()) AND co.[status] = 'GOOD' AND cl.location_id = 26"
    procedure = [shippedToday(connect('sp_tiles_logistics_shippedToday')), shippedToday(connect('sp_tiles_logistics_ready_for_shipment')), dueTime(connect('sp_tiles_logistics_due_time')), openQuotes(connect('sp_tiles_logistics_open_quotes')), doaHead(connect('sp_tiles_components_doa_past7days')), onFloor(connect('sp_tiles_components_closed5')), openComponents(connect('sp_tiles_components_wo_open')), repaired2Day(connect('sp_tiles_components_repaired_today_all')), SAvailability(runQuery(sAvail))]

    #   size of screen (11x6):
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 

    # different tile sizes, new ones can be specified
    tile_sizes = {
        # * *
        # * *
        'small_square': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(2 * tile_width + tile_offset_x)
        },

        'sync_idea': {
            'height': str(7),
            'width': str(27)
        },

        'header': {
            'height': str(7),
            'width': str(60) 
        },

        'half_rect':{
            'height': str(3 * tile_height + 7 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },

        'tiny_rect':{
            'height': str(2 * tile_height + 5 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },
        
        
        # * * * *
        # * * * *
        # * * * *
        # * * * *
        'big_square': {
            'height': str(4 * tile_height + 3 * tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * * *
        # * * * *
        'wide_rect': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        'double_long_rect': {
            'height': str(6 * tile_height + 5 * tile_offset_y),
            'width': str(3 * tile_width + 2 * tile_offset_x)
        },
    }

    # tile types:
    #         green_tile
    #           red_tile
    #          blue_tile
    #        yellow_tile
    #        purple_tile


    # first tile holds discription for all variables needed
    tiles = [

        {
            'class': 'tile_2',
            'type': 'yellow_tile',
            'posx': str(getx(0)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6">Open Quotes</font>',
            'content1': [
                '<span style="font-size:15em;vertical-align:center;">%s</span>' % procedure[3][1],
                '%s' % procedure[3][0],
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'sync',
            'type': 'blue_tile',
            'posx': str(4),
            'posy': str(1),
            'height': tile_sizes['sync_idea']['height'],
            'width': tile_sizes['sync_idea']['width'],
            'head': 'Components - Last refresh: %s' % currentTime,
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'header',
            'type': 'black_tile',
            'posx': str(39),
            'posy': str(1),
            'height': tile_sizes['header']['height'],
            'width': tile_sizes['header']['width'],
            'head': '<font size = "6" color="red">SCARAMANGA</font>',
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'tile_6',
            'type': 'red_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">S# On Floor > 5d</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">%s</span>' % procedure[5],
                ''
            ],
            'content2': [],
            'contentTable': [],

        },
        

        {
            'class': 'tile_7',
            'type': 'yellow_tile',
            'posx': str(getx(6)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">Avg days due</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">%s</span>' % procedure[2],
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_104',
            'type': 'purple_tile',
            'posx': str(getx(2)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">Shipped Today</font>',
            'content1': [
                '',
                '<span style="font-size:6em;vertical-align:center;">%s</span>' % procedure[0],
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_103',
            'type': 'green_tile',
            'posx': str(getx(0)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">Ready for Shipment</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">%s</span>' % procedure[1],
                ''
            ],
            'content2': []
        },


        {
            'class': 'tile_8',
            'type': 'green_tile',
            'posx': str(getx(8)),
            'posy': str(gety(0)),
            'height': tile_sizes['half_rect']['height'],
            'width': tile_sizes['half_rect']['width'],
            'head': '<font size="5"></font>',
            'content1': [
                '<h2></h2>',
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

        {
            'class': 'tile_110',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6"></font>',
            'content1': [
                '<h2></h2>',
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },
        {
            'class': 'tile_100',
            'type': 'purple_tile',
            'posx': str(getx(8)),
            'posy': str(62),
            'height': tile_sizes['tiny_rect']['height'],
            'width': tile_sizes['tiny_rect']['width'],
            'head': '<font size="6"></font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;"></span>',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

        
    ]


    return render_template('dashboards/LOGISTICS.html', tiles=tiles)


@app.route('/dashboard/PCB', methods=['GET'])
def dashboard_PCB():
    app.jinja_env.autoescape = False

    # start of tiles, atomic tile height, width and offsets between tiles
    # Note: these are percentages of the total width and height of the html body
    start_x = 3.5
    start_y = 10
    tile_width = 7.28
    tile_height = 13
    tile_offset_x = 1.54
    tile_offset_y = 1.5
    sync_x = 0
    sync_y = 0
    sync_offset_x = 0.0
    sync_offset_y = 0.0
    

    # return relative position in percentage from the internal tile positon
    def gety(y):
        return (start_y + y * tile_offset_y + y * tile_height)

    def getx(x):
        return (start_x + x * tile_offset_x + x * tile_width)

    def runCycle(result):
        for x in result:
            return str(x[0])

    def woOpenDef(result):
        return str(x[0][0])

    def openComponents(result):
	final = len(result)
	return final

    def onHold(result):
        """
        Creates a table of the top 5 on hold workorders.
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Part', 'Qty'])
        t = 0
        currentPos = 0
        typeDict = {}
        resultEmpty = 0
        final = []
	#tempSplitList = []
        for x in result:
            tempSplitList = []
            noHead = False
            varTitle = x[0].split()
	    if 'HEAD' in varTitle:
	        pass
	    else:
		resultEmpty += 1
		part = str(x[0])
		amount = str(x[1])
		print part, amount
		table.add_row([part,amount])
        #, "bgcolor":"#FF7449"
    	if resultEmpty == 0:
       	    happyString = "0"
            tableShow = ""
        else:
            happyString = ""
            tableShow = table.get_html_string(attributes={"text-align":"left", "size":"100%", "class":"Onhold"})
        final.append(happyString)
        final.append(tableShow)
        return final



    def threeColumn(result):
        """
        Create a table with three columns
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Description', 'Shortage'], border=True)
        t = 0
        table.border == True
        for x in result:
            if t <= 2:
                table.add_row([x[1], x[7]])
                t += 1
            else:
                break
        #, "bgcolor":"#08D00C"
        return table.get_html_string(attributes={"table align":"left", "col width":"130", "td width":"100%", "size":"50px", "class":"InvShortage", "cellpadding":"5", "align":"center"})

    def DOA(result):
        """
        Create a table for the DOA's (not including HEAD)
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border=True)
        for x in result:
            if x[0] == 'HEAD':
                pass
            else:
                table.add_row([x[0], x[1], x[2]])
        print table.get_html_string(attributes={"size":"50px", "class":"DOA", "background-color":"green"})
        #"bgcolor":"#61ABFF"
        return table.get_html_string(attributes={"size":"10px", "class":"DOA", "cellpadding":"5"})

    def doaHead(result):
        """
        Create a table for HEAD DOA's
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border= True)
        for x in result:
            table.add_row([x[0], x[1], x[2]])
        return table.get_html_string(attributes={"size":"10px", "class":"DOAHead", "border":"1"})

    def repairedTodayNum(result):
        """
        Create one large number to be displayed as a count
        for the amount of S-numbers repaired today
        """
        return result[0][0]

    def woOverdueDisp(result):
        return result

    def openWO(result):
        return result[0][0]
        

    def runQuery(query):
        """
        Run a query from the database
        Parameter:
        query - Query to be ran
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        try:
            qr = c.execute(query)
            qry = c.fetchall()
        except Exception, e:
            qry = e
        return qry

    def funPic():
        pass

    def onFloor(result):
	a = []
	componentUsers = ['mirsad', 'mohamed', 'omid', 'pawel', 'caroline', 'hayder', 'shahram', 'ineke', 'shahram']
	final = 0
	for i in result:
	    a.append(str(i[0]))
	for x in a:
	    if x in componentUsers:
	        final += 1
	return final

    def SAvailability(result):
        shipped = result[0][0]
        onhold = result[0][1]

        percentWO = 100 / int(shipped)
        percentOnHold = percentWO * int(onhold)
        total = str(int(math.floor(100 - percentOnHold)))
    
        return total

    def connect(storedProcedure):
        """
        Run a stored procedure from the database
        Parameter:
        storedProcedure - name of Stored Procedure within the database
        Please keep an eye on the driver (SQL Server Native Client 11.0)
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        proc = str(storedProcedure)
        try:
            fuz = c.execute("exec %s" % proc)
            fuzzy = c.fetchall()
        except Exception, e:
            fuzzy = e
        return fuzzy

    currentTime = datetime.datetime.now().strftime("%H:%M")
    if str(currentTime) == '17:00':
        funPic()
        print "It's five!"
    else:
        pass

    def repaired2Day(storedProcedure):
	return storedProcedure[0][0]

    def weekCalc():
        currentWeek = (datetime.date.today().isocalendar()[1])
        print "Week: %s " % currentWeek

        return currentWeek
    
    # Create a list of procedures to be carried out, these can be called upon .
    sAvail = "exec sp_com_part_availability @week='%s'" % weekCalc()
    woOverdue = "SELECT rp.received_wo 'WO in' FROM tbl_rmaproducts_generic AS rp, tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus WHERE rp.swapgroup_id NOT IN (5,8,13,12,17,18) AND rma.klant_id not in (178,179,213,306) AND rp.received_wo IS NOT NULL and part.category IN ('DRIVE', 'LOADER', 'LIBRARY') AND rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND part.category IN ('PCB', 'PSU', 'DECK') AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id NOT IN (447) AND dbo.GetWorkingDays(rma.receivedate,CONVERT(DATE, GETDATE())) <= 6"
    woOpen = "SELECT count(*) FROM tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus, tbl_rmaproducts_generic AS rp LEFT JOIN tbl_workorders w ON w.id = rp.received_wo LEFT JOIN tbl_loc_latest ll ON ll.workorder_id = w.id LEFT JOIN tbl_locations l ON l.id = ll.location_id WHERE rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id <> 306"
    repairedToday = "SELECT COUNT(*) AS 'Work orders closed today' FROM tbl_workorders AS wo WHERE CONVERT(DATE, wo.repairdate) = CONVERT(DATE, GETDATE())"
    sRepairedToday = "SELECT COUNT(*) FROM tbl_component_location AS cl JOIN tbl_component AS co ON cl.component_id = co.id WHERE CONVERT(DATE, cl.entrancetime) = CONVERT(DATE, GETDATE()) AND co.[status] = 'GOOD' AND cl.location_id = 26"
    procedure = [woOverdueDisp(runQuery(woOverdue)), onHold(connect('sp_tiles_report_onhold')), threeColumn(connect('sp_tiles_components_inventory_shortage')), DOA(connect('sp_tiles_components_doa_past7days')), doaHead(connect('sp_tiles_components_doa_past7days')), onFloor(connect('sp_tiles_components_closed5')), openComponents(connect('sp_tiles_components_wo_open')), repaired2Day(connect('sp_tiles_components_repaired_today_all')), SAvailability(runQuery(sAvail))]

    #   size of screen (11x6):
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 

    # different tile sizes, new ones can be specified
    tile_sizes = {
        # * *
        # * *
        'small_square': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(2 * tile_width + tile_offset_x)
        },

        'sync_idea': {
            'height': str(7),
            'width': str(27)
        },

        'header': {
            'height': str(7),
            'width': str(60) 
        },

        'half_rect':{
            'height': str(3 * tile_height + 7 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },

        'tiny_rect':{
            'height': str(2 * tile_height + 5 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },
        
        
        # * * * *
        # * * * *
        # * * * *
        # * * * *
        'big_square': {
            'height': str(4 * tile_height + 3 * tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * * *
        # * * * *
        'wide_rect': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        'double_long_rect': {
            'height': str(6 * tile_height + 5 * tile_offset_y),
            'width': str(3 * tile_width + 2 * tile_offset_x)
        },
    }

    # tile types:
    #         green_tile
    #           red_tile
    #          blue_tile
    #        yellow_tile
    #        purple_tile


    # first tile holds discription for all variables needed
    tiles = [

        {
            'class': 'tile_2',
            'type': 'red_tile',
            'posx': str(getx(0)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6">On Hold</font>',
            'content1': [
                '<h2>%s</h2>' % (procedure[1])[1],
                '<span style="font-size:250px;vertical-align:center;">%s</span>' % (procedure[1])[0],
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'sync',
            'type': 'blue_tile',
            'posx': str(4),
            'posy': str(1),
            'height': tile_sizes['sync_idea']['height'],
            'width': tile_sizes['sync_idea']['width'],
            'head': 'Components - Last refresh: %s' % currentTime,
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'header',
            'type': 'black_tile',
            'posx': str(39),
            'posy': str(1),
            'height': tile_sizes['header']['height'],
            'width': tile_sizes['header']['width'],
            'head': '<font size = "6" color="red">SCARAMANGA</font>',
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'tile_6',
            'type': 'red_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">S# On Floor > 5d</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">%s</span>' % procedure[5],
                ''
            ],
            'content2': [],
            'contentTable': [],

        },
        

        {
            'class': 'tile_7',
            'type': 'purple_tile',
            'posx': str(getx(6)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">S# Avail. last 7d</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">' + procedure[8] + '%</span>',
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_104',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">WOs Due</font>',
            'content1': [
                '',
                '<span style="font-size:6em;vertical-align:center;">%s</span>' % len(procedure[0]),
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_103',
            'type': 'yellow_tile',
            'posx': str(getx(0)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">WOs Open</font>',
            'content1': [
                '',
                '<span style="font-size:4em;vertical-align:center;">%s</span>' % procedure[6],
                ''
            ],
            'content2': []
        },


        {
            'class': 'tile_8',
            'type': 'blue_tile',
            'posx': str(getx(8)),
            'posy': str(gety(0)),
            'height': tile_sizes['half_rect']['height'],
            'width': tile_sizes['half_rect']['width'],
            'head': '<font size="5">Last 7 days Reported DOA</font>',
            'content1': [
                '<h2>%s</h2>' % procedure[3],
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

        {
            'class': 'tile_110',
            'type': 'green_tile',
            'posx': str(getx(4)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6">Inventory Shortage (Top 3)</font>',
            'content1': [
                '<h2>%s</h2>' % procedure[2],
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },
        {
            'class': 'tile_100',
            'type': 'yellow_tile',
            'posx': str(getx(8)),
            'posy': str(62),
            'height': tile_sizes['tiny_rect']['height'],
            'width': tile_sizes['tiny_rect']['width'],
            'head': '<font size="6">Repaired Today</font>',
            'content1': [
                '',
                '<span style="font-size:5em;vertical-align:center;">%s</span>' % procedure[7],
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

        
    ]


    return render_template('dashboards/PCB.html', tiles=tiles)

@app.route('/dashboard/HEAD', methods=['GET'])
def dashboard_HEAD():
    app.jinja_env.autoescape = False

    # start of tiles, atomic tile height, width and offsets between tiles
    # Note: these are percentages of the total width and height of the html body
    start_x = 3.5
    start_y = 10
    tile_width = 7.28
    tile_height = 13
    tile_offset_x = 1.54
    tile_offset_y = 1.5
    sync_x = 0
    sync_y = 0
    sync_offset_x = 0.0
    sync_offset_y = 0.0
    

    # return relative position in percentage from the internal tile positon
    def gety(y):
        return (start_y + y * tile_offset_y + y * tile_height)

    def getx(x):
        return (start_x + x * tile_offset_x + x * tile_width)

    def runCycle(result):
        for x in result:
            return str(x[0])

    def woOpenDef(result):
        return str(x[0][0])

    def openComponents(result):
	final = len(result)
	return final

    def onHold(result):
        """
        Creates a table of the top 5 on hold workorders.
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Part', 'Qty'])
        t = 0
        currentPos = 0
        typeDict = {}
        resultEmpty = 0
        final = []

        for x in result:
            tempSplitList = []
            noHead = False
            for t in x:
            	t = str(t)
            	tempVar = t.split()
            	tempSplitList.append(tempVar)
            	try:
                    if 'HEAD' not in tempSplitList[0]:
                        print "non-head found, removing from results..."
                        pass
                    else:
                        noHead = True
                        resultEmpty += 1
                except:
                    pass
            if noHead == True:
                table.add_row([x[0], x[1]])
            else:
                pass
        #, "bgcolor":"#FF7449"
    	if resultEmpty == 0:
            happyString = "0"
            tableShow = ""
    	else:
            happyString = ""
            tableShow = table.get_html_string(attributes={"text-align":"left", "size":"100%", "class":"Onhold"})
    	final.append(happyString)
    	final.append(tableShow)
    	return final


    def threeColumn(result):
        """
        Create a table with three columns
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Description', 'Shortage'], border=True)
        t = 0
        table.border == True
        for x in result:
            if t <= 2:
                table.add_row([x[1], x[7]])
                t += 1
            else:
                break
        #, "bgcolor":"#08D00C"
        return table.get_html_string(attributes={"table align":"left", "col width":"130", "td width":"100%", "size":"50px", "class":"InvShortage", "cellpadding":"5", "align":"center"})

    def DOA(result):
        """
        Create a table for the DOA's (not including HEAD)
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border=True)
        for x in result:
            if x[0] != 'HEAD':
                pass
            else:
                table.add_row([x[0], x[1], x[2]])
        print table.get_html_string(attributes={"size":"50px", "class":"DOA", "background-color":"green"})
        #"bgcolor":"#61ABFF"
        return table.get_html_string(attributes={"size":"10px", "class":"DOA", "cellpadding":"5"})

    def doaHead(result):
        """
        Create a table for HEAD DOA's
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border= True)
        for x in result:
            table.add_row([x[0], x[1], x[2]])
        return table.get_html_string(attributes={"size":"10px", "class":"DOAHead", "border":"1"})

    def repairedTodayNum(result):
        """
        Create one large number to be displayed as a count
        for the amount of S-numbers repaired today
        """
        return result[0][0]

    def woOverdueDisp(result):
        return result

    def openWO(result):
        return result[0][0]
        

    def runQuery(query):
        """
        Run a query from the database
        Parameter:
        query - Query to be ran
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        try:
            qr = c.execute(query)
            qry = c.fetchall()
        except Exception, e:
            qry = e
        return qry

    def funPic():
        pass

    def onFloor(result):
	a = []
	componentUsers = ['jasper', 'kevink', 'sergei']
	final = 0
	for i in result:
	    a.append(str(i[0]))
	for x in a:
	    if x in componentUsers:
	        final += 1
	print final
	return final

    def SAvailability(result):
        shipped = result[0][0]
        onhold = result[0][1]

        percentWO = 100 / int(shipped)
        percentOnHold = percentWO * int(onhold)
        total = str(int(math.floor(100 - percentOnHold)))
    
        return total

    def openFAs(result):
	final = len(result)
	return final

    def connect(storedProcedure):
        """
        Run a stored procedure from the database
        Parameter:
        storedProcedure - name of Stored Procedure within the database
        Please keep an eye on the driver (SQL Server Native Client 11.0)
        """
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
        cnxn = pyodbc.connect(con_string)
        c = cnxn.cursor()
        proc = str(storedProcedure)
        try:
            fuz = c.execute("exec %s" % proc)
            fuzzy = c.fetchall()
        except Exception, e:
            fuzzy = e
        return fuzzy

    currentTime = datetime.datetime.now().strftime("%H:%M")
    if str(currentTime) == '17:00':
        funPic()
        print "It's five!"
    else:
        pass

    def repaired2Day(storedProcedure):
	return storedProcedure[0][0]

    def weekCalc():
        currentWeek = (datetime.date.today().isocalendar()[1])
        print "Week: %s " % currentWeek

        return currentWeek
    
    # Create a list of procedures and various queries to be carried out by the tiles upon loading.
    sAvail = "exec sp_tiles_head_part_availability @week='%s'" % weekCalc()
    woOverdue = "SELECT rp.received_wo 'WO in' FROM tbl_rmaproducts_generic AS rp, tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus WHERE rp.swapgroup_id NOT IN (5,8,13,12,17,18) AND rma.klant_id not in (178,179,213,306) AND rp.received_wo IS NOT NULL and part.category IN ('HEAD') AND rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND part.category IN ('HEAD') AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id NOT IN (447) AND dbo.GetWorkingDays(rma.receivedate,CONVERT(DATE, GETDATE())) <= 6"
    woOpen = "SELECT count(*) FROM tbl_rma AS rma, tbl_parts As part, tbl_customers AS cus, tbl_rmaproducts_generic AS rp LEFT JOIN tbl_workorders w ON w.id = rp.received_wo LEFT JOIN tbl_loc_latest ll ON ll.workorder_id = w.id LEFT JOIN tbl_locations l ON l.id = ll.location_id WHERE rma.id = rp.rma_id AND part.id = rp.part_id AND rp.shipped_wo IS NULL AND cus.id = ISNULL(rp.shiptocustomer_id,rma.klant_id) AND rma.klant_id NOT IN (SELECT id FROM tbl_customers WHERE customertype = 'SEEDSTOCK') AND rma.klant_id <> 306"
    repairedToday = "SELECT COUNT(*) AS 'Work orders closed today' FROM tbl_workorders AS wo WHERE CONVERT(DATE, wo.repairdate) = CONVERT(DATE, GETDATE())"
    sRepairedToday = "SELECT COUNT(*) FROM tbl_component_location AS cl JOIN tbl_component AS co ON cl.component_id = co.id WHERE CONVERT(DATE, cl.entrancetime) = CONVERT(DATE, GETDATE()) AND co.[status] = 'GOOD' AND cl.location_id = 26"
    procedure = [woOverdueDisp(connect('sp_tiles_head_overdue')), onHold(connect('sp_tiles_report_onhold')), threeColumn(connect('sp_tiles_head_inventory_shortage')), DOA(connect('sp_tiles_head_doa_past7days')), doaHead(connect('sp_tiles_head_doa_past7days')), onFloor(connect('sp_tiles_head_closed5')), openComponents(connect('sp_tiles_head_wo_open')), repaired2Day(connect('sp_tiles_head_repaired_today_all')), SAvailability(runQuery(sAvail)), openFAs(connect('sp_tiles_head_openfa'))]

    #   size of screen (11x6):
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 
    #   * * * * * * * * * * * 

    # different tile sizes, new ones can be specified
    tile_sizes = {
        # * *
        # * *
        'small_square': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(2 * tile_width + tile_offset_x)
        },

        'sync_idea': {
            'height': str(7),
            'width': str(27)
        },

        'header': {
            'height': str(7),
            'width': str(60) 
        },

        'half_rect':{
            'height': str(3 * tile_height + 7 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },

        'tiny_rect':{
            'height': str(2 * tile_height + 5 * tile_offset_y),
            'width': str(2 * tile_width + 6 * tile_offset_x)
        },
        
        'small_rectangle':{
	    'height': str(2 * tile_height + tile_offset_y),
	    'width': str(2 * tile_width + 6 * tile_offset_x)
	},
        # * * * *
        # * * * *
        # * * * *
        # * * * *
        'big_square': {
            'height': str(4 * tile_height + 3 * tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * * *
        # * * * *
        'wide_rect': {
            'height': str(2 * tile_height + tile_offset_y),
            'width': str(4 * tile_width + 3 * tile_offset_x)
        },
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        # * * *
        'double_long_rect': {
            'height': str(6 * tile_height + 5 * tile_offset_y),
            'width': str(3 * tile_width + 2 * tile_offset_x)
        },
    }


    # tile types:
    #         green_tile
    #           red_tile
    #          blue_tile
    #        yellow_tile
    #        purple_tile


    # first tile holds discription for all variables needed
    tiles = [

        {
            'class': 'tile_999',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6">On Hold</font>',
            'content1': [
                '<h2>%s</h2>' % (procedure[1])[1],
                '<span style="font-size:250px;vertical-align:center;">%s</span>' % (procedure[1])[0],
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'sync2',
            'type': 'blue_tile',
            'posx': str(4),
            'posy': str(1),
            'height': tile_sizes['sync_idea']['height'],
            'width': tile_sizes['sync_idea']['width'],
            'head': 'Components - Last refresh: %s' % currentTime,
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'header2',
            'type': 'black_tile',
            'posx': str(39),
            'posy': str(1),
            'height': tile_sizes['header']['height'],
            'width': tile_sizes['header']['width'],
            'head': '<font size = "6" color="red">SCARAMANGA</font>',
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                ''
            ]
        },

        {
            'class': 'tile_61',
            'type': 'yellow_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">S# On Floor > 5d</font>',
            'content1': [
                '<span style="font-size:75px;vertical-align:center;">%s</span>' % procedure[5],
                '',
                ''
            ],
            'content2': [],
            'contentTable': [],

        },
        

        {
            'class': 'tile_71',
            'type': 'blue_tile',
            'posx': str(getx(6)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">S# Avail. last 7d</font>',
            'content1': [
                '<span style="font-size:75px;">' + procedure[8] + '%</span>',
                '',
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_1041',
            'type': 'red_tile',
            'posx': str(getx(2)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">WOs Due</font>',
            'content1': [
                '<span style="font-size:75px;vertical-align:top;">%s</span>' % len(procedure[0]),
                '',
                ''
            ],
            'content2': []
        },

        {
            'class': 'tile_1031',
            'type': 'green_tile',
            'posx': str(getx(0)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': '<font size="5">WOs Open</font>',
            'content1': [
                '<span style="font-size:75px;vertical-align:center;">%s</span>' % procedure[6],
                '',
                ''
            ],
            'content2': []
        },


        {
            'class': 'tile_81',
            'type': 'red_tile',
            'posx': str(getx(8)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_rectangle']['height'],
            'width': tile_sizes['small_rectangle']['width'],
            'head': '<font size="5">Last 7 days Reported DOA</font>',
            'content1': [
                '<h2>%s</h2>' % procedure[3],
              	''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

	{
            'class': 'tile_8122',
            'type': 'green_tile',
            'posx': str(getx(8)),
            'posy': str(gety(2)),
            'height': tile_sizes['small_rectangle']['height'],
            'width': tile_sizes['small_rectangle']['width'],
            'head': '<font size="5">Open FAs</font>',
            'content1': [
                '<span style="font-size:100px;vertical-align:center;">%s</span>' % procedure[9],
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },	

        {
            'class': 'tile_1101',
            'type': 'purple_tile',
            'posx': str(getx(4)),
            'posy': str(gety(2)),
            'height': tile_sizes['big_square']['height'],
            'width': tile_sizes['big_square']['width'],
            'head': '<font size="6">Inventory Shortage (Top 3)</font>',
            'content1': [
                '<h2>%s</h2>' % procedure[2],
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },
        {
            'class': 'tile_1001',
            'type': 'yellow_tile',
            'posx': str(getx(8)),
            'posy': str(68),
            'height': tile_sizes['small_rectangle']['height'],
            'width': tile_sizes['small_rectangle']['width'],
            'head': '<font size="6">Repaired Today</font>',
            'content1': [
                '<span style="font-size:100px;vertical-align:top;">%s</span>' % procedure[7],
                '',
                ''
            ],
            'content2': [
                '',
                '',
                ''
            ]
        },

        
    ]


    return render_template('dashboards/HEAD.html', tiles=tiles)


@app.route('/files/', defaults={'req_path': ''})
@app.route('/files/<path:req_path>')
def dir_listing(req_path):
    BASE_DIR = os.getcwd() + r'/files/'

    # Joining the base and the requested path
    abs_path = BASE_DIR + req_path

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        raise NotFound

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        fp = open(path,'rb')
        return Response(read_in_chunks(fp), direct_passthrough=True, mimetype='application/octet-stream')

    if not req_path.endswith('/') and req_path != '':
        req_path = req_path + '/'

    path = '/files/' + req_path
    abs_path = BASE_DIR + req_path

    # Show directory contents
    dir_contents = os.listdir(abs_path)
    files = []
    dirs = []
    for stuff in dir_contents:
        if os.path.isfile(abs_path + stuff):
            files.append(stuff)
        elif os.path.isdir(abs_path + stuff):
            dirs.append(stuff)

    return render_template('files.html', files=files, dirs=dirs, url=path)

@app.route('/EQL/getEQLfirmware<bit>')
def geteqlfirmware(bit):
    r_server=redis.Redis("127.0.0.1")

    if r_server.hexists('EQLfirmware',bit) == True:
        FWname=r_server.hget('EQLfirmware',bit)
    else:
        return 'couldn`t find redis info'
        #raise NotFound

    try:
        fp = open('files/Equallogic Files/Firmware/' + FWname,'rb')
    except:
        return 'couldn`t open file'
        #raise NotFound

    return Response(read_in_chunks(fp), headers={"etag": FWname}, direct_passthrough=True, mimetype='application/octet-stream')


@app.route('/EQL/RowScript.zip')
def checkversion():
    #updates a clients version of rowscript if it is outdated
    r_server=redis.Redis("127.0.0.1")
    
    if r_server.hexists('rowscript','currver') == True:
        currver=r_server.hget('rowscript','currver')
    else:
        return 'couldn`t find redis key-val pair'
        #raise NotFound

    try:
        fp = open('files/Equallogic Files/RowScript/' + currver,'rb')
    except:
        return 'couldn`t open file'
        #raise NotFound

    return Response(read_in_chunks(fp), headers={"etag": currver}, direct_passthrough=True, mimetype='application/octet-stream')




@app.route('/EQL/<client_id>', methods=['GET', 'POST'])
def status(client_id):
    # change the state or acces the state of a single client.
    current_time=time.time()
    r_server=redis.Redis("127.0.0.1")

    if request.method == 'POST':
        jsonobj=request.data
        data=json.loads(jsonobj)

        r_server.hset(client_id,'time',current_time)
        for k,v in data.iteritems():
            r_server.hset(client_id,k,v)

        return 'post'

    else:

        client = {'name':client_id, 'test':'N/A', 'status':'N/A', 'time':' '}

        if r_server.hexists(client['name'],'test') == True:
            client['test']=r_server.hget(client['name'],'test')

        if r_server.hexists(client['name'],'state') == True:
            client['status']=r_server.hget(client['name'],'status')

        if r_server.hexists(client['name'],'time') == True:
            old_time=float(r_server.hget(client['name'],'time'))
            client['time']=str(datetime.timedelta(seconds=int(current_time - old_time)))

        return json.dumps(client)



@app.route('/dashboard/EQL')
def clients():
    r_server=redis.Redis("127.0.0.1")
    current_time=time.time()

    start_x = 80
    start_y = 100
    tile_width = 335
    tile_height = 210
    tile_offset_x = 25
    tile_offset_y = 25

    # return relative position in percentage from the internal tile positon
    def gety(y):
        return (start_y + y * tile_offset_y + y * tile_height)

    def getx(x):
        return (start_x + x * tile_offset_x + x * tile_width)


    tile_sizes = {
        'EQL_tile': {
            'height': str(tile_height),
            'width': str(tile_width)
        }
    }

    #list of all clients for Equallogic, arranged in the same way they are arranged in the server stacks.
    tiles = [

        {
            'class': 'EQL1_1',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL1_2',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL1_3',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P3',
            'test': '',
            'time': '',
            'state': '',  
        },


        {
            'class': 'EQL2_1',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL2_2',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL2_3',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_1',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_2',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_3',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_1',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_2',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_3',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_1',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_2',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_3',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_4',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(3)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P4',
            'test': '',
            'time': '',
            'state': '',  
        }
    ]
    

    tile_type_conversion = {
        'busy':     'blue_tile',             
        'attention':'red_tile',    
        'done':     'green_tile',    
        'error':    'purple_tile'
    }

    
    #get the information for all the listed clients from redis
    for client in tiles:
        if r_server.hexists(client['client'],'test') == True:
            client['test']=r_server.hget(client['client'],'test')

        if r_server.hexists(client['client'],'state') == True:
            client['state']=r_server.hget(client['client'],'state')

        if r_server.hexists(client['client'],'time') == True:
            old_time=float(r_server.hget(client['client'],'time'))
            client['time']=str(datetime.timedelta(seconds=int(current_time - old_time)))

        if client['state'] in tile_type_conversion:
            client['type']=tile_type_conversion[client['state']]


    return render_template('dashboards/EQL.html',tiles=tiles)

@app.route('/dashboard/HEAD')
def clients1():
    r_server=redis.Redis("127.0.0.1")
    current_time=time.time()

    start_x = 80
    start_y = 100
    tile_width = 335
    tile_height = 210
    tile_offset_x = 25
    tile_offset_y = 25

    # return relative position in percentage from the internal tile positon
    def gety(y):
        return (start_y + y * tile_offset_y + y * tile_height)

    def getx(x):
        return (start_x + x * tile_offset_x + x * tile_width)


    tile_sizes = {
        'EQL_tile': {
            'height': str(tile_height),
            'width': str(tile_width)
        }
    }

    #list of all clients for Equallogic, arranged in the same way they are arranged in the server stacks.
    tiles = [

        {
            'class': 'EQL1_1',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL1_2',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL1_3',
            'type': 'blue_tile',
            'posx': str(getx(0)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR1P3',
            'test': '',
            'time': '',
            'state': '',  
        },


        {
            'class': 'EQL2_1',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL2_2',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL2_3',
            'type': 'blue_tile',
            'posx': str(getx(1)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR2P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_1',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_2',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL3_3',
            'type': 'blue_tile',
            'posx': str(getx(2)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR3P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_1',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_2',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL4_3',
            'type': 'blue_tile',
            'posx': str(getx(3)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLXR4P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_1',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P1',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_2',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(1)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P2',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_3',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(2)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P3',
            'test': '',
            'time': '',
            'state': '',  
        },

        {
            'class': 'EQL5_4',
            'type': 'blue_tile',
            'posx': str(getx(4)),
            'posy': str(gety(3)),
            'height': tile_sizes['EQL_tile']['height'],
            'width': tile_sizes['EQL_tile']['width'],
            'client': 'EQLPR1P4',
            'test': '',
            'time': '',
            'state': '',  
        }
    ]
    

    tile_type_conversion = {
        'busy':     'blue_tile',             
        'attention':'red_tile',    
        'done':     'green_tile',    
        'error':    'purple_tile'
    }

    
    #get the information for all the listed clients from redis
    for client in tiles:
        if r_server.hexists(client['client'],'test') == True:
            client['test']=r_server.hget(client['client'],'test')

        if r_server.hexists(client['client'],'state') == True:
            client['state']=r_server.hget(client['client'],'state')

        if r_server.hexists(client['client'],'time') == True:
            old_time=float(r_server.hget(client['client'],'time'))
            client['time']=str(datetime.timedelta(seconds=int(current_time - old_time)))

        if client['state'] in tile_type_conversion:
            client['type']=tile_type_conversion[client['state']]


    return render_template('dashboards/HEAD.html',tiles=tiles)

if __name__ == '__main__':
    app.run(
        debug=True,
        host="192.168.0.212",
        port=1313
    )
