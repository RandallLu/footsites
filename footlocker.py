import urllib.request
import urllib.error
import urllib.parse
import re
import http.cookiejar
from gzip import decompress
from datetime import datetime

#




# Let's go


"""
For footlocker, the requestKey will change after you add the item more than twice. It also changes when you add it at
least one time and when you refresh the page.
So here the idea is that we load the page once, and add it to cart no more than twice
No sure if the addToCart request failed it counts.
The requestKey is within the page source. So we need to find out the product page, then search through the code to find
out the requestKey, then add to cart. Every time we refresh the page, we need to search for the requestKey.
"""

"""
Need to figure out a way to stay in that connection and then make a post request
Not to post the request when open the page
It is to post the request after opening the page and search out the requestKey

Maybe cookie handler? may be it is. -> Yes, cookie can do the trick
Maybe connection? session? -> This is using requests module, which I might learn later.

possible checkout form
Two more cookie keys: ORDERAUTH, CHECKOUT_SESSION
https://www.footlocker.com/checkout/eventGateway?&method=validateShipMethodPane
https://www.footlocker.com/checkout/eventGateway?&method=validateBillPane
https://www.footlocker.com/checkout/eventGateway?&method=validatePaymentMethodPane
https://www.footlocker.com/checkout/eventGateway?&method=validateReviewPane
"""


url_footlocker = "http://www.footlocker.com"
url_footlocker_product_link = "http://www.footlocker.com/product/model:137127/sku:84664020/jordan-retro-6-mens/black/white/"
url_footlocker_addToCart_link = "http://www.footlocker.com/catalog/miniAddToCart.cfm?secure=0&"
url_footlocker_showCart_link = "http://www.footlocker.com/shoppingcart/default.cfm?"
url_footlocker_checkout_link = "https://www.footlocker.com/checkout/?uri=checkout"

user_Agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" \
             "55.0.2883.5 Safari/537.36"


header_footlocker_product_link = {
    "Host": 'www.footlocker.com',
    "User-Agent": user_Agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": 1,
    "Accept-Encoding": "gzip"
}

header_footlocker_add_link ={
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=ascii",
    "Host": "www.footlocker.com",
    "Origin": "http://www.footlocker.com",
    "Referer": "http://www.footlocker.com/product/model:262605/sku:43392611/nike-kd-9-mens/kevin-durant/red/white/",
    "X-Requested-With": "XMLHttpRequest"
}

# Here we first create a cookieJar instance to handle the first time we load the page and we extract the requestKey
cookie_jar_product_link = http.cookiejar.CookieJar()
cookie_processor_product_link = urllib.request.HTTPCookieProcessor(cookie_jar_product_link)
opener_product_link = urllib.request.build_opener(cookie_processor_product_link)
req = urllib.request.Request(url_footlocker_product_link, headers=header_footlocker_product_link)

try:
    res_product_link = opener_product_link.open(req)
except urllib.error.HTTPError as e:
    print("Cannot process product link")
    print("Reason is", e.code)
else:
    print(str(datetime.now()), "Successfully open the product page")
    charset = res_product_link.headers.get_content_charset()
    read = decompress(res_product_link.read())
    read = read.decode(charset)
    pattern_search_requestKey = re.compile("var requestKey = \'(.*?)\'")
    pattern_search_sku = re.compile("name=\"sku\" value=\"(.*?)\"")
    pattern_search_model = re.compile("name=\"the_model_nbr\" value=\"(.*?)\"")
    pattern_search_price = re.compile("name=\"selectedPrice\" value=\"(.*?)\"")
    pattern_search_name = re.compile("name=\"model_name\" value=\"(.*?)\"")
    pattern_search_size = re.compile("\"AVAILABLE_SIZES\":\[\" (.*?)\",")
    requestKey = re.findall(pattern_search_requestKey, read)
    sku = re.findall(pattern_search_sku, read)
    model = re.findall(pattern_search_model, read)
    price = re.findall(pattern_search_price, read)
    name = re.findall(pattern_search_name, read)
    size = re.findall(pattern_search_size, read)
    if requestKey is None:
        print("Failed to retrieve requestKey")
    else:
        # I don't know why but for some reason I don't have to post the data. Rather I can just include them inline
        # maybe because of the inlineAddtoCart var? But I set it to 0 it also works
        inline = "storeCostOfGoods=0.00&lineItemId=&&requestKey={0}&hasXYPromo=false" \
                 "&sameDayDeliveryConfig=false&sku={1}&the_model_nbr={2}&model_name={3}" \
                 "&skipISA=no&selectedPrice=%24{4}&qty=1&size={5}&fulfillmentType=SHIP_TO_HOME&storeNumber" \
                 "=00000&coreMetricsDo=true&coreMetricsCategory=Add+to+Wish+List+-+PDP&quantity=1&inlineAddToCart=1".\
            format(requestKey[0], "BA7748", 236754, name[0].replace(" ", "+"), price[0], "10.5")
        print(str(datetime.now()), "Successfully retrieve information")
        # create the cookie used to add to cart, from the product link
        cookie_product_link = ''
        for item in cookie_jar_product_link:
            cookie_product_link += item.name + '=' + item.value + ";"
        header_footlocker_add_link["Cookie"] = cookie_product_link
        result_link = url_footlocker_addToCart_link + inline
        req_again = urllib.request.Request(url_footlocker_addToCart_link + inline, headers=header_footlocker_add_link)

        # create another cookieJar instance to handle after we add the item to cart
        # This is because after adding, some values in the old cookie will change and I don't know how to modify the
        # original cookie so I just create another cookieJar
        cookie_jar_addToCart = http.cookiejar.CookieJar()
        cookie_processor_addToCart = urllib.request.HTTPCookieProcessor(cookie_jar_addToCart)
        opener_again_addToCart = urllib.request.build_opener(cookie_processor_addToCart)
        try:
            # res_again = urllib.request.urlopen(req_again)
            res_addToCart = opener_again_addToCart.open(req_again)
        except urllib.error.HTTPError as e:
            print(str(datetime.now()), "Cannot add the item to cart")
            print(e.reason, e.code)
        else:
            print(str(datetime.now()), "Successfully add the item to cart")
            charset = res_addToCart.headers.get_content_charset('utf-8')
            # print(cookie_jar_addToCart)
            read = decompress(res_addToCart.read())
            read = read.decode(charset)
            # print(read)

            # The next part is to show the cart. But now we need the new cookie value
            # Set-Cookie:INLINECARTSUMMARY=1%2C149%2E99;expires=Tue, 01-Jan-2047 23:57:54 GMT;path=/
            # Set-Cookie:CARTSKUS=43392611;path=/
            # create the cookie used to show the cart, from add to cart
            cookie_addToCart = ''
            # First from the last cookie get those unchanged values
            for item in cookie_jar_product_link:
                if item.name != "INLINECARTSUMMARY" and item.name != 'CARTSKUS':
                    cookie_addToCart += item.name + '=' + item.value + ";"
            # get the changed values
            for item in cookie_jar_addToCart:
                if item.name == "INLINECARTSUMMARY" or item.name == 'CARTSKUS':
                    cookie_addToCart += item.name + '=' + item.value + ";"
            # print(cookie_addToCart)

            # Now the problem is that the show car header is little different from add link header
            # It add a id value. Now assume the cookie is fine, which is updated with new inlinecartsummary and cartsku
            # values.
            # Where to find this id value so that we can fill in the referer value ?
            # "Referer":http://www.footlocker.com/product/sku:43392611/model:262605/?cm=&size=09%2E0&id=825916783&lineItemQty=1
            # I am gonna build another header for the show cart request
            '''header_footlocker_showCart = {
                "Referer": "http://www.footlocker.com/product/model:262605/sku:43392611/nike-kd-9-men\s "
                           "kevin-durant/red/white/",
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
                "Connection": "keep-alive",
                "Host": "www.footlocker.com",
                "Upgrade-Insecure-Requests": 1,
                "User-Agent": user_Agent,
                "Cookie": cookie_addToCart
            }'''
            # It seems that this header doesn't work? Don't know why but the add to cart header worked
            header_footlocker_add_link["Cookie"] = cookie_addToCart
            req_third = urllib.request.Request(url_footlocker_showCart_link, headers=header_footlocker_add_link)
            cookie_jar_showCart = http.cookiejar.CookieJar()
            cookie_processor_showCart = urllib.request.HTTPCookieProcessor(cookie_jar_showCart)
            opener_showCart = urllib.request.build_opener(cookie_processor_showCart)
            try:
                # res_third = urllib.request.urlopen(req_third)
                res_third = opener_showCart.open(req_third)
            except urllib.error.HTTPError as e:
                print(str(datetime.now()), "Cannot show the cart")
                print(str(datetime.now()), "reason:", e.reason, e.code)
            else:
                charset = res_third.headers.get_content_charset('utf-8')
                read_third = decompress(res_third.read())
                read_third = read_third.decode(charset)
                pattern_empty = re.compile("Your Cart is Empty")
                match = re.findall(pattern_empty, read_third)
                if match:
                    print("Adding to cart failed")
                else:
                    print(str(datetime.now()), "In cart: ")
                    # This below may or may not work. Depends on the form of the code of the cart page
                    pattern = re.compile("\"LINEITEMID\":(.*?),.*?\"PRICE\":(.*?),.*?\"MODEL_NBR\":("
                                         ".*?),.*?\"PRODUCTNAME\":(.*?),.*?\"QTY\":(.*?),.*?\"SKU\":("
                                         ".*?),.*?\"SIZE\":(.*?),")
                    result = re.findall(pattern, read_third)
                    sku = result[0][5]
                    model_nbr = result[0][2]
                    product = result[0][3]
                    size = result[0][6]
                    qty = result[0][4]
                    price = result[0][1]
                    line_item_id = result[0][0]
                    output = str("sku: {0}\nmodel_nbr: {1}\nproduct: {2}\nsize: {3}\nqty: {4}\nprice: {5}"
                                 "\nline_item_id: {6}").format(sku, model_nbr, product, size, qty, price, line_item_id)
                    print(output)

                    # The next step is to find out how to transfer out the cart so that I can use browser to open it
                    # And then find out the format for submitting the order for me
                    # Maybe how to search for the product link? link scraper?

