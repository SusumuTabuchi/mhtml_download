import time
import os
import glob
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class Files:
    """ファイルを読み込んだり吐き出したり"""
    zero_fill = 3
    archive_path = r'E:\susumuTabuchi\Desktop\workspace\development\mhtml_download\arshive'


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
        zero = self.zero_fill
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
        created_directory_path = os.path.join(self.archive_path, manga_title, number_of_stories)
        # 漫画ディレクトリ作成
        manga_dir_path = os.path.join(self.archive_path, manga_title)
        if not os.path.isdir(manga_dir_path):
            os.mkdir(manga_dir_path)
        # 話数ディレクトリ作成
        manga＿number_dir_path = os.path.join(self.archive_path, manga_title, number_of_stories)
        if not os.path.isdir(manga＿number_dir_path):
            os.mkdir(manga＿number_dir_path)
        # else:
        #     not_duplicate_number = 1
        #     while True:
        #         if not os.path.isdir(manga＿number_dir_path + "_" + str(not_duplicate_number)):
        #             os.mkdir(manga＿number_dir_path + "_" + str(not_duplicate_number))
        #             created_directory_path = manga＿number_dir_path + "_" + str(not_duplicate_number)
        #             break
        #         else:
        #             not_duplicate_number += 1
        
        return created_directory_path

class ChromeDriver(Files):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1000, 1400)

    def _get(self, uri):
        self.driver.get(uri)
        time.sleep(1)

    def get_manga_title(self):
        return self.driver.find_element_by_xpath('//*[@id="comicDetail"]/h1/a').text
    
    def get_manga_numbers(self):
        return self.driver.find_element_by_xpath('//*[@id="comicData"]').text

    def get_image_list(self):
        """
        ページ内の必要なimgelementを取得
        
        Returns
        -------
        element_list : list
            保存するimgの要素を返す
        """
        element_list = []
        img_list = self.driver.find_elements_by_tag_name("img")
        for i in img_list:
            id_name = i.get_attribute("id")
            src = i.get_attribute("src")
            if 'cvs' in id_name:
                print("id_name", id_name)
                print("src", src)
                element_list.append(i)
        return element_list
    
    def take_capture_by_element(self, element, save_path):
        """
        要素をキャプチャ

        Parameters
        ----------
        element : WebElement
            要素
        """
        png = element.screenshot_as_png
        with open(save_path, "wb") as f:
            f.write(png)
    
    def _move_to_element(self, element):
        """
        要素を表示領域に持っていく

        Parameters
        ----------
        element : WebElemet
        """
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.perform()

    
    def _quit(self):
        self.driver.quit()



def main():
    try:
        d = ChromeDriver()

        file_list = glob.glob(r'E:\susumuTabuchi\Downloads\chrome\*')
        a = 0
        for f in file_list:
            d._get(f)
            manga_tatle = d.get_manga_title()
            number_of_stories = d.get_manga_numbers()
            save_path = d.create_manga_directory(manga_tatle, number_of_stories)
            element_list = d.get_image_list()
            min_num, zero = d.get_min_filenumber(save_path)
            fin_count = 0
            for e in element_list:
                file_name = str(min_num).zfill(zero) + ".png"
                # d._move_to_element(e)
                d.take_capture_by_element(e, save_path + "\\" + file_name)
                min_num += 1
                print(file_name + " take")
                fin_count += 1


            


            a += 1
            if a == 2:
                break
        # time.sleep(60)
    except Exception as e:
        print(e)
    finally:
        d._quit()
        print('fin')

if __name__ == '__main__':
    main()