from odoo import api, models, fields
import re
from markupsafe import Markup


class OperationTypes(models.Model):
    _name = 'operation.types'
    _description = 'Operation Types for Manufacturing'
    _rec_name = 'name' # Важно: указывает, какое поле искать при вводе текста
    _order = 'sequence, name'

    name = fields.Char(string="Operation Type Name", required=True, translate=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string="Workcenter")
    equipment_id = fields.Many2one('maintenance.equipment', string="Default Equipment")
    code = fields.Char(string='Code', required=True)
    model_name = fields.Char(string='Model Name', help='Technical name of the related model')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index')
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
    

class OperaionCharge(models.Model):
    _name = 'operation.charge'
    _description = 'Charge Details for Processing (e.g., Heating)'

    name = fields.Char(string="Charge Name", required=True)
    #reverse relation with workorder
    workorder_id = fields.Many2one('mrp.workorder', string="Order")
    # workorder_id = fields.Integer(string="Order")
    
    operation_type_id = fields.Many2one(
        'operation.types', 
        string="Operation type",
        required=False 
    )
    
    workorder_list = fields.One2many('mrp.workorder', 'charge_id', string="Workorder List", context={'no_delete': True})
        
    
    #Calculate all workorders in the system
    wo_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="All WO Products",
        compute="_compute_wo_products",
        store=False
    )
    
    wo_components_ids = fields.Many2many(
        comodel_name="product.product",
        string="All WO Products",
        compute="_compute_wo_products",
        store=False
    )
    
    
    # Calculate all products from related WOs
    @api.onchange("selected_mo_ids")
    @api.depends()
    def _compute_wo_products(self):
        
        if not self.selected_mo_ids:
            all_wos = self.env['mrp.workorder'].search([])
        else:
            # all_wos = self.env['mrp.workorder'].search([('production_id', 'in', self.selected_mo_ids.ids)])
            all_wos = self.selected_mo_ids.mapped('workorder_ids')
            # print("Filtered WOs based on selected MOs:", all_wos.ids)
        
        for rec in self:
            # продукты МО, связанные с этими WO
            all_products = all_wos.mapped('production_id.product_id')
            
            # компоненты МО, связанные с этими WO
            all_components = all_wos.mapped('production_id.move_raw_ids.product_id')

            # объединяем
            rec.wo_product_ids = all_products
            rec.wo_components_ids = all_components
    
    
    
    # Operation charge list view
    # computed fields to show related manufacturing orders and products
    mo_ids = fields.Many2many(
        comodel_name="mrp.production",
        string="Manufacturing Orders",
        compute="_compute_mo_ids",
        store=False  # если нужно — можно поставить True
    )

    @api.depends("workorder_list")
    def _compute_mo_ids(self):
        for rec in self:
            rec.mo_ids = rec.workorder_list.mapped("production_id")
            
    # field to show raw material products used in the workorders' manufacturing orders
    mo_component_ids = fields.Many2many(
        comodel_name="product.product",
        string="Raw Materials",
        compute="_compute_raw_material_products",
        store=False
    )
    
    @api.depends("workorder_list.production_id.move_raw_ids.product_id")
    def _compute_raw_material_products(self):
        for rec in self:
            products = rec.workorder_list.mapped(
                "production_id.move_raw_ids.product_id"
            )
            rec.mo_component_ids = products
    
    # computed field to show products of manufacturing orders      
    mo_product_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_mo_products",
        string="MO Products",
        store=False
    )
        
    @api.depends("mo_ids")
    def _compute_mo_products(self):
        for rec in self:
            rec.mo_product_ids = rec.mo_ids.mapped("product_id")
            
    ########
    
    
    
    # Filter fields for adding workorders to charge list
    # поле для динамического добавления workorder        
    # выбор MOs вручную
    selected_mo_ids = fields.Many2many(
        comodel_name="mrp.production",
        string="Manufacturing Orders (Filter)",
        # domain="[('id', 'in', mo_ids)]"
        store=False
        
    )

    # выбор продуктов вручную
    selected_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Products (Filter)",
        relation='operation_charge_selected_product_rel',
        domain="[('id', 'in', wo_product_ids)]",
        store=False
    )

    # выбор компонентов вручную
    selected_component_ids = fields.Many2many(
        comodel_name="product.product",
        relation='operation_charge_selected_component_rel',
        string="Components (Filter)",
        domain="[('id', 'in', wo_components_ids)]",
        store=False
       
    )
    

    computed_wo_domain = fields.Char(
        string="Workorder Domain",
        compute="_compute_wo_domain",
        store=False
        
    )
    
    @api.depends('selected_mo_ids', "selected_component_ids",  "selected_product_ids")
    def _compute_wo_domain(self):
        for rec in self:
            domain = [('id', 'not in', self.workorder_list.ids)]
            if rec.selected_mo_ids:
                # rec.computed_wo_domain = "[('production_id','in', %s)]" % rec.selected_mo_ids.ids
                domain.append(('production_id', 'in', self.selected_mo_ids.ids))
            
            if self.selected_product_ids:
                domain.append(('product_id', 'in', self.selected_product_ids.ids))
                
            if self.selected_component_ids:
                domain.append(('production_id.move_raw_ids.product_id', 'in', self.selected_component_ids.ids))
            
            if self.operation_type_id:
                domain.append(('operation_type_id', 'in', self.operation_type_id.id))
                
                # print("Opernation type:", self.operation_type_id.id)
            
            rec.computed_wo_domain=str(domain)    
                
    ###############################
    
    
    

    ### test 12.51        
    #Add workorder field to add workorders dynamically              
    @api.onchange("workorder_id")
    def _onchange_workorder_id(self):
        if self.workorder_id:
            # добавить выбранный workorder в список
            self.workorder_list = [(4, self.workorder_id.id)]

            # очистить поле выбора
            self.workorder_id = False
            # return
           


class OperationStepsCutting(models.Model):
    _name = 'operation.steps.cutting'
    _description = 'Cutting Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Step Name', required=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    equipment_reference_id = fields.Char(related='equipment_id.reference_id', string="Equipment Ref.Id")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    income_material_weight = fields.Float(string="Incoming Material Weight (kg)")
    outcome_material_weight = fields.Float(string="Outgoing Material Weight (kg)")
    income_material_crosssection = fields.Char(string="Incoming Material Cross-Section (mmxmm)")   
    outcome_material_crosssection = fields.Char(string="Outgoing Material Cross-Section (mmxmm)")
    income_material_length = fields.Float(string="Incoming Material Length (mm)")
    outcome_material_length = fields.Float(string="Outgoing Material Length (mm)")
    notes = fields.Text(string="Additional Notes")
    
    
    
class OperationStepsHeating(models.Model):
    _name = 'operation.steps.heating'
    _description = 'Operation Steps for Manufacturing'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # operation_type_id = fields.Many2one('operation.types', string="Operation Type", required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    recipe_name = fields.Char(string="Recipe Name")
    charge_id = fields.Many2one('operation.charge', string="Charge ID")
    heating_date = fields.Date(string="Heating Date")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

    notes = fields.Text(string="Additional Notes")

    # SVG fields
    svg_builder_id = fields.Many2one('svg.builder', string="SVG")
    
    svg_preview = fields.Html(
        string="Preview",
        sanitize=False,           # Отключает базовую очистку
        sanitize_tags=False,      # Разрешает любые теги (rect, path и т.д.)
        sanitize_attributes=False,# Разрешает любые атрибуты (stroke-width и т.d.)
        sanitize_style=False,     # Разрешает инлайн стили
        strip_style=False,        # Не удалять теги <style>
        strip_classes=False,    # Не удалять классы CSS
        compute="_compute_svg_preview"
    )
    
    @api.depends('svg_builder_id', 'svg_builder_id.svg_content')
    def _compute_svg_preview(self):

                
        for rec in self:
            if rec.svg_builder_id and rec.svg_builder_id.svg_content:
                # svg_content = re.sub(r"<\?xml.*?\?>", "", rec.svg_builder_id.svg_content, flags=re.IGNORECASE | re.DOTALL).strip()
                svg_content = rec.svg_builder_id.svg_content
                rec.svg_preview = Markup(svg_content)
            else:
                rec.svg_preview = Markup('<p>No Graphic Available</p>')
    

    def action_open_svg(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "svg.builder",
            "res_id": self.svg_builder_id.id,
            "view_mode": "form",
            "target": "new",
        }
    

    

   
    

