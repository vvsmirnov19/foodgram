![example workflow](https://github.com/vvsmirnov19/foodgam/actions/workflows/main.yml/badge.svg)

## Описание проекта
Foodgram - проект социальной сети с возможностью публикации рецептов блюд, добавления их в избранное, корзину и формирования списка покупок.

Проект доступен по адресу https://foodgramsmirnov.hopto.org

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

## Стек
- python 3.9
- Django 3.2.3
- DRF 3.12.4
- Nginx
- Docker

## Как развернуть проект
На машине, в которой будет развернут проект, необходимы установленные Git и Docker.

1. Копируем проект на машину
```bash 
git clone https://github.com/vvsmirnov19/foodgram.git
```
2. Переходим в директорию проекта
```bash
cd foodgram
```
3. Создаем файл с переменными окружения .env
Он должен содержать следующие переменные:
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DB_HOST
DB_PORT
SECRET_KEY
ALLOWED_HOSTS
DEBUG
DB_POSTGRE
4. Для сборки из текущего репозитория выполняем:
```bash
docker compose up -d
```
Для сборки из Docker Hub выполняем:
```bash
docker compose -f docker-compose.production.yml up -d
```

Автор [Валерий Смирнов](https://github.com/vvsmirnov19)