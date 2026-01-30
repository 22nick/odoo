# -*- coding: utf-8 -*-
# from odoo import models, fields, api
# import json
# import base64
# import io
# Рекомендуется использовать matplotlib или pygal для генерации графиков в PDF
# import matplotlib.pyplot as plt 


from odoo import models, fields, api
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Важно: использование в неинтерактивном режиме
import matplotlib.pyplot as plt

class TimeChart(models.Model):
    _name = 'time.chart'
    _description = 'Time Chart'

    name = fields.Char('Название', required=True)
    
    # Поля для настройки осей
    line_1_label = fields.Char('Trend 1 Name', default='Value 1')
    line_1_unit = fields.Char('Trend 1 Unit', default='unit')
    
    line_2_label = fields.Char('Trend 2 Name', default='Value 2')
    line_2_unit = fields.Char('Trend 2 Unit', default='unit')
    
    line_ids = fields.One2many('time.chart.line', 'chart_id', string='Data')
    
    # Поле для хранения самого изображения
    graph_image = fields.Binary(compute='_compute_graph_image', string='Trends', store=False)

    @api.depends('line_ids', 'line_1_label', 'line_1_unit', 'line_2_label', 'line_2_unit', 'name')
    def _compute_graph_image(self):
        for rec in self:
            if not rec.line_ids:
                rec.graph_image = False
                continue

            lines = rec.line_ids.sorted('time')
            x = lines.mapped('time')
            y1 = lines.mapped('line_1')
            y2 = lines.mapped('line_2')

            color_1 = '#1f77b4' # Синий
            color_2 = '#d62728' # Красный

            fig, ax1 = plt.subplots(figsize=(12, 6), dpi=110)

            # Формируем названия для шкал: "Название, Ед.изм."
            label_1 = f"{rec.line_1_label or ''}, {rec.line_1_unit or ''}".strip(', ')
            label_2 = f"{rec.line_2_label or ''}, {rec.line_2_unit or ''}".strip(', ')

            # Левая ось
            lns1 = ax1.plot(x, y1, color=color_1, label=label_1, linewidth=2, marker='o')
            # ax1.set_xlabel('t, min')
            # ax1.set_ylabel(label_1, color=color_1, fontsize=11, fontweight='bold')
            ax1.tick_params(axis='y', labelcolor=color_1)
            ax1.grid(True, linestyle=':', alpha=0.5)

            # Правая ось
            ax2 = ax1.twinx()
            lns2 = ax2.plot(x, y2, color=color_2, label=label_2, linewidth=2, marker='s')
            # ax2.set_ylabel(label_2, color=color_2, fontsize=11, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor=color_2)

            # Объединяем легенду
            # lns = lns1 + lns2
            # labs = [l.get_label() for l in lns]
            # ax1.legend(lns, labs, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2)

            # plt.title(rec.name, fontsize=14, pad=20)
            fig.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            rec.graph_image = base64.b64encode(buf.getvalue())
            
class TimeChartLine(models.Model):
    _name = 'time.chart.line'
    _order = 'time'

    chart_id = fields.Many2one('time.chart')
    time = fields.Float('Time')
    line_1 = fields.Float('Value 1')
    line_2 = fields.Float('Value 2')





# class TimeChart(models.Model):
#     _name = 'time.chart'
#     _description = 'Time Chart Base'

#     name = fields.Char('Название диаграммы', required=True)
#     line_ids = fields.One2many('time.chart.line', 'chart_id', string='Данные')
    
#     # Поле для отображения графика в форме (JSON для виджета)
#     graph_data = fields.Text(compute='_compute_graph_data')
    
#     # Поле для хранения изображения для PDF
#     graph_image = fields.Binary(compute='_compute_graph_image', store=False)

#     @api.depends('line_ids.time', 'line_ids.line_1', 'line_ids.line_2')
#     def _compute_graph_data(self):
#         for rec in self:
#             # Сортируем данные по времени, чтобы график не "прыгал"
#             lines = rec.line_ids.sorted('time')
            
#             # Формат для стандартного Chart.js, который понимает Odoo
#             chart_data = [{
#                 'key': 'Линия 1',
#                 'values': [{'x': l.time, 'y': l.line_1} for l in lines],
#                 'color': '#7c7bad',
#             }, {
#                 'key': 'Линия 2',
#                 'values': [{'x': l.time, 'y': l.line_2} for l in lines],
#                 'color': '#ffbb78',
#             }]
#             rec.graph_data = json.dumps(chart_data)
        
#     def _compute_graph_image(self):
#         for rec in self:
#             # Генерация статического изображения для PDF с помощью Matplotlib
#             plt.figure(figsize=(8, 4))
#             times = [l.time for l in rec.line_ids]
#             y1 = [l.line_1 for l in rec.line_ids]
#             y2 = [l.line_2 for l in rec.line_ids]
            
#             plt.plot(times, y1, label='Line 1')
#             plt.plot(times, y2, label='Line 2')
#             plt.legend()
            
#             buf = io.BytesIO()
#             plt.savefig(buf, format='png')
#             rec.graph_image = base64.b64encode(buf.getvalue())
#             plt.close()

# class TimeChartLine(models.Model):
#     _name = 'time.chart.line'
#     _description = 'Chart Data Point'
#     _order = 'time asc'

#     chart_id = fields.Many2one('time.chart', ondelete='cascade')
#     time = fields.Float('Время (ч)') # или DateTime
#     line_1 = fields.Float('Значение 1')
#     line_2 = fields.Float('Значение 2')





# class TimeChart(models.Model):
#     _name = 'time.chart'
#     _description = 'Time line Chart'
#     _order = 'name'

#     name = fields.Char(string='Name', required=True)
#     description = fields.Text(string='Description')
#     date_created = fields.Date(string='Date', default=fields.Date.today)
#     line_ids = fields.One2many('time.chart.line', 'chart_id', string='Chatr Lines')
#     # time = fields.Float(related='line_ids.time', string='Time (min)', store=False)
#     # line_1 = fields.Float(related='line_ids.line_1', string='Line 1', store=False)
#     # line_2 = fields.Float(related='line_ids.line_2', string='Line 2', store=False)
#     time = fields.Float(compute='_compute_line_data', string='Time (min)', store=False)
#     line_1 = fields.Float(compute='_compute_line_data', string='Line 1', store=False)
#     line_2 = fields.Float(compute='_compute_line_data', string='Line 2', store=False)
#     line_count = fields.Integer(string='Point Number', compute='_compute_line_count')
    
#     @api.depends('line_ids')
#     def _compute_line_count(self):
#         for record in self:
#             record.line_count = len(record.line_ids)
            
#     @api.depends('line_ids')
#     def _compute_line_data(self):
#         for record in self:
#             record.time = record.line_ids.mapped('time')
#             record.line_1 = record.line_ids.mapped('line_1')
#             record.line_2 = record.line_ids.mapped('line_2')
#             return
           


# class TimeChartLine(models.Model):
#     _name = 'time.chart.line'
#     _description = 'Chart Line Point'
#     _order = 'time'

#     chart_id = fields.Many2one('time.chart', string='Chart', required=True, ondelete='cascade')
#     time = fields.Float(string='Time (min)', required=True, digits=(12, 2))
#     line_1 = fields.Float(string='Line 1', required=True, digits=(12, 2))
#     line_2 = fields.Float(string='Line 2', required=True, digits=(12, 2))
#     sequence = fields.Integer(string='Sequence', default=10)

#     _sql_constraints = [
#         ('time_chart_unique', 'unique(chart_id, time)', 
#          'Time points must be unique within a chart!'),
#     ]