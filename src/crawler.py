"""
/// @file crawler.py
/// @author Austin Vandegriffe
/// @date 2020-04-20
/// @brief Search CAS number and return name and standardized number
/// @pre No preprocessing required
/// @style K&R, "one true brace style" (OTBS), and '_' variable naming
/////////////////////////////////////////////////////////////////////
/// @references
/// ## https://webbook.nist.gov/chemistry/cas-ser/
/// ## https://en.wikipedia.org/wiki/CAS_Registry_Number#Format
/// ## isbn.py from https://drive.google.com/drive/u/0/folders/1l8x6ySlF5vjbWtSD497YaidGsVg99oLH
"""

from bs4 import BeautifulSoup as bs
import requests
import time


class InvalidCASError(Exception):
    """
        Exception class for invalid CAS numbers.
    """
    def __init__(self, *args):
        if args:
            self.number = args[0]
        else:
            self.number = None

    def __str__(self):
        if self.number:
            return f"Invalid CAS Number: {self.number}"
        else:
            return "Invalid CAS Number"


class CAS_Querier(object):
    def __init__(self):
        # Define sites to search, eval() will be called later since
        ## the variable 'cas' will be changing, so put any formatted
        ## strings in the string, i.e. 'f"{formatted}"' NOT f"formatted".
        self.nist_url = 'f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Units=SI"'
        self.nih_url = "https://chem.nlm.nih.gov/chemidplus/number/contains"
        self.sigmaaldrich_url = 'f"https://www.sigmaaldrich.com/catalog/search?' +\
                                 'interface=CAS%20No.&term={cas}&N=0&lang=en&r'  +\
                                 'egion=US&focus=product&mode=mode+matchall"'
    
    def nist_search(self, cas):
        """
            Query procedure for "webbook.nist.gov"
        """
        # Remove all spaces and '-' from CAS string
        ## this site ignores "-" and leading 0's
        r = requests.get(eval(self.nist_url))
        
        # If the site fails to find the CAS number
        ## more than 3 times, mark it as invalid.
        ## HTTP Code 200 := request has succeeded
        attempts = 1
        while r.status_code != 200:
            print(f"\t{r.status_code}, {type(r.status_code)}")
            if attempts > 3:
                raise InvalidCASError(cas)
            time.sleep(3)
            attempts += 1
            r = requests.get(eval(self.nist_url))

        # In the event of a successful request
        ## grab the page source.
        soup = bs(r.text, 'html5lib')

        if "Registry Number Not Found" in soup.text:
            # Site could not find record
            raise InvalidCASError(cas)


        # Navigate HTML to the CAS number
        ## and ingredient name.
        cas_name = soup.find("h1", {"id": "Top"}).text
        cas_num = []
        for i in soup.find_all("li"):
            if "CAS Registry Number:" in i.text:
                cas_num = i.text.split(": ")[-1].replace(" ","").split("-")
        if len(cas_num) != 3:
            raise InvalidCASError(cas)
        while len(cas_num[0]) < 7:
            cas_num[0] = "0" + cas_num[0]

        return (cas_name, "-".join(cas_num))
    
    def nih_search(self, cas):
        """
            Query procedure for "chem.nlm.nih.gov"
        """
        # Remove all spaces and '-' from CAS string
        cas = cas.replace(" ","").replace("-","")
        # Strip all leading zeroes.
        while cas[0] == '0':
            cas = cas[1:]

        # Request the webpage
        r = requests.get(f"{self.nih_url}/{cas}")

        # If the site fails to find the CAS number
        ## more than 3 times, mark it as invalid.
        ## HTTP Code 200 := request has succeeded
        attempts = 1
        while r.status_code != 200:
            if attempts > 3:
                raise InvalidCASError(cas)
            time.sleep(3)
            attempts += 1
            r = requests.get(f"{self.nih_url}/{cas}")

        # In the event of a successful request
        ## grab the page source.
        soup = bs(r.text, 'html5lib')
        
        # Navigate HTML to the CAS number
        ## and ingredient name.
        if "Substance Name:" in soup.text:
            cas_name = ""
            cas_num = []
            for i in soup.find_all("h1"):
                if "Substance Name:" in i.text:
                    k = i.text
                    for j in i.find_all("span"):
                        if "RN:" in j.text:
                            cas_num = j.text.replace('RN:\xa0',"").split('-')
                        k = k.replace(j.text,"")
                    cas_name = k.split('\xa0')[1]
                    break
            if len(cas_num) != 3:
                raise InvalidCASError(cas)
            while len(cas_num[0]) < 7:
                cas_num[0] = "0" + cas_num[0]

            return (cas_name, "-".join(cas_num))
        else:
            # The page source does not match that of
            ## a proper record.
            raise InvalidCASError(cas)
        
    def sigmaaldrich_search(self, cas):
        """
            Query procedure for "sigmaaldrich.com"
        """
        # Remove all spaces and '-' from CAS string
        cas = [x for x in cas if x.isdigit()]
        # Strip all leading zeroes.
        while cas[0] == '0':
            cas = cas[1:]
        # Put in proper CAS format:
        ##  #######-##-#
        cas = "".join(cas[0:-3]) + "-" + "".join(cas[-3:-1]) + "-" + cas[-1]

        # Request the webpage
        r = requests.get(eval(self.sigmaaldrich_url))

        # If the site fails to find the CAS number
        ## more than 3 times, mark it as invalid.
        ## HTTP Code 200 := request has succeeded
        attempts = 1
        while r.status_code != 200:
            if attempts > 3:
                raise InvalidCASError(cas)
            time.sleep(3)
            attempts += 1
            r = requests.get(f"{self.nih_url}/{cas}")

        # In the event of a successful request
        ## grab the page source.
        soup = bs(r.text, 'html5lib')

        # Navigate HTML to the CAS number
        ## and ingredient name.
        if not soup.find("div",{"id":"searchHero"}):
            raise InvalidCASError(cas)
        try:
            cas_name = soup.find("div",{"class":"productContainer-inner"}
                                ).find("h2",{"class":"name"}).text
            li_tags = soup.find("div",{"class":"productContainer-inner-content"}
                            ).find("li",{"class":"substance-display-attributes"}
                            ).find_all("li")
            for li in li_tags:
                if "cas number:" in li.text.lower():
                    cas_num = li.text.split('\xa0')[-1]
                    break
        except:
            raise InvalidCASError
                
        return (cas_name, cas_num)
    
    def search(self, cas):
        """
            Search for CAS number.
            Note:
                This can be improved by randomizing
                the order the websites are checked,
                allowing the program to query faster.
        """
        ret = (None, None)
        try:
            ret = self.nist_search(cas)
        except InvalidCASError:
            try:
                ret = self.nih_search(cas)
            except InvalidCASError:
                ret = self.sigmaaldrich_search(cas)

        return ret