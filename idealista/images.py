from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd

class Images(object):

    def __init__(self, driver:webdriver, code):
        self.driver = driver
        self.code = code

    def get_images(self):
        div_more_photos = self.driver.find_element_by_id("show-more-photos-button")
        div_more_photos.find_element_by_tag_name("a").click()

        #images = self.driver.find_elements_by_xpath('//div[@id="main-multimedia"]//img')
        images = WebDriverWait(self.driver, 2).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@id="main-multimedia"]//img'))
        )
        images = pd.DataFrame(data=[image.get_attribute('data-ondemand-img') for image in images])
        images['code'] = self.code
        return images
