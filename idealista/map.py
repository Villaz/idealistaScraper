from selenium import webdriver
from selenium import common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException

class Map(object):
    driver = None

    def __init__(self, driver:webdriver):
        self.driver = driver

    def get_lat_lon(self):
        self.load_map()
        return self.check_map()

    def _extract_lat_lon(self):
        m = self.driver.find_element_by_xpath("//div[@data-role='map-box']")
        div = m.find_element_by_class_name("gm-style")
        links = [a.get_attribute("href")
                 for a in div.find_elements_by_tag_name('a')
                 ]
        links = [link for link in links if link and link.startswith('https://maps.google.com/maps?ll')]
        if len(links):
            links = links[0].replace('https://maps.google.com/maps?ll=', '')
            links = links[:links.find('&')]
            return links.split(',')
        else:
            return None, None

    def load_map(self, value=750):
        map = self.driver.find_element_by_id('mapWrapper')
        try:
            webdriver.ActionChains(self.driver).move_to_element(map).perform()
        except MoveTargetOutOfBoundsException as ex:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", map)
            self.load_map(value + value)

    def check_map(self):
        try:
            element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "sMap"))
            )
            src = element.get_attribute("src")
            src = src.replace('https://maps.googleapis.com/maps/api/staticmap?center=', '')
            src = src[:src.find('&')]
            return src.split(',')
        except common.exceptions.TimeoutException as ex:
            self.driver.find_element_by_xpath("//a[@data-markup-map-link='detalle::map::link']").click()
            span = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@data-role='map-box']//div[@class='header show']/span")))
            span.click()
            return self._extract_lat_lon()