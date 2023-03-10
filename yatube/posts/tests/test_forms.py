import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    def test_create_post_authorized_client(self):
        """Валидная форма создает запись в post."""
        # Подсчитаем количество записей в group
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': '1',
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                group=self.group.slug,
                text='Тестовый текст'
            ).exists()
        )

    def test_create_post_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': '1',
            'image': self.uploaded,
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('posts:create'),
            data=form_data,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, '/auth/login/?next=/create/')
        # Проверяем, увеличилось ли число постов
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что не создалась запись с заданным слагом
        self.assertFalse(
            Post.objects.filter(
                group=self.group.slug,
                text='Тестовый текст'
            ).exists()
        )

    def test_post_edit_post_authorized_client(self):
        """Валидная форма изменяет запись в post."""
        # Подсчитаем количество записей в group
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Другой тестовый текст',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        # Проверяем изменение в посте
        self.assertNotEqual('Другой тестовый текст', self.post.text)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_post_guest_client(self):
        """Валидная форма изменяет запись в post."""
        # Подсчитаем количество записей в group
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Другой тестовый текст',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        # Проверяем изменение в посте
        self.assertNotEqual('Другой тестовый текст', self.post.text)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment_authorized_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post.pk,
            'author': self.user,
            'text': 'Тестовый коммент',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        # Проверяем, что не создалась запись с заданным слагом
        self.assertTrue(
            Comment.objects.filter(
                post=self.post.pk,
                text='Тестовый коммент'
            ).exists()
        )

    def test_create_comment_guest_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post.pk,
            'author': self.guest_client,
            'text': 'Тестовый коммент',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')
        # Проверяем, увеличилось ли число постов
        self.assertNotEqual(Comment.objects.count(), comment_count + 1)
        # Проверяем, что не создалась запись с заданным слагом
        self.assertFalse(
            Comment.objects.filter(
                post=self.post.pk,
                text='Тестовый коммент'
            ).exists()
        )
