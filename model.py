import time
import json
import shutil
import requests
import base64
import glob
import os
from logging import getLogger, StreamHandler, Formatter
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# setting load
config_file = open("./settings/setting.json", "r")
conf = json.load(config_file)
config_file.close()

logger = getLogger("__main__").getChild(__name__)

# conf
upload_xpath = conf["urasunday"]["xpath"]["upload"]
out_time = conf["urasunday"]["others"]["timeOut"]
update_list_path = conf["urasunday"]["path"]["list"]
view_xpath = conf["urasunday"]["xpath"]["view"]
view_after_xpath = conf["urasunday"]["xpath"]["viewAfter"]
views_surface_xpath = conf["urasunday"]["xpath"]["viewsSurface"]
save_path = conf["urasunday"]["path"]["savePath"]
archive_path = conf["urasunday"]["path"]["archivePath"]
number_of_stories_xpath = conf["urasunday"]["xpath"]["numberOfStories"]
zero_fill = conf["urasunday"]["others"]["zeroFill"]
img_url = conf["urasunday"]["url"]["imgUrl"]

class Files:
    """ファイルを読み込んだり吐き出したり"""

    def reed_file(self, file_path):
        """
        ファイルを読み込みリストで返す
        
        Parameters
        ----------
        file_path : str  
            ファイルのパス。絶対でも相対でも可
        
        Return
        ------
        l_strip : list
            ファイル1行を1要素としてリストで返す。
            改行コードは含まない
        """
        with open(file_path, encoding="utf-8") as f:
            l_strip = [s.strip() for s in f.readlines()]
        return l_strip

    def get_min_filenumber(self, target_path):
        """
        指定したフォルダに存在する連番が振られたファイル名の
        最小の値＋１を返す。
        len(ファイル名)をzfillとして返す。
        
        Parameters
        ----------
        target_path : str
            検索対象のファイルパス
        
        Returns
        -------
        unique_number : int
            最小値＋１の数字列を返す
        zero : int
            既定のzfillを返す。ただしファイル名のほうが長い場合、
            ファイル名の最大桁数を返す。
            ただし数字列のファイル名のみ判定対象とする。
        """
        file_list = glob.glob(os.path.join(target_path, "*[0-9]*"))
        file_name_list = []
        zero = zero_fill
        for f in file_list:
            base_name = os.path.basename(f).split(".")[0:-1][0]
            try:
                file_name_list.append(int(base_name))
                if len(base_name) > zero:
                    zero = len(base_name)
            except:
                pass
        if len(file_name_list) == 0:
            file_name_list.append(0)
        return max(file_name_list) + 1, zero
    
    def create_manga_directory(self, manga_title, number_of_stories):
        """
        archiveフォルダに漫画フォルダを作成する。
        すでに存在する場合は何もしない。
        漫画フォルダ直下に話数フォルダを作成する。
        すでにある場合はアンダースコア"_"をつけて連番を振る。
        
        Parameters
        ----------
        manga_title : str
            漫画のタイトル
        number_of_stories : str
            話数
        
        Returns
        -------
        created_directory_path : str
            作成した（もともとあっても）フォルダのパス
        """
        created_directory_path = os.path.join(archive_path, manga_title, number_of_stories)
        # 漫画ディレクトリ作成
        manga_dir_path = os.path.join(archive_path, manga_title)
        if not os.path.isdir(manga_dir_path):
            os.mkdir(manga_dir_path)
            logger.info("Make directory ""{0}"".".format(manga_title))
        # 話数ディレクトリ作成
        manga＿number_dir_path = os.path.join(archive_path, manga_title, number_of_stories)
        if not os.path.isdir(manga＿number_dir_path):
            os.mkdir(manga＿number_dir_path)
            logger.info("Make directory ""{0}"".".format(number_of_stories))
        else:
            not_duplicate_number = 1
            while True:
                if not os.path.isdir(manga＿number_dir_path + "_" + str(not_duplicate_number)):
                    os.mkdir(manga＿number_dir_path + "_" + str(not_duplicate_number))
                    created_directory_path = manga＿number_dir_path + "_" + str(not_duplicate_number)
                    break
                else:
                    not_duplicate_number += 1
        
        return created_directory_path


class Urasunday(Files):
    """裏サンデー
    
    Attributes
    ----------
    options : Options
        ChromeWebdriverのオプション
    driver : WebDriver
        seleniumで起動するdriver。基本的に1個だけ
    update_list : list
        自動取得するリスト。リストにないものは無視
    """

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    def __init__(self):
        self.update_list = self.reed_file(update_list_path)


    def page_move(self, url, sleep_time=0):
        """
        driverでページを移動する
        
        Parameters
        ----------
        url : str
            driverで開くURL
        sleep_time : int
            URLに移動した後の待機時間
        """
        self.driver.get(url)
        logger.debug("open: {0}".format(url))
        time.sleep(sleep_time)
    
    def is_display(self, xpath):
        """
        要素が表示されているかどうか判定する

        Parameters
        ----------
        xpath : str
            要素のXPATH
        
        Returns
        -------
        bool : bool
            要素が表示されている場合 True
            それ以外 False
        """
        try:
            if self.driver.find_element_by_xpath(xpath).is_displayed():
                logger.debug("{0} is True.".format(xpath))
                return True
            else:
                logger.debug("{0} is False.".format(xpath))
                return False
        except:
            logger.debug("{0} is not exist.".format(xpath))
            return False
    
    def wait_display(self, element):
        """
        要素が表示されるまで待機
        既定の時間まで表示されない場合は例外
        
        Parameters
        ----------
        element : str
            要素のxpath
        
        Returns
        -------
        bool : bool
            要素が表示されたらTrueを返す。
            表示できなかったら例外放出
        """
        time_out_limit = out_time
        while (not self.is_display(element)) and (time_out_limit > 0):
            time.sleep(1)
            time_out_limit -= 1
        if time_out_limit == 0:
            raise TimeOutError()
        else:
            return True
    
    def get_upload_list(self):
        """
        本日更新分漫画をlist(WebElements)で返す。
        timeoutすると例外放出

        Returns
        -------
        return_list : list
            本日更新分の漫画のWebElementをlistで返す
        """
        self.wait_display(upload_xpath)
                
        return_list = self.driver.find_elements_by_xpath(upload_xpath)
        return return_list
    
    def is_update_target(self, element):
        """
        更新対象かどうか調べる

        Parameters
        ----------
        element: WebElement

        Returns
        -------
        is_exsit : bool
            更新対象の場合Trueを返す
        title : str
            is_exsit=Trueの場合は漫画のタイトルを返す
            （updateListのtitle）
            Falseの場合は空文字
        """
        is_exsit = False
        title = ""
        for u in self.update_list:
            if u in element.text:
                is_exsit = True
                title = u
                break
        return is_exsit, title
    
    def click_element(self, element, new_tab=False, sleep_time=0):
        """
        要素をクリックする

        Parameters  
        ----------  
        element : WebElement
            driver.find_elementで取得したWebElement  
        new_tab : bool
            クリックしたときにページ遷移を伴う場合に
            新たにタブを開くかどうか
        sleep_time : int
            クリック後の待機時間（ｓ）
        """

        # 新tabを開く(=CTRL+クリック)
        if new_tab:
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL)
            actions.click(element)
            actions.perform()
            logger.debug("click element with 'CTRL key'")
        # 通常クリック
        else:
            element.click()
            logger.debug("click element.")
    
    def get_number_of_stories(self):
        """
        漫画ページで話数を取得する
        
        Returns
        -------
        number_of_stories : str
            話数を返す
        """
        number_of_stories = ""
        org_text = self.driver.find_element_by_xpath(number_of_stories_xpath).text
        number_of_stories = org_text.split(" ")[0]
        return number_of_stories
    
    def get_img_src(self):
        """
        ページ内の<img>タグのsrc属性をすべて取得

        Returns
        ----------
        img_src_list : list
            imgのsrc属性をリストですべて返す
        """
        img_list = self.driver.find_elements_by_tag_name("img")
        img_src_list = []
        for img in img_list:
            img_src = img.get_attribute("src")
            if img_url in img_src:
                img_src_list.append(img_src)
        
        return img_src_list
    
    def get_href_of_element(self, element):
        """
        要素内のhref属性を取得する
        
        Parameters
        ----------
        element : WebElement
            対象の要素
        
        Returns
        -------
        href : str
            要素内のhref属性の値を返す
            複数存在する場合は最初の1個を返す
        """
        href = element.find_element_by_tag_name("a").get_attribute("href")
        return href
    
    def page_prev(self):
        """
        view要素の左上をクリックし、ページを送る
        ページ送りが出来なくなったら終了
        """
        try:
            self.wait_display(views_surface_xpath)
        except TimeOutError:
            self.driver.refresh()
            time.sleep(3)
        
        css_text = self.driver.find_element_by_xpath(views_surface_xpath).get_attribute("style")
        loop_count = 1
        while True:
            if loop_count == 1:
                view_element = self.driver.find_element_by_xpath(view_xpath)
            else:
                try:
                    veiw_after_element_xpath = view_after_xpath.replace("{ADDNUMBER}", str(loop_count))
                    view_element = self.driver.find_element_by_xpath(veiw_after_element_xpath)
                except:
                    try:
                        veiw_after_element_xpath = view_after_xpath.replace("{ADDNUMBER}", str(loop_count)).replace("[2]", "")
                        view_element = self.driver.find_element_by_xpath(veiw_after_element_xpath)
                    except:
                        pass
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(view_element, 5, 5)
            actions.click()
            actions.perform()
            logger.debug("page prev.")
            time.sleep(0.1)
            now_css_text = self.driver.find_element_by_xpath(views_surface_xpath).get_attribute("style")
            print("css_text: ", css_text)
            print("now_css_text: ", now_css_text)
            if css_text == now_css_text:
                break
            else:
                css_text = now_css_text
            loop_count += 1
    
    def save_image(self, src, save_path=save_path):
        """
        srcから画像を取得して保存する
        
        Prameters
        ---------
        src : str
            画像のURL
        save_path : str
            画像を保存する場所（ファイル名を含むこと）
        """
        # Base64エンコードされた画像をデコードして保存する。
        if "base64," in src:
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(src.split(",")[1]))

        # 画像のURLから画像を保存する。
        else:
            res = requests.get(src, stream=True)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(res.raw, f)
        
        logger.debug("file:{0} save complete!".format(src))

    def _quit(self):
        """driverを閉じる"""
        self.driver.quit()
        logger.info("driver quit.")

class TimeOutError(Exception):
    """既定の時間以上処理が続いた場合に放出する例外"""
    def __init__(self):
        pass

    def __str__ (self):
        return ("既定のtimeoutに達しました。")


# 漫画ページで１話だけダウンロード
if __name__ == "__main__":
    # 対象のURL
    url = "https://urasunday.com/title/659"
    
    try:
        d = Urasunday()
        d.page_move(url, 5)
        title = d.driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[1]/div[1]/h1').text
        num = d.get_number_of_stories()
        save_dir = d.create_manga_directory(title, num)
        d.page_prev()
        src_list = d.get_img_src()
        min_num, zero = 1, 3
        for src in src_list:
            file_name = str(min_num).zfill(zero) + ".png"
            d.save_image(src, save_path=save_dir + "\\" + file_name)
            min_num += 1
    except Exception as e:
        print(e)
    finally:
        d._quit()