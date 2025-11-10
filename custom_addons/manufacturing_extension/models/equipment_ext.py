from odoo import api, models, fields


class ProductTemlpate(models.Model):
    _inherit = 'maintenance.equipment'

    
    workcenter_id = fields.Many2one("mrp.workcenter", string="Work Center")
    

