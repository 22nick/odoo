from odoo import api, models, fields


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    charge_id =  fields.Many2one(
        "operation.charge", 
        string="Charge ID"
        
        )
    
    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user,
        domain=lambda self: [('all_group_ids', 'in', self.env.ref('mrp.group_mrp_user').id)])
    
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


    # Operation Type field linked to operation.types
    operation_type_id = fields.Many2one(
        'operation.types', 
        string="Operation Type",
        required=False,
        tracking=True 
    )
    
    
    
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

                
    product_reference_no = fields.Char(related='production_id.product_id.product_reference_no', string="Product Ref.No.")
    
    component_id = fields.Many2one(related='production_id.move_raw_ids.product_id', string="Component")
    
    component_qty = fields.Float(related='production_id.move_raw_ids.product_uom_qty', string="Component Qty.")
    
    component_reference_no = fields.Char(related='production_id.move_raw_ids.product_id.product_reference_no', string="Component Ref.No.")
    
    operation_type_code = fields.Char(
        related='operation_type_id.code',
        string='Operation Type Code',
        store=True,
        readonly=True
    )
    
    # One2many relations to different operation models
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
    
    # welding_operation_ids = fields.One2many(
    #     'operation.steps.welding',
    #     'workorder_id',
    #     string="Welding Operations"
    # )
    
    grinding_operation_ids = fields.One2many(
        'operation.steps.grinding',
        'workorder_id',
        string="Grinding Operations"
    )
    

    
    # def action_print_cutting_report(self):
    #     """Print Cutting Operations Report"""
    #     return self.env.ref('mrp_operation_extension.action_report_cutting_operations').report_action(self)
    
    def action_print_workorder_report(self):
        """Print Workorder Operations Report"""
        return self.env.ref('mrp_operation_extension.action_report_workorder_operations').report_action(self)
    
    # def action_print_heating_report(self):
    #     """Print Heating Operations Report"""
    #     return self.env.ref('mrp_operation_extension.action_report_heating_operations').report_action(self)