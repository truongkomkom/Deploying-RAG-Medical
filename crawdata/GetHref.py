from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import urllib.parse
import concurrent.futures
from threading import Lock
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lock cho việc ghi file
file_lock = Lock()

def create_driver():
    """Tạo một instance mới của webdriver với các options phù hợp"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Chạy ẩn browser
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def get_initial_links(url):
    """Lấy danh sách links ban đầu từ trang chủ"""
    driver = create_driver()
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.SectionList_sectionListItem__NNP4c a"))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, "div.SectionList_sectionListItem__NNP4c a")
        links = set(urllib.parse.unquote(elem.get_attribute("href")) 
                   for elem in elements if elem.get_attribute("href"))
        logger.info(f"Tìm thấy {len(links)} links ban đầu")
        return links
    except Exception as e:
        logger.error(f"Lỗi khi lấy links ban đầu: {e}")
        return set()
    finally:
        driver.quit()

def process_link(parent_link):
    """Xử lý một link và trả về các links con"""
    driver = create_driver()
    try:
        driver.get(parent_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
        
        elements = driver.find_elements(By.TAG_NAME, "a")
        all_links = set(urllib.parse.unquote(elem.get_attribute("href")) 
                       for elem in elements if elem.get_attribute("href"))
        
        # Lọc links
        filtered_links = {link for link in all_links 
                         if link.startswith(parent_link) and len(link) > len(parent_link)}
        
        # Ghi links vào file an toàn với threading
        with file_lock:
            with open("links_data.txt", "a", encoding="utf-8") as f:
                for link in filtered_links:
                    f.write(link + "\n")
        
        logger.info(f"Đã xử lý {parent_link}: tìm thấy {len(filtered_links)} links")
        return filtered_links
    
    except Exception as e:
        logger.error(f"Lỗi khi xử lý {parent_link}: {e}")
        return set()
    finally:
        driver.quit()

def main():
    # URL gốc
    base_url = "https://www.msdmanuals.com/vi/professional/health-topics"
    
    # Xóa nội dung file cũ
    with open("links_data.txt", "w", encoding="utf-8") as f:
        f.write("")
    
    # Lấy danh sách links ban đầu
    initial_links = get_initial_links(base_url)
    if not initial_links:
        logger.error("Không tìm thấy links ban đầu. Dừng chương trình.")
        return

    # Xử lý các links với ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tất cả các công việc
        future_to_url = {executor.submit(process_link, url): url 
                        for url in initial_links}
        
        # Xử lý kết quả khi hoàn thành
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                sub_links = future.result()
                logger.info(f"Hoàn thành xử lý {url}: {len(sub_links)} sub-links")
            except Exception as e:
                logger.error(f"Lỗi khi xử lý {url}: {e}")

    logger.info("Đã hoàn thành việc crawl tất cả links")

if __name__ == "__main__":
    main()