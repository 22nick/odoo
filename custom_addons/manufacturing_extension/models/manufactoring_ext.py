from odoo import api, models, fields

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
    