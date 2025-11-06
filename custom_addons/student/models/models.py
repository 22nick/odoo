from odoo import api, models, fields #, api
from odoo.exceptions import UserError
from lxml import etree

class school(models.Model):
    _name = 'wb.school'
    _description = 'This is school profile'

    school_image = fields.Image("School Image",help="This field holds the image used as school image.")

    name = fields.Char("School Name")

    student_list = fields.One2many("wb.student","school_id", string="Student List")

    binary_field = fields.Binary("Upload One File", copy=True, attachment=True)
    binary_file_fname = fields.Char("Binary File Name")

    binary_fields = fields.Many2many("ir.attachment", string="Multiple Files Upload",)

    student_id = fields.Many2one("wb.student", string="Student")

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
       
        rtn = super(school, self).get_view(view_id=view_id, view_type=view_type, **options)
        # if view_type == 'form' and 'arch' in rtn:
        #     print("This is get view method of student.", self, view_id, view_type, options)
        #     doc = etree.fromstring(rtn['arch'])
        #     # school_field = etree.Element("field", {"name":"student_id"})
        #     # targetd_field = doc.xpath("//field[@name='name']")
        #     # if targetd_field:
        #     #     targetd_field[0].addnext(school_field)

        #     targetd_field = doc.xpath("//field[@name='name']")
        #     if targetd_field:
        #         targetd_field[0].set("string", "Customized School Name")


        #     rtn['arch'] = etree.tostring(doc, encoding='unicode')
            
        #     print(rtn)
        return rtn




    # def create(self, vals):
    #     print(self)
    #     print("Vals Data is : ", vals)
    #     rtn = super(school, self).create(vals)
    #     print("Return Data is : ", rtn)
    #     return rtn

    # @api.model
    @api.model_create_multi
    # @api.model_create_single
    def create(self, vals):
        print(self)
        print("Vals Data is : ", vals)
        rtn = super(school, self).create(vals)
        print("Return Data is : ", rtn)
        return rtn

    def custom_method(self):
        print("This is custom method of school.", self)
        # data = {"name": "New School from Custom Method"}
        # self.env["wb.school"].create(data)

        # print(self.search([]))
        # print(self.env["wb.student"].search([]))

        # print(self.search([("name", "like", "School")], order="name desc", limit=2))


        # stud_obj = self.env['wb.student']
        # student_ids = stud_obj.search([])
        # print(student_ids)

        # student_fees = []
        # for stud in student_ids:
        #     student_fees.append(stud.student_fees)

        # student_fees = student_ids.mapped('school_id').mapped('name')    
        student_fees = self.env['wb.student'].search([]).mapped('school_id').mapped('name')    

        print(student_fees)
        # print("Sum of Student Fees: ", sum(student_fees))

        stud_list = self.env['wb.student'].search([]).sorted(key=lambda stud: stud.student_fees, reverse=True)    
        print("Sorted Student List by Fees: ", stud_list)
        
    def abs_test(self):
        print("Button clicked! This is abs_test method.", self)

class student(models.Model):
    _name = 'wb.student'
    _description = 'This is student profile'

    school_id = fields.Many2one(comodel_name="wb.school",
                                string="School",
                                index=True)    

    school_data = fields.Json()

    @api.model
    def _get_vip_list(self):
        return [('a','1'), 
                ('b', '2'),
                ('c', '3')
             ]

    is_paid = fields.Boolean("Is Paid") 
    
    roll_number = fields.Integer(string="Enrollment Number", default=200, index=True)

    student_fees = fields.Float("Student Fees", digits=(3,2))    
    discount_fees = fields.Float("Discount Fees")
    
    gender = fields.Selection([('male','Male'), ('female', 'Female')])

    advance_gender = fields.Selection("_get_advance_gender_list")

    vip_gender = fields.Selection(_get_vip_list, string="VIP Gender")

    name = fields.Char("Name")
    name1 = fields.Char("Name1")
    name2 = fields.Char("Name2", copy = False)
    name3 = fields.Char("Name3", default="Weblearns", help="This is help")
    name4 = fields.Char("Name4", readonly=True)

    student_name = fields.Char("Student", required=True, index=True, help="This is student name")
    address_html = fields.Html("Address HTML", tracking=True)
    
    final_fees = fields.Float("Final Fees", compute="_compute_final_fees_cal", store=True)

    compute_address_html = fields.Html("Computed Address Field.")

    student_img = fields.Image("Student Image")


    



    @api.onchange('address_html')
    def _onchange_address_html_field(self):
        for record in self:
            record.compute_address_html = record.address_html


    def _compute_final_fees_cal(self):
        for record in self:
            record.final_fees = record.student_fees - record.discount_fees

    def _get_advance_gender_list(self):
        return [('male','Male'), 
                 ('female', 'Female'), 
                 ('other', 'Other')
                 ]
    
    def json_data_store(self):
        self.school_data = {
            "name": self.name,
            "id": self.id,
            "fees": self.student_fees,
            "g": self.gender}
        
    def custom_method(self):
        print("This is custom method of student.", self)




        # students = self.env['wb.student'].search([])
        # print("Students Records: ", students)

        # student_filtered = self.env['wb.student'].search([('name', 'like', 'ddd')])
        # print("Filtered Students Records: ", student_filtered)

        # student_filtered = self.env['wb.student'].search([("id","in",students.ids),('name', 'like', 'ddd')])
        # print("Filtered Students Records 2: ", student_filtered)

        # stud_obj = self.env['wb.student']
        # for stud in students:
        #     if 'ddd' in stud.name:
        #         stud_obj += stud

        # print("Filtered Students Obj: ", stud_obj)

        # stud_obj = students.filtered(lambda stud: '1' in str(stud.name))
        # print("Filtered Students Obj 2: ", stud_obj)

        # data = {"name": "New School from Custom Method"}
        # self.env["wb.school"].create(data)

        # search(domain, limit, offset, order, count)
        # [condition, more conditions]

        # print(self.search([]))
        
# class student_extend(models.Model):
#     _inherit = 'sale.order'

#     reference_note = fields.Char(string="Reference Note")   


#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

