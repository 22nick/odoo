from odoo import models, fields, api
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Важно: использование в неинтерактивном режиме
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

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
            # 1. СОЗДАЕМ ФИГУРУ ЯВНО (не через plt.figure)
            # Это гарантирует, что у каждой записи будет свой изолированный объект
            fig = Figure(figsize=(5, 5), dpi=110)
            canvas = fig.add_subplot(111) # Создаем оси внутри фигуры

            if not rec.line_ids:
                rec.graph_image = False
                continue

            lines = rec.line_ids.sorted('time')
            x = lines.mapped('time')
            y1 = lines.mapped('line_1')
            y2 = lines.mapped('line_2')

            # 2. РАБОТАЕМ ЧЕРЕЗ ОБЪЕКТ AX (canvas)
            # Левая ось
            color_1 = '#1f77b4'
            lns1 = canvas.plot(x, y1, color=color_1, label=rec.line_1_label, linewidth=2, marker='o')
            # canvas.set_xlabel('Время')
            # canvas.set_ylabel(rec.line_1_label, color=color_1, fontsize=11, fontweight='bold')
            canvas.tick_params(axis='y', labelcolor=color_1)
            canvas.grid(True, linestyle=':', alpha=0.5)

            # Правая ось
            color_2 = '#d62728'
            ax2 = canvas.twinx() 
            lns2 = ax2.plot(x, y2, color=color_2, label=rec.line_2_label, linewidth=2, marker='s')
            # ax2.set_ylabel(rec.line_2_label, color=color_2, fontsize=11, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor=color_2)

            # --- НАСТРОЙКА НАЧАЛА КООРДИНАТ (0,0) ---
        
            # 1. Фиксируем начало оси X на 0. 
            # Если вы хотите, чтобы справа тоже был запас, можно оставить правый край автоматическим
            canvas.set_xlim(left=0) 

            # 2. Фиксируем начало левой оси Y на 0
            canvas.set_ylim(bottom=0)

            # 3. Фиксируем начало правой оси Y на 0
            ax2.set_ylim(bottom=0)

            # 4. (Опционально) Добавляем жирные линии осей X=0 и Y=0
            canvas.axhline(0, color='black', linewidth=1.5) # Горизонтальная линия нуля
            canvas.axvline(0, color='black', linewidth=1.5) # Вертикальная линия нуля
            
            # Объединение легенды
            # lns = lns1 + lns2
            # labs = [l.get_label() for l in lns]
            # canvas.legend(lns, labs, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)

            # fig.suptitle(rec.name, fontsize=14)
            fig.tight_layout()

            # 3. СОХРАНЕНИЕ БЕЗ ИСПОЛЬЗОВАНИЯ PLT
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            rec.graph_image = base64.b64encode(buf.getvalue())

            # 4. ОЧИСТКА ПАМЯТИ
            # В объектном подходе важно явно освобождать ресурсы
            fig.clf() 
            plt.close(fig) # На всякий случай, если фигура попала в менеджер pyplot
        
        
        
            
class TimeChartLine(models.Model):
    _name = 'time.chart.line'
    _order = 'time'

    chart_id = fields.Many2one('time.chart')
    time = fields.Float('Time')
    line_1 = fields.Float('Value 1')
    line_2 = fields.Float('Value 2')

