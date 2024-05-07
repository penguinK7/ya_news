# Импортируем класс HTTPStatus.
from http import HTTPStatus
# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from news.forms import BAD_WORDS, WARNING
# Импортируем класс модели комментария.
from news.models import Comment
# Импортируем функцию проверки редиректа и ошибки валидации формы.
from pytest_django.asserts import assertRedirects, assertFormError


def test_anonymous_user_cant_create_comment(
        anonymous_client,
        comment_form_data,
        detail_url,
):
    # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
    # предварительно подготовленные данные формы с текстом комментария.
    anonymous_client.post(detail_url, data=comment_form_data)
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
    assert comments_count == 0


def test_user_can_create_comment(
        author,
        author_client,
        detail_url,
        comment_form_data,
        news,
):
    # Совершаем запрос через авторизованный клиент.
    response = author_client.post(detail_url, data=comment_form_data)
    # Проверяем, что редирект привёл к разделу с комментами.
    assertRedirects(response, f'{detail_url}#comments')
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Убеждаемся, что есть один комментарий.
    assert comments_count == 1
    # Получаем объект комментария из базы.
    comment = Comment.objects.get()
    # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
    assert comment.text == comment_form_data['text']
    assert comment.news, news
    assert comment.author, author


def test_user_cant_use_bad_words(
        author_client,
        detail_url,
):
    # Формируем данные для отправки формы; текст включает
    # первое слово из списка стоп-слов.
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    # Отправляем запрос через авторизованный клиент.
    response = author_client.post(detail_url, data=bad_words_data)
    # Проверяем, есть ли в ответе ошибка формы.
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    # Дополнительно убедимся, что комментарий не был создан.
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
        author_client,
        comment,
        comment_delete_url,
        comments_url,
):
    # От имени автора комментария отправляем DELETE-запрос на удаление.
    response = author_client.delete(comment_delete_url)
    # Проверяем, что редирект привёл к разделу с комментариями.
    # Заодно проверим статус-коды ответов.
    assertRedirects(response, comments_url)
    # Считаем количество комментариев в системе.
    comments_count = Comment.objects.count()
    # Ожидаем ноль комментариев в системе.
    assert comments_count == 0


def test_user_cant_delete_comment_of_another_user(
        comment,
        comment_delete_url,
        not_author_client,
):
    # Выполняем запрос на удаление от пользователя-читателя.
    response = not_author_client.delete(comment_delete_url)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что комментарий по-прежнему на месте.
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_edit_comment(
        author_client,
        comment,
        comment_edit_url,
        comment_form_data,
        comments_url,
):
    # Выполняем запрос на редактирование от имени автора комментария.
    response = author_client.post(comment_edit_url, data=comment_form_data)
    # Проверяем, что сработал редирект.
    assertRedirects(response, comments_url)
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст комментария соответствует обновленному.
    assert comment.text == comment_form_data['text']


def test_user_cant_edit_comment_of_another_user(
        not_author_client,
        comment,
        comment_edit_url,
        comment_form_data,
):
    # Выполняем запрос на редактирование от имени другого пользователя.
    response = not_author_client.post(comment_edit_url, data=comment_form_data)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст остался тем же, что и был.
    assert comment.text != comment_form_data['text']