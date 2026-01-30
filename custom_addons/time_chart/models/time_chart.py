# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TimeChart(models.Model):
    _name = 'time.chart'
    _description = 'Временная линейная диаграмма'
    _order = 'name'

    name = fields.Char(string='Название диаграммы', required=True)
    description = fields.Text(string='Описание')
    date_created = fields.Date(string='Дата создания', default=fields.Date.today)
    line_ids = fields.One2many('time.chart.line', 'chart_id', string='Данные диаграммы')
    line_count = fields.Integer(string='Количество точек', compute='_compute_line_count')
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)


class TimeChartLine(models.Model):
    _name = 'time.chart.line'
    _description = 'Элемент временной диаграммы'
    _order = 'time'

    chart_id = fields.Many2one('time.chart', string='Диаграмма', required=True, ondelete='cascade')
    time = fields.Float(string='Время (сек)', required=True, digits=(12, 2))
    power = fields.Float(string='Мощность (Вт)', required=True, digits=(12, 2))
    resistance = fields.Float(string='Сопротивление (Ом)', required=True, digits=(12, 2))
    sequence = fields.Integer(string='Порядок', default=10)

    _sql_constraints = [
        ('time_chart_unique', 'unique(chart_id, time)', 
         'Для каждой диаграммы время должно быть уникальным!')
    ]
