from didaalarm import db
import datetime

class shiftplan(db.Model):
    __tablename__ = 't_call_tmp_shiftplan'
    __bind_key__ = 'dida'
    duty_date = db.Column(db.DateTime, primary_key=True)
    cn_name = db.Column(db.String(255), unique=False)
    shift = db.Column(db.String(255), unique=False)

    def __repr__(self):
        return '<User %r>' % self.username


class userlogin(db.Model):
    __tablename__ = 'userlogin'
    __bind_key__ = 'dida'
    username = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255), unique=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Proxy_Ips(db.Model):
    __tablename__ = 'proxy_ips'
    ip_port = db.Column(db.String(255), primary_key=True)
    http_type = db.Column(db.String(255))
    location = db.Column(db.String(255))
    used_times = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)
    change_time = db.Column(db.DateTime, default=datetime.datetime.now)


#
#
# class Block_Detail(db.Model):
#     __tablename__ = 'queryhouse.block_detail'
#     projectid = db.Column(db.Integer, primary_key=True)
#     buildingid = db.Column(db.Integer, primary_key=True)
#     projectname = db.Column(db.VARCHAR(255))
#     enterprisename = db.Column(db.VARCHAR(255))
#     location = db.Column(db.VARCHAR(255))
#     presale_cert = db.Column(db.VARCHAR(255))
#     blockname = db.Column(db.VARCHAR(255))
#     max_floor = db.Column(db.Integer)
#     avg_price = db.Column(db.DECIMAL(10,2))
#     max_price = db.Column(db.DECIMAL(10,2))
#     max_price_floor = db.Column(db.VARCHAR(255))
#     min_price = db.Column(db.DECIMAL(10,2))
#     min_price_floor = db.Column(db.VARCHAR(255))
#     room_types = db.Column(db.VARCHAR(255))
#     soldout = db.Column(db.CHAR(1))
#     stamp = db.Column(db.DATETIME, default=datetime.datetime.now)
#
# class Block_Track(db.Model):
#     __tablename__ = 'queryhouse.block_track'
#     projectid = db.Column(db.Integer, primary_key=True)
#     buildingid = db.Column(db.Integer, primary_key=True)
#     scan_datetime = db.Column(db.DATETIME, primary_key=True, default=datetime.datetime.now)
#     sold = db.Column(db.Integer)
#     left = db.Column(db.Integer)
#
# class Run_Control(db.Model):
#     __tablename__ = 'queryhouse.run_control'
#     run_day = db.Column(db.DATE, primary_key=True)
#     run_status = db.Column(db.CHAR(1))
#     start_time = db.Column(db.DATETIME)
#     end_time = db.Column(db.DATETIME)
#     cur_minrow = db.Column(db.Integer)
#     cur_maxrow = db.Column(db.Integer)