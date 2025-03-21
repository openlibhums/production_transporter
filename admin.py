__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "OLH Tech Team"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities, Birkbeck, UoL"

from django.contrib import admin

from plugins.production_transporter import models
from utils import admin_utils as utils_admin_utils


class TransportFilesAdmin(utils_admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', 'files_selected_by')
    list_filter = ('article__journal',)
    search_fields = ('article__pk', 'article__title')
    raw_id_fields = ('article', 'files_selected_by')

admin_list = [
    (models.TransportFiles, TransportFilesAdmin),
]

[admin.site.register(*t) for t in admin_list]
