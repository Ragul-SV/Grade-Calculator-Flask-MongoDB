from selenium import webdriver
import unittest
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
cap = DesiredCapabilities().FIREFOX
cap["marionette"] = True
options = Options()
binary = r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
options.binary = binary
options.set_headless(headless=True)

driver = webdriver.Firefox(firefox_options=options,capabilities=cap,executable_path="C:\Users\Ragul\Desktop\geckodriver.exe")
driver.implicitly_wait(10)
driver.maximize_window()
driver.get("http://graco-project.herokuapp.com/")

#testing login page

x=driver.find_element_by_id('gotologin')
x.click()
x = driver.find_element_by_name("username")
x.send_keys("CB.EN.U4CSE17345")
x = driver.find_element_by_name("password")
x.send_keys("#Lordtech123")
x=driver.find_element_by_id('loginsubmit')
x.click()

#testing studentdashboard page

x = driver.find_element_by_name("viewgrades")
x.click()
time.sleep(5)
x=driver.find_element_by_id('logout')
x.click()

#testing register page

x = driver.find_element_by_id('register')
x.click()
x = driver.find_element_by_name('regfac')
x.click()
x = driver.find_element_by_name('goback')
x.click()
x = driver.find_element_by_name('regstu')
x.click()
x = driver.find_element_by_name("username")
x.send_keys("CB.EN.U4CSE17322")
x = driver.find_element_by_name("password")
x.send_keys("#Hello123")
x = driver.find_element_by_name("email")
x.send_keys("ragulsv1999@gmail.com")
x = driver.find_element_by_name("dob")
x.send_keys("01-01-2000")

x = Select(driver.find_element_by_name('batch'))
x.select_by_visible_text("2018-2022")
x = Select(driver.find_element_by_name('dept'))
x.select_by_visible_text("CSE")
x = Select(driver.find_element_by_name('section'))
x.select_by_visible_text("B")
x = driver.find_element_by_id('regsub')
x.click()

driver.quit()
