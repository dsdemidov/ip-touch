from classes import YandexPdd
from ipaddress import ip_address
import configparser
import socket


def main():
    config = configparser.RawConfigParser()
    config.read('config')
    try:
        targetDomain = config.get('General', 'targetDomain')
        targetSubdomain = config.get('General', 'targetSubdomain')
        targetIP = config.get('General', 'targetIP')
    except configparser.Error as e:
        print(e)
        return False

    # Ищем локальный IP
    if targetIP == 'local':
        newIP = socket.gethostbyname(socket.gethostname())
    else:
        newIP = targetIP
    try:
        newIP = ip_address(newIP)
    except ValueError as e:
        print("Неверно указан IP адрес: ", e)
        return False

    app = YandexPdd()
    if len(app.errors) > 0:
        print(app.errors)
        return False

    app.getDomains()

    dnsRecord = app.searchDnsRecord(targetDomain, targetSubdomain)

    if not dnsRecord:
        print( "Искомый поддомен не найден.")
        return False

    # Если все ок, меняем IP адрес и сохраняем
    dnsRecord.content = newIP
    if dnsRecord.save():
        print( "IP адрес успешно обновлен." )

    if len(app.errors) > 0:
        print("При выполнении приложения возникли ошибки: ", app.errors)

if __name__ == '__main__':
    main()

