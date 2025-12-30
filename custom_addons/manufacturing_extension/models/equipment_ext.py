from odoo import api, models, fields


class MaintenanceEquipmentWorkcenter(models.Model):
    _inherit = 'maintenance.equipment'

    
    workcenter_id = fields.Many2one("mrp.workcenter", string="Work Center")
    reference_id = fields.Char(string="Reference ID", unique=True, index=True)
    state = fields.Selection([
        ('alarm', 'Alarm'),                     # Warning (yellow)            'alarm': 'warning',         """ 'blocked' """
        ('idle', 'Idle'),                         # Idle (grey)                'idle': 'secondary',        """ 'ready' """
        ('comissioning', 'Comissioning'),                # Comissioning (blue)      'comissioning': 'info',     """ 'progress' """
        ('working', 'Working'),                       # Working (green)            'working': 'success',       """ 'done' """      
        ('out', 'Out Of Sercive')], string='Status',  # Out of service (red) 'out': 'danger',            """ 'cancel' """
        store=True,
        default='idle', copy=False, index=True)

    # def _get_state_color(self):
    #     """Возвращает цвет для badge виджета"""
    #     colors = {
    #         'working': 'success',      
    #         'alarm': 'warning',        
    #         'out': 'danger',           
    #         'comissioning': 'info',     
    #         'idle': 'secondary',       
    #     }
    #     return colors.get(self.state, 'secondary')
    
    used_on_eqiopment = fields.Many2one('maintenance.equipment', string= "Used on Equipment")
    



    

