from __future__ import division
import datetime
import time
import json
import redis
import math
import db
import pyodbc
from prettytable import PrettyTable
import cgi
import requests
import os, sys
import operator
from collections import OrderedDict
from flask import Flask,render_template,request,Response
import werkzeug.exceptions

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
        {'url':'/dashboard/PCB',         'name':'Components PCB'}
    ]


    return render_template('index.html',urls=urls,header=header)



@app.route('/dashboard/PCB', methods=['GET'])
def dashboard_PCB():
    app.jinja_env.autoescape = False    # Allows for pure HTML escape characters

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

    def onHold(result):
        """
        Creates a table of the top 5 on hold workorders.
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Workorder', 'Description'])
        t = 0
        currentPos = 0
        typeDict = {}
        for x in result:
            if x[2] in typeDict:    # Check if a description has been placed in Dict before, to prevent showing doubles
                z = x[2]
                typeDict[z] = typeDict[z] + 1   # Add +1 to the count for this description
            else:
                z = x[2]
                typeDict[z] = 1     # Add description to dictionary, and add 1 to it's counter

        
        sorted_x = sorted(typeDict.iteritems(), key=operator.itemgetter(1)) # Change list of tuples to dictionary
        sorted_x.reverse()  # Reverse order of list showing most items first
        sorted_x = OrderedDict(sorted_x)    # Keep original order of dictionary
        for j in sorted_x:
            print j
            if t < 3:
                table.add_row([str(j), typeDict[j]]) # Add to the table
                t += 1
            else:
                break
        return table.get_html_string(attributes={"size":"100%", "class":"Onhold", "bgcolor":"#FF7449"}) # Return HTML table

    def threeColumn(result):
        """
        Create a table with three columns
        Parameter:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Description', 'Shortage'], border=True)
        t = 0
        table.border == True
        print result
        for x in result:
            if t <= 2:
                table.add_row([x[1], x[6]]) # Add top three results to table
                t += 1
            else:
                break
        return table.get_html_string(attributes={"size":"50px", "class":"InvShortage", "bgcolor":"#08D00C", "cellpadding":"5", "align":"center"})

    def DOA(result):
        """
        Create a table for the DOA's (not including HEAD)
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border=True)
        for x in result:
            if x[0] == 'HEAD':  # Do not include 'HEAD' as a result
                pass
            else:
                table.add_row([x[0], x[1], x[2]])   # Add to the table
        print table.get_html_string(attributes={"size":"50px", "class":"DOA", "background-color":"green"})

        return table.get_html_string(attributes={"size":"10px", "class":"DOA", "bgcolor":"#61ABFF", "cellpadding":"5"})

    def doaHead(result):
        """
        Create a table for HEAD DOA's
        Parameters:
        result - tuple return from Stored Procedure
        """
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border= True)
        for x in result:
            table.add_row([x[0], x[1], x[2]])   # Add to the table
        return table.get_html_string(attributes={"size":"10px", "class":"DOAHead", "border":"1"})

    def connect(storedProcedure):
        """
        Run a stored procedure from the database
        Parameter:
        storedProcedure - name of Stored Procedure within the database
        """
        conn_string = "Driver={ODBC Driver 11 for SQL Server};Server=DC01\MSSQL2008;Database=oddjob;UID=dbuser;PWD=cocacola"
        db = pyodbc.connect(conn_string)    # Set up connection with the database
        c = db.cursor()             # Allocate the cursor
        proc = str(storedProcedure)     # Create variable of stored procedure given
        try:
            fuz = c.execute("exec %s" % proc)   # Run MS SQL query on the stored procedure
            fuzzy = c.fetchall()        # Take all results in a tuple ready to pass to function
        except Exception, e:
            fuzzy = e               # If an error occurs, give this as the result to display
        return fuzzy                # Return the result

    currentTime = datetime.datetime.now().strftime("%H:%M")
    
    # Create a list of procedures to be carried out, these can be called upon
    procedure = [connect('sp_dash_overdue_wo'), onHold(connect('sp_tiles_report_onhold')), threeColumn(connect('sp_com_inventory_shortage')), DOA(connect('sp_tiles_components_doa_past7days')), doaHead(connect('sp_tiles_head_doa_past7days'))]

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
            'head': 'On Hold',
            'content1': [
                '',
                '',
                ''
            ],
            'content2': [
                '<h3><em>%s</em></h3>' % procedure[1]
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
            'class': 'tile_6',
            'type': 'red_tile',
            'posx': str(getx(4)),
            'posy': str(gety(0)),
            'height': tile_sizes['small_square']['height'],
            'width': tile_sizes['small_square']['width'],
            'head': 'WOs Closed',
            'content1': [
                '',
                '',
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
            'head': 'WOs OVERDUE',
            'content1': [
                '',
                '<span style="font-size:6em;vertical-align:center;">%s</span>' % len(procedure[0]),
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
            'head': 'WOs Due',
            'content1': [
                '',
                '',
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
            'head': 'WOs Open',
            'content1': [
                '',
                '',
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
            'head': 'Last 7 days Reported DOA',
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
            'head': 'Inventory Shortage (Top 3)',
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
            'head': 'S# ',
            'content1': [
                '',
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


    return render_template('dashboards/PCB.html', tiles=tiles)


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

    start_x = 3.5
    start_y = 11.5
    tile_width = 17.3
    tile_height = 19
    tile_offset_x = 1.5
    tile_offset_y = 3

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



if __name__ == '__main__':
    app.run(
        debug=True,
        host="192.168.0.216",
        port=666
    )