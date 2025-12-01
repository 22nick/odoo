from odoo import api, models, fields


class OperationTypes(models.Model):
    _name = 'operation.types'
    _description = 'Operation Types for Manufacturing'


    name = fields.Char(string="Operation Type Name", required=True)


class OperaionCharge(models.Model):
    _name = 'operation.charge'
    _description = 'Charge Details for Processing (e.g., Heating)'

    charge_name = fields.Char(string="Charge Name", required=True)
    product_list = fields.Many2one('product.template', string="Product", required=True)
    

class OperationSteps_Heating(models.Model):
    _name = 'operation.steps'
    _description = 'Operation Steps for Manufacturing'


    name = fields.Char(string="Operation Step Name", required=True)
    operation_type_id = fields.Many2one('operation.types', string="Operation Type", required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment")
    recipe_name = fields.Char(string="Recipe Name")
    charge_id = fields.Many2one('operation.charge', string="Charge ID")
    heating_date = fields.Date(string="Heating Date")
    

   
    

