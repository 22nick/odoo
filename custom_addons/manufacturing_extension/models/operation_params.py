# Operation parameters
# Extens workorders with op_type-specific fields as incoming data for production

from odoo import api, models, fields, _
import base64


class OperationParamsForging(models.Model):
    _name = 'operation.params.forging'
    _description = 'Operation Parameters for Forging'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        invisible=True
    )
    
    order_dimensions = fields.Text(string="Order Dimensions")
    start_temperature = fields.Integer(string="Start Forging Temperature")
    end_temperature = fields.Integer(string="End ForgingTemperature")
    lubtication = fields.Char(string="Lubrication")
    

    
    _sql_constraints = [
        ('workorder_unique',
         'UNIQUE(workorder_id)',
         'Each Work Order can have only one Parameters!')
    ]
    

class OperationParamsSmelting(models.Model):
    _name = 'operation.params.smelting'
    _description = 'Operation Parameters for Smelting'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        invisible=True
    )
    
    equipment_id = fields.Many2one('maintenance.equipment', string='Smelting Station')
    new_heat_no = fields.Char(related='workorder_id.production_id.product_id.heat_no', string="Heat Number", readonly=False)
    material_grade_id = fields.Many2one('material.grade', string='Material Grade')
    operation_date = fields.Date(string="Operation Date")
    
    #PREPARATION FIELDS
    mould_id = fields.Many2one('maintenance.equipment', domain=[('category_id.name', '=', 'Mould')], string='Mould')
    hottop_id = fields.Many2one('maintenance.equipment', domain=['|', ('workcenter_id.name', '=', 'Melting and casting workcenter'), ('workcenter_id', '=', False)], string='Hot Top')
    tundish_id = fields.Many2one('maintenance.equipment', domain=['|', ('workcenter_id.name', '=', 'Melting and casting workcenter'), ('workcenter_id', '=', False)], string='Tundish')
    mould_coating_id = fields.Many2one('product.product', string='Mould Coating')
    charge_weight = fields.Float(
        string="Charge Weight",
        digits=(12, 5), 
        compute='_compute_charge_weight',
        store=True,
        readonly=True
    )
    ceramic_crucible_cast_count = fields.Integer(string="Ceramic Crucible Casting Count")
    lining_cast_count = fields.Integer(string="Lining Casting Count")
    casting_speed = fields.Float(string="Casting Speed")
    preparation_performer = fields.Many2one('res.users', string='Preparation Performer')
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    component_ids = fields.One2many(
        related='workorder_id.production_id.move_raw_ids', 
        string="Component"
    )
    
    
    # OPERATION FIELDS
    operation_performer = fields.Many2one('res.users', string='Operation Performer')
    operation_responsible = fields.Many2one('res.users', string='Operation Responsible')
    ksb_form_no_oper = fields.Char(string="KSB Form No. (if exist)")
    
    # @api.depends('workorder_id.production_id.move_raw_ids.product_uom_qty')
    # def _compute_charge_weight(self):
    #     for record in self:
    #         total_weight = 0.0
    #         if record.component_ids:
    #             total_weight = sum(record.component_ids.mapped('product_uom_qty'))
    #         record.charge_weight = total_weight
            
            
    @api.depends('workorder_id.production_id.move_raw_ids.product_uom_qty', 
             'workorder_id.production_id.move_raw_ids.product_uom')
    def _compute_charge_weight(self):
        for record in self:
            total_weight_kg = 0.0
            if record.component_ids:
                for component in record.component_ids:
                    qty = component.product_uom_qty
                    uom = component.product_uom
                    
                    if uom:
                        # Конвертируем в кг
                        qty_in_kg = uom._compute_quantity(
                            qty, 
                            self.env.ref('uom.product_uom_kgm'),
                            raise_if_failure=False
                        )
                        total_weight_kg += qty_in_kg
                        # print(f"Component {component.product_id.name}: {qty} {uom.name} = {qty_in_kg} kg")
                    else:
                        # Если единица измерения не указана, считаем что это уже кг
                        total_weight_kg += qty
                        
            record.charge_weight = total_weight_kg
   
    _sql_constraints = [
        ('workorder_unique',
         'UNIQUE(workorder_id)',
         'Each Work Order can have only one Parameters!')
    ]
    
class OperationParamsRemelting(models.Model):
    _name = 'operation.params.remelting'
    _description = 'Operation Parameters for Remelting'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=10, invisible=True)
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        invisible=True
    )
    
    equipment_id = fields.Many2one('maintenance.equipment', string='Smelting Station')
    new_heat_no = fields.Char(related='workorder_id.production_id.product_id.heat_no', string="New Heat No.", readonly=False)
    process_type = fields.Selection([
        ('var', 'VAR'),
        ('esr', 'ESR')
    ], string='Process Type')
    # material_grade_id = fields.Many2one('material.grade', string='Material Grade')
    
    grade = fields.Many2one(related='workorder_id.production_id.product_id.forging_material', string="Grade", readonly=False)
    
    component_ids = fields.One2many(
        related='workorder_id.production_id.move_raw_ids', 
        string="Component"
    )
    
    _sql_constraints = [
        ('workorder_unique',
         'UNIQUE(workorder_id)',
         'Each Work Order can have only one Parameters!')
    ]
    
