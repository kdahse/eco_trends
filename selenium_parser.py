from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import time


class PageParser:
    def __init__(self):
        self.months = {
                'January':      '1',
                'February':     '2',
                'March':        '3',
                'April':        '4',
                'May':          '5',
                'June':         '6',
                'July':         '7',
                'August':       '8',
                'September':    '9',
                'October':      '10',
                'November':     '11',
                'December':     '12'
            }
        self.rank_Xpath = '/html/body/div[2]/section[1]/div[2]/div[1]/p/span/span[1]/a'
        self.sr_score_Xpath = '/html/body/div[2]/section[1]/div[2]/div[2]/p'
        self.description_Xpath = '/html/body/div[2]/section[1]/div[3]/p[1]'
        self.website_Xpath = '/html/body/div[2]/section[1]/div[3]/p[2]/a'
        self.foundation_Xpath = '/html/body/div[2]/section[1]/div[3]/p[2]'

        self.main_table = pd.DataFrame(columns=['rank', 
                                                'startup', 
                                                'sr score', 
                                                'description',
                                                'website',
                                                'founding date'])
    
        self.competitors_table = pd.DataFrame(columns=['startup',
                                                       'competitor',
                                                       'industry'])
        
        self.funding_table = pd.DataFrame(columns=['startup',
                                                   'date',
                                                   'round',
                                                   'amount',
                                                   'investors'])

    def str2timestamp(self, str_date):
        date_list = str_date.replace(',', '').split()
        date_list[0] = self.months[date_list[0]]
        date = '/'.join(date_list)
        date = datetime.datetime.strptime(date, "%m/%d/%Y")
        return date
    
    def parse_funding_page(self, driver, startup):
        funding_link_Xpath = '/html/body/div[2]/section[5]/a[2]'
        funding_table_Xpath = '/html/body/div[2]/section/table'
        try:
            driver.find_element(By.XPATH, funding_link_Xpath).click()
            time.sleep(1)
            driver.refresh()
            funding_table = driver.find_element(By.XPATH, funding_table_Xpath)
            funding_rows = funding_table.find_elements(By.TAG_NAME, 'tr')
            for row in funding_rows[1:]:
                funding_dict = {}
                row_text = row.find_elements(By.TAG_NAME, 'td')
                funding_dict['startup'] = startup
                funding_dict['date'] = row_text[0].text
                funding_dict['round'] = row_text[1].text
                funding_dict['amount'] = row_text[2].text
                funding_dict['investors'] = row_text[3].text.replace('\n', ', ')
                self.funding_table = self.funding_table._append(funding_dict, ignore_index=True)
            driver.back()
            time.sleep(1)
        except:
            pass
    
    def parse_competitorse_page(self, driver, startup):
        competitors_link_Xpath = '/html/body/div[2]/section[4]/a[2]'
        competitors_table_Xpath = '/html/body/div[2]/section/table'
        try:
            driver.find_element(By.XPATH, competitors_link_Xpath).click()
            time.sleep(1)
            competitors_table = driver.find_element(By.XPATH, competitors_table_Xpath)
            competitors_rows = competitors_table.find_elements(By.TAG_NAME, 'tr')
            for row in competitors_rows[1:]:
                competitors_dict = {}
                row_text = row.find_elements(By.TAG_NAME, 'td')
                competitors_dict['startup'] = startup
                competitors_dict['competitor'] = row_text[0].text
                competitors_dict['industry'] = row_text[1].text
                self.competitors_table = self.competitors_table._append(competitors_dict, ignore_index=True)
            driver.back()
            time.sleep(1)
        except:
            pass

    def parse_startup_page(self, driver, id):
        startup_dict = {}
        startup = driver.find_element(By.XPATH, f'/html/body/div[2]/section/table/tbody/tr[{id}]/td[2]/div[2]/a')
        startup_dict['startup'] = startup.text
        startup.click()
        time.sleep(1)
        startup_dict['rank'] = driver.find_element(By.XPATH, self.rank_Xpath).text
        startup_dict['sr score'] = driver.find_element(By.XPATH, self.sr_score_Xpath).text
        startup_dict['description'] = driver.find_element(By.XPATH, self.description_Xpath).text
        startup_dict['website'] = driver.find_element(By.XPATH, self.website_Xpath).text
        try:
            date = driver.find_element(By.XPATH, self.foundation_Xpath).get_attribute("innerText").split('\n')[1][9:]
            startup_dict['founding date'] = self.str2timestamp(date)
        except IndexError:
            startup_dict['founding date'] = None
        
        self.main_table = self.main_table._append(startup_dict, ignore_index=True)
        self.parse_competitorse_page(driver, startup_dict['startup'])
        self.parse_funding_page(driver, startup_dict['startup'])

        driver.back()
        time.sleep(1)


def main():
    service = Service(r"C:\\Python\\Selenium\\geckodriver.exe")
    options = webdriver.FirefoxOptions()
    url = "https://www.startupranking.com/top"
    parser = PageParser()

    try:
        driver = webdriver.Firefox(service=service, options=options)
        driver.get(url)
        time.sleep(5)
        startup_table = driver.find_element(By.TAG_NAME, 'table')
        startup_elems = startup_table.find_elements(By.TAG_NAME, 'tr')
        for i in range(1, len(startup_elems)):
            time.sleep(2)
            parser.parse_startup_page(driver, i)
            time.sleep(2)
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':
    main()
