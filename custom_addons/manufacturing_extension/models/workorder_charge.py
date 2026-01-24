from odoo import api, models, fields
from odoo.exceptions import ValidationError


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    charge_id =  fields.Many2one("operation.charge", string="Charge ID")
    
    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user,
        domain=lambda self: [('all_group_ids', 'in', self.env.ref('mrp.group_mrp_user').id)])
    
    
    

    # Operation Type field linked to operation.types
    operation_type_id = fields.Many2one(
        'operation.types', 
        string="Operation Type",
        required=False,
        tracking=True 
    )
                

    product_reference_no = fields.Char(related='production_id.product_id.product_reference_no', string="Product Ref.No.")
    
    component_id = fields.Many2one(related='production_id.move_raw_ids.product_id', string="Component")
    
    # component_ids = fields.Many2many(related='production_id.move_raw_ids', string="Components")
    
    component_qty = fields.Float(related='production_id.move_raw_ids.product_uom_qty', string="Component Qty.")
    
    component_reference_no = fields.Char(related='production_id.move_raw_ids.product_id.product_reference_no', string="Component Ref.No.")
    
    operation_type_code = fields.Char(
        related='operation_type_id.code',
        string='Operation Type Code',
        store=True,
        readonly=True
    )
    
    operation_notes = fields.Text(string="Operation Notes")
    
    operation_files = fields.Many2many("ir.attachment", string="Upload Files")
    
    
    # One2many relations to different operation models
    # Steps
    cutting_operation_ids = fields.One2many(
        'operation.steps.cutting',
        'workorder_id',
        string="Cutting Operations"
    )
    
    heating_operation_ids = fields.One2many(
        'operation.steps.heating',
        'workorder_id',
        string="Heating Operations"
    )
    
    forging_operation_ids = fields.One2many(
        'operation.steps.forging',
        'workorder_id',
        string="Forging Operations"
    )
    
    grinding_operation_ids = fields.One2many(
        'operation.steps.grinding',
        'workorder_id',
        string="Grinding Operations"
    )
    
    machining_operation_ids = fields.One2many(
        'operation.steps.machining',
        'workorder_id',
        string="Machining Operations"
    )
    
    weighing_operation_ids = fields.One2many(
        'operation.steps.weighing',
        'workorder_id',
        string="Weighing Operations"
    )
    
    smelting_operation_ids = fields.One2many(
        'operation.steps.smelting',
        'workorder_id',
        string="Smelting Operations"
    )
    
    leakage_test_operation_ids = fields.One2many(
        'operation.steps.leakage.test',
        'workorder_id',
        string="Leakage Test Operations"
    )
    
    casting_operation_ids = fields.One2many(
        'operation.steps.casting',
        'workorder_id',
        string="Casting Operations"
    )
    
    smelting_quality_control_ids = fields.One2many(
        'operation.steps.smelting.quality',
        'workorder_id',
        string="Smelting Quality Control"
    )
    
    
    # Parameters
    forging_operation_params_id = fields.One2many(
        'operation.params.forging',
        'workorder_id',
        string="Operation Parameters",
    )
    
    smelting_operation_params_id = fields.One2many(
        'operation.params.smelting',
        'workorder_id',
        string="Operation Parameters",
    )
    
    
    
    
    @api.constrains('forging_operation_params_id')
    def _check_one2one(self):
        for record in self:
            if len(record.forging_operation_params_id) > 1:
                raise ValidationError('Only one Operation Parameters can be linked!')
    

    def unlink(self):
        # если удаление вызвано из формы Charge
        ctx = self.env.context
        print("Unlink context:", ctx)
        if ctx.get('no_delete'):
            print("Deletion blocked by context 'no_delete'")
            for wo in self:
                wo.charge_id = False
            return False  # Блокируем удаление
        else:
            return super().unlink()

    
    def action_print_workorder_report(self):
        """Print Workorder Operations Report"""
        return self.env.ref('manufacturing_extension.action_report_workorder_operations').report_action(self)
    

    # Магия синхронизации:
    # Когда пользователь выбирает или создает запись в выпадающем списке,
    # мы копируем её название в стандартное поле 'name', которое требует Odoo.
    @api.onchange('operation_type_id')
    def _onchange_operation_type_id(self):

        if self.operation_type_id:
            self.name = self.operation_type_id.name
            
            # (Опционально) Сразу подтягиваем рабочий центр, если он задан в типе
            if self.operation_type_id.workcenter_id:
                self.workcenter_id = self.operation_type_id.workcenter_id
        
            """Clear operation lines when operation type changes"""
            self.cutting_operation_ids = [(5, 0, 0)]
            self.heating_operation_ids = [(5, 0, 0)]
            # self.welding_operation_ids = [(5, 0, 0)]
            # self.grinding_operation_ids = [(5, 0, 0)]
    
    
    
    @api.onchange('operation_type_id')
    def _onchange_operation_type_id_notes(self):
        if not self.operation_type_id:
            return

        self.operation_notes = self._get_operation_notes_template(
            self.operation_type_id
        )
    
    def _get_operation_notes_template(self, operation_type):
        return operation_type.operation_notes_template or ""
    