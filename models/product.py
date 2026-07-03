from odoo import models, fields

class FuneralProductRate(models.Model):
    _name = 'funeral.product.rate'
    _description = 'Product Rate'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    product_id = fields.Many2one('funeral.product', string='Product ID')

    name = fields.Char(string='Sub-Plan Name', help='e.g., Bronze Plan, Hukama Standard')
    structural_type_id = fields.Many2one('funeral.structural.type', string='Plan Type', required=True)
    extended_family_top_up = fields.Float(string='Extended Family Top-Up (USD)', default=2.0)
    grocery_benefit = fields.Float(string='Grocery Benefit (USD)')
    casket_allocation = fields.Selection([
        ('standard', 'Standard Casket'),
        ('two_tier', 'Two-Tier Casket'),
        ('three_tier', 'Three-Tier Casket'),
        ('dome', 'Dome-Shape Casket'),
        ('custom', 'Custom Casket')
    ], string='Casket Allocation')
    premium_amount = fields.Float(string='Premium Amount')
    sum_assured = fields.Float(string='Sum Assured')
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
