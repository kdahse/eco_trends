from time import time
import zipfile
import shutil
import os
import re
from fake_useragent import UserAgent
from config import setup_proxy_extension
from DrissionPage import ChromiumPage
from DrissionPage import ChromiumOptions
import pandas as pd


def unzip_and_overwrite(zip_path):
    folder_path = zip_path.rsplit('.', 1)[0]
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path, exist_ok=True)
    # Открытие ZIP-архива
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Извлечение всех файлов в указанную папку
        zip_ref.extractall(folder_path)


def create_driver(proxy: dict = None,
                  need_gui: bool = True,
                  user_agent: bool = True
                  ) -> ChromiumPage:
    """
    Создает объект ChromiumPage с настройками драйвера.

    Аргументы:
    proxy: dict
        При передачи словаря вида {
        'PROXY_HOST': '',
        'PROXY_PORT': '',
        'PROXY_USER': '',
        'PROXY_PASS': ''
        } можно использовать приватный proxy сервер
    need_gui: bool
        Включение/выключение графического интерфейса браузера.
    user_agent:
        Подмена User Agent.

    Возвращает:
    Объект класса ChromiumPage со настроенными параметрами.
    """

    chrome_options = ChromiumOptions()
    chrome_options.set_paths(browser_path='C:\Program Files\Google\Chrome\Application\chrome.exe',
                             user_data_path='C:\Programms\PyCharm\PyCharm Community Edition 2022.3.1\PyCharm_Projects\parsing')

    if user_agent:
        ua = UserAgent()
        chrome_options.set_user_agent(ua.random)

    if not need_gui:
        chrome_options.set_argument(arg='--headless')
        chrome_options.set_argument(arg='--disable-gpu')

    if proxy:
        plugin_file = 'proxy_auth_plugin.zip'
        manifest_json, background_js = setup_proxy_extension(proxy['PROXY_HOST'],
                                                             proxy['PROXY_PORT'],
                                                             proxy['PROXY_USER'],
                                                             proxy['PROXY_PASS']
                                                             )
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        unzip_and_overwrite(plugin_file)
        chrome_options.add_extension('.\proxy_auth_plugin')

    return ChromiumPage(chrome_options)


def get_all_pages(driver) -> dict:
    """
    Парсит информацию с главной страницы https://www.startupranking.com/top в .csv файл.

    Аргументы:
    driver: ChromiumPage
        Инициализированный драйвер со всеми сопутствующими настройками.

    Возвращает:
    dct : dict
        Словарь с информацией с последнего запроса.
    """

    dct = {'id': [],
           'url': [],
           'name': [],
           'SR_Score': []
           }

    driver = driver
    file_path = 'general_info1.csv'
    pd.DataFrame(columns=['id', 'url', 'name', 'SR_Score']).to_csv(file_path, index=False)
    start_time = time()
    cur_len_dct = 0
    for i in range(278):
        if i == 0:
            url = 'https://www.startupranking.com/top'
        else:
            url = f'https://www.startupranking.com/top/0/{i + 1}'
        try:
            driver.get(url)
            startups = driver.eles('css:.ranks tr')
            for startup in startups:
                dct['id'] = startup.ele('css:td').text
                dct['url'] = startup.ele('css:a').attr('href')
                dct['name'] = startup.ele('css:.name a').text
                dct['SR_Score'] = startup.ele('css:.tright.sr-score').text

                df = pd.DataFrame([dct])
                df.to_csv(file_path, mode='a', header=False, index=False)

            print(f'Старница {i + 1} успешно обработана')
            print(f'На странице {i + 1} обработано {len(dct["id"]) - cur_len_dct} стартапов')
            print(f'Не потерялась ли информация? - '
                  f'{len(dct["id"]) == len(dct["url"]) == len(dct["name"]) == len(dct["SR_Score"])}')
            print('-----------------------------------------')
            cur_len_dct = len(dct["id"])

        except Exception as e:
            print(f'Произошла ошибка: {e}')
            print(f'Последняя посещенная страница: {i}')
            print(f'Время работы программы: {time() - start_time}')
    print(f'Время работы фунции get_all_pages: {time() - start_time}')
    driver.quit()
    return dct


def get_info_startup(driver):
    """
    Парсит информацию о каждом стартапе в .csv файл.

    Аргументы:
    driver: ChromiumPage
        Инициализированный драйвер со всеми сопутствующими настройками.

    Возвращает:
    dct : dict
        Словарь с информацией с последнего запроса.
    """
    driver = driver
    all_pages = pd.read_csv('general_info.csv')
    dct_info = {'id': [],
                'name': [],
                'logo': [],
                'short_description': [],
                'full_description': [],
                'website': [],
                'founded': [],
                'region': []
                }
    dct_funding = {'id': [],
                   'name': [],
                   'date': [],
                   'round': [],
                   'amount': [],
                   'investors': []
                   }
    dct_products = {'id': [],
                    'name': [],
                    'product': [],
                    'stage': [],
                    'description': []
                    }
    file_path1 = 'every_startup_info.csv'
    file_path2 = 'every_startup_funding.csv'
    file_path3 = 'every_startup_products.csv'
    pd.DataFrame(columns=['id',
                          'name',
                          'logo',
                          'short_description',
                          'full_description',
                          'website',
                          'founded',
                          'region',
                          ]).to_csv(file_path1, index=False)
    pd.DataFrame(columns=['id',
                          'name',
                          'date',
                          'round',
                          'amount',
                          'investors',
                          ]).to_csv(file_path2, index=False)
    pd.DataFrame(columns=['id',
                          'name',
                          'product',
                          'stage',
                          'description',
                          ]).to_csv(file_path3, index=False)
    start_time = time()
    for id, url, name in zip(all_pages['id'], all_pages['url'], all_pages['name']):
        try:
            driver.get(url)
            # Парсинг основной информации.
            dct_info['id'] = id
            dct_info['name'] = name
            dct_info['logo'] = driver.ele('css:.su-logo img').attr('src')
            info = driver.ele('css:.su-info')
            dct_info['short_description'] = info.ele('css:.su-phrase').text
            dct_info['full_description'] = info.ele('css:p').text
            dct_info['website'] = info.ele('css:.su-loc a').attr('href')
            founded_text = info.ele('css:.su-loc').text
            date = re.search(r'Founded: (\w+ \d{2}, \d{4})', founded_text)
            if date:
                dct_info['founded'] = date.group(1)
            else:
                dct_info['founded'] = 'Информация отсутствует'
            dct_info['region'] = driver.ele('css:.country-rank').text

            # Парсинг информации о финансировании
            dct_funding['id'] = id
            dct_funding['name'] = name
            sections = driver.eles('css:section.stats')
            target_section_funding = None
            for section in sections:
                h2_element = section.ele('css:h2')
                if 'Funding' in h2_element.text:
                    target_section_funding = section
                    break
            rows_funding = target_section_funding.s_eles('css:table.rank_table tbody.ranks tr')
            dates = []
            rounds = []
            amounts = []
            investors = []
            for row in rows_funding:
                date = row.ele('css:td:nth-child(1)').text
                if date == 'There are no funding rounds.':
                    break
                round = row.ele('css:td:nth-child(2)').text
                amount = row.ele('css:td:nth-child(3) span').text
                investor = row.ele('css:td:nth-child(4)').text
                dates.append(date)
                rounds.append(round)
                amounts.append(amount)
                investors.append(re.sub(r'\n', ',', investor))
            dct_funding['date'] = dates
            dct_funding['round'] = rounds
            dct_funding['amount'] = amounts
            dct_funding['investors'] = investors

            # Парсинг информации о Products
            dct_products['id'] = id
            dct_products['name'] = name
            target_section_products = None
            for section in sections:
                h2_element = section.ele('css:h2')
                if 'Products' in h2_element.text:
                    target_section_products = section
                    break
            rows_products = target_section_products.s_eles('css:table.rank_table tbody.ranks tr')
            products = []
            stages = []
            descriptions = []
            for row in rows_products:
                product = row.ele('css:td:nth-child(1)').text
                if product == 'There are no products.':
                    break
                stage = row.ele('css:td:nth-child(2)').text
                description = row.ele('css:td:nth-child(3) span').text
                products.append(product)
                stages.append(stage)
                descriptions.append(description)
            dct_products['product'] = products
            dct_products['stage'] = stages
            dct_products['description'] = descriptions

            # Обновление csv-файлов
            df1 = pd.DataFrame([dct_info])
            df1.to_csv(file_path1, mode='a', header=False, index=False)
            df2 = pd.DataFrame([dct_funding])
            df2.to_csv(file_path2, mode='a', header=False, index=False)
            df3 = pd.DataFrame([dct_products])
            df3.to_csv(file_path3, mode='a', header=False, index=False)

            print(f'Старница {url} успешно обработана')
            print(f'На странице {url} обнаружено '
                  f'{len(rows_funding) if dct_funding["date"] != [] else 0}'
                  f' Foundings и'
                  f' {len(rows_products) if dct_products["product"] != [] else 0}'
                  f' Products')
            print('-----------------------------------------')

        except Exception as e:
            print(f'Произошла ошибка: {e}')
            print(f'Последняя посещенная страница: {id}')
            print(f'Время работы программы: {time() - start_time}')


def main():
    proxy = {
        'PROXY_HOST': '217.29.62.222',
        'PROXY_PORT': '11668',
        'PROXY_USER': 'rkKaTJ',
        'PROXY_PASS': 'cmpXKJ'
    }
    driver = create_driver(proxy=proxy)
    get_all_pages(driver)
    get_info_startup(driver)


if __name__ == '__main__':
    main()
