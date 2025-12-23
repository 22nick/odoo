from odoo import api, models, fields


class MaintenanceEquipmentWorkcenter(models.Model):
    _inherit = 'maintenance.equipment'

    
    workcenter_id = fields.Many2one("mrp.workcenter", string="Work Center")
    reference_id = fields.Char(string="Reference ID", unique=True, index=True)


    

