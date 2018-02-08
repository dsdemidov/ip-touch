# IPTouch
## Обновление днс записи на pdd.yandex.ru локальным IP адресом

Небольшая утилита для автоматического обновления IP адреса на pdd.yandex.ru

Для начала настроим скрипт:

```
cd PATH_TO_THE_APP
cp config.dist config
chmod +x iptouch
sudo ln -s PATH_TO_THE_APP/iptouch /usr/local/bin
```
В файле config изменим настройки на свои.

Затем запускаем:

```
iptouch
```

Если все хорошо, то должны увидеть следующее:

```
IP адрес успешно обновлен.
```