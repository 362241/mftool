"""
    The MIT License (MIT)

    Copyright (c) 2020 Sujit Nayakwadi

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import requests
import json
from bs4 import BeautifulSoup
import datetime
from datetime import date,timedelta

class Mftool():
    """
    class which implements all the functionality for
    Mutual Funds in India
    """

    def __init__(self):
        self._session = requests.session()
        # URL list
        self._get_quote_url = 'https://www.amfiindia.com/spages/NAVAll.txt'
        self._get_scheme_url = 'https://api.mfapi.in/mf/'
        self._get_open_ended_equity_scheme_url = 'http://www.valueresearchonline.com/amfi/fund-performance-data/?' \
                                                 'end-type=1&primary-category=SEQ&category=CAT&amc=ALL'
        self._open_ended_equity_category = {'Large Cap': 'SEQ_LC',
                                            'Large & Mid Cap': 'SEQ_LMC',
                                            'Multi Cap': 'SEQ_MLC',
                                            'Mid Cap': 'SEQ_MC',
                                            'Small Cap': 'SEQ_SC',
                                            'Value': 'SEQ_VAL',
                                            'ELSS': 'SEQ_ELSS',
                                            'Contra': 'SEQ_CONT',
                                            'Dividend Yield': 'SEQ_DIVY',
                                            'Focused': 'SEQ_FOC'}

    def get_scheme_codes(self, as_json=False):
        """
        returns a dictionary with key as scheme code and value as scheme name.
        cache handled internally
        :return: dict / json
        """
        scheme_info = {}
        url = self._get_quote_url
        response = self._session.get(url)
        data = response.text.split("\n")
        for scheme_data in data:
            if ";INF" in scheme_data:
               scheme = scheme_data.split(";")
               scheme_info[scheme[0]] = scheme[3]

        return self.render_response(scheme_info, as_json)

    def is_valid_code(self, code):
        """
        check whether a given scheme code is correct or NOT
        :param code: a string scheme code
        :return: Boolean
        """
        if code:
            scheme_codes = self.get_scheme_codes()
            if code in scheme_codes.keys():
                return True
            else:
                return False
        else:
            return False

    def get_scheme_quote(self, code, as_json=False):
        """
        gets the quote for a given scheme code
        :param code: scheme code
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        if self.is_valid_code(code):
            scheme_info = {}
            url = self._get_quote_url
            response = self._session.get(url)
            data = response.text.split("\n")
            for scheme_data in data:
                if code in scheme_data:
                    scheme = scheme_data.split(";")
                    scheme_info['scheme_code'] = scheme[0]
                    scheme_info['scheme_name'] = scheme[3]
                    scheme_info['last_updated'] = scheme[5].replace("\r", "")
                    scheme_info['nav'] = scheme[4]
                    break
            return self.render_response(scheme_info, as_json)
        else:
            return None

    def get_scheme_details(self, code, as_json=False):
        """
        gets the scheme info for a given scheme code
        :param code: scheme code
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        if self.is_valid_code(code):
            scheme_info = {}
            url = self._get_scheme_url+code
            response = self._session.get(url).json()
            scheme_data = response['meta']
            scheme_info['fund_house'] = scheme_data['fund_house']
            scheme_info['scheme_type'] = scheme_data['scheme_type']
            scheme_info['scheme_category'] = scheme_data['scheme_category']
            scheme_info['scheme_code'] = scheme_data['scheme_code']
            scheme_info['scheme_name'] = scheme_data['scheme_name']
            scheme_info['scheme_start_date'] = response['data'][int(len(response['data']) -1)]
            return self.render_response(scheme_info, as_json)
        else:
            return None

    def get_scheme_historical_nav(self, code, as_json=False):
        """
        gets the scheme historical data till last updated for a given scheme code
        :param code: scheme code
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        if self.is_valid_code(code):
            scheme_info = {}
            url = self._get_scheme_url + code
            response = self._session.get(url).json()
            scheme_info = self.get_scheme_details(code)
            scheme_info.update(data= response['data'])
            return self.render_response(scheme_info, as_json)
        else:
            return None

    def calculate_balance_units_value(self, code, balance_units, as_json=False):
            """
            gets the market value of your balance units for a given scheme code
            :param code: scheme code, balance_units : current balance units
            :return: dict or None
            """
            code = str(code)
            if self.is_valid_code(code):
                scheme_info = {}
                scheme_info = self.get_scheme_quote(code)
                market_value = float(balance_units)*float(scheme_info['nav'])
                scheme_info.update(balance_units_value= "{0:.2f}".format(market_value))
                return self.render_response(scheme_info, as_json)
            else:
                return None

    def render_response(self, data, as_json=False):
            if as_json is True:
                return json.dumps(data)
            else:
                return data

    def get_scheme_historical_nav_year(self, code, year, as_json=False):
        """
        gets the scheme historical data of given year for a given scheme code
        :param code: scheme code
        :param code: year
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        if self.is_valid_code(code):
            scheme_info = {}
            data = []
            url = self._get_scheme_url + code
            response = self._session.get(url).json()
            nav = self.get_scheme_historical_nav(code)
            scheme_info = self.get_scheme_details(code)
            for dat in nav['data']:
                navDate = dat['date']
                d = datetime.datetime.strptime(navDate, '%d-%m-%Y')
                if d.year == int(year):
                    data.append(dat)
            if len(data) == 0:
                data.append({'Error': 'For Year '+str(year)+' Data is NOT available'})

            scheme_info.update(data=data)
            return self.render_response(scheme_info, as_json)
        else:
            return None

    def is_holiday(self):
        if date.today().strftime("%a") in ['Sat', 'Sun', 'Mon']:
            return True
        else:
            return False

    def get_friday(self):
        days = {'Sat': 1, 'Sun': 2, 'Mon': 3}
        diff = int(days[date.today().strftime("%a")]) - 1
        return (date.today() - timedelta(days=diff)).strftime("%d-%b-%Y")

    def get_open_ended_equity_scheme_performance(self, as_json=False):
        """
        gets the daily performance of open ended equity schemes for all AMCs
        :return: json format
        :raises: HTTPError, URLError
        """
        scheme_performance = {}
        for key in self._open_ended_equity_category.keys():
            scheme_performance_url = self._get_open_ended_equity_scheme_url.replace('CAT',self._open_ended_equity_category[key])
            scheme_performance[key] = self.get_daily_scheme_performance(scheme_performance_url, False)
        return self.render_response(scheme_performance,as_json)

    def get_daily_scheme_performance(self, performance_url,as_json):
        fund_performance = []
        if self.is_holiday():
            url = performance_url + '&nav-date=' + self.get_friday()
        else:
            url = performance_url + '&nav-date=' + date.today().strftime("%d-%b-%Y")
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        rows = soup.select("table tbody tr")
        try:
            for tr in rows:
                scheme_details = {}
                cols = tr.select("td.nav.text-right")
                scheme_details['scheme_name'] = tr.select("td")[0].get_text()
                scheme_details['benchmark'] = tr.select("td")[1].get_text()

                scheme_details['latest NAV- Regular'] = cols[0].contents[0]
                scheme_details['latest NAV- Direct'] = cols[1].contents[0]

                oneYr = tr.find_all("td", recursive=False, class_="1Y text-right", limit=2)
                scheme_details['1-Year Return(%)- Regular'] = oneYr[0].contents[0]
                scheme_details['1-Year Return(%)- Direct'] = oneYr[1].contents[0]

                threeYr = tr.find_all("td", recursive=False, class_="3Y text-right hidden", limit=2)
                scheme_details['3-Year Return(%)- Regular'] = threeYr[0].contents[0]
                scheme_details['3-Year Return(%)- Direct'] = threeYr[1].contents[0]

                fiveYr = tr.find_all("td", recursive=False, class_="5Y text-right hidden", limit=2)
                scheme_details['5-Year Return(%)- Regular'] = fiveYr[0].contents[0]
                scheme_details['5-Year Return(%)- Direct'] = fiveYr[1].contents[0]

                fund_performance.append(scheme_details)

        except Exception:
            return self.render_response(['The underlying data is unavailable for Today'], as_json)

        return self.render_response(fund_performance, as_json)

