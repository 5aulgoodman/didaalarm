#coding:utf-8
import requests,json,time,datetime,re
import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,func
from sqlalchemy.types import *
import threading
import mysql_cfg as cfg

BaseModel = declarative_base()
FREQEUENCY_TIME = 0
FREQEUENCY_LIMIT = 10
IP_PORT_LIST = []

class Block_Detail(BaseModel):
    __tablename__ = 'block_detail'
    buildingid = Column(VARCHAR(255), primary_key=True)
    projectid = Column(Integer)
    projectname = Column(VARCHAR(255))
    enterprisename = Column(VARCHAR(255))
    location = Column(VARCHAR(255))
    presale_cert = Column(VARCHAR(255))
    blockname = Column(VARCHAR(255))
    max_floor = Column(Integer)
    avg_price = Column(DECIMAL(10,2))
    max_price = Column(DECIMAL(10,2))
    max_price_floor = Column(VARCHAR(255))
    min_price = Column(DECIMAL(10,2))
    min_price_floor = Column(VARCHAR(255))
    room_types = Column(VARCHAR(255))
    soldout = Column(CHAR(1))
    stamp = Column(DATETIME, default=datetime.datetime.now)

class Block_Track(BaseModel):
    __tablename__ = 'block_track'
    buildingid = Column(Integer, primary_key=True)
    scan_datetime = Column(DATETIME, primary_key=True, default=datetime.datetime.now)
    projectid = Column(Integer)
    sold = Column(Integer)
    left = Column(Integer)

class Run_Control(BaseModel):
    __tablename__ = 'run_control'
    run_day = Column(DATE, primary_key=True)
    run_status = Column(CHAR(1))
    start_time = Column(DATETIME)
    end_time = Column(DATETIME)
    cur_minrow = Column(Integer)
    cur_maxrow = Column(Integer)
    time = Column(Integer)

class Proxy_Ips(BaseModel):
    __tablename__ = 'proxy_ips'
    ip_port = Column(VARCHAR(255), primary_key=True)
    http_type = Column(VARCHAR(255))
    location = Column(VARCHAR(255))
    used_times = Column(Integer)
    create_time = Column(DATETIME, default=datetime.datetime.now)
    change_time = Column(DATETIME, default=datetime.datetime.now)

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
    timeOut = 10
    dumpJsonData = json.dumps(payloadData)
    rc, ip_list = get_Proxy_Ips(30)
    if len(ip_list) == 0:
        try:
            res = requests.post(postUrl, data=dumpJsonData, headers=payloadHeader, timeout=timeOut, allow_redirects=True)
        except:
            return 89, [] #requests error
    else:
        for [http_type, ip_port] in ip_list:
            try:
                res = requests.post(postUrl, data=dumpJsonData, headers=payloadHeader, timeout=timeOut,
                                    allow_redirects=True, proxies={http_type: ip_port})
                if res.status_code == 200:
                    add_sub_Proxy_Ip(ip_port, 'add')
                    rc = 0
                    break
            except:
                add_sub_Proxy_Ip(ip_port, 'sub')
                res = None
                rc = 89

    if res is not None:
        rc = 0
        display = []
        response_json = json.loads(res.text)
        a = response_json["d"].replace('[', '').replace(']', '').replace('},', '}@@@')
        b = a.split('@@@')
        if b == ['']:
            return rc, []
        for presale in b:
            p = json.loads(presale)
            blockname_list = p['blockname'].split(',')
            buildingid_list = p['buildingid'].split(',')
            lenofbid = len(buildingid_list)
            for i in range(lenofbid):
                tmp = {'projectname': p['projectname'], 'enterprisename': p['enterprisename'], \
                       'f_presale_cert': p['f_presale_cert'], 'location': p['location'], 'projectid': p['projectid']}
                tmp['blockname'] = blockname_list[i]
                tmp['buildingid'] = buildingid_list[i]
                display.append(tmp)
        return rc, display
    return rc, []


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
    timeOut = 10
    dumpJsonData = json.dumps(payloadData)
    rc, ip_list = get_Proxy_Ips(30)
    if len(ip_list) == 0:
        try:
            res = requests.post(url, data=dumpJsonData, headers=payloadHeader, timeout=timeOut, allow_redirects=True)
        except:
            return 89, [] #requests error
    else:
        for [http_type, ip_port] in ip_list:
            try:
                res = requests.post(url, data=dumpJsonData, headers=payloadHeader, timeout=timeOut,
                                    allow_redirects=True, proxies={http_type: ip_port})
                if res.status_code == 200:
                    add_sub_Proxy_Ip(ip_port, 'add')
                    rc = 0
                    break
            except:
                add_sub_Proxy_Ip(ip_port, 'sub')
                res = None
                rc = 89

    if res is not None:
        rc = 0
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
        return rc, rooms_status_list
    else:
        return rc, []


def get_Proxy_Ips(limit):
    global FREQEUENCY_TIME, FREQEUENCY_LIMIT, IP_PORT_LIST
    try:
        if FREQEUENCY_TIME % FREQEUENCY_LIMIT == 0:
            if limit == 0:
                r = session.query(Proxy_Ips).order_by(Proxy_Ips.used_times.desc()).all()
            else:
                r = session.query(Proxy_Ips).order_by(Proxy_Ips.used_times.desc()).limit(limit).all()
            IP_PORT_LIST = []
            for rr in r:
                IP_PORT_LIST.append([rr.http_type.lower(), rr.ip_port])
            FREQEUENCY_TIME = 1
            return 0, IP_PORT_LIST
        else:
            FREQEUENCY_TIME += 1
            return 0, IP_PORT_LIST
    except:
        return 99, []

def add_sub_Proxy_Ip(ip_port, type):
    try:
        if type == 'add':
            session.query(Proxy_Ips).filter_by(ip_port=ip_port).update({"used_times": Proxy_Ips.used_times + 1,
                                                                        "change_time": datetime.datetime.now()})
        elif type == 'sub':
            session.query(Proxy_Ips).filter_by(ip_port=ip_port).update({"used_times": Proxy_Ips.used_times - 1,
                                                                        "change_time": datetime.datetime.now()})
        session.commit()
    except:
        pass


def process_block(block):
    session = DBSession()
    max_floor = 0
    avg_price = 0.00
    max_price = 0.00
    max_price_floor = 0
    min_price_floor = 0
    min_price = 999999.00
    room_types = []
    avg_count = 0
    avg_price_total = 0.00
    sold_count = 0
    left_count = 0
    sold_out = ''
    # block sample:
    # {'projectname': '中南玖宸二期', 'enterprisename': '重庆锦腾房地产开发有限公司', 'f_presale_cert': '渝住建委（2020）预字第（184）号', 'location': '北碚区蔡家组团M分区M09-01/04号宗地', 'projectid': '719729', 'blockname': '2号楼', 'buildingid': '1199714'}
    projectid = block["projectid"]
    buildingid = block["buildingid"]
    projectname = block["projectname"]
    enterprisename = block["enterprisename"]
    location = block["location"]
    presale_cert = block["f_presale_cert"]
    blockname = block["blockname"]

    house_found = False
    bd_found = session.query(Block_Detail).filter(Block_Detail.buildingid == buildingid).first()
    bt_found = session.query(Block_Track).filter( \
        func.date(Block_Track.scan_datetime) == func.date(datetime.datetime.now()), \
        Block_Track.buildingid == buildingid).all()

    if bd_found is not None and len(bt_found) > 0:
        session.close()
        return 0

    if bd_found is not None:
        match_obj_old = re.match(regex_str, bd_found.presale_cert)
        match_obj_new = re.match(regex_str, presale_cert)
        if match_obj_old and match_obj_new:
            if (match_obj_new.group(1) > match_obj_old.group(1)) or \
                    (match_obj_new.group(1) == match_obj_old.group(1) and
                     match_obj_new.group(2) > match_obj_old.group(2)):
                session.query(Block_Detail).filter(Block_Detail.buildingid == buildingid). \
                    update({"presale_cert": presale_cert})
                session.commit()

        if bd_found.soldout == "Y":
            session.close()
            return 0

    rc, b = getRoomJson(buildingid)
    for rj in b:
        if rj["use"] == "成套住宅":
            if not house_found:
                house_found = True
            if rj["flr"].isdigit():
                if max_floor < int(rj["flr"]):
                    max_floor = int(rj["flr"])

            if rj["rType"] not in room_types:
                room_types.append(rj["rType"])

            nsjg = float(rj["nsjg"])
            if nsjg > 0:
                avg_count = avg_count + 1
                avg_price_total = avg_price_total + nsjg

                if nsjg > max_price:
                    max_price = nsjg
                    max_price_floor = rj["flr"]

                if nsjg < min_price:
                    min_price = nsjg
                    min_price_floor = rj["flr"]

            if rj["roomstatus"] in ["网签", "认购"]:
                sold_count = sold_count + 1
            elif rj["pid"] == 0:
                left_count = left_count + 1

            # ['期房', '网签', '认购', '测绘锁定', '现房', '房屋抵押']
            # ['成套住宅', '办公', '', '物管用房', '其他', '商业服务', '仓储', '其他用房', '教育', '非成套住宅', '停车用房', '商服用房', '教育用房', '集体宿舍', '金融保险', '医疗卫生', '仓储用房', '文化', '体育', '铁路']
            # ['钢筋混凝土结构', '钢和钢筋混凝土结构', '', '混合结构', '砖木结构', '其他结构', '钢结构']
            # ['8', '1', '2', '3', '4', '5', '6', '7', '9', '负1', '32', '16', '15', '14', '11', '10', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '38', '39', '40', '41', '17', '18', '42', '43', '44', '34', '35', '36', '37', '33', '12', '13', '地下1', '地下2', '商业1', '商业2', '商业3', '7+1', '负3', '负2']

    if avg_count != 0:
        avg_price = round(avg_price_total / avg_count, 2)
    if left_count == 0 and sold_count > 0:
        sold_out = 'Y'
        if bd_found is not None:
            session.query(Block_Detail).filter(Block_Detail.buildingid == buildingid). \
                update({"soldout": sold_out})
            session.commit()
    else:
        sold_out = 'N'

    if house_found:
        if bd_found is None:
            new_blcok = Block_Detail(projectid=projectid, buildingid=buildingid, projectname=projectname, \
                                     enterprisename=enterprisename, location=location,
                                     presale_cert=presale_cert, blockname=blockname, max_floor=max_floor,
                                     avg_price=avg_price, max_price=max_price, max_price_floor=max_price_floor,
                                     min_price=min_price, min_price_floor=min_price_floor,
                                     room_types=str(room_types), soldout=sold_out)
            session.add(new_blcok)
            # 提交事务
            session.commit()

        if len(bt_found) == 0:
            if sold_count == 0 and left_count == 0:
                pass
            else:
                new_track = Block_Track(projectid=projectid, buildingid=buildingid, sold=sold_count, left=left_count)
                session.add(new_track)
                # 提交事务
                session.commit()
    session.close()


if __name__ == "__main__":
    run_day = datetime.date.today()
    time_limit = 3
    engine = create_engine(cfg.MYSQL_URI,
                           pool_pre_ping=True,
                           max_overflow=0,  # 超过连接池大小外最多创建的连接
                           pool_size=400,  # 连接池大小
                           pool_timeout=36000,  # 池中没有线程最多等待的时间，否则报错
                           pool_recycle=-1  # 多久之后对线程池中的线程进行一次连接的回收（重置）
                           )
    DBSession = sessionmaker(bind=engine)
    regex_str = "^[\u4E00-\u9FA5]{1,10}[（(]([0-9]{4})[）)][\u4E00-\u9FA5]{1,10}[（(]([0-9]{1,5})[)）]"

    session = DBSession()
    rc_found = session.query(Run_Control).filter(Run_Control.run_day == run_day).first()
    if rc_found is None:
        rc_time = 1
        new_rc = Run_Control(run_day=run_day,run_status="R",start_time=datetime.datetime.now(),\
                             end_time=None,cur_minrow=1,cur_maxrow=21,time=rc_time)
        session.add(new_rc)
        session.commit()
        letsgoA = True
        letsgoB = True
        payloadData = {"siteid": "", "useType": "1", "areaType": "", "entName": "", "location": "",
                       "minrow": "1", "maxrow": "21", "projectname": ""}
    else:
        rc_time = rc_found.time
        if rc_found.run_status == "C" and rc_found.time == time_limit:
            letsgoA = False
            letsgoB = False
        elif rc_found.run_status == "F":
            letsgoA = False
            letsgoB = True
        elif rc_found.run_status == "R" or rc_found.time < time_limit:
            cur_minrow = rc_found.cur_minrow
            cur_maxrow = rc_found.cur_maxrow
            letsgoA = True
            letsgoB = True
            payloadData = {"siteid": "", "useType": "1", "areaType": "", "entName": "", "location": "",
                           "minrow": str(cur_minrow), "maxrow": str(cur_maxrow), "projectname": ""}
    session.close()

    while letsgoA:
        found = False
        rc, a = getblocks(payloadData)
        thread_list = []
        for i in a:
            t = threading.Thread(target=process_block, args=(i,))
            thread_list.append(t)
        for t in thread_list:
            t.start()
            t.join()

        session = DBSession()
        if len(a) == 0:
            session.query(Run_Control).filter(Run_Control.run_day == run_day). \
                update({"run_status":"F", "end_time":datetime.datetime.now()})
            session.commit()
            break

        payloadData["minrow"] = str(int(payloadData["minrow"]) + 20)
        payloadData["maxrow"] = str(int(payloadData["maxrow"]) + 20)
        session.query(Run_Control).filter(Run_Control.run_day == run_day).\
            update({"cur_minrow":int(payloadData["minrow"]),"cur_maxrow":int(payloadData["maxrow"])})
        session.commit()
        session.close()
        time.sleep(1)

    sqlb = '''
    select buildingid,projectname
    from block_detail
    where buildingid not in (select buildingid
                             from block_track
                             where date(scan_datetime) = CURRENT_DATE)
      and buildingid not in (select a.buildingid
                             from (select buildingid,max(scan_datetime) as max_scan_datetime
                                   from block_track
                                   group by buildingid) as a
                             where a.max_scan_datetime < date_add(now(), interval - 20 day))
      and soldout = 'N'
                '''
    session = DBSession()
    if letsgoB:
        house_found = False
        cursor1 = session.execute(sqlb)
        b = cursor1.fetchall()
        proj_buil_id_list = []
        projectname_list = []
        for bb in b:
            proj_buil_id_list.append(bb.buildingid)
            projectname_list.append(bb.projectname)

        projectname_set = set(projectname_list)
        for pn in projectname_set:
            payloadData = {"siteid": "", "useType": "1", "areaType": "", "entName": "", "location": "",
                           "minrow": "1", "maxrow": "21", "projectname": pn}
            rc, bns = getblocks(payloadData)
            for bn in bns:
                if bn["buildingid"] in proj_buil_id_list:
                    sold_count = 0
                    left_count = 0
                    rc, rjs = getRoomJson(bn["buildingid"])
                    for rj in rjs:
                        if rj["use"] == "成套住宅":
                            house_found = True
                            if rj["roomstatus"] in ["网签", "认购"]:
                                sold_count = sold_count + 1
                            elif rj["pid"] == 0:
                                left_count = left_count + 1

                    if left_count == 0 and sold_count > 0:
                        sold_out = 'Y'
                        session.query(Block_Detail).filter(Block_Detail.buildingid == bn["buildingid"]). \
                            update({"soldout": sold_out})
                        session.commit()
                    else:
                        sold_out = 'N'

                    new_track = Block_Track(buildingid=bn["buildingid"], sold=sold_count,
                                            left=left_count)
                    session.add(new_track)
                    # 提交事务
                    session.commit()

        if not house_found:
            if rc_time == time_limit:
                session.query(Run_Control).filter(Run_Control.run_day == run_day). \
                    update({"run_status": "C", "end_time": datetime.datetime.now()})
                session.commit()
            else:
                session.query(Run_Control).filter(Run_Control.run_day == run_day). \
                    update({"run_status": "R", "end_time": datetime.datetime.now(),
                            "cur_minrow":1, "cur_maxrow":21, "time": rc_time+1})
                session.commit()

    # 关闭session
    session.close()
