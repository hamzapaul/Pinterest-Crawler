import logging
import random
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime
import re
from os.path import expanduser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from custom_logging import init_logger

init_logger('pinterest', 'pinterest.log')


def sleep():
    time.sleep(random.randint(4, 6))


def generate_time_data():
    year = datetime.now().year
    timestamp = datetime.timestamp(datetime.now())
    month = datetime.now().month
    day = datetime.now().day
    now = datetime.now()
    tmstmp = str(timestamp).split(".")[0]

    return year, timestamp, month, day, now, tmstmp


class Pinterest:
    def __init__(self, crawl_link, user, headless=True):
        self.crawl_link = crawl_link
        self.username, self.password = user

        # logger
        self.logger = logging.getLogger('pinterest')

        # Setting up Chrome options
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('disable-notifications')
        self.options.add_argument("--window-size=1920x1080")
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-gpu')

        # Initializing the driver as None
        self.driver = None

    def start(self):
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.crawl_created(self.crawl_link)
        except Exception as ex:
            print(ex)
        finally:
            if self.driver:
                self.driver.quit()

    def crawl_created(self, url):
        try:
            self.login()

            print(f'Crawling: {url}')
            pin_links = self.get_pin_links(url)

            if pin_links is None:
                return

            print(f'{len(pin_links)} pins Found.')

            followers = self.get_followers()

            data = []
            for index, pin_link in enumerate(pin_links):
                x = self.scrape_pin(pin_link, followers, index)

                if x is not None:
                    data.append(x)

            if len(data) == 0:
                print(
                    f'Page could not be found: please check url')
        except Exception as e:
            print(e)

    def login(self):
        try:
            self.driver.get('https://www.pinterest.de/login/')  # 1

            sleep()  # 2

            in_put = self.driver.find_element(By.XPATH,
                                              '//input[@id="email"]')  # 3
            in_put.send_keys(self.username)  # 3

            pass_wrd = self.driver.find_element(By.XPATH, '//input[@id="password"]')  # 4
            pass_wrd.send_keys(self.password)  # 4

            btn = self.driver.find_element(By.XPATH, '//button[@class="red SignupButton active"]')  # 5
            btn.click()  # 5
        except Exception as e:
            print(f'Login Failed: {e}')  # 6

    def get_pin_links(self, url):
        self.driver.get(url)

        sleep()

        self.scroll_load(self.driver)

        try:
            links = self.driver.find_element(By.XPATH, '//div[@role="list"]')
            links = links.find_elements(By.TAG_NAME, 'a')
        except NoSuchElementException:
            try:
                links = self.driver.find_element(By.XPATH, '//div[@data-test-id="created-tab-feed"]//div[@role="list"]')
                links = links.find_elements(By.TAG_NAME, 'a')
            except NoSuchElementException as e:
                self.logger.error(e)
                return None

        posts = []
        for link in links:
            posts.append(link.get_attribute('href'))
            if len(posts) > 3:
                break

        return posts

    @staticmethod
    def scroll_load(driver, divider=10):
        height = driver.find_element(By.TAG_NAME,
                                     "body").size['height']

        for i in range(divider):
            start_scroll = i * height / divider
            end_scroll = (i + 1) * height / divider
            driver.execute_script("window.scrollTo(" +
                                  str(start_scroll) +
                                  ", " +
                                  str(end_scroll) +
                                  ")")
            time.sleep(1)

        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.HOME)

    def get_followers(self):
        try:
            div = self.driver.find_element(By.XPATH, '//div[@data-test-id="profile-followers-count"]')
        except NoSuchElementException:
            try:
                div = self.driver.find_element(By.XPATH,
                                               '//div[@data-test-id="profile-followers-link"]')
            except NoSuchElementException:
                print('NoSuchElementException: Followers Not Found')
                return None

        if div:
            return div.get_attribute('innerText').replace(' followers', '')

    def scrape_pin(self, pin_link, followers, index):
        try:
            self.driver.get(pin_link)  # 1
            sleep()  # 2

            try:  # 3
                main_div = self.driver.find_element(By.XPATH, '//div[@data-test-id="closeup-lego-container"]')
            except NoSuchElementException:
                try:
                    main_div = self.driver.find_element(By.XPATH,
                                                        '//div[@data-layout-shift-boundary-id="CloseupPageBody"]')
                except NoSuchElementException:
                    self.logger.error('Main Element Not Found')
                    return

            img = self.image(main_div, index)  # 4
            title = self.title(main_div)

            page_source = self.driver.page_source  # 5
            like_count = self.like_count(page_source)  # 6
            comment_count = self.comment_count(page_source)
            share_count = self.share_count(page_source)

            data = {'followers': followers,  # 7
                    'title': title,
                    'img': img,
                    'link': pin_link,
                    'comments': comment_count,
                    'likes': like_count,
                    'shares': share_count
                    }
            self.print(data)
            return data
        except Exception as e:
            print(e)

    @staticmethod
    def print(data):
        print(f"""
        followers: {data['followers']}
        title: {data['title']}
        img: {data['img']}
        link: {data['link']}
        comments: {data['comments']}
        likes: {data['likes']}
        shares: {data['shares']}
        """)

    def image(self, main_div, index):
        try:
            img = main_div.find_element(By.XPATH, './/div[@data-test-id="visual-content-container"]//img')
            return img.get_attribute('src')
        except NoSuchElementException:
            try:
                img = main_div.find_element(By.XPATH, './/div[@data-test-id="visual-content-container"]//video')
                return img.get_attribute('poster')
            except NoSuchElementException:
                try:
                    img = self.driver.find_element(By.XPATH, './/div[@data-test-id="story-pin-closeup-page"]//img')
                    return img.get_attribute('src')
                except NoSuchElementException:
                    try:
                        img = self.driver.find_element(By.XPATH,
                                                       './/div[@data-test-id="story-pin-closeup-page"]//video')
                        return img.get_attribute('src')
                    except NoSuchElementException:
                        try:
                            img = main_div.find_element(By.XPATH, './/div[@data-test-id="pin-closeup-image"]//img')
                            return img.get_attribute('src')
                        except NoSuchElementException:
                            try:
                                return self.take_screenshot(index)
                            except NoSuchElementException as e:
                                print(e)
                                return None

    def take_screenshot(self, index):
        # 1
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day

        # 2
        timestamp = datetime.timestamp(datetime.now())
        tmstmp = str(timestamp).split(".")[0]

        # 3
        pic_name_png = f"pin_{str(year) + str(month).zfill(2) + str(day).zfill(2)}_{tmstmp}_{str(index)}.png"

        # 4
        body = self.driver.find_element(By.XPATH, '//body')
        path = expanduser('~') + '/PINTEREST_MEDIA/' + pic_name_png

        # 6
        body.screenshot(path)

        # 7
        return path

    def title(self, main_div):
        try:
            return main_div.find_element(By.TAG_NAME, 'h1').get_attribute('innerText')
        except NoSuchElementException:
            try:
                return main_div.find_element(By.TAG_NAME, 'h2').get_attribute('innerText')
            except NoSuchElementException:
                try:
                    return self.driver.find_element(By.XPATH,
                                                    '//div[@data-test-id="truncated-text"]').get_attribute(
                        'innerText')
                except NoSuchElementException:
                    try:
                        div = main_div.find_element(By.XPATH,
                                                    './/div[@data-test-id="main-pin-description-text"]')
                        return div.get_attribute('innerText')
                    except NoSuchElementException:
                        try:
                            return main_div.find_element(By.XPATH,
                                                         './/div[@data-test-id="description"]').get_attribute(
                                'innerText')
                        except NoSuchElementException:
                            try:
                                return main_div.find_element(By.XPATH,
                                                             './/div[@data-test-id="basic-layout"]').get_attribute(
                                    'innerText')
                            except NoSuchElementException:
                                try:
                                    div = main_div.find_element(By.XPATH,
                                                                './/div[@data-test-id="truncated-description"]')
                                    return div.get_attribute('innerText')
                                except NoSuchElementException:
                                    try:
                                        div = main_div.find_element(By.XPATH,
                                                                    '//div[@data-test-id="product-description"]')
                                        return div.get_attribute('innerText')
                                    except NoSuchElementException:
                                        self.logger.error(f'Text Not Found')
                                        return None

    def share_count(self, page_source):
        try:
            x = re.search('"share_count":[0-9]*', page_source)
            if x:
                return x.group().replace('"share_count":', '')
        except Exception as e:
            self.logger.error(e)

    def comment_count(self, page_source):
        try:
            x = re.search('"comment_count":[0-9]*', page_source)
            if x:
                return x.group().replace('"comment_count":', '')
        except Exception as e:
            self.logger.error(e)

    def like_count(self, page_source):
        try:
            x = re.search('"reaction_counts":{"1":[0-9]*}', page_source)
            if x:
                return x.group().replace('"reaction_counts":{"1":', '').replace('}', '')
        except Exception as e:
            self.logger.error(e)


if __name__ == '__main__':
    Pinterest('https://www.pinterest.com/lamborghini/_created/',
              ('your_pinterest_username', 'your_pinterest_password')).start()
