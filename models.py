from django.db import models


class TransportLog(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    date_time = models.DateTimeField(
        auto_now_add=True,
    )
    updated_by = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f'Article #{self.article.pk} transported by {self.updated_by}'


class TransportFiles(models.Model):
    article = models.OneToOneField(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    files = models.ManyToManyField(
        'core.File',
        blank=True,
    )
    files_selected_by = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f'Transporter files for {self.article.title}'
