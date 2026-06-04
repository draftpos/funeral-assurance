from odoo import models, fields

class FuneralProductRate(models.Model):
    _name = 'funeral.product.rate'
    _description = 'Product Rate'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    product_id = fields.Many2one('funeral.product', string='Product ID')
    age_range = fields.Char(string='Age Range')
    premium_amount = fields.Float(string='Premium Amount')
    coverage_amount = fields.Float(string='Coverage Amount')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralProduct(models.Model):
    _name = 'funeral.product'
    _description = 'Product'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Product Name', required=True)
    product_description = fields.Text(string='Product Description')
    coverage_details = fields.Text(string='Coverage Details')
    premium_structure = fields.Text(string='Premium Structure')
    eligibility_criteria = fields.Text(string='Eligibility Criteria')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralCommissionRate(models.Model):
    _name = 'funeral.commission.rate'
    _description = 'Commission Rate'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    agent_category_id = fields.Many2one('funeral.agent.category', string='Agent Category ID')
    product_id = fields.Many2one('funeral.product', string='Product ID')
    commission_percentage = fields.Float(string='Commission Percentage')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)
