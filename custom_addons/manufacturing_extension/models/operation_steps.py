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
        index=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # operation_type_id = fields.Many2one('operation.types', string="Operation Type", required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    recipe_name = fields.Char(string="Recipe Name")
    
    charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    heating_date = fields.Date(string="Heating Date")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
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
        index=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
    
    # recipe_name = fields.Char(string="Recipe Name")
    
    # charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    # charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
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
        readonly=True,
    )

    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
    
    # recipe_name = fields.Char(string="Recipe Name")
    
    # charge_id = fields.Many2one(related="workorder_id.charge_id", string="Charge ID", readonly=True)
    # charge_component_ids = fields.Many2many(related="charge_id.mo_component_ids", string="Charge Component IDs", readonly=True)
    
    operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
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
        readonly=True,
    )

    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    tools_ids = fields.Many2many('maintenance.equipment', string= "Used tools")
            
    start_date_time = fields.Datetime(string="Start Date & Time")
    end_date_time = fields.Datetime(string="End Date & Time")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
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
        index=True
    )


    name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    equipment_id = fields.Many2one('maintenance.equipment', string="Measurement Equipment")
    
    # operation_date = fields.Date(string="Operation Date")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    # resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
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
        index=True
    )


    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    # resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
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
    
    
class OperationStepsLeakageTest(models.Model):
    _name = 'operation.steps.leakage.test'
    _description = 'Leakage Test Steps'
    _order = 'sequence, id'
    
    workorder_id = fields.Many2one(
        'mrp.workorder', 
        string='Work Order', 
        required=True,
        ondelete='cascade',
        index=True
    )


    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    operation_date_time = fields.Datetime(string="Date & Time")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    # Vakuum leakage test (before smelting)
    chamber_pressure = fields.Float(string="Chamber Pressure (mbar)", digits='Process Parameter')
    chamber_pressure_5min = fields.Float(string="Chamber Pressure after 5 min (mbar)", digits='Process Parameter')
    chamber_pressure_difference = fields.Float(
        string="Chamber Pressure Difference (mbar)", 
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
        index=True
    )


    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    # OPERATION PARAMETERS
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    # resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
    scales_id = fields.Many2one('maintenance.equipment', string="Scales Id.")
    measurement_id = fields.Many2one('maintenance.equipment', string="Measurement Id.")
    # quality_approval = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    marking = fields.Boolean(string="Marking")
    # heat_no = fields.Char(string="Heat Number") # New heat number field
    heat_no = fields.Char(related='ingot_product_id.heat_no', string="Heat Number", readonly=False) # New heat number field
    
    # Can be calculated from step reports
    mold_number = fields.Integer(
        string="Mold Qty",
        compute='_compute_mold_number',
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
    def _compute_mold_number(self):
        """Calculate mold number as count of all casting steps for this workorder"""
        for record in self:
            if record.workorder_id:
                # Count all casting steps for this workorder
                record.mold_number = self.env['operation.steps.casting'].search_count([
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
        index=True
    )

    # name = fields.Char(string="Operation Step Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    
    operation_date_time = fields.Datetime(string="Operation Date & Time")
    
    performer_id = fields.Many2one('res.users', string="Performer")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    # resposible_quality_id = fields.Many2one('res.users', string="Responsible for Quality")
    # approver_quality_id = fields.Many2one('res.users', string="Approver for Quality")
    measurement_device_id = fields.Many2one('maintenance.equipment', string="Measurement Device")
    measurement_standard_id = fields.Many2one('standard.info', string="Measurement Standard")
    
    result = fields.Selection([('approve','Approve'), ('reject', 'Reject')])
    ksb_form_no = fields.Char(string="KSB Form No. (if exist)")
    
    notes = fields.Char(string="Notes")