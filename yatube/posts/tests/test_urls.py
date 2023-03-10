from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    # Проверяем общедоступные страницы
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = PostURLTests.post
        group = PostURLTests.group
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{group.slug}/': 'posts/group_list.html',
            f'/profile/{post.author}/': 'posts/profile.html',
            f'/posts/{post.pk}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем несуществующую страницу
    def test_unexisting_url_exists_at_desired_location(self):
        """Страница unexisting не существует."""
        response = self.guest_client.get('gest.html')
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_create_url_exists_at_desired_location(self):
        """Страница 'create/' доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_edit_url_exists_at_desired_location(self):
        """Страница 'posts/edit/' доступна авторизованному пользователю."""
        post = PostURLTests.post
        print(f'Страница с адресом PK = {post.pk}, {post.author}, {post.text}')
        response = self.authorized_client.get(f'/posts/{post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем редиректы для неавторизованного пользователя
    def test_create_url_exists_redirect_anonymous(self):
        """Страница 'create/' перенаправляет анонимного
        пользователя.
        """
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_posts_edit_url_redirect_anonymous(self):
        """Страница 'posts/edit/' перенаправляет анонимного
        пользователя.
        """
        post = PostURLTests.post
        response = self.guest_client.get(f'/posts/{post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Проверяем редиректы для неавторизованного пользователя
    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_posts_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /task/test_slug/ перенаправит анонимного
        пользователя на страницу логина.
        """
        post = PostURLTests.post
        response = self.guest_client.get(f'/posts/{post.pk}/edit/',
                                         follow=True)
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{post.pk}/edit/'))

    # Проверка вызываемых HTML-шаблонов
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        post = PostURLTests.post
        group = PostURLTests.group
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{group.slug}/': 'posts/group_list.html',
            f'/profile/{post.author}/': 'posts/profile.html',
            f'/posts/{post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
