import os
import re
import time
import math
import json
from random import uniform
from datetime import datetime as dt

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from tqdm.auto import tqdm


class KinopoiskReviewsScrapper:
    def __init__(self, headless: bool = False):
        self.options = webdriver.FirefoxOptions()
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument('--incognito')
        if headless:
            self.options.add_argument("--headless")
        self.driver = None

    def collect_urls(self, urls: list[str], urls_bar, pages_bar, reviews_bar) -> list[str]:
        """
        Runs though list of urls and collects reviews. Incorrect urls are saved into list
        and returned in the end.

        :param urls: URLs to scrape. URL must target to movie start page.
        :param urls_bar: tqdm bar to show urls progress.
        :param pages_bar: tqdm bar to show pages progress in one url.
        :param reviews_bar: tqdm bar to show reviews progress on one page.
        :return: List of urls that were not collected.
        """
        self.driver = webdriver.Firefox(options=self.options)
        self.driver.implicitly_wait(10)

        wrong_urls = list()
        try:
            for url_i in range(len(urls)):
                url = urls[url_i]
                try:
                    comments_page = self.generate_comments_url(movie_url=url)
                except ValueError:
                    wrong_urls.append(url)
                    continue

                temp_folder = self.temp_folder(url)
                # Reset pages bar on new url start
                pages_bar.reset()
                reviews_bar.reset(total=0)
                pages_bar.desc = f'Pages for {url}'
                pages_bar.refresh()
                try:
                    # Open movie start page
                    self.driver.get(url)
                    # Wait til page is loaded
                    self.loading_pause()

                    if 'captcha' in self.driver.current_url:
                        input('Press return when captcha ends')
                        time.sleep(uniform(5, 10))

                    # Save movie heading to add to final data
                    movie_heading = self.driver.find_element(by=By.TAG_NAME, value='h1')
                    movie_heading_text = movie_heading.text
                    # Switch to reviews page
                    self.driver.get(comments_page)
                    while True:
                        # Wait until it's loaded
                        self.loading_pause()
                        # Start time tracking
                        start_time = time.time()
                        # Scroll to random value
                        self.__random_scroll()

                        # Collect data from page
                        comments_div = self.driver.find_element(by=By.CLASS_NAME, value='clear_all')
                        reviews_on_page = comments_div.find_elements(by=By.CLASS_NAME, value='userReview')
                        reviews_bar.reset(total=len(reviews_on_page))
                        reviews_data = list()
                        for review in reviews_on_page:
                            data = self.__review_data(review)
                            # Add movie data to each record
                            data['movie_title'] = movie_heading_text
                            data['movie_link'] = url
                            reviews_data.append(data)
                            reviews_bar.update()
                            reviews_bar.refresh()

                        # Generate temp filename based on existing temp files count
                        temp_file_path = os.path.join(temp_folder, f'{len(os.listdir(temp_folder))}.json')
                        # Save collected data to temp file
                        with open(temp_file_path, 'w', encoding='utf-8') as f:
                            json.dump(dict(data=reviews_data), f, indent=4, ensure_ascii=False)
                        # Finish time tracking
                        end_time = time.time()
                        # If time spent on page is less than 5-12 seconds,
                        # wait til 10 seconds passes
                        time_elapsed = end_time - start_time
                        expected_time = uniform(5, 12)
                        if time_elapsed < expected_time:
                            time.sleep(expected_time - time_elapsed)

                        urls_bar.update()
                        pages_bar.update()
                        # Switch to next page
                        if self.__next_page():
                            self.loading_pause()
                        else:
                            print('No more pages available: ' + url)
                            break

                except Exception as e:
                    print(f'Error occurred while scraping comments for {url}: {e}')
                    self.loading_pause()
                    wrong_urls.append(url)
                    continue

        except Exception as e:
            print(f'Global error occurred: {e}')
        finally:
            self.driver.quit()
            return wrong_urls

    def __review_data(self, review_element):
        # Get id from element attributes
        review_id = review_element.get_attribute('data-id')

        # Get kind (positive/neutral/bad) from elements kind
        # as review background color depends on this class
        kind_div_id = f'div_review_{review_id}'
        review_div = review_element.find_element(by=By.ID, value=kind_div_id)
        kind_ = review_div.get_attribute('class').split()[-1]
        kind_ = kind_ if kind_ in ['good', 'neutral', 'bad'] else None

        # Get review heading from its element data
        heading_id = f'ext_title_{review_id}'
        heading = review_element.find_element(by=By.ID, value=heading_id)
        heading_text = heading.text

        # Get review body from its element data
        text_id = f'ext_text_{review_id}'
        text_body = review_element.find_element(by=By.ID, value=text_id).find_element(by=By.TAG_NAME, value='span')
        text_body_content = text_body.get_attribute('innerHTML')
        text_body_content = text_body_content.replace('<br>', '')
        text_body_content = re.sub(r'\n{2,}', '\n', text_body_content)

        # Get useful counts from element data
        useful_id = f'comment_num_vote_{review_id}'
        useful_element = review_element.find_element(by=By.ID, value=useful_id)
        useful_raw_text = useful_element.text
        useful_positive, userful_negative = list(map(int, useful_raw_text.split(' / ')))

        # Get review publication date from element data
        date_ = review_element.find_element(by=By.CLASS_NAME, value='date')
        date_text = date_.text
        month_name = re.search(r'\d{1,2} (\w+)', date_text).group(1)
        date_text = date_text.replace(month_name, self.month_to_number(month_name))
        date_value = dt.strptime(date_text, '%d %m %Y | %H:%M').isoformat()

        # Get link to the comment itself
        try:
            link_element = review_element.find_element(by=By.CLASS_NAME, value='links').find_element(by=By.TAG_NAME,
                                                                                                     value='a')
            link = link_element.get_attribute('href')
        except NoSuchElementException:
            link = None

        # Collect all data pieces together
        review_data_result = {
            'comment_id': review_id,
            'comment_date': date_value,
            'comment_link': link,
            'comment_kind': kind_,
            'comment_heading': heading_text,
            'comment_text': text_body_content,
            'comment_useful_positive': useful_positive,
            'comment_useful_negative': userful_negative,
        }
        return review_data_result

    def __next_page(self) -> bool:
        """
        Tries to find next page arrow on the current page.
        :return: Next page arrow is found and clicked.
        """
        try:
            navigator = self.driver.find_element(by=By.XPATH, value='//div[@class="navigator"]/ul[@class="list"]')
            arrows = navigator.find_elements(by=By.XPATH, value='//li[@class="arr"]')
            found = False
            for arr in arrows:
                if arr.text == '»':
                    arr.click()
                    found = True
                    break
            return found
        except NoSuchElementException:
            return False

    def __random_scroll(self):
        scroll_value = math.floor(uniform(100, 300))
        ActionChains(self.driver).scroll_by_amount(0, scroll_value).perform()

    @staticmethod
    def loading_pause():
        sleep_time = uniform(20, 30)
        print(f'Pause for {sleep_time} seconds')
        time.sleep(sleep_time)
        print(f'Pause finished')

    @staticmethod
    def generate_comments_url(movie_url: str):
        """
        Generates url to first reviews page. Sets perpage to 200 to decrease webdriver request to host,
        thus, lower the kinopoisk chance of defining the parser and blocking it.
        :param movie_url: URL to moview start page.
        :return: URL to reviews start page.
        """

        expected_link_pattern = r'https://www.kinopoisk.ru/(film|series)/\d+/?'
        if re.fullmatch(expected_link_pattern, movie_url):
            movie_url = movie_url.replace('series', 'film')
            return movie_url.strip('/') + '/reviews/ord/date/status/all/perpage/200/'
        else:
            raise ValueError('Invalid link to movie provided, please, check it')

    @staticmethod
    def temp_folder(start_url):
        """
        Generates temporary folder to store parsing results.

        :param start_url: URL to movie page on kinopoisk to include its id into folder name.
        :return: Path to temporary folder.
        """
        temp_folder_name = f'{start_url.strip("/").split("/")[-1]}_' + dt.now().strftime('%y%m%d%H%M')
        os.makedirs(temp_folder_name)
        return temp_folder_name

    @staticmethod
    def month_to_number(month_name) -> str:
        """
        :return: Month number from its russian name.
        """
        months_dict = {
            'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12',
        }
        return months_dict[month_name]

