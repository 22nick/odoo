from odoo import api, models, fields
from odoo.fields import Domain
import re

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # product_reference_no = fields.Char(string='Material reference No.', default='[New]', readonly=True, copy=False, index=True, required=True, help="Reference Number of the material")
    product_reference_no = fields.Char(
        string='Material reference No.',
        related='product_tmpl_id.product_reference_no',
        store=True,  # ВАЖНО: store=True для индексации и поиска
        readonly=False,
        copy=False,
        index=True,
        help="Reference Number of the material"
    )
    
    heat_no = fields.Char(string='Heat No.', 
        related='product_tmpl_id.heat_no', 
        required=True, 
        store=True,  # ВАЖНО: store=True для индексации и поиска
        readonly=False,
        copy=False,
        index=True, help="Heat Number of the material", 
        default="N/A")
    
    
                
    @api.model_create_multi
    def create(self, vals_list):
        
        for val in vals_list:
            if val.get('product_reference_no', '[New]') == '[New]':
                val['product_reference_no'] = (self.env['ir.sequence'].
                next_by_code('product_sequense'))
        records = super(ProductProduct, self).create(vals_list)
         
        for rec in records:
            if rec.product_variant_ids:
                # Мы пишем в поле шаблона, а Odoo сама должна обновить related.
                # Но если store=True глючит, можно обновить варианты напрямую:
                rec.product_variant_ids.write({'product_reference_no': rec.product_reference_no})
                
                        
        return records

    @api.model
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):


        rec = super(ProductProduct, self).web_name_search(name, specification, domain, operator, limit)
        res = []
        for r in rec:
            product = self.browse(r['id'])
            
            r['__formatted_display_name'] = f"--{product.product_reference_no}--\t {r['__formatted_display_name']}"
            # print("Modified Record :: ", r)
            res.append(r)

        return res
    
    @api.model
    def _search_display_name(self, operator, value):
        print("Search Display Name Called :self: ", self)
        is_positive = not operator in Domain.NEGATIVE_OPERATORS
        combine = Domain.OR if is_positive else Domain.AND
        domains = [
            [('name', operator, value)],
            [('default_code', operator, value)],
        ]
        if operator == 'in':
            domains.append([('barcode', 'in', value)])
            for v in value:
                if isinstance(v, str) and (m := re.search(r'(\[(.*?)\])', v)):
                    domains.append([('default_code', '=', m.group(2))])
        elif operator.endswith('like') and is_positive:
            domains.append([('barcode', 'in', [value])])
        if partner_id := self.env.context.get('partner_id'):
            supplier_domain = [
                ('partner_id', '=', partner_id),
                '|',
                ('product_code', operator, value),
                ('product_name', operator, value),
            ]
            domains.append([('product_tmpl_id.seller_ids', 'any', supplier_domain)])
        return combine(domains)
   
    # product_reference_no = fields.Char(string='Material reference No.', default='[New]', readonly=True, copy=False, index=True, required=True, help="Reference Number of the material")


class ProductTemplate(models.Model):
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
    
    display_dimensions = fields.Char(string='Display Dimensions') #, compute='_compute_display_dimensions')    
    
    # forging_material = fields.Char(string='Material')
    forging_material = fields.Many2one('material.grade', string='Grade of Material')


    product_reference_no = fields.Char(string='Material reference No.', default='[New]', readonly=False, copy=False, index=True, required=True, help="Reference Number of the material")

    heat_no = fields.Char(string='Heat No.', required=True, help="Heat Number of the material", default="N/A")
    
    # slag_data_ids = fields.One2many('product.slag.data', 'product_id', string='Slag Inclusion Data')
    slag_data_id = fields.Many2one('product.slag.data', string='Slag Inclusion Data')
    
    # physical_data_ids = fields.One2many('product.physical.data', 'product_id', string='Physical Data')
    physical_data_id = fields.Many2one('product.physical.data', string='Physical Data')


    @api.model_create_multi
    def create(self, vals_list):
        
        for val in vals_list:
            if val.get('product_reference_no', '[New]') == '[New]':
                val['product_reference_no'] = (self.env['ir.sequence'].
                next_by_code('product_sequense'))
        records = super(ProductTemplate, self).create(vals_list)
         
        for rec in records:
            if rec.product_variant_ids:
                # Мы пишем в поле шаблона, а Odoo сама должна обновить related.
                # Но если store=True глючит, можно обновить варианты напрямую:
                rec.product_variant_ids.write({'product_reference_no': rec.product_reference_no})
                
                        
        return records
    

    
    @api.onchange('forging_type')
    def _change_forging_type(self):
        print("Forging Type Changed", self)
        

