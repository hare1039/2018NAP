import requests
import simplejson as json
import sys
import getopt
import os
import base64
import pandas
import getpass
from prettytable import from_csv
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    name = sys.argv[-1]
    for o, a in opts:
        if o in ("-h", "--help"):
            print("python get_schedule.py [options] student_id")
            print("  [options]")
            print("    -h, --help          -- display this help")
            sys.exit()
        else:
            assert False, "Unreconized options"
    
    password = getpass.getpass("Password for " + name + ": ")
    driver = webdriver.Remote (
        command_executor="http://hare1039.nctu.me:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.CHROME
    )

    driver.get("https://portal.nctu.edu.tw/portal/login.php")
    parsed = False
    while not parsed:
        img = driver.find_element(By.ID, "captcha")
        img_captcha_base64 = driver.execute_async_script("""
            var ele = arguments[0], callback = arguments[1];
            ele.addEventListener("load", function fn() {
                ele.removeEventListener("load", fn, false);
                var cnv = document.createElement("canvas");
                cnv.width = this.width; cnv.height = this.height;
                cnv.getContext("2d").drawImage(this, 0, 0);
                callback(cnv.toDataURL("image/jpeg").substring(22));
            }, false);
            ele.dispatchEvent(new Event("load"));
        """, img)
        with open(r"/tmp/getcaptcha.jpg", "wb") as f:
            f.write(base64.b64decode(img_captcha_base64))
        files = {"file": open("/tmp/getcaptcha.jpg", "rb")}
        res = requests.post("https://hare1039.nctu.me/cracknctu", files=files)
        os.remove("/tmp/getcaptcha.jpg")
        if res.status_code == requests.codes.ok and res.text != "ERROR":
            print(res.text)
            cap = driver.find_element(By.ID, "seccode")
            cap.send_keys(res.text)
            parsed = True
        else:
            print("refresh!")
            reload_but = driver.find_element(By.ID, "seccode_refresh")
            ActionChains(driver).click(reload_but).perform()

    print("ゲットだぜ")

    namefield = driver.find_element(By.ID, "username")
    namefield.send_keys(name)
    passfield = driver.find_element(By.ID, "password")
    passfield.send_keys(password)
    passfield.submit()
    
    driver.get("https://portal.nctu.edu.tw/portal/relay.php?D=cos")
    try:
        element_present = EC.presence_of_element_located((By.ID, "submit"))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
        assert False, "Timed out waiting for page to load"
    driver.find_element(By.ID, "submit").submit()
    
    driver.find_element(By.ID, "idfrmSetPreceptor").submit()
    
    driver.switch_to.frame("frmMenu")
    driver.execute_script("checkDiv('CrsTakenStateSearch');")
    driver.find_element(By.XPATH, "//a[@href='adSchedule.asp']").click()

    driver.switch_to.default_content();
    driver.switch_to.frame("frmMain")

    try:
        element_present = EC.presence_of_element_located((By.XPATH, "/html/body/center/p/table[2]"))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
        assert False, "Timed out waiting for page to load"
    
    html_table = driver.find_element(By.XPATH, "/html/body/center/p/table[2]")
    table = pandas.read_html(html_table.get_attribute("outerHTML"))
    table[0].to_csv("/tmp/getclasses.csv")
    fp = open("/tmp/getclasses.csv", "r")
    ptable = from_csv(fp)
    fp.close()
    os.remove("/tmp/getclasses.csv")
    print(ptable)
    driver.quit()
