# -*- coding:utf-8 -*-
from flask import Flask,session
import requests
import json
import base64
import time
#创建项目
app = Flask(__name__)
#session密钥
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#手机userAgent
mobileUA ='Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'
#电脑userAgent
PCUA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
#session flask的session 是写在客户端的
netSession = requests.session()
#selenium 驱动
driver = None
#所有移动api
urls = {
    'getRdmdAndCaptchaCode':'https://login.10086.cn/captchazh.htm?type=05',
    'checkNum':'https://login.10086.cn/chkNumberAction.action',
    'sendRequestForVerifyTextCode':'https://login.10086.cn/sendRandomCodeAction.action',
    'getNumArea':'http://touch.10086.cn/i/v1/res/numarea/',
    'getPersonInfo':'http://touch.10086.cn/i/v1/cust/info/',
    'getArtifact':'https://login.10086.cn/login.htm',
    'getTHXDData':'https://shop.10086.cn/i/v1/fee/detailbillinfojsonp/',
    'sendTemporaryIDRandomCode':'https://shop.10086.cn/i/v1/fee/detbillrandomcodejsonp/',
    'sendTemporaryIDRandomImage':'http://shop.10086.cn/i/authImg',
    'authTemporaryID':'https://shop.10086.cn/i/v1/fee/detailbilltempidentjsonp/',
}
#本项目错误映射
errorCode = {
    '100000':u'参数错误',
    '100001':u'非移动电话号码',
    '100002':u'验证码发送失败',
    '100003':u'获得assertAcceptURL，artifact失败',
    '100004':u'没有登录信息',
    '100005':u'cookies获取不全',
    '100006':u'无有效用户名',
    '100007':u'未登录,请完成之前登录步骤',
    '100008':u'rd和cc的session未写入',
    '100009':u'个人信息获取失败',
    '100010':u'号码信息获取失败',
    '100011':u'临时身份认证失败',
    '100012':u'短信验证码与图片验证码发送失败',
    '100013':u'获取通话详单失败',
    '100014':u'无有效服务密码',
}
#成功代码映射
successCode = {
    '110001':u'发送成功，请等待接收',
    '110002':u'认证成功',
    '110003':u'获取成功',
    '110004':u'临时身份认证成功',
    '110005':u'短信验证码与图片验证码发送完毕，如未收到，请稍后刷新本页面',
    '110006':u'获取通话详单成功',
}
#其他可以汇编的参数
otherParams = {
    'channelID':'12014',
    'type':'01'
}
#请求头
headers = {
            'accept': "application/json, text/javascript, */*; q=0.01",
            'accept-encoding':'gzip,deflate,br',
            'accept-language':'zh-CN, zh;q = 0.8',
            'Connection':'keep-alive',
            'user-agent':mobileUA,#'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
            'referer':'https://login.10086.cn/html/login/touch.html',
            'x-requested-With':'XMLHttpRequest',
            'cache-control': "no-cache",
            'Upgrade-Insecure-Requests':'1',

}
#获得captchaCode cookie  否则无法得到个人信息
def getRdmdAndCaptchaCode(netSession,headers):
    global urls
    netSession.get(urls['getRdmdAndCaptchaCode'],headers=headers)
    return netSession.cookies.get_dict()
#检查电话号码是否为移动
def checkNum(userName,headers):
    global urls
    playload = {'userName':userName}
    response = requests.request('POST',urls['checkNum'],data=playload, headers=headers)
    if response.text == 'true':
        cookies=response.cookies.get_dict()
        return {'code':1,'cookies':cookies}
    else:
        return {'code':0,}
#发送验证码
def sendRequestForVerifyTextCode(userName,headers,channelID,type):
    global urls
    playload = {'userName':userName,'type':type,'channelID':channelID}
    response = requests.request('POST',urls['sendRequestForVerifyTextCode'],data=playload,headers=headers)
    if not bool(int(response.text)):
        return {'code':1,'cookies':response.cookies.get_dict()}
    else:
        return {'code':0,}
#获得jsessionid-echd-cpt-cmcc-jt和ssologinprovince cookie
def auth(artifact,assertAcceptURL,cookies,netSession):
    global headers
    playload = {'backUrl':'http://touch.10086.cn/i/mobile/home.html','artifact':artifact}
    response = netSession.get(assertAcceptURL,params=playload,headers=headers,cookies=cookies)
    response.encoding='utf-8'
    return netSession.cookies.get_dict()
#移动的变态时间
def getTime():
    timeStamp = str(time.time()).split('.')[1][:3]
    return (time.strftime("%Y")+str(int(time.strftime('%m')))+str(int(time.strftime('%d')))+time.strftime('%H')+time.strftime('%M')+time.strftime('%S')+timeStamp)
#获得手机号的信息
def getNumArea(netSession,cookies,headers):
    global urls
    getNumAreaUrl = urls['getNumArea']+session['username']
    playload = {'time':getTime(),'channel':'02'}
    response = netSession.get(getNumAreaUrl,params=playload,cookies=cookies,headers=headers)
    session['cookies'] = netSession.cookies.get_dict()
    return response.text
#获得个人信息（包括手机号信息）
@app.route('/getPersonInfo')
def getPersonInfo():
    global netSession
    global successCode
    global errorCode
    global headers
    global urls
    if 'username' not in session.keys():
        return json.dumps({'code':'100006','errorMsg':errorCode['100006']},ensure_ascii=False)
    if 'cookies' not in session.keys():
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
    getPInfoUrl = urls['getPersonInfo']+session['username']
    if session['isLogin'] and 'cookies' in session.keys():
        playload = {'time':getTime(),'channel':'02'}
        response = netSession.get(getPInfoUrl,params=playload,headers=headers,cookies=session['cookies'])
        response.encoding='utf-8'
        pInfo = json.loads(response.text)
        if 'retCode' not in pInfo.keys() and pInfo['reCode'] != '000000':
            return json.dumps({'code':'100009','errorMsg':errorCode['100009'],'realMsg':response.text},ensure_ascii=False)

        numInfoText=getNumArea(netSession,session['cookies'],headers)
        numInfo = json.loads(numInfoText)
        if 'retCode' not in numInfo.keys() and numInfo['reCode'] != '000000':
            return json.dumps({'code':'100010','errorMsg':errorCode['100010'],'realMsg':numInfoText},ensure_ascii=False)
        personInfo = dict(pInfo['data'],**numInfo['data'])
        return json.dumps({'code':'110003','Msg':successCode['110003'],'data':personInfo},ensure_ascii=False)
    else:
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
#退出（包括，自身session清空和网络session的重置，如果登录，退出移动登录）
@app.route('/quitQuery')
def quitQury():
    global headers
    global PCUA
    global errorCode
    global netSession
    selfHeaders = headers
    session.pop('username',None)
    session.pop('cookies',None)
    session.pop('isLogin',None)
    netSession =''
    netSession = requests.session()
    return '退出成功'
    # if 'isLogin' in session.keys() and session['isLogin'] is True:
    #     logOutUrl = 'http://shop.10086.cn/i/v1/auth/userlogout'
    #     playload = {'_':str(int(round(time.time() * 1000)))}
    #     selfHeaders['Referer'] = 'http://shop.10086.cn/i/?welcome='+str(int(round(time.time() * 1000))-1000)
    #     selfHeaders['User-Agent'] = PCUA
    #     response = requests.request('GET',logOutUrl,params=playload,cookies=session['cookies'],headers=selfHeaders)
    #     print(response.cookies.get_dict())
    #     return response.text
    # else:
    #     return json.dumps({'code':'100004','errorMsg':errorCode['100004']},ensure_ascii=False)
#通过用户名给客户发送验证码
@app.route('/giveBackTextCode/<userName>')
def giveBackTextCode(userName):
    global headers
    global errorCode
    global successCode
    global otherParams
    global netSession
    cookies = getRdmdAndCaptchaCode(netSession,headers=headers)
    if 'CaptchaCode' not in cookies.keys() and 'rdmdmd5' not in cookies.keys():
        return json.dumps({'code': '100008', 'errorMsg': errorCode['100008']}, ensure_ascii=False)
    if userName == '':
        return json.dumps({'code':'100000','errorMsg':errorCode['100000']},ensure_ascii=False)
    session['username'] = userName
    session['cookies'] = netSession.cookies.get_dict()
    isNum = checkNum(userName,headers)
    if not bool(int(isNum['code'])):
        session.pop('username',None)
        return json.dumps({'code':'100001','errorMsg':errorCode['100001']},ensure_ascii=False)

    isSend = sendRequestForVerifyTextCode(userName,headers,otherParams['channelID'],otherParams['type'])

    if not bool(int(isSend['code'])):#2是短信下发已到达上限
        return json.dumps({'code':'100002','errorMsg':errorCode['100002']},ensure_ascii=False)

    return json.dumps({'code':'110001','Msg':successCode['110001']},ensure_ascii=False)
#通过随机短信码和服务密码，去移动进行验证
@app.route('/authLogin/<servicepassword>/<textCode>')
def getArtifact(servicepassword,textCode):
    global errorCode
    global successCode
    global headers
    global otherParams
    global netSession
    global urls
    if servicepassword =='' or textCode =='':
        return json.dumps({'code':'100000','errorMsg':errorCode['100000']})
    if 'username' not in session.keys():
        return json.dumps({'code':'100006','errorMsg':errorCode['100006']},ensure_ascii=False)
    if 'cookies' not in session.keys():
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
    session['servicepassword'] = servicepassword
    playload = {
                'accountType':otherParams['type'],
		        'account':session['username'],
		        'password':servicepassword,
		        'pwdType':'01',
		        'smsPwd':textCode,
		        'inputCode':'',
		        'backUrl':'',
		        'rememberMe':0,
		        'channelID':otherParams['channelID'],
		        'protocol':'https:',
		        'timestamp':str(int(round(time.time() * 1000)))
    }
    response = netSession.get(urls['getArtifact'],params=playload,headers=headers)
    responseDic = json.loads(response.text)
    if 'artifact' in responseDic.keys() and 'assertAcceptURL' in responseDic.keys():

        session['cookies'] = netSession.cookies.get_dict()
        assertAcceptURL = responseDic['assertAcceptURL']
        artifact = responseDic['artifact']
        authUrl = assertAcceptURL+'?backUrl=http://touch.10086.cn/i/mobile/home.html&artifact='+artifact
        print(authUrl)
        print(netSession.cookies.get_dict())
        cookie = auth(artifact,assertAcceptURL,session['cookies'],netSession)
        if 'jsessionid-echd-cpt-cmcc-jt' in cookie.keys() and 'ssologinprovince' in cookie.keys():
            print(netSession.cookies.get_dict())
            session['isLogin'] = True
            session['cookies'] = cookie
            return json.dumps({'code':'110002','Msg':successCode['110002'],'realMsg':responseDic['desc']},ensure_ascii=False)
        else:
            session['isLogin'] = False
            return json.dumps({'code': '100005', 'errorMsg': errorCode['100005']},ensure_ascii=False)
    else:
        session.pop('servicepassword',None)
        return json.dumps({'code':'100003','errorMsg':errorCode['100003'],'realMsg':responseDic['desc']},ensure_ascii=False)

#临时身份验证
@app.route('/temporaryPIAuth/<randomCode>/<randomImage>')
def authTemporaryID(randomCode,randomImage):
    global netSession
    global headers
    global PCUA
    global successCode
    global errorCode
    if randomCode =='' or randomImage == '':
        return json.dumps({'code': '100000', 'errorMsg': errorCode['100000']}, ensure_ascii=False)
    if 'username' not in session.keys():
        return json.dumps({'code':'100006','errorMsg':errorCode['100006']},ensure_ascii=False)
    if 'cookies' not in session.keys():
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
    if 'servicepassword' not in session.keys():
        return json.dumps({'code': '100014', 'errorMsg': errorCode['100014']}, ensure_ascii=False)
    servicePasswordBase64 = base64.b64encode(session['servicepassword'].encode(encoding='utf-8')).decode()
    randomCodeBase64 = base64.b64encode(randomCode.encode(encoding='utf-8')).decode()
    playLoad={
        'pwdTempSerCode': servicePasswordBase64,
        'pwdTempRandCode': randomCodeBase64,
        'captchaVal': randomImage,
        '_': str(int(round(time.time() * 1000))),
    }
    response = netSession.get(urls['authTemporaryID']+session['username'],params=playLoad,headers=headers,cookies=session['cookies'])
    #null({"data": null, "retCode": "000000", "retMsg": "认证成功!", "sOperTime": null})
    try:
        result = response.text[4:].lstrip('(').rstrip(')')
        resultDic = json.loads(result)
        if resultDic['retCode'] == '000000':
            session['cookies'] = netSession.cookies.get_dict()
            return json.dumps({'code': '110004', 'Msg': successCode['110004'],'realMsg':resultDic['retMsg']}, ensure_ascii=False)
        else:
            return json.dumps({'code': '100011', 'errorMsg': errorCode['100011'],'realMsg':resultDic['retMsg']}, ensure_ascii=False)
    except:
        return json.dumps({'code': '100011', 'errorMsg': errorCode['100011'], 'realMsg': response.text},ensure_ascii=False)

#发送临时身份验证码和图片
@app.route('/prepareAuth')
def prepareAuth():
    global urls
    global headers
    global netSession
    if 'username' not in session.keys():
        return json.dumps({'code':'100006','errorMsg':errorCode['100006']},ensure_ascii=False)
    if 'cookies' not in session.keys():
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
    userName = session['username']
    code = sendTemporaryIDRandomCode(netSession,urls['sendTemporaryIDRandomCode'],userName,headers,session['cookies'])
    image = sendTemporaryIDRandomImage(netSession,urls['sendTemporaryIDRandomImage'],headers,session['cookies'])
    if code is True and image is True:
        return json.dumps({'code': '110005', 'Msg': successCode['110005'],},ensure_ascii=False)
    else:
        return json.dumps({'code': '100012', 'errorMsg': errorCode['100012'],},ensure_ascii=False)
#发送临时身份验证短信码
def sendTemporaryIDRandomCode(netSession,url,userName,headers,cookies):
    global PCUA
    playLoad = { '_': str(int(round(time.time() * 1000)))}
    headers['referer'] = 'http://shop.10086.cn/i/?welcome='+str(int(round(time.time() * 1000))-1000)
    headers['user-agent'] = PCUA
    response = netSession.get(url+userName,params=playLoad,headers=headers,cookies=cookies)
    result = response.text[4:].lstrip('(').rstrip(')')
    resultDic = json.loads(result)
    if resultDic['retCode'] == '000000':
        return True
    else:
        print(resultDic['retMsg'])
        return False
#发送验证图片
def sendTemporaryIDRandomImage(netSession,url,headers,cookies):
    global PCUA
    playLoad = {'t':'0.646509821274071'}
    headers['referer'] = 'http://shop.10086.cn/i/?welcome=' + str(int(round(time.time() * 1000)) - 1000)
    headers['user-agent'] = PCUA
    response = netSession.get(url, params=playLoad, headers=headers, cookies=cookies,stream=True)
    #print(response.text)
    try:
        f = open('./code.png','wb')
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
            f.flush()
        f.close()
        return True
    except:
        return False

 # 获取详单数据
def getTHXDData(url,netSession,headers,timeStr,curor,step):
    playLoad = {
        'curCuror': curor,
        'qryMonth': timeStr,
        'step': step,
        'billType': '02',
        '_': str(int(round(time.time() * 1000))+1000)
    }
    response = netSession.get(url + session['username'], params=playLoad, headers=headers,
                              cookies=session['cookies'])
    try:
        resultStr = response.text[4:].lstrip('(').rstrip(')')
        result = json.loads(resultStr)
        if result['retCode'] != '000000':
            print(result['retMsg'])
            return {'data':None,'msg':result['retMsg']}
        else:
            return {'data':result,'msg':'success'}
    except:
        print(response.text)
        return {'data':None,'msg':response.text}
#获得近六个月的通话详单数据
@app.route('/getTHXD')
def getAllTHXDData():
    global headers
    global urls
    global PCUA
    global errorCode
    global successCode
    if 'username' not in session.keys():
        return json.dumps({'code':'100006','errorMsg':errorCode['100006']},ensure_ascii=False)
    if 'cookies' not in session.keys():
        return json.dumps({'code':'100007','errorMsg':errorCode['100007']},ensure_ascii=False)
    thisHeaders = headers
    thisHeaders['referer'] = 'http://shop.10086.cn/i/?welcome=' + str(int(round(time.time() * 1000)) - 1000)
    thisHeaders['user-agent'] = PCUA
    currentTime = int(time.strftime('%Y%m'))
    timeList=[]
    for i in range(6):
        timeList .append(str(currentTime-i))
    allData={}
    errMsg={}
    for item in timeList:
        result = getTHXDData(urls['getTHXDData'],netSession,thisHeaders,item,1,500)
        if result['data'] is not None:
            if int(result['data']['totalNum']) > 500:
                moreData = getTHXDData(urls['getTHXDData'],netSession,thisHeaders,item,501,int(result['data']['totalNum'])-500)
                if moreData['data'] is not None:
                    result['data']['data'].extend(moreData['data']['data'])
            allData[item] = result['data']['data']
        else:
            errMsg[item] = result['msg']
    if allData == {}:
        return json.dumps({'code':'100013','data':allData,'errorMsg':errorCode['100013'],'realMsg':errMsg},ensure_ascii=False)
    else:
        return json.dumps({'code':'110006','data':allData,'Msg':successCode['110006']},ensure_ascii=False)

#开启项目
if __name__ == '__main__':
    app.run(debug=True)
