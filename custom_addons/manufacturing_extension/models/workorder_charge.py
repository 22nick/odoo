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
        required=False 
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
    
    # Test 13.41
    # Override write method to log charge_id changes            
    # def write(self, vals):
    #     import logging
    #     _logger = logging.getLogger(__name__)
    #     _logger.info(f"WO write called with vals: {vals}")
    #     _logger.info(f"Current charge_id: {self.charge_id.id if self.charge_id else None}")
        
    #     result = super(MrpWorkorder, self).write(vals)
        
    #     if 'charge_id' in vals:
    #         _logger.info(f"After write, charge_id: {self.charge_id.id if self.charge_id else None}")
        
    #     return result
                
    product_reference_no = fields.Char(related='production_id.product_id.product_reference_no', string="Product Ref.No.")
    
    component_id = fields.Many2one(related='production_id.move_raw_ids.product_id', string="Component")
    
    component_reference_no = fields.Char(related='production_id.move_raw_ids.product_id.product_reference_no', string="Component Ref.No.")
    

    