#导入库
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException,NoSuchElementException,NoSuchAttributeException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from  selenium.webdriver.support import expected_conditions as EC
import time
import requests
import re
import json
from PIL import Image

#phantomjs配置
dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap['phantomjs.page.settings.loadImages'] = True
dcap["phantomjs.page.settings.userAgent"] = (
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
#'Mozilla/5.0 (Windows NT 6.1; rv:48.0) Gecko/20100101 Firefox/48.0'
)
#driver = webdriver.Chrome(executable_path = '/Users/slimdy/Downloads/chromedriver')
driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',desired_capabilities=dcap)
url = "https://login.10086.cn/login.html"
#验证是否需要验证码的url
verifyUrl = 'https://login.10086.cn/needVerifyCode.htm'
#脚本配置
try:
    errorHandle = open('error.log','a')
except IOError as error:
    print('WARING:无法打开 error.log----继续执行')
#错误截图存放地址
imagePath = '/Users/slimdy/Downloads/'
#验证码截图存放地址
verifyImagePath = '/Users/slimdy/Downloads/'


#获得用户验证码或者服务码，tip：提示语 method：登录方式
def verifyInputCode(tip,method=1):
    code = input(tip).strip()
    if method == 1:
        if code == '0':
            return False
        if code.isdigit():
            return code
        else:
            print_log("ERROR:验证码有误，退出")
            exit_close()
    elif method == 2:
        if code != '':
            return code
        else:
            print_log("ERROR:服务码有误或者验证码，退出")
            exit_close()


#写入用户名 userName ：用户手机  method：登录方式
def sendUserName(userName,method=1,isNeedVerify=False):
    global driver
    global isVerify
    try:
        if method == 1 :
            driver.find_element_by_id('radiobuttonSMS').click()
            driver.find_element_by_id('p_name').clear()
            driver.find_element_by_id('p_name').send_keys(userName)
            driver.find_element_by_id('getSMSpwd').click()
        else:
            driver.find_element_by_id('p_name').clear()
            driver.find_element_by_id('p_name').send_keys(userName)
            driver.find_element_by_id('p_pwd').click()
        print_log('写入用户名成功')
    except NoSuchElementException as noElement:
        print_log('ERROR:找不到元素，退出'+str(noElement))
        print_errorImage('error_find_sendUsername')
        exit_close()

#写入用户验证码或服务码
def sendCode(code1,code2=None):
    global driver
    try:
        driver.find_element_by_id('p_pwd').clear()
        driver.find_element_by_id('p_pwd').send_keys(code1)
        if code2 is not None:
            driver.find_element_by_id('sms_pwd').send_keys(code2)
        print_log('写入密码成功')
        driver.find_element_by_id('submit_bt').click()
        print_log('开始登陆')
    except :
        #print_log('ERROR:找不到元素，退出' + str(noElement))
        print_errorImage('error_find_sendCode')
        exit_close()

#登录是否成功
def isLoginSuccess():
    global driver
    global url
    count = 0
    while True:
        time.sleep(3)
        if driver.current_url == url:
            count += 1
            if count == 9:
                return False
            continue
        else:
            break
    return True
# 数据是否加载

def isLoaded(tableID,td):
    global driver
    breakFlag = True
    count = 0
    while True:
        time.sleep(3)
        try:
            table = driver.find_element_by_id(tableID)
            tdValues = table.find_elements_by_tag_name(td)
        except NoSuchElementException as noElement:
            print_log(tableID+'或者'+td+'找不到：'+str(noElement))
            print_errorImage('error_wait_'+tableID+'_'+td)
            exit_close()

        for tdValue in tdValues:
            if tdValue.text.strip() == '':
                continue
            else:
                breakFlag = False
                break
        if breakFlag == True:
            count += 1
            if count == 9:
                print_log('WARING:没有数据....可能是网络原因，也有可能是本身就没有数据')
                return  tdValues
            continue
        else:
            return tdValues

#key value 两个list 装换成字典
def listChangeDict(list):
    i = 1
    keys = []
    values = []
    for item in list:
        if i % 2 == 1:
            keys.append(item.text)
        else:
            values.append(item.text)
        i += 1
    return dict(zip(keys, values))

#获得用户username
def getUserName():
    #获得用户手机号码
    userName = input('请输入要查看的移动手机号码：').strip()
    #判断号码是否正确
    reg = r'^1(3[4-9]|5[0-2,7-9]|47|8[2-4,7-8])\d{8}$'
    if userName =='' or re.match(reg, userName) is  None:
        print('ERROR:请输入正确的移动电话号')
        getUserName()
    else:
        return userName

#获得用户登录方式
def getLoginMethod():
    print('请选择登录方式：')
    print('1.随机短信码登录。')
    print('2.服务密码登录。')
    choice = int(input('请输入1或者2进行选择：'))
    if choice != 1 and choice != 2:
        print('WARING:输入错误')
        return getLoginMethod()
    else:
        return choice
def needVerifyCode(userName):
    global driver
    params ={
        'accountType':'01',
        'account':userName,
        'timestamp':int(round(time.time() * 1000))
    }
    cookies = driver.get_cookies()
    dict = {}
    for cookie in cookies:
        dict[cookie['name']] = cookie['value']
    print(dict)
    try:
        r = requests.get(verifyUrl,params=params,cookies=dict)
        result = json.loads(r.text)
        return result
    except:
        return None

#验证码图片是否加载
def isVerifyCodeImageLoaded(selfDriver):
    driver = selfDriver
    return driver.execute_script("return document.getElementById('imageVec').complete")
#错误截图
def print_errorImage(imageName):
    global imagePath
    global driver
    filePath = imagePath+imageName+'.png'
    driver.get_screenshot_as_file(filePath)
    print_log('ERROR:错误截图存放于'+filePath)
#打印，加打印日志
def print_log(message):
    global errorHandle
    #if 'errorHandle' in dir():
    try:
        print('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']'+message,file=errorHandle)
    except:
        pass
    print(message)
#非正常退出
def exit_close():
    global errorHandle
    global driver
    try:
        driver.find_element_by_css_selector('div[id="undefined"]>span.fr.diacancle.pio-close.dialog-close').click()
        print_log('已关闭')
    except:
        pass
    try:
        driver.find_element_by_id('logout').click()
        print_log('已注销')
    except:
        pass
    try:
        errorHandle.close()
        print_log('非正常退出....')
    except:
        pass
    driver.delete_all_cookies()
    driver.quit()
    exit()

# 获得认证所用的用户信息
def getAllInfoForAuth(driver, verifyImagePath, servicePassword):
    print('请耐心等待30秒，以便顺利收到验证码')
    time.sleep(30)
    textCode = sendTextCode(driver)
    if textCode is None:
        return None
    verifyPath = getVerifyImage(driver, verifyImagePath)
    print('认证消息已全部得到')
    return {'servicePassword': servicePassword, 'textCode': textCode, 'verifyPath': verifyPath}

# 认证
def auth(dict):
    if dict is None:
        return {'result': False, 'msg': '认证信息不对'}
    print(dict)
    driver.find_element_by_id('vec_servpasswd').clear()
    driver.find_element_by_id('vec_servpasswd').send_keys(dict['servicePassword'])
    driver.find_element_by_id('vec_smspasswd').send_keys(dict['textCode'])
    verifyCode = verifyInputCode('请输入在' + dict['verifyPath'] + ' 内看到的图片验证码: ', 2)
    driver.find_element_by_id('vec_imgcode').send_keys(verifyCode)
    print('认证消息填写完成')
    return {'result': True, 'msg': ''}

# 获得验证码图片存放地址
def getVerifyImage(driver, verifyImagePath):
    # 验证码
    div = driver.find_element_by_id('undefined')
    driver.get_screenshot_as_file(verifyImagePath + 'all.png')
    # 通过Image处理图像
    im = Image.open(verifyImagePath + 'all.png')
    x = 250
    y = 525
    region = (x, y, div.size['width'] + x, div.size['height'] + y)
    im = im.crop(region)
    im.save(verifyImagePath + 'code.png')
    return verifyImagePath + 'code.png'

# 接收认证短信随机码 3次机会
def sendTextCode(driver, count=3):
    if count == 0:
        return None
    driver.execute_script('window.alert = function(){return true;};')
    driver.find_element_by_id('stc-send-sms').click()
    code = verifyInputCode('请输入你收到的短信验证码(如何1分钟未收到请输入0重新获取)：')
    if code is False:
        print('验证码未收到，请等待60秒后重新获取...')
        print_errorImage('warning_noTextCode'+str(count))
        time.sleep(60)
        return sendTextCode(driver, count - 1)
    else:
        return code
def normalQuit():
    global driver
    print_log('正常退出')
    try:
        driver.find_element_by_css_selector('div[id="undefined"]>span.fr.diacancle.pio-close.dialog-close').click()
        print_log('已关闭')
    except:
        pass
    try:
        driver.find_element_by_id('logout').click()
        print_log('已注销')
    except:
        pass
    driver.delete_all_cookies()
    driver.quit()
    errorHandle.close()
    exit()
#询问用户是否需要继续进行"详单查询"
def isGoOn():
    print('是否进行该用户详单查询：\n  1.继续  \n  0.退出')
    isQuit = input('请输入0或者1进行选择')
    if isQuit == '0' :
        return False
    elif isQuit == '1':
        return True
    else:
       return isGoOn()


def waitTbody(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, "tbody"))
        )
        print('<tbody id="tbody">已出现')
        tbody = driver.find_element_by_id('tbody')
        tr = tbody.find_element_by_tag_name('tr')
        tds = tr.find_elements_by_tag_name('td')
        if len(tds) > 1:
            print('并且里面有数据')
        return {'code':True,'msg':''}
    except (TimeoutException,NoSuchElementException) as timeOut:
        return {'code':False,'msg':str(timeOut)}
def getTHXQData(trs):
    allRecordList = []
    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        recordList = []
        for td in tds:
            recordList.append(td.text)
        allRecordList.append(recordList)
    return allRecordList
def getOPTHXQData():
    global driver
    tbody = driver.find_element_by_id('tbody')
    trs = tbody.find_elements_by_tag_name('tr')
    OPRecord = getTHXQData(trs)
    return OPRecord
def needRewriteAuthInfo():
    print('是否需要重新认证：')
    print('0.退出.')
    print('1.重新认证')
    choice = input('请输入0或者1进行选择')
    if not choice.isdigit():
        print('Warning:请输入数字0或1进行选择')
        return needRewriteAuthInfo()
    else:
        if int(choice) != 0 and int(choice) != 1:
            print('Warning:请输入数字0或1进行选择')
            return needRewriteAuthInfo()
        return bool(int(choice))
def reAuth():
    global driver
    count = 0
    while True:
        time.sleep(1)
        count +=1
        if count == 2:
            return False
        try:
            driver.find_element_by_id('vecbtn').click()
            WebDriverWait(driver, 30).until_not(
                EC.visibility_of_element_located((By.ID, "undefined"))
            )
            return True
        except:
            return reAuth()
# 这个月是否有数据
def isNoDataInMoth(driver):
    try:
        WebDriverWait(driver,30).until(
            EC.visibility_of_element_located((By.ID,'tbody'))
        )
        print('<tobody id="tobody"> 已出现')
    except TimeoutException as timeOut:
        print_log('Error:本月数据加载超时：' + str(timeOut))
        print_errorImage('error_getData_timeOut')
        return False
    try:
        tbody = driver.find_element_by_id('tbody')
        tr = tbody.find_element_by_tag_name('tr')
        tds = tr.find_elements_by_tag_name('td')
        if len(tds) > 1:
            print('并且里面有数据')
            return True
    except NoSuchElementException as noElement:
        print_log('Warning:本月无数据：' + str(noElement))
        print_errorImage('warning_noData')
        return False
def AuthProcess(driver,verifyImagePath,servicePassword):
    #等待认证框出现
    isAuth = authJudge(driver,verifyImagePath,servicePassword)
    if not isAuth:
        return False
    isAuthSuccessOrFail = isAuthSuccess(driver)
    if not isAuthSuccessOrFail:
        return False
    print('认证成功！！！')
    return True

def waitAuthWindow(driver):
    print('等待认证窗口出现')
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, "undefined"))
        )
    except TimeoutException as timeOut:
        return {'code': False, 'msg': 'ERROR:认证窗口未打开，已超时:' + str(timeOut)}
    print_log('等待验证码图片加载')
    # 等待验证码是否加载
    try:
        WebDriverWait(driver, 30).until(isVerifyCodeImageLoaded, '验证码图片30秒未加载')
        print_log('验证码图片加载完毕')
        return {'code':True,'msg':''}
    except TimeoutException as timeOut:
        return {'code': False, 'msg': 'Error：验证码图片加载超时：' + str(timeOut)}
def authJudge(driver,verifyImagePath,servicePassword):
    #认证并判断
    try:
        userInfo = getAllInfoForAuth(driver,verifyImagePath,servicePassword)
        isAuth = auth(userInfo)
        if isAuth['result']:
            driver.get_screenshot_as_file('auth.png')

            driver.find_element_by_id('vecbtn').click()
            print('点击认证按钮成功')
            return True
        else:
            print_log('ERROR:'+isAuth['msg'])
            print_errorImage('error_auth')
            return False
    except NoSuchElementException as noElement:
        print_log('Error: 无法找到认证元素：' + str(noElement))
        print_errorImage('error_find_Auth')
        return False
    except FileNotFoundError as noFile:
        print_log('Error:无法找到验证码截图'+ str(noFile))
        return False
def isAuthSuccess(driver):
    try:
        WebDriverWait(driver, 15).until_not(
            EC.visibility_of_element_located((By.ID, "undefined"))
        )
        print('认证框以消失')
    except TimeoutException as timeOut:
        if reAuth() is False:
            print_log('Warning: ：认证框未消失,可能验证信息有误：' + str(timeOut))
            print_errorImage('error_wait_disappear_undefined')
            return False
        else:
            print('认证框经过两次点击消失')
            pass
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.TAG_NAME, "tbody"))
        )
        print('<tbody>标签出现')
        return True
    except TimeoutException as timeOut:
        print_log('Error: ：数据页面未加载' + str(timeOut))
        print_errorImage('error_wait_appear_tbody')
        return False


def getAllTHXDData(driver):
    allData = []
    try:
        nextColor = driver.find_element_by_css_selector(
            'div[id="page-demo"]>a[class="next"]').value_of_css_property('color')
        OPRecords = getOPTHXQData()
        for OPRecord in OPRecords:
            allData.append(OPRecord)
        while True:
            isEnable = (driver.find_element_by_css_selector(
                'div[id="page-demo"]>a[class="next"]').value_of_css_property('color') == nextColor)
            print(isEnable)
            if isEnable:
                element = driver.find_element_by_css_selector('div[id="page-demo"]>a[class="next"]')
                element.click()
                result = isNoDataInMoth(driver)
                if result:
                    OPRecords = getOPTHXQData()
                    for OPRecord in OPRecords:
                        allData.append(OPRecord)
                else:
                    print_log('Error: ：下一页数据未加载：')
                    print_errorImage('error_wait_next_tbody')
                    exit_close()
            else:
                break
        return allData

    except (NoSuchElementException, TimeoutException) as noElement:
        print_log('Error: ：元素未找到或超时：' + str(noElement))
        print_errorImage('error_getData')
        return None
try:
    #开始运行
    print_log('\n'+'脚本开始运行...')
    #打开网页
    print_log('正在打开网页：'+url+'....')
    driver.get(url)
    userName = getUserName()
    #获得用户登录方式选择1 短信 2 服务码
    choice = getLoginMethod()
    # 发送用户名称
    sendUserName(userName,choice)
    #两种不同的登录方式
    if choice == 1:
        # 得到验证码
        verification = verifyInputCode('如果收到验证码，请输入:')
        # 写入验证码发并登陆
        sendCode(verification)
    elif choice == 2:
        # 得到服务密码
        servicePassword = verifyInputCode('请输入服务密码 :', choice)
        isNeedVerify = needVerifyCode(userName)
        if isNeedVerify is not None:
            if bool(int(isNeedVerify['needVerifyCode'])):
                try:
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.ID, 'getSMSPwd'))
                    )
                    driver.find_element_by_id('getSMSPwd').click()
                except TimeoutException as timeOut:
                    print_log('WARING:发送验证码按钮未找到，已超时:' + str(timeOut))
                    print_errorImage('error_wait_getSMSPwd')
                    exit_close()
        if isNeedVerify is not None:
            if bool(int(isNeedVerify['needVerifyCode'])):
                # 得到验证码
                verification = verifyInputCode('如果收到验证码，请输入:')
                sendCode(servicePassword, verification)
            else:
                #写入服务码并登陆
                print_log('不需要验证码')
                sendCode(servicePassword)
    #是否登录成功
    result = isLoginSuccess()
    if result is not True:
        print_log('ERROR:网络or验证码or服务密码错误，请重新运行脚本')
        exit_close()
    else:
        print_log('登录成功，正在加载页面...')

    #等待 左侧标签栏加载
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located((By.XPATH,'//a[@class="list-second"]'))
        )
        print_log('左侧标签栏已加载完毕，正在尝试点击"我的信息"...')
    except TimeoutException as timeOut:
        print_log('ERROR:左侧标签栏未找到，已超时:'+str(timeOut))
        print_errorImage('error_wait_list_second')
        exit_close()

    #点击我的信息的标签
    try:
        listSeconds = driver.find_elements_by_xpath("//a[@class='list-second']")
        for listSecond in listSeconds:
            listSecond.click()
        print_log('"所有左侧标签栏打开，正在打开"个人信息"')
    except NoSuchElementException as noElement:
        print_log('ERROR:未找到左侧某个标签,已超时：'+str(noElement))
        print_errorImage('error_find_list_second')
        exit_close()

    #等待个人信息标签加载
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@code='020800']"))
        )
    except TimeoutException as timeOut:
        print_log('"ERROR:个人信息"未找到，已超时:'+str(timeOut))
        print_errorImage('error_wait_a_code_020800]')
        exit_close()

    #点击个人信息标签
    try:
        #driver.get_screenshot_as_file('4.png')
        driver.find_element_by_xpath("//a[@code='020800']").click()
        #driver.get_screenshot_as_file('5.png')
        print_log('"个人信息"已点击，正在加载内容...')
    except (NoSuchElementException,NoSuchAttributeException) as noElement:
        print_log('"ERROR:个人信息"无法点击：'+ str(noElement))
        print_errorImage('error_find_a_code_020800')
        exit_close()

    #等到个人信息数据标签加载并且提取数据
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "pdlr-5"))
        )
        print_log('"个人信息" 标签已经加载完毕，正在提取..')
    except TimeoutException as timeOut:
        print_log('ERROR:数据加载未完成，已超时:' + str(timeOut))
        print_errorImage('error_wait_pdlr_5')
        exit_close()
    #检查跟人信息数据是否加载成功
    tdValues = isLoaded('table_net','td')
    result = listChangeDict(tdValues)
    #
        # for item in result:
        #     print_log(item)
    print(result)
    #等待用户联系方式数据加载并且提取数据
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "tl"))
        )
    except TimeoutException as timeOut:
        print_log('ERROR:数据加载未完成，已超时:' + str(timeOut))
        print_errorImage('error_wait_tl')
        exit_close()
    tdValues = isLoaded('table_userInfo','td')
    result = listChangeDict(tdValues)
    print(result)

    time.sleep(2)
    #询问用户是否继续
    isQuit = isGoOn()
    if not isQuit:
        normalQuit()

    #继续
    #判断是否有服务密码
    if 'servicePassword'  not in locals().keys():
        servicePassword = verifyInputCode('请输入服务密码：',2)
    #点击'详单查询'标签
    try:
        driver.find_element_by_xpath("//a[@code='020700']").click()
        print_log('"详单查询"已点击，正在加载内容...')
    except (NoSuchElementException,NoSuchAttributeException) as noElement:
        print_log('"ERROR:详单查询"无法点击：'+ str(noElement))
        print_errorImage('error_find_a_code_020700')
        exit_close()
    #判断通话详单是否加载
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "ul[id='switch-data']>li[eventcode='UCenter_billdetailqry_type_THXD']>a"))
        )
    except TimeoutException as timeOut:
        print_log('ERROR:通话详单加载，已超时:' + str(timeOut))
        print_errorImage('error_wait_THXD')
        exit_close()
    #点击通话详单
    try:
        THXD_li = driver.find_element_by_css_selector("ul[id='switch-data']>li[eventcode='UCenter_billdetailqry_type_THXD']")
        while True:
            if 'active' in THXD_li.get_attribute('class'):
                break
            else:
                THXD_li.find_element_by_tag_name('a').click()
                THXD_li.click()
                time.sleep(2)
                continue
    except (NoSuchElementException,NoSuchAttributeException) as noElement:
        print_log('Error: 通讯详单无法点击'+str(noElement))
        print_errorImage('error_find_THXD')
        exit_close()

    #获得页面时间列表
    print_log('正在准备打印时间列表:')
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "ul[id='month-data']>li"))
        )
        time.sleep(5)
    except TimeoutException as timeOut:
        print_log('ERROR:时间列表未加载，已超时:' + str(timeOut))
        print_errorImage('error_wait_Moth_data')
        exit_close()

    timeListElements = driver.find_element_by_id('month-data').find_elements_by_tag_name('li')
    timeList = []
    for timeEle in timeListElements:
        timeList.append(timeEle.get_attribute("v"))
    print(timeList)
    #点击第一个时间
    for timeEle in timeListElements:
        print_log(timeEle.get_attribute("v"))
        timeEle.click()
        time.sleep(3)
        if timeEle == timeListElements[0]:
            #认证框是否出现
            isWaitWindowSuccess = waitAuthWindow(driver)
            if not isWaitWindowSuccess['code']:
                print_log('ERROR:认证窗口未打开，已超时:' + isWaitWindowSuccess['msg'])
                print_errorImage('error_wait_undefined')
                exit_close()
            #认证是否成功
            if  not AuthProcess(driver,verifyImagePath,servicePassword) :
                print_log('认证失败')
                exit_close()
            if not isNoDataInMoth(driver):
                continue

        driver.get_screenshot_as_file('done'+timeEle.get_attribute("v")+'.png')
        #检查每个月数据是否加载
        isTbodyShow = waitTbody(driver)
        if isTbodyShow['code']:
            #获得一个月的数据
            result = getAllTHXDData(driver)
        else:
            continue
        print(result)


except (Exception,KeyboardInterrupt) as error:
    print_log('Error:出现未知错误：'+str(error))
    print_errorImage('error_unkonow')
    exit_close()
normalQuit()



