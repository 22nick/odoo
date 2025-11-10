{
    'name': "manufacturing_extension",

    'summary': "Extends manufacturing module with additional features",

    'description': """
1. Connect Eqıuipment to Work Centers 


    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/equipment_ext.xml'
    ],

    "assets":{
        "web.assets_backend": [
            # "student/static/src/xml/list_controller.xml",
            # "student/static/src/js/script.js"
        ]
    }


   
}

