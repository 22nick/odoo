# -*- coding: utf-8 -*-
{
    'name': 'Time Chart Manager',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Управление временными линейными диаграммами',
    'description': """
        Модуль для создания и управления временными линейными диаграммами
        с параметрами time, power, resistance
    """,
    'author': 'Your Company',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/time_chart_views.xml',
        'reports/time_chart_report.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'time_chart/static/src/js/chart_widget.js',
            'time_chart/static/src/xml/chart_widget.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
