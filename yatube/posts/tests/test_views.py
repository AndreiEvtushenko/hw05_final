import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 2',
            slug='2',
            description='Тестовое описание 2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_page_correct_template(self):
        """URL-адрес использует шаблон posts/index.html."""
        post = PostViewsTests.post
        group = PostViewsTests.group
        templates_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': post.author}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': post.pk}): 'posts/post_detail.html',
            reverse('posts:create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': post.pk}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                print(f'Finished with {template}')

    def test_index_page_list_is_1(self):
        """Проверка количества постов на страницу index"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        list_posts = response.context.get('page_obj')
        self.assertEqual(len(list_posts), 1)
        print('На страницу index выводиться правильное количество объектов')

    def test_post_detail_page_correct_id(self):
        """Проверка поста по id на странице post_detail"""
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_object = response.context['posts'][0]
        post_id = first_object.pk
        self.assertEqual(post_id, self.post.pk)
        print(f'На страницу post_detail выводить пост {self.post.id}')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        post = PostViewsTests.post
        response = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        post_object = response.context['page_obj'][0]
        post_author = post_object.author
        post_text = post_object.text
        post_slug = post_object.group
        post_image = post_object.image
        self.assertEqual(post_author, post.author)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_slug, post.group)
        self.assertEqual(post_image, post.image)
        print('Проверка index_page успешно завершена')

    def test_pages_correct_context(self):
        """URL-адрес использует шаблон posts/index.html."""
        post = PostViewsTests.post
        group = PostViewsTests.group
        templates_page_names = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list',
                    kwargs={'slug': group.slug}): 'page_obj',
            reverse('posts:profile',
                    kwargs={'username': post.author}): 'page_obj',
            reverse('posts:post_detail',
                    kwargs={'post_id': post.pk}): 'posts',
        }
        for reverse_name, page_object in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_object = response.context[page_object][0]
                self.assertEqual(post_object.image, post.image)
                print(f'Finished with {reverse_name}')

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                print(f'Finished with {value}, {expected}')

    def test_create_page_additional(self):
        """Шаблон create сформирован с правильным контекстом."""
        cache.clear()
        response_index = self.authorized_client.get(reverse('posts:index'))
        post_object = response_index.context['page_obj'][0]
        post_pk = post_object.pk
        self.assertEqual(post_pk, self.post.pk)
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        cache.clear()
        post_object = response_group_list.context['page_obj'][0]
        post_pk = post_object.pk
        self.assertEqual(post_pk, self.post.pk)
        cache.clear()
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        post_object = response_profile.context['page_obj'][0]
        post_pk = post_object.pk
        self.assertEqual(post_pk, self.post.pk)
        self.assertFalse(
            Post.objects.filter(
                group=self.group_1
            ).exists()
        )

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post = PostViewsTests.post
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                print(f'Finished with {value}, {expected}')


class PaginatorViewsTest(TestCase):
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
        cls.posts = [Post(
            author=cls.user,
            text=i,
            group=PaginatorViewsTest.group,) for i in range(13)]
        Post.objects.bulk_create(cls.posts)
        cache.clear()

    def test_paginator_contains_correct_records(self):
        """Проверка паджинатора на корректное
            количество записаей на страницу"""
        count_posts_first_page = 10
        count_posts_second_page = 3
        templates_page_names = {
            reverse('posts:index'): 'posts:index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts:group_list',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts:profile',
        }
        for page, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client.get(page)
                self.assertEqual(len(response.context['page_obj']),
                                 count_posts_first_page)
                print(f'Finished with {template} {count_posts_first_page}')
            with self.subTest(template=template):
                response = self.client.get(page, {"page": 2})
                self.assertEqual(len(response.context['page_obj']),
                                 count_posts_second_page)
                print(f'Finished with {template} {count_posts_second_page}')


class FollowTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='test_user_1')
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.user_1)

        cls.user_2 = User.objects.create_user(username='test_user_2')
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)

        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост 1',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовый пост 2',
        )

    def test_profile_follow(self):
        """Проверка создания подписки на автора"""
        self.authorized_client_1.post(
            reverse('posts:profile_follow',
                    args=[self.user_2.username]))
        self.assertTrue(Follow.objects.filter
                        (user=self.user_1, author=self.user_2).exists())

    def test_profile_unfollow(self):
        """Проверка удаления подписки на автора"""
        Follow.objects.create(user=self.user_1, author=self.user_2)
        self.authorized_client_1.post(
            reverse('posts:profile_unfollow',
                    args=[self.user_2.username]))
        self.assertFalse(Follow.objects.filter
                         (user=self.user_1, author=self.user_2).exists())

    def test_feed(self):
        """Проверка корректного контекста на странице follow_index
            с постами на подписаннго автора"""
        Follow.objects.create(user=self.user_1, author=self.user_2)
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.post_2.text)
        self.assertNotContains(response, self.post_1.text)
