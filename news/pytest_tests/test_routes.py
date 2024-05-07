# Импортируем библиотеку pytest.
import pytest
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse
# Импортируем класс HTTPStatus.
from http import HTTPStatus
# Импортируем функцию проверки редиректа.
from pytest_django.asserts import assertRedirects


# Устанавливаем маркер подключения к БД.
@pytest.mark.django_db
# Устанавливаем перечень страниц для проверки.
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    ),
)
def test_pages_availability(
        client,
        name,
        args,
):
    # Вместо прямого указания адреса
    # получаем его при помощи функции reverse().
    url = reverse(name, args=args)
    # Загружаем страницу.
    response = client.get(url)
    # Проверяем, что код ответа равен статусу OK (он же 200).
    assert response.status_code == HTTPStatus.OK


# Устанавливаем перечень пользователей и ожидаемых для них ответов.
@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
# Устанавливаем перечень страниц для проверки.
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('comment_id_for_args')),
        ('news:delete', pytest.lazy_fixture('comment_id_for_args')),
    ),
)
def test_availability_for_comment_edit_and_delete(
        parametrized_client,
        name,
        args,
        expected_status,
):
    # Вместо прямого указания адреса
    # получаем его при помощи функции reverse().
    url = reverse(name, args=args)
    # Загружаем страницу.
    response = parametrized_client.get(url)
    # Проверяем, что код ответа равен статусу ожидаемого для пользователя.
    assert response.status_code == expected_status


# Устанавливаем перечень страниц для проверки.
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('comment_id_for_args')),
        ('news:delete', pytest.lazy_fixture('comment_id_for_args')),
    ),
)
def test_redirect_for_anonymous_client(client, name, args):
    # Устанавливаем адрес страницы переадресации
    login_url = reverse('users:login')
    # Формируем адрес страницы обращения.
    url = reverse(name, args=args)
    # Устанавливаем адрес на которой должен попасть пользователь после авторизации.
    expected_url = f'{login_url}?next={url}'
    # Загружаем страницу.
    response = client.get(url)
    # Проверяем переадресацию.
    assertRedirects(response, expected_url)