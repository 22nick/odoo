from odoo import api, models, fields
from odoo.fields import Domain

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

    product_reference_no = fields.Char(string='Material reference No.', default='[New]', readonly=True, copy=False, index=True, required=True, help="Reference Number of the material")

    # reference_note = fields.Char(string="Reference Note")
    # print("Product Template Inherited Successfully")   

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('product_reference_no', '[New]') == '[New]':
                val['product_reference_no'] = (self.env['ir.sequence'].
                next_by_code('product_sequense'))
        return super().create(vals)

    @api.onchange('forging_type')
    def _change_forging_type(self):
        print("Forging Type Changed", self)

    # @api.depends('name', 'product_reference_no')
    # @api.model
    # def name_get(self):
    #     result = []
    #     print("Name Get Called")
    #     for record in self:
    #         name = record.name
    #         # if record.product_reference_no:
    #         #     name = f"[{record.product_reference_no}] {name}"
    #         reference_no = record.product_reference_no
    #         result.append((reference_no, name))
    #     return result
    
# class SaleOrder(models.Model):
#    _inherit = 'sale.order'



# class student_extend(models.Model):
#     _inherit = 'wb.student'

#     reference_note = fields.Char(string="Reference Note")   

class product_product(models.Model):
    _inherit = "product.product"


    @api.model
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):
        
        # print("Web Name Search Called :self: ", self)
        # print("Web Name Search Called :name: ", name)
        # print("Web Name Search Called :specification: ", specification)
        # print("Web Name Search Called :domain: ", domain)
        # print("Web Name Search Called :operator: ", operator)

        # specification.update({'product_reference_no': {}})

        # print("Web Name Search Modified :specification: ", specification)

        rec = super(product_product, self).web_name_search(name, specification, domain, operator, limit)
        res = []
        for r in rec:
            product = self.browse(r['id'])
            
            r['__formatted_display_name'] = f"--{product.product_reference_no}--\t {r['__formatted_display_name']}"
            # print("Modified Record :: ", r)
            res.append(r)

        # print("Web Name Search Called Original:: ", rec)
        # print("Web Name Search Called Modified:: ", res)

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

