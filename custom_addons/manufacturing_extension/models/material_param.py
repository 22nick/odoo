# Material properties
# 
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class MaterialGrade(models.Model):
    _name = 'material.grade'
    _description = 'Grade of Material'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
        
    name = fields.Char(string="Grade", required=True)
    material_type_id = fields.Many2one("material.type", string="Material Type", required=True)
    material_group_id = fields.Many2one("material.group", string="Material Group", required=True, domain="[('material_type_id', '=', material_type_id)]")
    density = fields.Float(string="Density (g/cm3)")
    shrinkage_factor = fields.Float(string="Shrinkage Factor")
    description = fields.Text(string="Description")
    
    @api.onchange('material_type_id')
    def _onchange_material_type(self):
        """Очищаем material_group если изменился material_type"""
        if self.material_group_id and self.material_group_id.material_type_id != self.material_type_id:
            self.material_group_id = False
        return {
            'domain': {
                'material_group_id': [('material_type_id', '=', self.material_type_id.id)]
            }
        }
    
    @api.onchange('material_group_id')
    def _onchange_material_group(self):
        """Автоматически устанавливаем material_type при выборе material_group"""
        if self.material_group_id:
            self.material_type_id = self.material_group_id.material_type_id
    
    @api.constrains('material_type_id', 'material_group_id')
    def _check_material_consistency(self):
        """Валидация соответствия material_type и material_group"""
        for record in self:
            if record.material_group_id and record.material_type_id:
                if record.material_group_id.material_type_id != record.material_type_id:
                    raise ValidationError(
                        'Material Group "%s" не соответствует выбранному Material Type "%s". '
                        'Этот Material Group относится к типу "%s".' % (
                            record.material_group_id.name,
                            record.material_type_id.name,
                            record.material_group_id.material_type_id.name
                        )
                    )
    

class MaterialType(models.Model):
    _name = 'material.type'
    _description = 'Type of Material'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
    
    name = fields.Char(string="Material Type", required=True)
    # material_group_ids = fields.One2many("material.group", "name", string="Material Groups")
    description = fields.Text(string="Description")    

    
class MateriaGroup(models.Model):
    _name = 'material.group'
    _description = 'Group of Material'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
     
    name = fields.Char(string="Material Group", required=True)
    material_type_id = fields.Many2one("material.type", string="Material Type", required=True)
    description = fields.Text(string="Description")
    

class ProductSlagData(models.Model):
    _name = 'product.slag.data'
    _description = 'Slag Data for Material'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
     
    name = fields.Char(string="Slag Name", required=True)
    description = fields.Text(string="Description")
    
    # product_id = fields.Many2one('product.template', string='Product')
    product_id = fields.One2many('product.template', 'slag_data_id', string='Product')
    
    slag_caf2_part = fields.Float(string="Slag CaF2 Part (%)")
    slag_al2o3_part = fields.Float(string="Slag Al2O3 Part (%)")
    slag_mgO_part = fields.Float(string="Slag MgO Part (%)")
    slag_cao_part = fields.Float(string="Slag CaO Part (%)")
    slag_sio2_part = fields.Float(string="Slag SiO2 Part (%)")
    slag_tio2_part = fields.Float(string="Slag TiO2 Part (%)")

    
    
class ProductPhysicalData(models.Model):
    _name = 'product.physical.data'
    _description = 'Product Physical Data'
    _order = 'sequence, id'
    
    
    sequence = fields.Integer(string='Sequence', default=11, invisible=True)
    active = fields.Boolean(string='Active', default=True)
     
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    
    # product_id = fields.Many2one('product.template', string='Product')
    product_id = fields.One2many('product.template', 'physical_data_id', string='Product')