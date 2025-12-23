{
    'name': 'Vector Graphics Editor',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Simple vector graphics editor with shapes and text',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/vector_canvas_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vector_editor/static/src/js/vector_editor_field.js',
            'vector_editor/static/src/xml/vector_editor_field.xml',
        ],
    },
    'installable': True,
    'application': True,
}