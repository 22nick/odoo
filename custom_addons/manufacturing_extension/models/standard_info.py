from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class StandardInfo(models.Model):
    _name = 'standard.info'
    _description = 'Stardard Information'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
        
    name = fields.Char(string="Grade", required=True)
    description = fields.Text(string="Description")
    
    