from weasyprint import HTML
import cairocffi
import os
import gi
from gi.repository import GLib, Gtk
import subprocess
import sys
import time
from .share import share
# config = share.config
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path + '/data/')


class Printo:
    def __init__(self, url, landscape=False):
        self.operation = Gtk.PrintOperation()

        document = HTML(string=url).render()

        self.operation.connect('begin-print', self.begin_print, document)
        self.operation.connect('draw-page', self.draw_page, document)

        self.operation.set_use_full_page(False)
        self.operation.set_unit(Gtk.Unit.POINTS)
        self.operation.set_embed_page_setup(True)
        if landscape == True:
            pageSetup = Gtk.PageSetup()
            pageSetup.set_orientation(Gtk.PageOrientation.LANDSCAPE)
            self.operation.set_default_page_setup(pageSetup)

        settings = Gtk.PrintSettings()

        directory = GLib.get_user_special_dir(
            GLib.UserDirectory.DIRECTORY_DOCUMENTS) or GLib.get_home_dir()
        ext = settings.get(Gtk.PRINT_SETTINGS_OUTPUT_FILE_FORMAT) or 'pdf'
        uri = 'file://%s/weasyprint.%s' % (directory, ext)
        settings.set(Gtk.PRINT_SETTINGS_OUTPUT_URI, uri)
        self.operation.set_print_settings(settings)

    def run(self):
        self.operation.run(Gtk.PrintOperationAction.PRINT_DIALOG)

    def begin_print(self, operation, print_ctx, document):
        operation.set_n_pages(len(document.pages))

    def draw_page(self, operation, print_ctx, page_num, document):
        page = document.pages[page_num]
        cairo_context = print_ctx.get_cairo_context()
        cairocffi_context = cairocffi.Context._from_pointer(
            cairocffi.ffi.cast(
                'cairo_t **', id(cairo_context) + object.__basicsize__)[0],
            incref=True)
        page.paint(cairocffi_context, left_x=0, top_y=-40, scale=0.75)


class WeasyprintReport:
    def __init__(self):
        if share.config.locale == 'en_US':
            self.direction = 'left'
        else:
            self.direction = 'right'
        self.subjectHeaderStyle = 'style="text-align:center;"'
        self.detailHeaderStyle = 'style="text-align:' + \
            self.direction + '; font-size:9px;"'

    def doPrint(self, html, landscape=False):
        Printo(html, landscape).run()

    def showPreview(self, html, landscape=False):
        HTML(string=html, base_url=__file__).write_pdf('report.pdf')
        if sys.platform == 'linux':
            subprocess.call(["xdg-open", 'report.pdf'])
        else:
            os.startfile('report.pdf')
        time.sleep(3)
        os.remove('report.pdf')

    def createTable(self, report_header, report_data, col_wid=[]):
        hasWidth = True if len(col_wid) else False
        col_width = [None] * len(report_header)
        for i in range(0, len(report_header)):
            col_width[i] = 'style="width:' + \
                str(col_wid[i]) + 'pt" ' if hasWidth else ""
        i = 0
        if share.config.locale == 'en_US':
            text_align = "left"
            html = '<table>\
                    <thead><tr>'
            for header in report_header:
                html += '<th '+col_width[i]+'>' + header + '</th>'
                i += 1
            html += '</tr></thead>\
                    <tbody>'
            for row in report_data:
                html += '<tr>'
                for data in row:
                    html += '<td>' + str(data) + '</td>'
                html += '</tr>'
            html += '</tbody></table>'
        else:
            text_align = "right"
            html = '<table >\
                    <thead><tr>'
            report_header = report_header[::-1]
            col_width = col_width[::-1]
            for header in report_header:
                html += '<th '+col_width[i]+'>' + header + '</th>'
                i += 1
            html += '</tr></thead>\
                    <tbody>'
            for row in report_data:
                row = row[::-1]
                html += '<tr>'
                for data in row:
                    html += '<td>' + str(data) + '</td>'
                html += '</tr>'
            html += '</tbody></table>'
        html = '<!DOCTYPE html> <html> <head> \
                <style> @font-face {font-family: Vazir; src: url(data/font/Vazir.woff); } \
                table {border-collapse: collapse; border-bottom:1px solid black; text-align:'+text_align+'; width:100%; font-size:8pt;}\
                th {border: 2px solid black;  padding: 7pt;font-size:10pt;}\
                td {border-left:1px solid; border-right:1px solid; padding: 10pt;} \
                 body {font-family: "Vazir"} \
                 </style> \
                <meta charset="UTF-8"> </head>\
                <body>' + html + '</body> </html>'
        return html
