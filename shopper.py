# import module
from bs4 import BeautifulSoup
import codecs
import pyperclip
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
from webdriver_manager.chrome import ChromeDriverManager


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/90.0.4430.212 Safari/537.36",
    "Accept-Language": "en-US, en;q=0.5",
}

if len(sys.argv) < 4:
    print("Usage: shopper.py <url> <max-pages-to-compile> <max-tokens>")
    exit(0)


def cus_rev(soup):
    data_str = ""

    search = soup.find_all(
        "span",
        class_=["a-size-base", "review-text", "review-text-content"],
    )
    for item in search:
        data_str = data_str + item.get_text()

    result = data_str.split("\n")
    return (result, len(search))


def tokenize(input_str):
    return len(input_str) // 4


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
base_url = sys.argv[1]
base_url = base_url.replace("&pageNumber=1", "")
product_name = base_url.split("/")[3]
wait = WebDriverWait(driver, 20)

page = 1
maxPage = int(sys.argv[2])
rev_result = []
token_limit = int(sys.argv[3])
while True:
    if page >= maxPage:
        break
    if page == 1:
        url = base_url
    else:
        url = base_url + f"&pageNumber={page}"
    page += 1

    print("Scrolling down..")
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight,)")

    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "review-text")))
    driver.execute_script("return document.readyState")

    page_source = driver.page_source

    soup = BeautifulSoup(page_source, features="html.parser")

    rev_data, count = cus_rev(soup)
    if count == 0:
        break
    for review in rev_data:
        r = review.strip()
        if r == "":
            pass
        else:
            rev_result.append(r)
    tkn = tokenize(str(rev_result))
    if tkn > token_limit:
        print(f"Reducing tokens to <={token_limit} from {tkn}")
        while tokenize(str(rev_result)) > token_limit:
            rev_result = rev_result[:-1]
        break

driver.close()
print(rev_result)

with open("context.txt", "r") as f:
    prompt = f.read()

prompt = prompt.replace("{$1}", product_name).replace("{$2}", ",\n".join(rev_result))
print(prompt)

pyperclip.copy(prompt)
print("Prompt copied to clipboard!")
