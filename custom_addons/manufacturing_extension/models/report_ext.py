import io
import base64
from odoo import models
from pypdf import PdfReader, PdfWriter

class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # Применяем кастомную логику только к нужному отчёту
        report = self._get_report(report_ref)
        if report.report_name != "my_module.my_report_template":
            return super()._render_qweb_pdf(report_ref, res_ids, data)

        # 1. Генерируем обычный QWeb PDF (страницы 1-2)
        pdf_content, content_type = super()._render_qweb_pdf(
            report_ref, res_ids, data
        )

        # 2. Достаём готовый PDF (страницы 3-5), например из attachment
        record = self.env[report.model].browse(res_ids[0])
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", record._name), ("res_id", "=", record.id),
             ("name", "=", "appendix.pdf")],
            limit=1,
        )
        if not attachment:
            return pdf_content, content_type

        extra_pdf_bytes = base64.b64decode(attachment.datas)

        # 3. Склеиваем через pypdf
        writer = PdfWriter()

        reader_main = PdfReader(io.BytesIO(pdf_content))
        for page in reader_main.pages:
            writer.add_page(page)

        reader_extra = PdfReader(io.BytesIO(extra_pdf_bytes))
        for page in reader_extra.pages:
            writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        merged_pdf = output_stream.getvalue()

        return merged_pdf, "pdf"