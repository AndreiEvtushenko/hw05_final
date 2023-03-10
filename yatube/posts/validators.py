from django import forms


def validate_not_empty(value):
    # Проверка "а заполнено ли поле?"
    if value == '':
        raise forms.ValidationError(
            'Введите текст поста.',
            params={'value': value},
        )
