from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from werkzeug.utils import secure_filename
import os
import time
import sqlite3
import json
import sys
import qrcode
import hashlib
import numpy as np
import pyzbar.pyzbar as pyzbar
from random import randint
from PIL import Image
from datetime import timedelta

from gevent import pywsgi

# 设置允许的文件格式
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp', 'BMP'])
time_last = ""
webpath = "ellye.cn:8987"
localpath = "127.0.0.1:8987"
tag_wl = 0
# tag_wl用于控制使用本地路径还是服务器路径进行访问 1代表local 0代表web
# 根据字符串得到图片

AllData_fp = open('AllData.json', encoding='utf-8')
AllData = json.load(AllData_fp)
AllData_fp.close()
con = sqlite3.connect(AllData['DataBaseName'], check_same_thread=False)
cursor = con.cursor()


#---------------------------------------------#
# AllData.json   :{DataBaseName:,TableName:,Columns:}
#在已经打开数据库的情况下查验数据表，无则创建
def GetAllTable():
    try:
        #cursor.execute(f"PRAGMA table_info({tablename})")
        cursor.execute("select name from sqlite_master where type=='table'")
        result = list(map(lambda x: x[0], cursor.fetchall()))
    except Exception as e:
        # print(repr(e))
        return None
    else:
        return result


def CreateTable(tablename, columns):
    order = f"CREATE TABLE {tablename} ("
    p = ','.join(list(map(lambda x: f"{x[0]} {x[1]} not null", list(columns.items()))))
    order = order + p + ");"
    try:
        cursor.execute(order)
        con.commit()
    except Exception as e:
        con.rollback()
        print(repr(e))
        print("Create Fail")
        return 0
    else:
        print("Create Succeed")
        return 1


def DeleteTable(tablename):
    try:
        cursor.execute(f"DROP TABLE {tablename}")
        con.commit()
    except Exception as e:
        con.rollback()
        print("Delete Fail")
        return 0
    else:
        print("Delete Succeed")
        return 1


def CheckTable(tablename, columns):
    try:
        cursor.execute(f"PRAGMA table_info({tablename})")
        result = dict(map(lambda x: (x[1], x[2]), cursor.fetchall()))
    except Exception as e:
        # print(repr(e))
        return None
    else:
        return result == columns


def InitTable(AllData):
    result = GetAllTable()
    if result == None:
        print("发生未知错误,在库中查找数据表失败")
        sys.exit()
    elif AllData['TableName'] not in result:
        CreateTable(AllData['TableName'], AllData['Columns'])
    else:
        answer = CheckTable(AllData['TableName'], AllData['Columns'])
        if answer == None:
            print("发生未知错误,数据表信息查询失败")
            sys.exit()
        elif answer == False:
            DeleteTable(AllData['TableName'])
            CreateTable(AllData['TableName'])


def InsertTable(tablename, values):
    a = "INSERT INTO {} VALUES {};".format(tablename, values)
    try:
        cursor.execute(a)
        con.commit()
    except Exception as e:
        print(repr(e))
        print("Insert Fail")
        con.rollback()
        return 0
    else:
        print("Insert Succeed")
        return 1


def CheckValue(tablename, value, column):
    a = "select * from {} where {} == '{}'".format(tablename, column, value)
    try:
        cursor.execute(a)
        result = cursor.fetchall()
    except Exception as e:
        print(repr(e))
        return 0
    else:
        return len(result)


def getHash(string, encoding='utf-8'):
    return hashlib.sha256(string.encode(encoding)).hexdigest()


def make(url, name):
    if len(url) < 1 or len(url) > 1024:
        return ""
    else:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=20, border=0)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        # 图片保存至指定路径
        img.save("./static/images/" + name + ".png")
        #img.save("./static/images/" + hashlib.sha256(url.encode("utf-8")).hexdigest)
        return img


# (Image对象)从图片中读取二维码并返回字符串


def get_code_data(img):
    if isinstance(img, np.ndarray) == True:
        img = Image.fromarray(img.astype(np.uint8))
    img = img.convert('L')
    DataList = list()
    DataDict = dict()
    barcodes = pyzbar.decode(img)
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
        barcoderect = barcode.rect
        DataList.append(barcoderect)
        DataDict[barcoderect] = barcodeData
    if len(DataList) == 0:
        return ""
    FirstCode = DataList[0]
    for i in DataList:
        if i.top < FirstCode.top:
            FirstCode = i
        elif i.top == FirstCode.top:
            if i.left < FirstCode.left:
                FirstCode = i
    '''if 'http://' not in DataDict[FirstCode] and 'https://' not in DataDict[FirstCode]:
      DataDict[FirstCode] = 'http://'+DataDict[FirstCode]'''
    return DataDict[FirstCode]


# 图像转矩阵


def ImageToMatrix(im):
    width, height = im.size
    im = im.resize((width // 20, height // 20), Image.ANTIALIAS)
    im = im.convert('L')  # 灰度化
    width, height = im.size
    data = im.getdata()
    data = np.matrix(data, dtype='float') / 255
    new_data = np.reshape(data, (height, width))
    new_data = np.array(new_data)
    new_data = new_data - 1
    new_data[new_data < 0] = 1
    return new_data


# 矩阵转图像


def MatrixToImage(data):
    data = 1 - data
    data = data * 255
    h, w = data.shape
    new_data = np.zeros((h * 20, w * 20))
    for i in range(0, h * 20):
        for j in range(0, w * 20):
            new_data[i][j] = data[i // 20][j // 20]
    new_im = Image.fromarray(new_data.astype(np.uint8))
    return new_im


# 从指定路径中获取制作样式和背景


def get_src(filename):
    files = os.listdir(filename)
    src = dict()
    file = list()
    k = [str(i) for i in range(0, 10000)]
    background = ""
    for i in files:
        if '.' in i:
            file.append(i)
    for i in file:
        index = i.index('.')
        suf = i[index + 1:]
        if suf == 'png':
            if len(background) == 0 and i[:2] == 'bg':
                background = i
            elif len(i[:index]) != 5:
                continue
            else:
                l = i[:index].split('_')
                if len(l) == 3 and l[0] in k and l[1] in k and l[2] in k:
                    h, w = int(l[1]), int(l[0])
                    if (h, w) in src.keys():
                        src[(h, w)] += 1
                    else:
                        src[(h, w)] = 1
    return src, background


# 去除三个矫正点


def notreco(visit, const):
    for i in range(0, const):
        for j in range(0, const):
            visit[i][j] = 0
            visit[i][visit.shape[1] - 1 - j] = 0
            visit[visit.shape[0] - 1 - i][j] = 0


# 判断在连通域内


def inarea(visit, queue, area, i, j):
    queue.append((i, j))
    area.append((i, j))
    visit[i][j] = 0


# 查找连通域


def bfs(visit, i, j):
    area = list()
    queue = list()
    inarea(visit, queue, area, i, j)
    while len(queue) > 0:
        x, y = queue.pop(0)
        a1 = max(0, x - 1)
        a2 = min(x + 1, visit.shape[0] - 1)
        b1 = max(y - 1, 0)
        b2 = min(y + 1, visit.shape[1] - 1)
        a, b = a1, b1
        while a <= a2:
            while b <= b2:
                if a == x or b == y:
                    if visit[a][b] == 1:
                        inarea(visit, queue, area, a, b)
                b = b + 1
            a = a + 1
            b = b1
    return area


# 获取连通域


def get_matrix_con(data, const):
    visit = np.array(data)
    notreco(visit, 7)
    h, w = visit.shape
    conare = list()
    area = list()
    for i in range(0, h):
        for j in range(0, w):
            if visit[i][j] == 1:
                conare.append(bfs(visit, i, j))
    return conare


# 连通域分类


def itemcon(conare, srclist, data):
    new_data = np.array(data)
    pre_visit = sorted(srclist.keys(), key=lambda d: d[0] * d[1], reverse=True)
    arehead = {i: list() for i in pre_visit}
    for i in conare:
        visit = pre_visit.copy()
        while len(visit) > 1:
            find_num = 0
            for j in i:
                h, w = j
                run = True
                while (run):
                    for x in range(0, visit[0][0]):
                        for y in range(0, visit[0][1]):
                            if (h + x, w + y) not in i:
                                run = False
                        if (x + 1, y + 1) == visit[0]:
                            break
                    if run == True:
                        find_num += 1
                        arehead[visit[0]].append(j)
                        for x in range(0, visit[0][0]):
                            for y in range(0, visit[0][1]):
                                new_data[h + x][w + y] = pre_visit.index(visit[0]) + 2
                                i.pop(i.index((h + x, w + y)))
            if find_num == 0:
                visit.pop(0)
        if len(i) > 0:
            for j in i:
                h, w = j
                arehead[visit[0]].append(j)
                new_data[h][w] = pre_visit.index(visit[0]) + 2
    return new_data, arehead


# 指定矫正点颜色


def reco(r, g, b):
    reco = np.zeros((140, 140, 3))
    for i in range(0, 140):
        for j in range(0, 140):
            a, c = i // 20, j // 20
            if (a > 0 and a < 6 and (c == 1 or c == 5)) or (c > 0 and c < 6 and (a == 1 or a == 5)):
                reco[i][j] = (255, 255, 255)
            else:
                reco[i][j] = (r, g, b)
    reco = Image.fromarray(reco.astype(np.uint8))
    return reco


# 制作艺术二维码


def autoclear(path, date):
    files = os.listdir(path)
    for i in files:
        name, suf = os.path.splitext(i)
        if suf == ".png":
            if name[:8] != date:
                os.remove(path + i)


def allclear(date):
    autoclear("./static/new/", date)


def artqrcode(filename, img_path, name):
    img = Image.open(img_path)
    url = get_code_data(img)
    img = make(url, name)
    data = ImageToMatrix(img)
    conare = get_matrix_con(data, 7)
    srclist, background = get_src(filename)
    if len(srclist) == 0:
        img = MatrixToImage(data)
        h, w = img.size
        h, w = 300 * h // w, 300
        small = img.resize((h, w))
        h, w = img.size
        h_m, w_m = max(h, w), min(h, w)
        h_m, w_m = 800, (800 * w_m) // h_m
        d = 2 * (h >= w) - 1
        h, w = (h_m, w_m)[::d]
        big = img.resize((h, w))
        temp = filename.split("/")
        big.save("./static/new/" + temp[-2] + '/' + name + "_big.png")
        small.save("./static/new/" + temp[-2] + '/' + name + "_small.png")
        return img
    new_data, arehead = itemcon(conare, srclist, data)
    imgx = dict()
    for i in srclist.keys():
        for j in range(1, srclist[i] + 1):
            imgx[(i, j)] = Image.open(filename + "%d_%d_%d.png" % (i[1], i[0], j))
    h, w = data.shape
    all_im = Image.new("RGB", (h * 20, w * 20), "#FFFFFF")
    for i, j in arehead.items():
        for sub in j:
            h, w = sub
            imgk = imgx[(i, randint(1, srclist[i]))].convert("RGBA")
            imgk = imgk.resize((i[1] * 20, i[0] * 20))
            all_im.paste(imgk, (w * 20, h * 20), imgk)
    h, w = data.shape
    if len(background) == 0:
        h, w = data.shape
        back = Image.new("RGB", (h * 20, w * 20), "#FFFFFF")
        x, y, l, k, r, g, b = 0, 0, h * 20, w * 20, 255, 96, 0
    else:
        back = Image.open(filename + background)
        x = background.split('.')[0]
        x, y, l, r, g, b = x.split("_")[1:]
        x, y, l = int(x), int(y), int(l)
        k, r, g, b = l, int(r), int(g), int(b)
    rec = reco(r, g, b)
    all_im.paste(rec, (0, 0))
    all_im.paste(rec, ((h - 7) * 20, 0))
    all_im.paste(rec, (0, (w - 7) * 20))
    all_im = all_im.resize((l, k))
    back.paste(all_im, (x, y))
    all_im = back
    h, w = all_im.size
    h, w = 300 * h // w, 300
    small = all_im.resize((h, w))
    h, w = all_im.size
    h_m, w_m = max(h, w), min(h, w)
    h_m, w_m = 800, (800 * w_m) // h_m
    d = 2 * (h >= w) - 1
    h, w = (h_m, w_m)[::d]
    big = all_im.resize((h, w))
    temp = filename.split("/")
    big.save("./static/new/" + temp[-2] + '/' + name + "_big.png")
    small.save("./static/new/" + temp[-2] + '/' + name + "_small.png")
    return all_im


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


if len(time_last) == 0:
    time_last = time.strftime("%Y%m%d", time.localtime())
    allclear(time_last)

app = Flask(__name__)
# 设置静态文件缓存过期时间
app.send_file_max_age_default = timedelta(seconds=1)
app.config['JSON_AS_ASCII'] = False


@app.route('/', methods=['POST', 'GET'])
def home():
    return redirect(url_for('index'), code=302)


@app.route('/index', methods=['POST', 'GET'])  # 添加路由
def index():
    time_stamp = int(time.time())
    time_array = time.localtime(time_stamp)
    __timearray = time.strftime("%Y%m%d%H%M%S", time_array)
    if (tag_wl == 1):
        path = localpath
    else:
        path = webpath
    if request.method == 'POST':
        #   ip从这里获取
        #ip =
        ip = '202.120.167.82'
        f = request.files['file']
        if not (f and allowed_file(f.filename)):
            return render_template('error.html', _path=path)
        basepath = os.path.dirname(__file__)  # 当前文件所在路径
        #upload_path = os.path.join(basepath, 'static/images', __timearray + '.png')
        #f.save(upload_path)
        img = Image.open(f)
        url = get_code_data(img)
        print(url)
        if (len(url) == 0):
            return render_template('error.html', _path=path)
        hashedurl = getHash(url)
        upload_path = os.path.join(basepath, 'static/images', hashedurl + '.png')
        img.save(upload_path)
        if CheckValue(AllData['TableName'], url, 'url'):
            pass
        else:
            artqrcode("./static/style/style_1/", upload_path, hashedurl)
            artqrcode("./static/style/style_2/", upload_path, hashedurl)
            artqrcode("./static/style/style_3/", upload_path, hashedurl)
            artqrcode("./static/style/style_4/", upload_path, hashedurl)
            artqrcode("./static/style/style_5/", upload_path, hashedurl)
            artqrcode("./static/style/style_6/", upload_path, hashedurl)
            artqrcode("./static/style/style_7/", upload_path, hashedurl)
            artqrcode("./static/style/style_8/", upload_path, hashedurl)
            artqrcode("./static/style/style_9/", upload_path, hashedurl)
            artqrcode("./static/style/style_10/", upload_path, hashedurl)
            artqrcode("./static/style/style_11/", upload_path, hashedurl)
            time_now = time.strftime("%Y%m%d", time.localtime())
            if time_now != time_last:
                allclear(time_now)
                timelast = time_now
        InsertTable(AllData['TableName'], (__timearray, url, hashedurl, ip))
        return render_template('upload_ok.html', userinput=url, val1=time.time(), hashedurl=hashedurl, _path=path)
    return render_template('index.html', _path=path)


@app.route('/index2', methods=['POST', 'GET'])  # 添加路由
def index2():
    time_stamp = int(time.time())
    time_array = time.localtime(time_stamp)
    __timearray = time.strftime("%Y%m%d%H%M%S", time_array)
    if (tag_wl == 1):
        path = localpath
    else:
        path = webpath
    if request.method == 'POST':
        #   ip从这里获取
        #ip =
        ip = '220.126.45.43'
        user_input = request.form.get("name")
        hashedurl = getHash(user_input)
        img = make(user_input, hashedurl)
        basepath = os.path.dirname(__file__)  # 当前文件所在路径
        upload_path = os.path.join(basepath, 'static/images', hashedurl + '.png')
        if CheckValue(AllData['TableName'], user_input, 'url'):
            pass
        else:
            artqrcode("./static/style/style_1/", upload_path, hashedurl)
            artqrcode("./static/style/style_2/", upload_path, hashedurl)
            artqrcode("./static/style/style_3/", upload_path, hashedurl)
            artqrcode("./static/style/style_4/", upload_path, hashedurl)
            artqrcode("./static/style/style_5/", upload_path, hashedurl)
            artqrcode("./static/style/style_6/", upload_path, hashedurl)
            artqrcode("./static/style/style_7/", upload_path, hashedurl)
            artqrcode("./static/style/style_8/", upload_path, hashedurl)
            artqrcode("./static/style/style_9/", upload_path, hashedurl)
            artqrcode("./static/style/style_10/", upload_path, hashedurl)
            artqrcode("./static/style/style_11/", upload_path, hashedurl)
            time_now = time.strftime("%Y%m%d", time.localtime())
            if time_now != time_last:
                allclear(time_now)
                timelast = time_now
        InsertTable(AllData['TableName'], (__timearray, user_input, hashedurl, ip))
        return render_template('upload_ok.html', userinput=user_input, val1=time.time(), hashedurl=hashedurl, _path=path)
    return render_template('index2.html', _path=path)


if __name__ == '__main__':
    InitTable(AllData)
    server = pywsgi.WSGIServer(('0.0.0.0', 8987), app)
    server.serve_forever()
    #app.debug = True
    #app.run(host='0.0.0.0', port=8987, debug=True)
