from flask import Blueprint,render_template,redirect,request,session,url_for,flash
from didaalarm import db,app
from .models import shiftplan,userlogin
import datetime,time
from Crypto.Cipher import AES 
from binascii import b2a_hex
bocdshift = Blueprint('bocdshift',__name__)

ALLOWED_EXTENSIONS = set(['csv'])
AES_KEY = b'\xe9>\xa9@\xcb\xcf\x19H\xa2\xe6Q\xbe\xc3\xbcKN'
KEEP_SESSTION_MINS = 10


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@bocdshift.route('/do',methods=['GET','POST'])
def do():
    if 'username' not in session:
        return redirect(url_for('.login'))
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            db.session.query(shiftplan).delete()
        else:
            return 'input error'
        for i in file:
            duty_date = ''
            shift = ''
            s = i.decode().split(",")
            if len(s) < 2:
                continue
            duty_date_a = s[0].lstrip(' ').rstrip(' ')
            shift = s[1].strip('\r\n').lstrip(' ').rstrip(' ')
            # duty_date = duty_date_a + ' 00:00:00'
            # wk = datetime.datetime.strptime(duty_date_a, '%Y-%m-%d').weekday()
            wk = time.strftime('%A', time.strptime(duty_date_a, '%Y-%m-%d'))
            newplan = shiftplan(duty_date=duty_date, cn_name=wk, shift=shift)
            db.session.add(newplan)
        db.session.commit()
        plans = shiftplan.query.all()
        flash('upload successfully', "info")
        return render_template('bocdshift/do.html',plans=plans)
        
    plans = shiftplan.query.all()
    return render_template('bocdshift/do.html',plans=plans)


@bocdshift.route('/', methods=['GET', 'POST'])
@bocdshift.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "username" not in session:
            return render_template('bocdshift/login.html')
        else:
            return render_template('bocdshift/logout.html',username=(session['username']))
    username = request.form['username']
    password = request.form['password']
    if not checkuserpass(username, password):
        if 'username' in session:
            session.pop('username', None)
        flash('Username or Password is invalid.', 'error')
        return render_template('bocdshift/login.html')
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=KEEP_SESSTION_MINS)
    session['username'] = username
    #flash('Logged in successfully', "info")
    return redirect(url_for('.do'))


def checkuserpass(username,password):
    pc = prpcrypt(AES_KEY)      #初始化密钥
    userdata = userlogin.query.filter_by(username=username).first()
    if userdata and userdata.password == pc.encrypt(password):
        return True
    else:
        return False


@bocdshift.route('/logout')        
def logout():
    session.pop('username', None)
    #time.sleep(0.001)
    return redirect(url_for('.login'))


class prpcrypt():
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC
     
    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        length = 16
        count = len(text)
        if(count % length != 0) :
            add = length - (count % length)
        else:
            add = 0
        text = text + ('\0' * add)
        ciphertext = cryptor.encrypt(text)
        return b2a_hex(ciphertext).decode()
