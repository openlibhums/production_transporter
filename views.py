from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from janeway_ftp import ftp

from plugins.production_transporter import (
    plugin_settings,
    utils as pt_utils,
    forms,
    models as pt_models
)
from core import forms as core_forms, files, models as core_models
from core.templatetags.files import file_type
from submission import models
from utils import setting_handler
from security.decorators import has_journal, any_editor_user_required


@has_journal
@staff_member_required
def index(request):
    settings = [
        {
            'name': 'enable_transport',
            'object': setting_handler.get_setting('plugin', 'enable_transport', request.journal),
        },
        {
            'name': 'transport_production_manager',
            'object': setting_handler.get_setting('plugin', 'transport_production_manager', request.journal),
        },
        {
            'name': 'transport_email_production_manager',
            'object': setting_handler.get_setting('plugin', 'transport_email_production_manager', request.journal),
        },
        {
            'name': 'transport_ftp_address',
            'object': setting_handler.get_setting('plugin', 'transport_ftp_address', request.journal),
        },
        {
            'name': 'transport_ftp_username',
            'object': setting_handler.get_setting('plugin', 'transport_ftp_username', request.journal),
        },
        {
            'name': 'transport_ftp_password',
            'object': setting_handler.get_setting('plugin', 'transport_ftp_password', request.journal),
        },
        {
            'name': 'transport_ftp_remote_path',
            'object': setting_handler.get_setting('plugin', 'transport_ftp_remote_path', request.journal),
        },
        {
            'name': 'transport_file_selection_text',
            'object': setting_handler.get_setting('plugin', 'transport_file_selection_text', request.journal),
        }
    ]
    setting_group = 'plugin'
    manager_form = core_forms.GeneratedSettingForm(
        settings=settings
    )
    if request.POST:
        manager_form = core_forms.GeneratedSettingForm(
            request.POST,
            settings=settings,
        )
        if manager_form.is_valid():
            manager_form.save(
                group=setting_group,
                journal=request.journal,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Form saved.',
            )
            return redirect(
                reverse('production_transporter_manager')
            )

    template = 'production_transporter/index.html'
    context = {
        'manager_form': manager_form,
    }
    return render(
        request,
        template,
        context,
    )


@any_editor_user_required
def handshake_url(request):
    articles_in_stage = models.Article.objects.filter(
        stage=plugin_settings.STAGE,
    )
    template = 'production_transporter/handshake.html'

    if request.POST:
        if 'download' in request.POST:
            article_pk = request.POST.get('download')
            article = get_object_or_404(
                models.Article,
                pk=article_pk,
                journal=request.journal,
            )
            try:
                zipped_folder_path, folder_string = pt_utils.prep_zip_folder(
                    request,
                    article,
                )
                return files.serve_temp_file(
                    zipped_folder_path,
                    f"{folder_string}.zip",
                )
            except ObjectDoesNotExist:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'This article has no files set for deposit.'
                )
        if 'ftp' in request.POST:
            article_pk = request.POST.get('ftp')
            article = get_object_or_404(
                models.Article,
                pk=article_pk,
                journal=request.journal,
            )
            try:
                zipped_folder_path, folder_string = pt_utils.prep_zip_folder(
                    request,
                    article,
                )
                ftp_server, ftp_username, ftp_password, ftp_remote_directory = pt_utils.get_ftp_details(
                    request.journal,
                )
                ftp.send_file_via_ftp(
                    ftp_server=ftp_server,
                    ftp_username=ftp_username,
                    ftp_password=ftp_password,
                    remote_path=ftp_remote_directory,
                    file_path=zipped_folder_path,
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Article files transported via FTP.',
                )
                pt_utils.send_notification(request, article)
            except ObjectDoesNotExist:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'This article has no files set for deposit.'
                )

    context = {
        'articles_in_stage': articles_in_stage,
    }
    return render(
        request,
        template,
        context,
    )


@any_editor_user_required
def jump_url(request, article_id):
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    article_files = core_models.File.objects.filter(
        article_id=article.pk,
    ).order_by(
        '-last_modified',
    )
    try:
        transport_files = article.transportfiles
    except AttributeError:
        transport_files = None

    form = forms.TransportFilesForm(
        instance=transport_files,
        article=article,
        article_files=article_files,
        files_selected_by=request.user
    )
    if request.POST:
        form = forms.TransportFilesForm(
            request.POST,
            instance=transport_files,
            article=article,
            article_files=article_files,
            files_selected_by=request.user,
        )
        if form.is_valid():
            form.save()
            if 'save_and_send' in request.POST:
                zipped_folder_path, folder_string = pt_utils.prep_zip_folder(
                    request,
                    article,
                )
                ftp_server, ftp_username, ftp_password, ftp_remote_directory = pt_utils.get_ftp_details(
                    request.journal,
                )
                ftp.send_file_via_ftp(
                    ftp_server=ftp_server,
                    ftp_username=ftp_username,
                    ftp_password=ftp_password,
                    remote_path=ftp_remote_directory,
                    file_path=zipped_folder_path,
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Article files transported via FTP.',
                )
                pt_utils.send_notification(request, article)
            messages.add_message(
                request,
                messages.SUCCESS,
                'File for transport saved.',
            )
            return redirect(
                reverse(
                    'production_transporter_handshake_url',
                )
            )

    manuscript_files = []
    other_files = []
    for _file in article_files:
        _type = file_type(article, _file)
        if _type == 'Manuscript':
            manuscript_files.append(_file)
        else:
            other_files.append(_file)

    template = 'production_transporter/jump.html'
    context = {
        'article': article,
        'form': form,
        'files': article_files,
        'manuscript_files': manuscript_files,
        'other_files': other_files,
        'file_text': setting_handler.get_setting(
            'plugin',
            'transport_file_selection_text',
            request.journal
        ).processed_value
    }
    return render(
        request,
        template,
        context,
    )
