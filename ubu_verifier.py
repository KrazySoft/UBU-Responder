from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from pprint import pprint

def login(driver):
    driver.get('https://ubu.app/')
    driver.implicitly_wait(10)

    account = driver.find_element_by_css_selector('input[type=tel]')
    password = driver.find_element_by_css_selector('input[type=password]')
    login = driver.find_element_by_css_selector('button[class=auth-button]')

    account.send_keys(current_app.config['ACCOUNT_NO']) #Account number excluding leading 0 or +27 so only 123456789
    password.send_keys(current_app.config['ACCOUNT_PIN']) #full 6 digit pin

    login.click()

    return driver


def navigate_to_transfer_history(driver):
    history = driver.find_element_by_css_selector('a[href="/history"]')

    history.click()

    transferred = driver.find_element_by_css_selector('a[href="/history/transfer"]')

    transferred.click()

    driver.find_element_by_css_selector('table[class=ubu-history-table]')
    return driver


def get_transfer_data(keyword = None, cost = 0):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(chrome_options=options)

    driver = login(driver)

    driver = navigate_to_transfer_history(driver)

    soup = BeautifulSoup(driver.page_source, features="html.parser")

    driver.close()

    data = []
    table = soup.find('table', attrs={'class':'ubu-history-table'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if cols:
            transfer = {'amount': cols[0].text.strip(), 'desc': cols[1].text.strip(), 'from': cols[2].text.strip(), 'to': cols[3].text.strip(), 'date': cols[4].text.strip(), 'time':cols[5].text.strip()}
            if not keyword:
                data.append(transfer)
            elif keyword.lower() == transfer['desc'].lower():
                if cost == 0:
                    data.append(transfer)
                elif cost == float(transfer['amount'][::-1]):
                    data.append(transfer)

    return data


def verify_users():
    db = get_db()
    unverified_count = db.execute('SELECT COUNT(id) as "NUM_UNVER" '
        'FROM user '
        'WHERE access_level = 0'
    ).fetchone()
    print(unverified_count)
    if unverified_count['NUM_UNVER'] > 0:
        unverified = db.execute(
            'SELECT id, account_no '
            'FROM user '
            'WHERE access_level = 0 '
        ).fetchall()
        payments = get_transfer_data('treasure', 50)
        confirmed_account_numbers = [payment['from'] for payment in payments]
        for unverified_account in unverified:
            if unverified_account['account_no'] in confirmed_account_numbers:
                db.execute(
                    'UPDATE users '
                    'SET access_level = 1 '
                    'WHERE id = ? ',
                    (unverified_account['id'],)
                )
                db.commit()


if __name__ == '__main__':
    start = datetime.now()
    data = get_transfer_data()
    pprint(data)
    end = datetime.now()
    print("Ended: {}".format((end - start).total_seconds()))
