from odoo import api, models, fields, _
import re
from markupsafe import Markup
from odoo.exceptions import UserError
import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64


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
    
    # model operation.types
    operation_notes_template = fields.Text(
        string="Operation Notes Template"
    )
    
    properties_definition = fields.PropertiesDefinition('Additional Properties Definition')

    

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
                
                
                # Parsing SVG content
                # 1. Убираем XML-заголовок (на всякий случай)
                # svg_content = re.sub(r"<\?xml.*?\?>", "", svg_content).strip()

                # 2. Парсим XML
                root = ET.fromstring(svg_content)

                texts = []

                # 3. SVG namespace
                ns = {"svg": "http://www.w3.org/2000/svg"}

                # 4. Ищем все <text>
                for text_el in root.findall(".//svg:text", ns):
                    if text_el.text:
                        texts.append(text_el.text.strip())

                print("Extracted texts from SVG:", texts)
                
                
                
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

    template_svg_id = fields.Many2one(
        'svg.builder', 
        string="Use Template", 
        help="Select a template to copy from"
    )

    def action_create_svg(self):
        self.ensure_one()
        if not self.name:
            raise UserError(_("Please enter a Charge Name before creating an SVG."))

        # # Инициализируем переменные для нового SVG
        # svg_content = ""
        # width = 800
        # height = 600
        # bg_color = "#ffffff"

        # --- ЛОГИКА ВЫБОРА ШАБЛОНА ---

        # Вариант 2: Если выбран шаблон в форме
        source = self.template_svg_id
        
        if source:
            svg_content = source.svg_content
            canvas_w = source.width or 800
            canvas_h = source.height or 600
            bg_color = source.background_color or "#ffffff"

        # Вариант 1 (Настройки): Если в форме пусто, ищем "Глобальный шаблон" в настройках
        else:
            # Ищем ID шаблона по умолчанию в системных параметрах
            default_template_id = self.env['ir.config_parameter'].sudo().get_param('operation_charge.default_svg_template_id')
            template = self.env['svg.builder'].browse(int(default_template_id)) if default_template_id else False
            
            if template:
                svg_content = template.svg_content
                canvas_w = template.width
                canvas_h = template.height
                bg_color = template.background_color
            else:
                # Вариант 1 (Код): Хардкодный фоллбек, если ничего не найдено
                canvas_w, canvas_h, bg_color = 800, 600, "#ffffff"
                svg_content = f'<svg width="{canvas_w}" height="{canvas_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: {bg_color}"></svg>'
                
        # 2. Подготовка к генерации фигур
        rect_w, rect_h = 200, 100
        padding = 20
        # Рассчитываем количество колонок исходя из ширины полотна
        cols = max(1, canvas_w // (rect_w + padding))
        
        components = self.mo_component_ids
        generated_elements = []

        for i, product in enumerate(components):
            # Рассчитываем координаты X и Y
            row = i // cols
            col = i % cols
            x = 50 + padding + col * (rect_w + padding)
            y = padding + row * (rect_h + padding)

            # Получаем текст (по вашей логике связей)
            # ВНИМАНИЕ: так как product - это product.product, нам нужно найти 
            # соответствующий move из связанных записей текущей формы.
            # Здесь пример получения данных:
            ref = getattr(product, 'product_reference_no', '') or ''
            # ref = product.product_reference_no
            
            # Поиск heat_no: так как в M2M только продукты, 
            # ищем heat_no в move_raw_ids связанных производств
            # (Логика может меняться в зависимости от того, как связаны данные в вашей системе)
            heat_no = product.heat_no
            
            # heat_no = ""
            # related_move = self.workorder_id.production_id.move_raw_ids.filtered(lambda m: m.product_id == product)[:1]
            # if related_move:
            #     heat_no = related_move.product_id.heat_no or ""

            display_text = f"{ref}".strip() or "N/A"
            display_text2 = f"{heat_no}".strip() or "N/A"

            # Генерируем SVG-код для прямоугольника и текста в центре
            rect_tag = f'<rect x="{x}" y="{y}" width="{rect_w}" height="{rect_h}" fill="#FFFFFF" stroke="#000000" stroke-width="2" />'
            
            # Текст: x + 50 (половина ширины), y + 25 (половина высоты)
            text_tag = (
                f'<text x="{x + 2}" y="{y + rect_h/2 - 14}" '
                f'font-size="14" font-family="Arial" '
                f'text-anchor="left" dominant-baseline="central" fill="#000000">'
                f'{display_text}</text>'
            )
            
            text2_tag = (
                f'<text x="{x + 2}" y="{y + rect_h/2 + 14}" '
                f'font-size="14" font-family="Arial" '
                f'text-anchor="left" dominant-baseline="central" fill="#000000">'
                f'{display_text2}</text>'
            )
            
            
            
            # group_tag = f'<g>\\n {rect_tag}\\n  {text_tag}\\n    </g>
            # generated_elements.append(group_tag)
            
            # generated_elements.append('<g>')
            generated_elements.append(rect_tag)
            generated_elements.append(text_tag)
            generated_elements.append(text2_tag)
            
            # generated_elements.append('</g>')


        # 3. Внедряем элементы в SVG
        # Находим закрывающий тег </svg> и вставляем перед ним
        # print("Generated SVG Elements:", generated_elements)
        
        new_elements_str = "\n    ".join(generated_elements)
        # print("New Elements String:", new_elements_str)
        
        if "</svg>" in svg_content:
            svg_content = svg_content.replace("</svg>", f"    {new_elements_str}\n</svg>")
        else:
            # Если тега нет (битый XML), просто собираем заново
            svg_content = f'<svg width="{canvas_w}" height="{canvas_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: {bg_color}">{new_elements_str}</svg>'
            

        # Создаем новую запись
        new_svg = self.env['svg.builder'].create({
            'name': self.name,
            'svg_content': svg_content,
            'width': canvas_w,
            'height': canvas_h,
            'background_color': bg_color,
        })

        self.svg_builder_id = new_svg.id
        return self.action_open_svg()
    
    
    def action_delete_svg(self):
        """Удаляет связь с SVG и саму запись SVG"""
        self.ensure_one()
        if self.svg_builder_id:
            # Сначала сохраняем ID, чтобы удалить запись из БД совсем, 
            # если она больше нигде не используется
            svg_to_delete = self.svg_builder_id
            self.svg_builder_id = False
            # Если нужно удалить запись из БД физически:
            svg_to_delete.unlink()
        return True
    
    
    

class OperationStepsCutting(models.Model):
    _name = 'operation.steps.cutting'
    _description = 'Cutting Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Step Name', required=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    equipment_reference_id = fields.Char(related='equipment_id.reference_id', string="Equipment Ref.Id")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    income_material_weight = fields.Float(string="Incoming Material Weight (kg)")
    outcome_material_weight = fields.Float(string="Outgoing Material Weight (kg)")
    income_material_crosssection = fields.Char(string="Incoming Material Cross-Section (mmxmm)")   
    outcome_material_crosssection = fields.Char(string="Outgoing Material Cross-Section (mmxmm)")
    income_material_length = fields.Float(string="Incoming Material Length (mm)")
    outcome_material_length = fields.Float(string="Outgoing Material Length (mm)")
    notes = fields.Text(string="Additional Notes")
    
    
    
class OperationStepsHeating(models.Model):
    _name = 'operation.steps.heating'
    _description = 'Heating Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # operation_type_id = fields.Many2one('operation.types', string="Operation Type", required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    recipe_name = fields.Char(string="Recipe Name")
    
    charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    heating_date = fields.Date(string="Heating Date")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

    notes = fields.Text(string="Additional Notes")

    # SVG fields
    svg_builder_id = fields.Many2one('svg.builder', string="SVG", compute='_compute_svg_builder_id', store=True)
    
    @api.model
    @api.depends('charge_id', 'charge_id.svg_builder_id')
    def _compute_svg_builder_id(self):
        for rec in self:
            # Попытка найти связанный charge_id и его SVG
            if rec.charge_id and rec.charge_id.svg_builder_id:
                rec.svg_builder_id = rec.charge_id.svg_builder_id
            else:
                rec.svg_builder_id = False
                
    
    svg_preview = fields.Html(
        string="Preview",
        sanitize=False,           # Отключает базовую очистку
        sanitize_tags=False,      # Разрешает любые теги (rect, path и т.д.)
        sanitize_attributes=False,# Разрешает любые атрибуты (stroke-width и т.d.)
        sanitize_style=False,     # Разрешает инлайн стили
        strip_style=False,        # Не удалять теги <style>
        strip_classes=False,    # Не удалять классы CSS
        compute="_compute_svg_preview",
        store=False
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
                
    svg_image = fields.Text(
        string="SVG Image",
        compute="_compute_svg_image",
        store=True
    )

    @api.depends('svg_preview')
    def _compute_svg_image(self):
        for rec in self:
            if rec.svg_preview:
                svg_bytes = rec.svg_preview.encode('utf-8')
                b64 = base64.b64encode(svg_bytes).decode('utf-8')
                rec.svg_image = f"data:image/svg+xml;base64,{b64}"
            else:
                rec.svg_image = False
                
    hardness_target_low = fields.Float(string="Hardness (low)")
    hardness_target_high = fields.Float(string="Hardness (high)")
    hardness_UOM =fields.Selection([('hrc','HRC'), ('hb', 'HB')], string="Unit", default='hrc')
    hardness_measured = fields.Float(string="Measured hardness")
    quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
      

   
class OperationStepsGringing(models.Model):
    _name = 'operation.steps.grinding'
    _description = 'Grinding Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
    
    # recipe_name = fields.Char(string="Recipe Name")
    
    # charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    # charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    # measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

    notes = fields.Text(string="Additional Notes")
    
    
# Operations steps for forging and rolling
class OperationStepsForging(models.Model): 
    _name = 'operation.steps.forging'
    _description = 'Forging Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
    
    # recipe_name = fields.Char(string="Recipe Name")
    
    # charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    # charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

    notes = fields.Text(string="Additional Notes")
    
    step_dimensions = fields.Text(string="Step Dimensions")
    start_temperature = fields.Integer(string="Start Temperature")
    end_temperature = fields.Integer(string="End Temperature")
        
        
# Operations steps for machining
class OperationStepsMachining(models.Model): 
    _name = 'operation.steps.machining'
    _description = 'Machining Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
            
    start_date_time = fields.Datetime(string="Start Date & Time")
    end_date_time = fields.Datetime(string="End Date & Time")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    # measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    income_material_crossection = fields.Char(string="Incoming Material Cross-Section (mmxmm)")   
    outcome_material_crossection = fields.Char(string="Outgoing Material Cross-Section (mmxmm)")
    income_material_length = fields.Float(string="Incoming Material Length (mm)")
    outcome_material_length = fields.Float(string="Outgoing Material Length (mm)")
    
    desired_material_crossection = fields.Char(string="Desired Material Cross-Section (mmxmm)")   
    measured_material_crossection = fields.Char(string="Measured Material Cross-Section (mmxmm)")   
    measurement_device_ids = fields.Many2many('maintenance.equipment', 'measured_device', string= "Measurement Devices")

    notes = fields.Text(string="Additional Notes")
    

class OperationStepsWeighing(models.Model):
    _name = 'operation.steps.weighing'
    _description = 'Weighing Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Measurement Equipment")
    
    # operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    # resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    # quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

    notes = fields.Text(string="Additional Notes")                

class OperationStepsSmelting(models.Model):
    _name = 'operation.steps.smelting'
    _description = 'Smelting Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    # resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    pyrometer_id = fields.Many2one('maintenance.equipment', string="Pyrometer")
    thermocouple_id = fields.Many2one('maintenance.equipment', string="Thermocouple")
    # quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    
    medium = fields.Selection(
        [('vacuum', 'Vacuum'),
         ('argon', 'Argon')],
        string="Medium")
    pressure = fields.Float(string="Pressure", digits='Process Parameter')
    pressure_uom = fields.Many2one('uom.uom', string="Unit Of Measure")
    power = fields.Float(string="Melting power")
    pyrometer_value = fields.Float(string="Temperature (pyrometer)")
    thermocouple_value = fields.Float(string="Temperature (thermocouple)")
    

    notes = fields.Char(string="Notes")
    
    def action_duplicate_line(self):
        for rec in self:
            rec.copy({
                'id': rec.id,
            })
    
    
class OperationStepsLeakageTest(models.Model):
    _name = 'operation.steps.leakage.test'
    _description = 'Leakage Test Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    operation_date_time = fields.Datetime(string="Date & Time")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    # Vakuum leakage test (before smelting)
    chamber_pressure = fields.Float(string="Chamber Pressure", digits='Process Parameter')
    chamber_pressure_5min = fields.Float(string="Chamber Pressure after 5 min", digits='Process Parameter')
    chamber_pressure_difference = fields.Float(
        string="Chamber Pressure Difference", 
        digits='Process Parameter',
        compute='_compute_chamber_pressure_difference',
        store=True,
        readonly=True)
    pressure_uom = fields.Many2one('uom.uom', string="Pressure Unit Of Measure")
    
    leakage_test_result = fields.Selection(
        [('passed', 'Passed'),
         ('failed', 'Failed')],
        string='Leakage Test Result')

    # notes = fields.Char(string="Notes")
    
    @api.depends('chamber_pressure', 'chamber_pressure_5min')
    def _compute_chamber_pressure_difference(self):
        for record in self:
            record.chamber_pressure_difference = record.chamber_pressure - record.chamber_pressure_5min 
            
            
    
class OperationStepsCasting(models.Model):
    _name = 'operation.steps.casting'
    _description = 'Casting Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )


    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    # OPERATION PARAMETERS
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    # responsible_id = fields.Many2one('hr.employee', string="Responsible")
    # resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    scales_id = fields.Many2one('maintenance.equipment', string="Scales Id.")
    measurement_id = fields.Many2one('maintenance.equipment', string="Measurement Id.")
    # quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    marking = fields.Boolean(string="Marking")
    # heat_no = fields.Char(string="Heat Number") # New heat number field
    heat_no = fields.Char(related='ingot_product_id.heat_no', string="Heat Number", readonly=False) # New heat number field
    
    # Can be calculated from step reports
    mould_number = fields.Integer(
        string="Mould Qty",
        compute='_compute_mould_number',
        store=True,
        readonly=True
    )
    total_weight = fields.Float(
        string="Total Weight (kg)",
        compute='_compute_total_weight',
        store=True,
        readonly=True
    )
    
    # ingot_product_id = fields.Many2one('product.product', string="Ingot Product")
    # ingot_quantity = fields.Float(string="Ingot Weight (kg)")
    
    # hottop_height = fields.Float(string="Hottop Height (mm)")
    # ingot_dimensions = fields.Char(string="Ingot Dimensions (mmxmm)")

    
    # CLAUDE
    # Link to production order through workorder
    production_id = fields.Many2one(
        'mrp.production',
        related='workorder_id.production_id',
        string="Production Order",
        store=True,
        readonly=True
    )
    
    # Available finished products from production
    available_ingot_ids = fields.One2many(
        'stock.move',
        related='production_id.move_finished_ids',
        string="Available Ingots",
        readonly=True
    )
    
    # Selected ingot product - auto-filled
    ingot_product_id = fields.Many2one(
        'product.product', 
        string="Ingot Product",
        compute='_compute_ingot_product',
        required=True,
        store=True,
        readonly=False,  # Allow manual override if needed
        domain="[('id', 'in', available_ingot_product_ids)]"
    )
    
    # Computed field for domain
    available_ingot_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_available_ingot_products',
        string="Available Ingot Products"
    )
    
    # Ingot quantity - auto-filled
    ingot_quantity = fields.Float(
        string="Ingot Weight (kg)",
        compute='_compute_ingot_quantity',
        inverse='_inverse_ingot_quantity',
        store=True,
        readonly=False  # Allow manual override
    )
    
    hottop_height = fields.Float(string="Hottop Height (mm)")
    ingot_dimensions = fields.Char(string="Ingot Dimensions (mmxmm)")
    
    @api.depends('production_id', 'production_id.move_finished_ids', 'workorder_id')
    def _compute_available_ingot_products(self):
        """Compute available products from production's finished moves, excluding already used ones"""
        for record in self:
            if record.workorder_id and record.production_id and record.production_id.move_finished_ids:
                # Get all products from finished moves
                all_products = record.production_id.move_finished_ids.mapped('product_id')
                
                # Find already used products in other casting steps for this workorder
                domain = [
                    ('workorder_id', 'in', record.workorder_id.ids),
                    ('ingot_product_id', '!=', False)
                ]
                
                # Exclude current record only if it exists (has ID)
                if record.id and isinstance(record.id, int):
                    domain.append(('id', '!=', record.id))
                
                used_products = self.env['operation.steps.casting'].sudo().search(domain).mapped('ingot_product_id')
                
                # Filter out used products
                available_products = all_products - used_products
                record.available_ingot_product_ids = available_products
            else:
                record.available_ingot_product_ids = False
    
    @api.depends('production_id', 'production_id.move_finished_ids', 
                 'production_id.move_finished_ids.product_id', 'workorder_id')
    def _compute_ingot_product(self):
        """Automatically set ingot product from production's finished moves"""
        for record in self:
            # Only auto-set if not manually set
            if not record.ingot_product_id and record.workorder_id and record.production_id:
                moves = record.production_id.move_finished_ids
                if moves:
                    # Get already used products
                    domain = [
                        ('workorder_id', 'in', record.workorder_id.ids),
                        ('ingot_product_id', '!=', False)
                    ]
                    
                    # Exclude current record only if it exists
                    if record.id and isinstance(record.id, int):
                        domain.append(('id', '!=', record.id))
                    
                    used_products = self.env['operation.steps.casting'].sudo().search(domain).mapped('ingot_product_id')
                    
                    # Find first unused product
                    available_moves = moves.filtered(
                        lambda m: m.product_id not in used_products
                    )
                    
                    if available_moves:
                        record.ingot_product_id = available_moves[0].product_id
                    # else:
                    #     # All products used, take first one anyway
                    #     record.ingot_product_id = moves[0].product_id
                else:
                    record.ingot_product_id = False
            elif not record.production_id:
                record.ingot_product_id = False
    
    @api.depends('ingot_product_id', 'production_id.move_finished_ids',
                 'production_id.move_finished_ids.product_uom_qty')
    def _compute_ingot_quantity(self):
        """Auto-fill quantity from corresponding stock move"""
        for record in self:
            if record.ingot_product_id and record.production_id:
                # Find the stock move for selected product
                move = record.production_id.move_finished_ids.filtered(
                    lambda m: m.product_id == record.ingot_product_id
                )
                if move:
                    # Take first move if multiple exist
                    record.ingot_quantity = move[0].product_uom_qty
                else:
                    record.ingot_quantity = 0.0
            else:
                record.ingot_quantity = 0.0
    
    def _inverse_ingot_quantity(self):
        """Sync ingot_quantity back to stock move's product_uom_qty"""
        for record in self:
            if record.ingot_product_id and record.production_id:
                # Find the corresponding stock move
                move = record.production_id.move_finished_ids.filtered(
                    lambda m: m.product_id == record.ingot_product_id
                )
                if move:
                    # Update the stock move quantity
                    move[0].sudo().write({
                        'product_uom_qty': record.ingot_quantity,
                        'quantity': record.ingot_quantity,  # Also update quantity field
                    })
    
    @api.depends('production_id', 'production_id.product_id', 'production_id.product_id.heat_no')
    def _compute_heat_no(self):
        """Auto-fill heat_no from production's product"""
        for record in self:
            if record.production_id and record.production_id.product_id:
                # Get heat_no from production's main product
                record.heat_no = record.production_id.product_id.heat_no or False
            else:
                record.heat_no = False
    
    @api.depends('workorder_id', 'workorder_id.casting_operation_ids')
    def _compute_mould_number(self):
        """Calculate mold number as count of all casting steps for this workorder"""
        for record in self:
            if record.workorder_id:
                # Count all casting steps for this workorder
                record.mould_number = self.env['operation.steps.casting'].search_count([
                    ('workorder_id', 'in', record.workorder_id.ids)
                ])
            else:
                record.mold_number = 0
    
    @api.depends('workorder_id', 'workorder_id.casting_operation_ids', 
                 'workorder_id.casting_operation_ids.ingot_quantity')
    def _compute_total_weight(self):
        """Calculate total weight as sum of all ingot quantities for this workorder"""
        for record in self:
            if record.workorder_id:
                # Get all casting steps for this workorder
                all_steps = self.env['operation.steps.casting'].search([
                    ('workorder_id', 'in', record.workorder_id.ids)
                ])
                # Sum all ingot quantities
                record.total_weight = sum(all_steps.mapped('ingot_quantity'))
            else:
                record.total_weight = 0.0
    
    @api.onchange('workorder_id')
    def _onchange_workorder_id(self):
        """Update available products when workorder changes"""
        if self.workorder_id:
            # Force recompute of available products
            self._compute_available_ingot_products()
            # Force recompute of ingot product
            if not self.ingot_product_id:
                self._compute_ingot_product()
    
    @api.onchange('ingot_product_id')
    def _onchange_ingot_product_id(self):
        """Update quantity when product changes manually"""
        if self.ingot_product_id and self.production_id:
            move = self.production_id.move_finished_ids.filtered(
                lambda m: m.product_id == self.ingot_product_id
            )
            if move:
                self.ingot_quantity = move[0].product_uom_qty
    
    @api.model_create_multi
    def create(self, vals_list):
        """Ensure fields are set on creation and update ingot product's heat_no"""
        # Pre-fill scales_id and measurement_id from previous record
        for vals in vals_list:
            if 'workorder_id' in vals and vals.get('workorder_id'):
                # Find the last (most recent) casting step for this workorder
                last_step = self.env['operation.steps.casting'].search([
                    ('workorder_id', '=', vals['workorder_id'])
                ], order='id asc', limit=1)
        
                if last_step:
                    # Copy scales_id if not provided
                    if vals['scales_id']==False and last_step.scales_id:
                        vals['scales_id'] = last_step.scales_id.id
                        
                    # Copy measurement_id if not provided
                    if vals['measurement_id']==False and last_step.measurement_id:
                        vals['measurement_id'] = last_step.measurement_id.id
                    
                    if vals['ksb_form_no']==False and last_step.ksb_form_no:
                        vals['ksb_form_no'] = last_step.ksb_form_no
                    
                    if vals['marking']==False and last_step.marking:
                        vals['marking'] = last_step.marking
                        # print("Vals Being Created:}[[[[[[[[[[[[[[]]]]]]]]]]]]]]", vals['scales_id'], vals['measurement_id'])
        
        records = super().create(vals_list)
        
        # Trigger computes to auto-fill fields
        records._compute_ingot_product()
        records._compute_heat_no()
        
        # Update heat_no on ingot products
        for record in records:
            if record.ingot_product_id and record.heat_no:
                record.ingot_product_id.sudo().write({'heat_no': record.heat_no})
        
        return records
    
    def write(self, vals):
        """Handle updates and sync heat_no to ingot product"""
        result = super().write(vals)
        
        # If workorder changed, recompute ingot product
        if 'workorder_id' in vals:
            self._compute_ingot_product()
        
        # If heat_no or ingot_product_id changed, update the product
        if 'heat_no' in vals or 'ingot_product_id' in vals:
            for record in self:
                if record.ingot_product_id and record.heat_no:
                    record.ingot_product_id.sudo().write({'heat_no': record.heat_no})
        
        return result
    
class OperationStepsSmeltingQuality(models.Model):
    _name = 'operation.steps.smelting.quality'
    _description = 'Smelting Operation Quality Control Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    responsible_id = fields.Many2one('hr.employee', string="Responsible")
    # resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('hr.employee', string="Approver for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    measurement_standard_id = fields.Many2one('standard.info', string="Measurement Standard")
    
    result = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    
    notes = fields.Char(string="Notes")
    
    operation_files = fields.Many2many("ir.attachment", string="Upload Files")
    
    
# class OperationStepsWeighing(models.Model):
#     _name = 'operation.steps.weighing'
#     _description = 'Weighing Operation Steps'
#     _order = 'sequence, id'
    
#     workorder_id = fields.Many2one(
#         'mrp.workorder', 
#         string='Work Order', 
#         required=True,
#         ondelete='cascade',
#         index=True,
#         readonly=True
#     )


#     name = fields.Char(string="Operation Step Name", required=True)
#     sequence = fields.Integer(string='Sequence', default=10)
    
#     equipment_id = fields.Many2one('maintenance.equipment', string="Measurement Equipment")
    
#     # operation_date = fields.Date(string="Operation Date")
    
#     performer_id = fields.Many2one('hr.employee', string="Performer")
#     # responsible_id = fields.Many2one('hr.employee', string="Responsible")
#     # resposible_quality_id = fields.Many2one('hr.employee', string="Responsible for Quality")
#     # quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
#     ksb_form_no = fields.Char(string="KSB Form No. (if exist)")

#     notes = fields.Text(string="Additional Notes")      
              
    
class OperationStepsRemeltingPreparation(models.Model):
    _name = 'operation.steps.remelting.preparation'
    _description = 'Remelting Operation Preparation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    sequence = fields.Integer(string='Sequence', default=10)
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    # WELDING FIELDS
    weld_material_id = fields.Many2one('product.product', string='Welding Material')
    electrod_dia = fields.Float(string='Electrod Diameter (mm)')
    electrod_length = fields.Float(string='Electrod Length (mm)')
    electrod_surface = fields.Char(string='Electrod Surface')
    performer_id = fields.Many2one('hr.employee', string='Preparation Performer')
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    
    stub_weight = fields.Float(string="Stub Weight (kg)")
    stub_length = fields.Float(string="Stub Length (mm)")
    total_length = fields.Float(string="Total Length (mm)", compute='_compute_total_length', store=True, readonly=True)
    
    # HARDNESS CONTROL FIELDS
    quality_date_time = fields.Datetime(string="Control Date & Time")
    quality_performer = fields.Many2one('hr.employee', string='Quality Performer')
    quality_responsible = fields.Many2one('hr.employee', string='Quality Responsible')
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    ksb_form_no_quality = fields.Char(string="KSB Form No. (if exist)")
    
    hardness_top = fields.Float(string="Hardness Top")
    hardness_middle = fields.Float(string="Hardness Middle")
    hardness_bottom = fields.Float(string="Hardness Bottom")
    hardness_average = fields.Float(string="Hardness Average", compute='_compute_hardness_average', store=True, readonly=True)
        
    hardness_UOM =fields.Selection([('hrc','HRC'), ('hb', 'HB')], string="Unit", default='hrc')
    
    

    @api.depends('hardness_top', 'hardness_middle', 'hardness_bottom')
    def _compute_hardness_average(self):
        for record in self:
            total = 0
            count = 0
            for value in [record.hardness_top, record.hardness_middle, record.hardness_bottom]:
                if value:
                    total += value
                    count += 1
            record.hardness_average = total / count if count > 0 else 0.0
            
    @api.depends('stub_length', 'electrod_length')
    def _compute_total_length(self):
        for record in self:
            record.total_length = record.stub_length + record.electrod_length

class OperationStepsRemeltingQuality(models.Model):
    _name = 'operation.steps.remelting.quality'
    _description = 'Remelting Operation Quality Control Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    sequence = fields.Integer(string='Sequence', default=10)
    
    # MACROSTRUCTURE FIELDS
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    performer_id = fields.Many2one('hr.employee', string="Performer")
    responsible_id = fields.Many2one('hr.employee', string="Responsible")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    etching_info = fields.Char(string="Etching Info")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    operation_files = fields.Many2many("ir.attachment", string="Upload Addition Files")
    image = fields.Binary(string="Upload Image")
    
    # QUALITY FIELDS
    operation_date_time_2 = fields.Datetime(string="Operation Date & Time")
    performer_id_2 = fields.Many2one('hr.employee', string="Performer")
    ksb_form_no_2 = fields.Char(string="KSB Form No. (if exist)")
    size_measurement_device_id = fields.Many2one('maintenance.equipment', string="Size Measurement Device")
    hardness_measurement_device_id = fields.Many2one('maintenance.equipment', string="Hardness Measurement Device")
    weight_measurement_device_id = fields.Many2one('maintenance.equipment', string="Weight Measurement Device")
    size_measurement_result = fields.Char(string="Size Measurement Result")
    hardness_measurement_result = fields.Char(string="Hardness Measurement Result")
    weight_measurement_result = fields.Char(string="Weight Measurement Result")
    heat_treatment_requirement = fields.Boolean(string="Is Heat Treatment Required?", infotext="Hardness should be below 260 HB.For exceptional circumstances, please obtain approval from the Process Supervisor.")


class OperationStepsRemelting(models.Model):
    _name = 'operation.steps.remelting'
    _description = 'Remelting Operation Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True,
        readonly=True
    )

    sequence = fields.Integer(string='Sequence', default=10)
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    process_type = fields.Selection(related='workorder_id.remelting_operation_params_id.process_type', string="Process Type", readonly=True)
    
    performer_id = fields.Many2one('hr.employee', string="Performer")
    mould_id = fields.Many2one('maintenance.equipment', string="Mould")
    # equipment_properties = fields.Properties(related='mould_id.equipment_properties', string="Mould Properties", readonly=True)
    mould_dia = fields.Float( string="Mould Diameter (mm)", readonly=True)
    

                
    aim_ingot_weight = fields.Float(string="Aim Ingot Weight (kg)")
    instruction_no = fields.Char(string="Instruction No.")
    
    # start_curve_id = fields.Char(string="Starting Curve ID")
    start_curve_id = fields.Many2one('time.chart', string="Starting Curve ID")
    start_curve_img = fields.Binary(related='start_curve_id.graph_image', string="Starting Curve Image", store=False)
    start_time = fields.Integer(string="Starting duration time (min)", compute="_compute_start_time", store=True, readonly=True)
                
    hottop_start_weight = fields.Float(string="Hottoping Start Weight (kg)")
    
    # hottop_curve_id = fields.Char(string="Hottoping Curve ID")
    hottop_curve_id = fields.Many2one('time.chart', string="Hottoping Curve ID")
    hottop_curve_img = fields.Binary(related='hottop_curve_id.graph_image', string="Hottoping Curve Image", store=False)
    hottop_time = fields.Integer(string="Hottoping duration time (min)", compute="_compute_hottop_time", store=True, readonly=True)
    hottop_stop_weight = fields.Float(string="Hottoping Stop Weight (kg)")

    
    # ESR MELTING FIELDS
    voltage_max = fields.Float(string="ESR Voltage Max (V)")
    current_max = fields.Float(string="ESR Current Max (kA)")
    swing = fields.Float(string="ESR Swing (mOhm)")
    swing_increase_ht = fields.Float(string="ECR Swing Increase HT (%)")
    
    # VAR MELTING FIELDS
    gap_set_value = fields.Float(string="VAR Gap Set Value (mm)")
    gap_auto_adjustment = fields.Boolean(string="VAR Gap Auto Adjustment")
    gap_set_value_start = fields.Float(string="VAR Gap Set Value at Start (mm)")
    gap_measurement_interval = fields.Integer(string="VAR Gap Measurement Interval (min)")
    dripshort_detection = fields.Float(string="VAR Dripshort Detection (V)")
    shortcircuit_detection = fields.Float(string="VAR Short Circuit Detection (V)")
    dripshort_frequency = fields.Integer(string="VAR Dripshort Frequency (Hz)")
    dripshort_controller = fields.Boolean(string="VAR Dripshort Controller On/Off")
    
    # ESR & VAR MELTING FIELDS
    meltrate = fields.Float(string="Meltrate (kg/h)")
    
    # COOLING FIELDS
    delta_t_set = fields.Float(string="Delta T (°C)")
    aftercooling_time = fields.Integer(string="Aftercooling Time (min)")
    pressure_hold_time = fields.Integer(string="Pressure Hold Time (min)")

    # ESR VACUUM AND PROTECTIVE GAS FIELDS
    vacuum_overpressure = fields.Float(string="Vacuum overpressure (mbar)")
    nitrogen_part = fields.Float(string="Nitrogen part (%)")
    argon_part = fields.Float(string="Argon part (%)")
    amount_flooding = fields.Float(string="Amount of Flooding (Nm3/h)")
    hood = fields.Float(string="Hood (mbar)")
    
    # VAR VACUUM AND PROTECTIVE GAS FIELDS
    leak_rate_max = fields.Float(string="VAR Leak Rate Max (mbar/min)")
    leak_rate_test_time = fields.Integer(string="VAR Leak Rate Test Time (min)")
    leak_rate_test_wait_time = fields.Integer(string="VAR Leak Rate Test Wait Time (min)")
    oil_boost_1 = fields.Boolean(string="Oil Boost 1 On/Off")
    oil_boost_2 = fields.Boolean(string="Oil Boost 2 On/Off")
    partial_pressure_on = fields.Boolean(string="Partial Pressure On/Off")
    helium_on = fields.Boolean(string="Helium On/Off")  
    gas_pressure_set = fields.Float(string="Pressure Gas Set (mbar)")
    gas_ingot_weight_start = fields.Float(string="Gas Ingot Weight at Start (kg)")
    gas_ingot_weight_stop = fields.Float(string="Gas Ingot Weight at Stop (kg)")
    helium_pressure_set = fields.Float(string="Helium Pressure Set (mbar)")
    helium_ingot_weight_start = fields.Float(string="Helium Ingot Weight at Start (kg)")
    helium_ingot_weight_stop = fields.Float(string="Helium Ingot Weight at Stop (kg)")
    
    # ESR SLAG FIELDS
    # slag_id = fields.One2many('product.product', string="Slag Type")
    # slag_amount = fields.Float(string="Slag Amount (kg)")
    start_slag_amount = fields.Float(string="Starting Slag Amount (%)")
    start_slag_time = fields.Integer(string="Start of Slag Dosing Afler Power On (min)", info="Start of Slag Dosing Afler Power On (%) min of start duration")
    continous_slag_dosing = fields.Integer(string="Continuous Slag Dosing (min)")
    # slag_total_weight = fields.Float(string="Slag Total Weight (kg)")

    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    notes = fields.Text(string="Notes")
    
    
    @api.depends("start_curve_id", "start_curve_id.line_ids", "start_curve_id.line_ids.time")
    def _compute_start_time(self):
        for record in self:
            if record.start_curve_id:
                times = record.start_curve_id.mapped('line_ids.time')
                record.start_time = int(max(times))
            else:
                record.start_time = 0
                
                
    @api.depends("hottop_curve_id", "hottop_curve_id.line_ids", "hottop_curve_id.line_ids.time")
    def _compute_hottop_time(self):
        for record in self:
            if record.hottop_curve_id:
                times = record.hottop_curve_id.mapped('line_ids.time')
                record.hottop_time = int(max(times))
            else:
                record.hottop_time = 0
    
    
    @api.depends("mould_id")
    @api.onchange("mould_id")
    def _compute_mould_dia(self, label='Diameter'):
        self.ensure_one()
        # 1. Находим определение свойства по его метке 'string'
        definition = self.mould_id.category_id.equipment_properties_definition or []
        prop_def = next((p for p in definition if p.get('string') == label), None)

        if not prop_def:
            return False

        # 2. Получаем техническое имя (ключ)
        internal_name = prop_def.get('name')
        
        self.mould_dia = self.mould_id.equipment_properties.get(internal_name)