{
    'name': "Student Inherit Views",

    'summary': "Inherit views of student module",

    'description': """
Inherit views of student module
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'student', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/student_extend.xml',
        
    ],

    "assets":{
        "web.assets_backend": [
            "student_inherit_views/static/src/xml/forging_fields_validate.xml",
            "student_inherit_views/static/src/js/forging_fields_validate.js"
        ]
    }


    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}

