from bs4 import BeautifulSoup
import requests
import re
import xlsxwriter

ALLOW_ACCESS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

col = 0
row = 0


def media_markt(brand, model, memory):
    if memory > 128:
        memo = "128-01-gb-i-wiecej"
    elif 64 < memory <= 128:
        memo = "64-01-gb-128-gb"
    elif 32 < memory <= 64:
        memo = "32-01-gb-64-gb"
    elif 16 < memory < 32:
        memo = "16-01-gb-32-gb"
    else:
        memo = ""
    model_f = model.replace(" ", "-").lower() 
    return f"https://mediamarkt.pl/telefony-i-smartfony/smartfony/wszystkie-smartfony.{brand}/&pamiec-wbudowana={memo}&model={model_f}"

def info_from_markt(phone_names, model, memory, brand):
    phones = {}
    findings = []
    link = media_markt(brand, model, memory)

    for info in phone_names:   
        pricing = info.find_next("div", {"class": "pricing"})
        price_raw = pricing.find("span", {"class": "whole"})

        try:
            price_raw_clean = price_raw.text
        except AttributeError:
            continue 
        else:
            price_clean = int(price_raw_clean.replace("\n", "").strip())
                    
        phones.update({info.text: price_clean})

    for key, value in phones.items():
        if str(memory) in key:
            findings.append([key, value])

    if len(findings) <= 0:
        print(f"{model} {memory} GB not found")
    else:
        findings.insert(0, [link, "Media Markt"])
        
    return findings

def search_markt(brand, memory):
        print()
        shop = "Media Markt"
        print(shop)
        model = input("Enter the SPECIFIC model of the smartphone (eg. galaxy a52 || galaxy z flip3 5g  || iphone 14 pro): ")

        markt = requests.get(media_markt(brand, model, memory), headers={"User-Agent": ALLOW_ACCESS})
        
        if markt.status_code == 200:
            soup = BeautifulSoup(markt.content, "html.parser")
            phone_names = soup.find_all("h2", {"class": "title"})

            return info_from_markt(phone_names, model, memory, brand)
        
        else:
            print(f"ERROR {markt.status_code}")


def media_expert(brand, model, memory, page):
    model_f = model.replace(" ", "-").lower()
    return f"https://www.mediaexpert.pl/smartfony-i-zegarki/smartfony/pamiec-wbudowana-gb_{memory}/popularne-serie_{brand}-{model_f}?page={page}"

def search_expert_phones(soup, frst_phone_name, frst_phone_price):
    phone_names = []
    phone_prices = []

    if frst_phone_name and frst_phone_price:
        phone_names.append(frst_phone_name)
        phone_prices.append(frst_phone_price)

    for object in soup.find_all("span", {"whenvisible": "[object Object]"}):
        phone_name = object.find("h2", {"class": "name is-section"})

        try:
            phone_price = object.find("div", {"class": "main-price is-big"}).find("span", {"class": "whole"})
        except:
            continue

        phone_names.append(phone_name.text.replace("\n", "").strip())

        try:
            phone_price = int(phone_price.text.replace(u"\u202f", ""))
        except AttributeError:
            continue
        else:
            phone_prices.append(phone_price)
        
    return phone_names, phone_prices

def list_from_models_expert_or_euro(phones, model, memory):
    
    model_list = []   
    for key in phones.keys():
        key_ = key.lower()
        name_ = re.search(f"{model}(.*){memory}", key_)

        try:
            model_ = name_.group(1)
        except AttributeError:
            print(f"{model} {memory} GB not found")
            break
        else:    

            if "iphone" in key_:
                model_ = model_.replace("\u200c", "")
                if model_.strip() == "":
                    model_list.append(f"Press ENTER for regular {model}")

                else:
                    model_list.append(model_.strip())

            else:
                model_list.append(model_.strip() + str(memory) + "GB")

    model_list = set(model_list)

    models = ", ".join(model_list)

    return models

def info_expert_or_euro(phones, model_spec, model, memory, shop, page, brand):
    if shop == "Media Expert":
        link = media_expert(brand, model, memory, page)
    else:
        link = rtv_euro(model, memory, page)
    findings = []
    
    findings.append([link, shop])

    for key, value in phones.items():
        if "iphone" in key.lower():
            if model_spec == re.search(f"{model}(.*){memory}", key.lower()).group(1).strip().replace("\u200c", ""):
                findings.append([key, value]) 

        elif model_spec == re.search(f"{model}(.*){memory}", key.lower()).group(1).strip() + f"{memory}GB":
            findings.append([key, value])
                
    if len(phones) <= 0:
        findings.append(f"{model} {memory} GB not found in {shop}") 

    return findings

def search_expert(model, brand, memory):
    shop = "Media Expert"
    print()
    print(shop)

    model_f = model.replace(" ", "-").lower()
    pages_raw = requests.get(f"https://www.mediaexpert.pl/smartfony-i-zegarki/smartfony/pamiec-wbudowana-gb_{memory}/popularne-serie_{brand}-{model_f}")

    if pages_raw.status_code == 200:
        pages_soup = BeautifulSoup(pages_raw.content, "html.parser")
        pages_html = pages_soup.find("span", {"class": "from"})

        try:
            pages = int(pages_html.text[2:])
        except AttributeError:
            pages = 1

        for page in range(1, pages+1):
            expert = requests.get(media_expert(brand, model, memory, page), headers={"User-Agent": ALLOW_ACCESS})
            soup = BeautifulSoup(expert.content, "html.parser")

            frst_phone = soup.find("div", {"class": "offers-list"})
            frst_phone_name = frst_phone.find("h2", {"class": "name is-section"}).text.replace("\n", "").strip()

            try:
                frst_phone_price = int(frst_phone.find("div", {"class": "main-price is-big"}).find("span", {"class": "whole"}).text.replace(u"\u202f", ""))
            except AttributeError:
                continue

            phone_names, phone_prices = search_expert_phones(soup, frst_phone_name, frst_phone_price)
            
            phones = dict(zip(phone_names, phone_prices))

            models = list_from_models_expert_or_euro(phones, model, memory)

            if len(models) <= 0:
                break

            model_spec = input(f"Which model would you like: {model} [{models}]: ")

            return info_expert_or_euro(phones, model_spec, model, memory, shop, page, brand="")

    else:
        print(f"ERROR {pages_raw.status_code}")


def rtv_euro(model, memory, page):
    model_f = model.replace(" ", "-").lower()
    return f"https://www.euro.com.pl/telefony-komorkowe,pamiec-wbudowana-gb-!-{memory},seria!{model_f},strona-{page}.bhtml"

def search_euro(model, memory):
    shop = "RTV Euro AGD"
    print()
    print(shop)

    model_f = model.replace(" ", "-").lower()
    pages_raw = requests.get(f"https://www.euro.com.pl/telefony-komorkowe,pamiec-wbudowana-gb-!-{memory},seria!{model_f}.bhtml")
    
    if pages_raw.status_code == 200:
        pages_soup = BeautifulSoup(pages_raw.content, "html.parser")
        pages_html = pages_soup.find("a", {"class": "paging-number"})

        try:
            pages = int(pages_html.text[2:])
        except AttributeError:
            pages = 1

        for page in range(1, pages + 1):
            euro = requests.get(rtv_euro(model, memory, page), headers={"User-Agent": ALLOW_ACCESS})
            soup = BeautifulSoup(euro.content, "html.parser")
            
            names = []
            prices = []

            for product in soup.find_all("div", {"class": "product-for-list"}):
                name_raw = product.find("h2", {"class": "product-name"}).find("a", {"class": "js-save-keyword"})
                price_raw = product.find("div", {"class": "price-normal selenium-price-normal"})
                
                try:
                    name = name_raw.text.replace("\n", "").replace("\t", "")
                    price = price_raw.text.replace("\n", "").replace("\t", "").replace("zł","").replace(u"\xa0", "")
                except AttributeError:
                    continue

                names.append(name)
                prices.append(int(price))

            phones = dict(zip(names, prices))

            models = list_from_models_expert_or_euro(phones, model, memory)

            if len(models) <= 0:
                break

            model_spec = input(f"Which model would you like: {model} [{models}]: ")

            return info_expert_or_euro(phones, model_spec, model, memory, shop, page, brand="")

    else:
        print(f"ERROR {pages_raw.status_code}")        


def add_to_worksheet(list, worksheet):
    global row
    global col

    try:
        for phone_name, phone_price in list:
            worksheet.write(row, col, phone_name)
            worksheet.write(row, col + 1, phone_price)
            row += 1
    except TypeError:
        worksheet.write(row, col, "")
        row += 1
    finally:
        worksheet.write(row, col, "")
        row += 1

def save_search_excel(filename):
    workbook = xlsxwriter.Workbook(f"./excel_files/{filename}.xlsx")
    worksheet = workbook.add_worksheet()
    worksheet.set_column(0, 0, 65)

    memory = int(input("Enter the memory you are interested in [GB]: "))
    brand = input("Enter the brand of the smartphone: ")
    list_markt = search_markt(brand, memory)

    add_to_worksheet(list_markt, worksheet)

    print()

    model = input("Enter the GENERAL model (eg. galaxy s || z flip || fold || iphone 14): ")
    list_expert = search_expert(model, brand, memory)
    add_to_worksheet(list_expert, worksheet)

    list_euro = search_euro(model, memory)
    add_to_worksheet(list_euro, worksheet)

    workbook.close()


def main():
    filename = input("Enter the excel filename: ")
    save_search_excel(filename)


if __name__ == "__main__":
    main()