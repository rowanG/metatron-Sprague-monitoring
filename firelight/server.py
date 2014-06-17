from flask import Flask, render_template
import db
import pyodbc
from prettytable import PrettyTable
import cgi
import datetime
import operator
from collections import OrderedDict

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    # app.jinja_env.autoescape = False

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
        table = PrettyTable(['Workorder', 'Description'])
        t = 0
        currentPos = 0
        typeDict = {}
        for x in result:
            if x[2] in typeDict:
                z = x[2]
                typeDict[z] = typeDict[z] + 1
            else:
                z = x[2]
                typeDict[z] = 1

        
        sorted_x = sorted(typeDict.iteritems(), key=operator.itemgetter(1))
        sorted_x.reverse()
        sorted_x = OrderedDict(sorted_x)
        for j in sorted_x:
            print j
            if t < 3:
                print
                print "LOOOOOOOOOOK!!!! %s " % j
                print
                table.add_row([str(j), typeDict[j]])
                t += 1
            else:
                break
        return table.get_html_string(attributes={"size":"100%", "class":"Onhold", "bgcolor":"#FF7449"})

    def threeColumn(result):
        table = PrettyTable(['Description', 'Shortage'], border=True)
        t = 0
        table.border == True
        print result
        for x in result:
            if t <= 2:
                table.add_row([x[1], x[6]])
                t += 1
            else:
                break
        return table.get_html_string(attributes={"size":"50px", "class":"InvShortage", "bgcolor":"#08D00C", "cellpadding":"5", "align":"center"})

    def DOA(result):
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border=True)
        for x in result:
            if x[0] == 'HEAD':
                pass
            else:
                table.add_row([x[0], x[1], x[2]])
        print table.get_html_string(attributes={"size":"50px", "class":"DOA", "background-color":"green"})

        return table.get_html_string(attributes={"size":"10px", "class":"DOA", "bgcolor":"#61ABFF", "cellpadding":"5"})

    def doaHead(result):
        table = PrettyTable(['Commodity', 'Used', 'DOA'], border= True)
        for x in result:
            table.add_row([x[0], x[1], x[2]])
        return table.get_html_string(attributes={"size":"10px", "class":"DOAHead", "border":"1"})

    def connect(storedProcedure):
        conn_string = "Driver={SQL Server Native Client 11.0};Server=DC01\MSSQL2008;Database=oddjob;UID=dbuser;PWD=cocacola;"
        db = pyodbc.connect(conn_string)
        c = db.cursor()
        proc = str(storedProcedure)
        try:
            fuz = c.execute("exec %s" % proc)
            fuzzy = c.fetchall()
        except Exception, e:
            fuzzy = e
        return fuzzy

    currentTime = datetime.datetime.now().strftime("%H:%M")
    procedure = [connect('sp_dash_overdue_wo'), onHold(connect('sp_tiles_report_onhold')), threeColumn(connect('sp_com_inventory_shortage')), DOA(connect('sp_tiles_components_doa_past7days')), doaHead(connect('sp_tiles_head_doa_past7days'))]

    #   size of screen (11x6):
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

    return render_template('tile1.html', tiles=tiles)


if __name__ == '__main__':
    app.run(
        debug=True,
        host="127.0.0.1",
        port=666
    )
