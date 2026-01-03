# Operation parameters
# Extens workorders with op_type-specific fields as incoming data for production

from odoo import api, models, fields, _
import base64


class OperationParamsForging(models.Model):
    _name = 'operation.params.forging'
    _description = 'Operation Parameters for Forging'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True
    )
    
    order_dimensions = fields.Text(string="Order Dimensions")
    start_temperature = fields.Integer(string="Start Forging Temperature")
    end_temperature = fields.Integer(string="End ForgingTemperature")