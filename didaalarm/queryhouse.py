from flask import Blueprint, render_template, redirect, request, session, url_for, flash
from didaalarm import db, app
import datetime, time
import json,requests
import os
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.family']='sans-serif'
plt.rcParams['axes.unicode_minus'] = False
from io import BytesIO
import base64
import math
import textwrap

queryhouse = Blueprint('queryhouse', __name__)

KEEP_SESSTION_MINS = 10
ROOMSJSON = []
PROJECTNAME,BLOCKNAME,SORTTYPE = '','',''
# payloadData数据
PAYLOADDATA = {"siteid": "", "useType": "", "areaType": "", "entName": "", "location": "",
            "minrow": "1", "maxrow": "21","projectname":""}


@queryhouse.route('/', methods=['GET', 'POST'])
@queryhouse.route('/searchcomp', methods=['GET', 'POST'])
def searchcomp():
    if request.method == 'GET':
        return render_template('queryhouse/searchcomp.html')
    if request.method == 'POST':
        projectname = request.form['projectname']
        areaType = request.form['selectareatype']
        siteid = request.form['selectxzq']
        useType = request.form['selectusertype']
        if projectname == '' and areaType == '' and siteid == '' and useType == '':
            flash('请至少选择一个搜索选项', 'error')
            # return render_template('queryhouse/searchcomp.html')
            return redirect(url_for('.searchcomp'))
        else:
            return redirect(url_for('.displayblocks',projectname=projectname,areaType=areaType,siteid=siteid,useType=useType))


@queryhouse.route('/displayblocks', methods=['GET', 'POST'])
def displayblocks():
    if request.method == 'GET':
        global PAYLOADDATA
        for i in ['projectname','areaType','siteid','useType']:
            v = request.args.get(i)
            PAYLOADDATA[i] = v
        blocks = getblocks(PAYLOADDATA)
        if len(blocks) == 0:
            flash('没有找到相关的楼盘，请重新输入', 'error')
            return redirect(url_for('.searchcomp'))
        else:
            return render_template('queryhouse/displayblocks.html',blocks=blocks,title='搜索结果')


@queryhouse.route('/displayrooms', methods=['GET', 'POST'])
def displayrooms():
    global ROOMSJSON,PROJECTNAME,BLOCKNAME,SORTTYPE
    if request.method == 'GET':
        ROOMSJSON = []
        PROJECTNAME,BLOCKNAME = '',''
        buildingid = request.args.get('buildingid')
        PROJECTNAME = request.args.get('projectname')
        BLOCKNAME = request.args.get('blockname')
        rooms_status_list = getRoomJson(buildingid)
        for rj in rooms_status_list:
            # if '井' not in rj['rn'] and '架空' not in rj['rn']:
            if rj["use"] == "成套住宅" and rj["pid"] == 0:
                rj['rn'] = str(rj['rn'])
                rj['flr'] = str(rj['flr'])
                if rj['roomstatus'] in ('期房', '现房'):
                    rj['roomstatus'] = rj['roomstatus'] + '可售'
                elif rj['roomstatus'] in ('网签', '认购'):
                    rj['roomstatus'] = '已' + rj['roomstatus']
                else:
                    pass
                ROOMSJSON.append(rj)
        roomsjson_dis = ROOMSJSON

    if request.method == 'POST':
        checksale = request.form.getlist('checksale')
        roomsjson_dis = []
        if 'saled' in checksale:
            roomsjson_dis = ROOMSJSON
        else:
            for rjs in ROOMSJSON:
                if '可售' in rjs['roomstatus']:
                    roomsjson_dis.append(rjs)

        if request.form['selectsorttype'] != '':
            SORTTYPE = request.form['selectsorttype']
        if request.form['selectsorttype'] == '' and SORTTYPE == '':
            SORTTYPE = 'rn'
        if SORTTYPE == 'nszj':
            roomsjson_dis = sorted(roomsjson_dis, key=lambda rj: rj['iArea'] * rj['nsjg'])
        else:
            roomsjson_dis = sorted(roomsjson_dis,key = lambda rj:rj[SORTTYPE])

    return render_template('queryhouse/displayrooms.html', rooms=roomsjson_dis, projectname=PROJECTNAME,
                           blockname=BLOCKNAME, roomcount=len(roomsjson_dis))


@queryhouse.route('/show', methods=['GET', 'POST'])
def show():
    if request.method == 'GET':
        buildingid = request.args.get('buildingid')
        projectname = request.args.get('projectname')
        blockname = request.args.get('blockname')

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        myTitle = projectname+blockname
        myTitle = "\n".join(textwrap.wrap(myTitle, 30))+"\n剩余套数趋势图"
        ax.set_title(myTitle)
        if buildingid is None:
            return redirect(url_for('.searchcomp'))
        # print(buildingid,projectname,blockname)
        sql = '''
    select a.projectid,a.buildingid,DATE(a.scan_datetime) as `date`,
    a.`left`,(a.`left` +a.`sold`) as total
    from  block_track a
    inner join block_detail  b
    on a.buildingid = b.buildingid
    and DATE(a.scan_datetime) <= CURRENT_DATE '''+ " " \
    "and b.buildingid = \'"+buildingid+"\' order by a.buildingid, a.scan_datetime"
        try:
            cursor = db.session.execute(sql)
            result = cursor.fetchall()
            db_conn = True
        except:
            db_conn = False

        date_list = []
        left_list = []
        total_list = []

        if db_conn:
            # if len(result) > 15:
            pace = int(len(result) / 20)
            pace = pace if pace > 0 else 1
            for j in range(0, len(result), pace):
                date_list.append(result[j].date)
                left_list.append(int(result[j].left))
                total_list.append(result[j].total)
            if j < len(result) - 1:
                date_list.append(result[-1].date)
                left_list.append(int(result[-1].left))
                total_list.append(result[-1].total)
            # else:
            #     for r in result:
            #         date_list.append(r.date)
            #         left_list.append(int(r.left))
            #         total_list.append(r.total)

            if len(result) == 0:
                plt.yticks([])
                plt.xticks([])
                plt.text(0.5, 0.5, '没有跟踪数据', ha='center', va='center',fontsize=10)
            elif len(result) == 1 and left_list[-1] == 0:
                plt.yticks([])
                plt.xticks([])
                plt.text(0.5, 0.5, '总套数：' + str(max(total_list))+",已售罄", ha='center', va='center',
                         fontsize=10)
            else:
                plt.xticks(range(len(date_list)),date_list,rotation=70)
                y_pace = math.ceil(abs((left_list[0]-left_list[-1]))/(len(left_list)))
                # pace = math.ceil((left_list[0] - left_list[-1]) / 5)
                y_pace = y_pace if y_pace > 0 else 1
                plt.yticks(range(math.floor(min(left_list)), math.ceil(max(left_list))+1, y_pace))
                plt.plot(range(len(left_list)), left_list)
                plt.scatter(range(len(left_list)), left_list, s=12)
                try:
                    quhualv = '{:.0%}'.format((result[-1].total - result[-1].left) / result[-1].total)
                except:
                    quhualv = 'N/A'
                cus_legend = '\n总计：'+str(max(total_list))+"套\n去化率："+str(quhualv)
                # plt.text(len(left_list)-1, (max(left_list)+min(left_list))/2, '总套数：'+str(max(total_list))+"\n去化率："+str(quhualv), ha='center', va='bottom')
                before_b = 999999
                for a, b in zip(range(len(date_list)), left_list):
                    if before_b != b:
                        plt.text(a, b, '%.0f' % b, ha='center', va='bottom', fontsize=10)
                    before_b = b
                # avg = sum(left_list) / len(left_list)
                # mid = (min(left_list) + max(left_list)) / 2
                # # len_min = len([i for i in left_list if i < avg(left_list)])
                # # len_max = len([i for i in left_list if i > avg(left_list)])
                # if avg <= mid:
                #     loc = 'upper right'
                # else:
                #     loc = 'lower left'
                plt.legend(["剩余："+str(left_list[-1])+"套"+cus_legend],loc='best')

        else:
            plt.yticks([])
            plt.xticks([])
            plt.text(0.5, 0.5, '数据库连接失败，请返回重试', ha='center', va='center', fontsize=10)

        # basepath = os.path.dirname(__file__)
        # pic_name = projectname+'_'+blockname+'.png'
        # full_filename = os.path.join('static/images', pic_name)
        # save_path = os.path.join(basepath,full_filename)
        # plt.savefig(save_path)
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer)
        image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()
        # return render_template("queryhouse/show.html", user_image='/'+full_filename)
        return render_template("queryhouse/show.html", image_data=image_data)


def getblocks(payloadData):
    # postUrl = 'http://www.cq315house.com/WebService/Service.asmx/getParamDatas2'
    postUrl = 'http://www.cq315house.com/WebService/WebFormService.aspx/getParamDatas2'
    # 请求头设置
    payloadHeader = {
        'Host': 'www.cq315house.com',
        'Content-Type': 'application/json',
        # 'POST': '/WebService/Service.asmx/getParamDatas2'
        'POST': '/WebService/WebFormService.aspx/getParamDatas2',
        #
        # 'Referer': 'http://www.cq315house.com/HtmlPage/PresaleDetail.html',
        # # 'Cookie': 'ASP.NET_SessionId=uro33bq5ddt1fkwcyxyugzx5',
        # 'Origin': 'http://www.cq315house.com',
        # # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
        # # # 'User-Agent':'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36 Maxthon/5.2.7.4000',
        # 'X-Requested-With': 'XMLHttpRequest',
        # 'Accept': 'application/json, text/javascript, */*; q=0.01',
        # 'Connection': 'keep-alive',
        # 'Content-Length': '111',
        # 'POST': '/WebService/WebFormService.aspx/getParamDatas2',
        # 'DNT': "1",
        # 'Accept-Encoding': 'gzip, deflate',
        # 'Accept-Language': 'en-US'
    }
    # 下载超时
    timeOut = 25
    dumpJsonData = json.dumps(payloadData)
    res = requests.post(postUrl, data=dumpJsonData, headers=payloadHeader, timeout=timeOut, allow_redirects=True)
    display = []
    if res.status_code == 200:
        try:
            response_json = json.loads(res.text)
            a = response_json["d"].replace('[', '').replace(']', '').replace('},', '}@@@')
            b = a.split('@@@')
            if b == ['']:
                return []
            for presale in b:
                p = json.loads(presale)
                blockname_list = p['blockname'].split(',')
                buildingid_list = p['buildingid'].split(',')
                lenofbid = len(buildingid_list)
                for i in range(lenofbid):
                    tmp = {'projectname':p['projectname'],'enterprisename':p['enterprisename']}
                    # print(blockname_list[i], ":", buildingid_list[i])
                    tmp['blockname'] = blockname_list[i]
                    tmp['buildingid'] = buildingid_list[i]
                    display.append(tmp)
        except:
            return []
    return display


def getRoomJson(bid):
    # url = 'http://www.cq315house.com/WebService/Service.asmx/GetRoomJson'
    url = 'http://www.cq315house.com/WebService/WebFormService.aspx/GetRoomJson'
    payloadData = {}
    payloadData['buildingid'] = bid
    payloadHeader = {
        'Host': 'www.cq315house.com',
        'Content-Type': 'application/json'
    }
    rooms_status_list = []
    timeOut = 30
    dumpJsonData = json.dumps(payloadData)
    res = requests.post(url, data=dumpJsonData, headers=payloadHeader, timeout=timeOut, allow_redirects=True)
    if res.status_code == 200:
        rooms_status = json.loads(res.text)['d']
        a = rooms_status[1:-1].replace('},{\"id\"', '}@@@{\"id\"')
        b = a.split('@@@')
        for bb in b:
            try:
                bbjson = json.loads(bb)
                for i in bbjson["rooms"]:
                    rooms_status_list.append(i)
            except:
                pass
        return rooms_status_list
    else:
        return []
