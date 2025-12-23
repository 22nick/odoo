from odoo import models, fields, api
import json

class VectorCanvas(models.Model):
    _name = 'vector.canvas'
    _description = 'Vector Canvas'

    name = fields.Char(string='Name', required=True)
    canvas_data = fields.Text(string='Canvas Data', default='{"shapes": []}')
    canvas_width = fields.Integer(string='Canvas Width', default=800)
    canvas_height = fields.Integer(string='Canvas Height', default=600)
    
    @api.model
    def create(self, vals):
        if 'canvas_data' not in vals:
            vals['canvas_data'] = json.dumps({"shapes": []})
        return super(VectorCanvas, self).create(vals)
    
    def write(self, vals):
        if 'canvas_data' in vals and isinstance(vals['canvas_data'], dict):
            vals['canvas_data'] = json.dumps(vals['canvas_data'])
        return super(VectorCanvas, self).write(vals)