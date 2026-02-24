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
    
    final_quality_ids = fields.One2many('mrp.production.final.quality', 'production_id', string='Final Quality')
    
    def action_print_report(self):
        """Метод для печати отчета"""
        return self.env.ref('manufacturing_extension.action_report_manufacturing_order').report_action(self)
    
class StockMove(models.Model):
    _inherit = "stock.move"

    min_consume_qty = fields.Float(string='Min Consume Qty')
    max_consume_qty = fields.Float(string='Max Consume Qty')
    measurement_tool_id = fields.Many2one('maintenance.equipment', string='Measurement Tool')
    
    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """Корректировка product_uom_qty в пределах min/max"""
        for record in self:
            if record.product_uom_qty and (record.min_consume_qty or record.max_consume_qty):
                # Получаем ближайшее допустимое значение
                corrected_qty = record._get_corrected_qty(
                    record.product_uom_qty,
                    record.min_consume_qty,
                    record.max_consume_qty
                )
                if corrected_qty != record.product_uom_qty:
                    record.product_uom_qty = corrected_qty
    
    @api.onchange('min_consume_qty')
    def _onchange_min_consume_qty(self):
        """Корректировка min_consume_qty и product_uom_qty"""
        for record in self:
            if record.min_consume_qty:
                # Если min больше max, устанавливаем min = max
                if record.max_consume_qty and record.min_consume_qty > record.max_consume_qty:
                    record.min_consume_qty = record.max_consume_qty
                
                # Корректируем product_uom_qty если необходимо
                if record.product_uom_qty and record.product_uom_qty < record.min_consume_qty:
                    record.product_uom_qty = record.min_consume_qty
    
    @api.onchange('max_consume_qty')
    def _onchange_max_consume_qty(self):
        """Корректировка max_consume_qty и product_uom_qty"""
        for record in self:
            if record.max_consume_qty:
                # Если max меньше min, устанавливаем max = min
                if record.min_consume_qty and record.max_consume_qty < record.min_consume_qty:
                    record.max_consume_qty = record.min_consume_qty
                
                # Корректируем product_uom_qty если необходимо
                if record.product_uom_qty and record.product_uom_qty > record.max_consume_qty:
                    record.product_uom_qty = record.max_consume_qty
    
    @api.constrains('min_consume_qty', 'max_consume_qty', 'product_uom_qty')
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
            
            # Проверяем product_uom_qty в пределах
            if record.product_uom_qty:
                if record.min_consume_qty and record.product_uom_qty < record.min_consume_qty:
                    raise ValidationError(
                        _('Real Quantity (%s) cannot be less than Min Consume Qty (%s)') 
                        % (record.product_uom_qty, record.min_consume_qty)
                    )
                if record.max_consume_qty and record.product_uom_qty > record.max_consume_qty:
                    raise ValidationError(
                        _('Real Quantity (%s) cannot be greater than Max Consume Qty (%s)') 
                        % (record.product_uom_qty, record.max_consume_qty)
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
        
        # Корректируем product_uom_qty в пределах min/max
        if 'product_uom_qty' in vals or 'min_consume_qty' in vals or 'max_consume_qty' in vals:
            for record in self:
                product_uom_qty = vals.get('product_uom_qty', record.product_uom_qty)
                min_qty = vals.get('min_consume_qty', record.min_consume_qty)
                max_qty = vals.get('max_consume_qty', record.max_consume_qty)
                
                corrected_qty = self._get_corrected_qty(product_uom_qty, min_qty, max_qty)
                if corrected_qty != product_uom_qty:
                    vals['product_uom_qty'] = corrected_qty
        
        return super(StockMove, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Корректировка значений при создании"""
        for vals in vals_list:
            min_qty = vals.get('min_consume_qty', 0)
            max_qty = vals.get('max_consume_qty', 0)
            product_uom_qty = vals.get('product_uom_qty', 0)
            
            # Корректируем min/max
            if min_qty and max_qty and min_qty > max_qty:
                vals['min_consume_qty'] = max_qty
                min_qty = max_qty
            
            # Корректируем product_uom_qty
            if product_uom_qty:
                vals['product_uom_qty'] = self._get_corrected_qty(product_uom_qty, min_qty, max_qty)
        
        return super(StockMove, self).create(vals_list)
    


class MrpProductionFinalQuality(models.Model):
    _name = 'mrp.production.final.quality'
    _description = 'Production Final Quality Control'
    _order = 'sequence, id'
    
    production_id = fields.Many2one(
        'mrp.production', 
        string='Manufacturing Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    sequence = fields.Integer(string='Sequence', default=10)
    
    name = fields.Datetime(string="Date & Time")
    # operation_date_time = fields.Datetime(string="Operation Date & Time")
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    
    controlled_qty = fields.Integer(string="Controlled Quantity")
    accepted_qty = fields.Integer(string="Accepted Quantity")
    rejected_qty = fields.Integer(string="Rejected Quantity")
    non_report_no = fields.Char(string="Non-Comformity Report No.")
    
    step_ids = fields.One2many('mrp.production.final.quality.step', 'report_id', string="Step")
        
    # QUESTION FIELDS
    question_1 = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No'),
         ('na', 'N/A')],
        string='Overall, is the visual examination result satisfactory?', 
        default='na')
    reference_1 = fields.Char(string="Reference Document(s)")

    question_2 = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No'),
         ('na', 'N/A')],
        string='Does the material meet the specifications? (If requested with specifications)', 
        default='na')
    reference_2 = fields.Char(string="Reference Document(s)")
        
    question_3 = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No'),
         ('na', 'N/A')],
        string='Does the product conform to the technical drawing? (If applicable)', 
        default='na')
    reference_3 = fields.Char(string="Reference Document(s)")
        
    question_4 = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No'),
         ('na', 'N/A')],
        string='Have tests been conducted? Please attach the test reports if any have been completed.', 
        default='na')
    reference_4 = fields.Char(string="Reference Document(s)")
        
    question_5 = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No'),
         ('na', 'N/A')],
        string='Is there FOD?', 
        default='na')
    reference_5 = fields.Char(string="Reference Document(s)")
        
    
    
        
class MrpProductionFinalQualityStep(models.Model):
    _name = 'mrp.production.final.quality.step'
    _description = 'Production Final Quality Control Step'
    _order = 'sequence, id'
    
    report_id = fields.Many2one(
        'mrp.production.final.quality', 
        string='Quality Report', 
        required=True,
        ondelete='cascade',
        # index=True,
        readonly = True
    )
    
    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string="Requested Features")
    requested_values = fields.Char(string="Requested Values (min-max)", infotext="Minimum-maximum value range is entered")
    measured_values = fields.Char(string="Measured Values")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    reference = fields.Char(string="Referenced Technical Plan/Instructions")
