#coding:utf-8
import requests,datetime
import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,func
from sqlalchemy.types import *
from bs4 import BeautifulSoup
import didaalarm.config as cfg

BaseModel = declarative_base()

class Proxy_Ips(BaseModel):
    __tablename__ = 'proxy_ips'
    ip_port = Column(VARCHAR(255), primary_key=True)
    http_type = Column(VARCHAR(255))
    location = Column(VARCHAR(255))
    used_times = Column(Integer)
    create_time = Column(DATETIME, default=datetime.datetime.now)
    change_time = Column(DATETIME, default=datetime.datetime.now)


def is_Chinese(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


if __name__ == "__main__":
    engine = create_engine(cfg.MYSQL_URI)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    rq1 = requests.get('https://www.xicidaili.com/wt/', headers=header)
    # print(rq1.text)
    bs1 = BeautifulSoup(rq1.text, 'lxml')
    tbody = bs1.find("table", attrs={'id': 'ip_list'})
    # print(tbody)
    data = [[td.get_text(strip=True) for td in tr.find_all('td', class_=False)] for tr in tbody.findChildren('tr')]
    # print(data)
    for d in data:
        ip = ''
        port = ''
        http_type = ''
        location = ''
        used_times = ''
        # create_time = datetime.datetime.now()
        # change_time = datetime.datetime.now()
        for dd in d:
            if len(dd.split('.')) == 4:
                ip = dd
            if dd.isnumeric():
                port = dd
            if 'HTTP' in dd:
                http_type = dd
            if is_Chinese(dd) and not dd[0].isnumeric():
                location = dd

        ip_port = ip+':'+port
        # print(ip_port)
        pi_found = session.query(Proxy_Ips).filter(Proxy_Ips.ip_port == ip_port).first()
        if pi_found is None and ip != '':
            new_pi = Proxy_Ips(ip_port=ip_port, http_type=http_type,location=location,used_times=0)
            session.add(new_pi)
            session.commit()
