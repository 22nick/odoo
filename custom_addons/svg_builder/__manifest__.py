# svg_builder/__manifest__.py
{
    'name': 'Odoo SVG Builder',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'SVG Builder with OWL 2 Components',
    'description': """
        A powerful SVG builder tool built with OWL 2 framework
        allowing users to create and edit SVG graphics directly in Odoo.
    """,
    "website": "https://www.linkedin.com/in/composercodes/",
    'author': 'Maged Ibrahim',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/svg_builder_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'svg_builder/static/src/js/svg_builder.js',
            'svg_builder/static/src/js/svg_components.js',
            'svg_builder/static/src/xml/svg_builder.xml',
            'svg_builder/static/src/css/svg_builder.css',
        ],
    },
    "images": ["static/description/banner.jpeg"],
    "license": "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}