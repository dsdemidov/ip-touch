import configparser
import requests
import json
from math import ceil


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class YandexPdd(metaclass=Singleton):
    def __init__(self):
        self.errors = []
        self.domains = []
        config = configparser.RawConfigParser()
        config.read('config')
        try:
            self.pddToken = config.get('Yandex', 'pdd-token')
            self.host = config.get('Yandex', 'host')
            self.itemsPerList = 10
        except configparser.Error as e:
            self.errors.append(e)
            return None

    def getExternalIP(self):
        try:
            request = requests.get('https://api.ipify.org?format=json')
        except requests.exceptions.RequestException as e:
            self.errors.append(e)
            return False
        response = request.json()
        return response['ip']

    def searchDnsRecord(self, targetDomain, targetSubdomain):
        for i in range(len(self.domains)):
            # Ищем нужный домен
            domain = self.domains[i]
            if domain.name == targetDomain:
                for k in range( len(domain.dnsRecords) ):
                    # Ищем поддомен
                    record = domain.dnsRecords[k]
                    if record.subdomain == targetSubdomain:
                        return record
                        break
                break
        return False

    def getDomains(self):
        domainList = []

        # Получаем первые 10 доменов
        result = self.getDomainList(1)

        if not result:
            return False

        domainList.extend(result['domains'])

        # Теперь мы знаем сколько всего страниц с доменами надо получить
        overallDomainCount = int( result['total'] )
        overallPages = ceil( overallDomainCount / self.itemsPerList )

        if overallPages > 1:
            for i in range(2, overallPages + 1):
                result = self.getDomainList(i)
                if not result:
                    return False
                domainList.extend(result['domains'])

        # Можем формировать список из моделей
        for i in range(len(domainList)):
            domainDesc = domainList[i]
            self.domains.append( Domain( domainDesc['name'], domainDesc['status']) )

        return self.domains

    def getDomainList(self, page):
        params = {
         'page' : page,
         'on_page' : self.itemsPerList
        }
        result = self.makeRequest('/api2/admin/domain/domains', params)
        if not result:
            return False
        if result['success'] == 'ok':
            return result
        else:
            self.errors.append({'getDomainList': result['error']})
            return False

    def getDNSRecords(self, name):
        params = {
         'domain' : name,
        }
        result = self.makeRequest('/api2/admin/dns/list', params)
        if not result:
            return False
        if result['success'] == 'ok':
            return result
        else:
            self.errors.append({'getDNSRecords': "{} – {}".format(result['domain'],result['error'] )})
            return False

    def editDNSRecord(self, params):
        result = self.postRequest('/api2/admin/dns/edit', params)
        if not result:
            return False
        if result['success'] == 'ok':
            return result
        else:
            self.errors.append({'editDNSRecord': "{} – {}".format(result['domain'],result['error'] )})
            return False

    def URL(self, uri):
        return "{}{}".format(self.host, uri)

    def makeRequest(self, uri, params=None):
        headers = {
            'PddToken' : self.pddToken
        }
        try:
            request = requests.get(self.URL(uri), params=params, headers=headers)
        except requests.exceptions.RequestException as e:
            self.errors.append(e)
            return False
        return request.json()

    def postRequest(self, uri, params=None):
        headers = {
            'PddToken' : self.pddToken
        }
        try:
            request = requests.post(self.URL(uri), params=params, headers=headers)
        except requests.exceptions.RequestException as e:
            self.errors.append(e)
            return False
        return request.json()


class Domain():
    def __init__( self, name, status ):
        self.name = name
        self.status = status
        self.dnsRecords = []
        # Тут же получаем DNS записи
        self.getDNSRecords()

    def __repr__(self):
        return self.name

    def getDNSRecords(self):
        app = YandexPdd()
        dnsRecordsList = app.getDNSRecords(self.name)
        for i in range(len(dnsRecordsList['records'])):
            DR = dnsRecordsList['records'][i]
            self.dnsRecords.append( DNSRecord(
                DR['record_id'],
                DR['type'],
                DR['domain'],
                DR['fqdn'],
                DR['ttl'],
                DR['subdomain'],
                DR['content'],
                DR['priority']
            ))
        return self.dnsRecords


class DNSRecord():
    def __init__(self, record_id, type, domain, fqdn, ttl, subdomain, content, priority ):
        self.record_id = record_id
        self.type = type
        self.domain = domain
        self.fqdn = fqdn
        self.ttl = ttl
        self.subdomain = subdomain
        self.content = content
        self.priority = priority

    def __repr__(self):
        return "{}: {} – {}".format(self.type, self.fqdn, self.content)

    def save(self):
        app = YandexPdd()
        params = {
            'domain' : self.domain,
            'record_id' : self.record_id,
            'content' : self.content,
            'priority' : self.priority,
            'subdomain' : self.subdomain,
            'ttl' : self.ttl
        }
        result = app.editDNSRecord(params)
        if result['success'] == 'ok':
            return True
        else:
            self.errors.append({'editDNSRecord': "{} – {}".format(result['domain'],result['error'] )})
            return False
