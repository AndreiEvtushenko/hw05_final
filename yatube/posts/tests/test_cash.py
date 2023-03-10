from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()
        print(cls.post.pk)

    def test_cash_index_page(self):
        """Проверка работы кеша на странице index."""
        # Запрашиваем пост на странице index
        response_first = self.authorized_client.get(reverse('posts:index'))
        # Изменим пост
        post_1 = Post.objects.get(pk=1)
        post_1.delete()
        # Второй раз pапрашиваем пост на странице index
        # Сравниваем результаты перед изменением поста
        response_second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_first.content, response_second.content)
        # Очистим кеш
        cache.clear()
        # Третий раз запрашиваем пост на странице index
        # Сравниваем результаты перед изменением поста
        response_third = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_first.content, response_third.content)
