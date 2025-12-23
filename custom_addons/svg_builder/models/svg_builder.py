from odoo import models, fields, api


class SvgBuilder(models.Model):
    _name = 'svg.builder'
    _description = 'SVG Builder'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    svg_content = fields.Text(string='SVG Content')
    width = fields.Integer(string='Width', default=800)
    height = fields.Integer(string='Height', default=600)
    background_color = fields.Char(string='Background Color', default='#ffffff')

    @api.model
    def create_svg(self, name, svg_content, width=800, height=600, background_color='#ffffff'):
        """Create a new SVG record"""
        return self.create({
            'name': name,
            'svg_content': svg_content,
            'width': width,
            'height': height,
            'background_color': background_color,
        })

    def update_svg(self, svg_content):
        """Update SVG content"""
        self.svg_content = svg_content
        return True


