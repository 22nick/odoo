from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # Example field to extend mrp.production
    partner_id = fields.Many2one('res.partner', string='Customer')
    sales_order_reference = fields.Char(string='Sales Order')
    customer_order_reference = fields.Char(string='Customer Order')
    manufacturing_order_revision_number = fields.Char(string='Manufacturing Order Rev.No.')
    manufacturing_order_revision_note = fields.Text(string='Manufacturing Order Revision Note')
    technical_drawing_revision_number = fields.Char(string='Technical Drawing Rev.No.')
    technical_drawing_revision_note = fields.Text(string='Technical Drawing Rev. Note')
    technical_feasibility = fields.Boolean(string='HAS THE TECHNICAL FEASIBILITY BEEN EVALUATED?')
    technical_feasibility_form_no = fields.Char(string='Technical Feasibility Form No.')
    manufactoring_features = fields.Selection(
        [('prototype', 'Customer prototype'),
         ('trial', 'Trial'),
         ('fac', 'FAC'),
         ('serial', 'Serial Production'),
         ('special', 'Special Process'),
         ('other', 'Other')],
        string='Manufacturing Features')
    
    manufactoring_part_no = fields.Char(string='Manufacturing Part No.')
    product_dimensions = fields.Char(string='Product Dimensions')
    product_material_standart= fields.Char(string='Material Quality and Standart')
    customer_requirements = fields.Selection(string='Customer Requirements',
                                             selection=[('item', 'Item'),
                                                        ('tolerance', 'Tolerance'),
                                                        ('heattrearment', 'Heat Treatment'),
                                                        ('documents', 'Customer Documentstion'),])
    customer_requirements_notes = fields.Text(string='Customer Requirements Notes')
    
    binary_field = fields.Many2many("ir.attachment", string="Upload Files",)
    
    
    component_reference_no = fields.Char(related='move_raw_ids.product_id.product_reference_no', string="Component Ref.No.")
    manufactoring_explanation_note = fields.Text(string='Explanations')
    
    
    def action_print_report(self):
        """Метод для печати отчета"""
        return self.env.ref('manufacturing_extension.action_report_manufacturing_order').report_action(self)
    
class StockMove(models.Model):
    _inherit = "stock.move"

    min_consume_qty = fields.Float(string='Min Consume Qty')
    max_consume_qty = fields.Float(string='Max Consume Qty')
    measurement_tool_id = fields.Many2one('maintenance.equipment', string='Measurement Tool')
    
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Корректировка product_qty в пределах min/max"""
        for record in self:
            if record.product_qty and (record.min_consume_qty or record.max_consume_qty):
                # Получаем ближайшее допустимое значение
                corrected_qty = record._get_corrected_qty(
                    record.product_qty,
                    record.min_consume_qty,
                    record.max_consume_qty
                )
                if corrected_qty != record.product_qty:
                    record.product_qty = corrected_qty
    
    @api.onchange('min_consume_qty')
    def _onchange_min_consume_qty(self):
        """Корректировка min_consume_qty и product_qty"""
        for record in self:
            if record.min_consume_qty:
                # Если min больше max, устанавливаем min = max
                if record.max_consume_qty and record.min_consume_qty > record.max_consume_qty:
                    record.min_consume_qty = record.max_consume_qty
                
                # Корректируем product_qty если необходимо
                if record.product_qty and record.product_qty < record.min_consume_qty:
                    record.product_qty = record.min_consume_qty
    
    @api.onchange('max_consume_qty')
    def _onchange_max_consume_qty(self):
        """Корректировка max_consume_qty и product_qty"""
        for record in self:
            if record.max_consume_qty:
                # Если max меньше min, устанавливаем max = min
                if record.min_consume_qty and record.max_consume_qty < record.min_consume_qty:
                    record.max_consume_qty = record.min_consume_qty
                
                # Корректируем product_qty если необходимо
                if record.product_qty and record.product_qty > record.max_consume_qty:
                    record.product_qty = record.max_consume_qty
    
    @api.constrains('min_consume_qty', 'max_consume_qty', 'product_qty')
    def _check_consume_qty_limits(self):
        """Проверка ограничений при сохранении"""
        for record in self:
            # Проверяем соотношение min/max
            if record.min_consume_qty and record.max_consume_qty:
                if record.min_consume_qty > record.max_consume_qty:
                    raise ValidationError(
                        _('Min Consume Qty (%s) cannot be greater than Max Consume Qty (%s)') 
                        % (record.min_consume_qty, record.max_consume_qty)
                    )
            
            # Проверяем product_qty в пределах
            if record.product_qty:
                if record.min_consume_qty and record.product_qty < record.min_consume_qty:
                    raise ValidationError(
                        _('Real Quantity (%s) cannot be less than Min Consume Qty (%s)') 
                        % (record.product_qty, record.min_consume_qty)
                    )
                if record.max_consume_qty and record.product_qty > record.max_consume_qty:
                    raise ValidationError(
                        _('Real Quantity (%s) cannot be greater than Max Consume Qty (%s)') 
                        % (record.product_qty, record.max_consume_qty)
                    )
    
    def _get_corrected_qty(self, qty, min_qty, max_qty):
        """Возвращает скорректированное значение в допустимых пределах"""
        if min_qty and qty < min_qty:
            return min_qty
        if max_qty and qty > max_qty:
            return max_qty
        return qty
    
    def write(self, vals):
        """Корректировка значений при записи"""
        # Корректируем min_consume_qty если нарушается условие с max
        if 'min_consume_qty' in vals:
            for record in self:
                max_qty = vals.get('max_consume_qty', record.max_consume_qty)
                if max_qty and vals['min_consume_qty'] > max_qty:
                    vals['min_consume_qty'] = max_qty
        
        # Корректируем max_consume_qty если нарушается условие с min
        if 'max_consume_qty' in vals:
            for record in self:
                min_qty = vals.get('min_consume_qty', record.min_consume_qty)
                if min_qty and vals['max_consume_qty'] < min_qty:
                    vals['max_consume_qty'] = min_qty
        
        # Корректируем product_qty в пределах min/max
        if 'product_qty' in vals or 'min_consume_qty' in vals or 'max_consume_qty' in vals:
            for record in self:
                product_qty = vals.get('product_qty', record.product_qty)
                min_qty = vals.get('min_consume_qty', record.min_consume_qty)
                max_qty = vals.get('max_consume_qty', record.max_consume_qty)
                
                corrected_qty = self._get_corrected_qty(product_qty, min_qty, max_qty)
                if corrected_qty != product_qty:
                    vals['product_qty'] = corrected_qty
        
        return super(StockMove, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Корректировка значений при создании"""
        for vals in vals_list:
            min_qty = vals.get('min_consume_qty', 0)
            max_qty = vals.get('max_consume_qty', 0)
            product_qty = vals.get('product_qty', 0)
            
            # Корректируем min/max
            if min_qty and max_qty and min_qty > max_qty:
                vals['min_consume_qty'] = max_qty
                min_qty = max_qty
            
            # Корректируем product_qty
            if product_qty:
                vals['product_qty'] = self._get_corrected_qty(product_qty, min_qty, max_qty)
        
        return super(StockMove, self).create(vals_list)
    # move_display_name = fields.Char(
    #     string='Display Name',
    #     compute='_compute_move_display_name',
    #     store=False
    # )
    
    # @api.depends('product_id', 'product_id.name', 'product_id.default_code', 'product_uom_qty', 'product_uom')
    # def _compute_move_display_name(self):
    #     """Compute display name with product info"""
    #     for move in self:
    #         if move.product_id:
    #             product = move.product_id
    #             ref = product.default_code or ''
    #             qty = move.product_uom_qty
    #             uom = move.product_uom.name if move.product_uom else ''
                
    #             name = f"{product.name}"
    #             if ref:
    #                 name += f" [{ref}]"
    #             if qty and uom:
    #                 name += f" - {qty:.2f} {uom}"
    #             move.move_display_name = name
    #         else:
    #             move.move_display_name = move.name or ''
    
    # def name_get(self):
    #     """Override name_get to show product info for finished moves"""
    #     result = []
    #     for move in self:
    #         # Check if this move is a finished product move
    #         if move.production_id and move in move.production_id.move_finished_ids:
    #             if move.product_id:
    #                 product = move.product_id
    #                 ref = product.default_code or ''
    #                 qty = move.product_uom_qty
    #                 uom = move.product_uom.name if move.product_uom else ''
                    
    #                 # Format: "Product Name [REF] - 100.0 kg"
    #                 name = f"{product.name}"
    #                 if ref:
    #                     name += f" [{ref}]"
    #                 name += f" - {qty:.2f} {uom}"
    #                 result.append((move.id, name))
    #             else:
    #                 result.append((move.id, super(StockMove, move).name_get()[0][1]))
    #         else:
    #             # Default behavior for non-finished moves
    #             result.append((move.id, super(StockMove, move).name_get()[0][1]))
    #     return result