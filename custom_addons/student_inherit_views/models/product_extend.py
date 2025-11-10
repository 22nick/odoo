from odoo import api, models, fields


class ProductTemlpate(models.Model):
    _inherit = 'product.template'

    product_type = fields.Selection([
        ('forging', 'Forging'),
        ('ingot', 'Ingot'),
        ('part', 'Part'),
    ], string='Product Type', default='forging')

    forging_type = fields.Selection([
        ('round', 'Round Bar'),
        ('square', 'Square Bar'),
        ('rectangle', 'Rectangle Bar'),
        ('disk', 'Disk'),
        ('disk_hollow', 'Hollow Disk')
        
    ], string='Product Shape', default='round')

    forging_min_length = fields.Integer(string='Length (min)')
    forging_max_length = fields.Integer(string='Length (max)')
    forging_width = fields.Integer(string='Width')
    forging_height = fields.Integer(string='Height')
    forging_diameter = fields.Integer(string='Diameter')
    forging_diameter_inner = fields.Integer(string='Inner diameter')
    
    forging_material = fields.Char(string='Material')

    # reference_note = fields.Char(string="Reference Note")
    # print("Product Template Inherited Successfully")   

    @api.onchange('forging_type')
    def _change_forging_type(self):
        print("Forging Type Changed", self)

# class SaleOrder(models.Model):
#    _inherit = 'sale.order'



# class student_extend(models.Model):
#     _inherit = 'wb.student'

#     reference_note = fields.Char(string="Reference Note")   