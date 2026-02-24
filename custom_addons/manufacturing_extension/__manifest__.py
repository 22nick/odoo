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
    'depends': ['base', 'maintenance', 'mrp', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/equipment_ext.xml',
        'views/product_extend.xml',
        'views/workorder_charge.xml',
        'views/operations_steps.xml',
        'views/manufacturing_ext.xml',
        # 'data/operation_types_data.xml', # initional data for operation types (examle)
        'data/product_defaults.xml',
        'data/decimal_precision.xml',
        'views/material_params.xml',
        'views/standard_info.xml',
        'views/time_chart_views.xml',
        'reports/manufacturing_order_report.xml',
        # 'reports/cutting_operation_report.xml',
        'reports/workorder_operation_report.xml',
        'reports/mrp_production_report_ext.xml',
        # 'reports/heating_operation_report.xml', 
        'reports/report_cutting_opertions_steps_template.xml',
        'reports/report_heating_opertions_steps_template.xml',
        'reports/report_grinding_opertions_steps_template.xml',
        'reports/report_forging_opertions_steps_template.xml',
        'reports/report_machining_opertions_steps_template.xml',
        'reports/report_smelting_opertions_steps_template.xml',
        'reports/report_remelting_opertions_steps_template.xml',
        'reports/manufactoring_final_quality_report.xml',
    ],

    "assets":{
        "web.assets_backend": [
            'manufacturing_extension/static/lib/fabric.min.js',
            'manufacturing_extension/static/src/js/layout_editor.js',
            'manufacturing_extension/static/src/xml/layout_editor.xml',
        ]
    }


   
}

#/home/user/odoo19env/bin/python3 /home/user/odoo/odoo-bin -c /home/user/odoo/odoo.conf -u manufacturing_extension

# sudo systemctl start odoo

# sudo systemctl status odoo
