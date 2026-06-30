from odoo import models, fields, api, _

class FuneralRegion(models.Model):
    _name = 'funeral.region'
    _description = 'Region'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Region Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralGender(models.Model):
    _name = 'funeral.gender'
    _description = 'Gender'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Gender Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralAgentCategory(models.Model):
    _name = 'funeral.agent.category'
    _description = 'Agent Category'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Category Name', required=True)
    months_to_pay = fields.Integer(string='Months to Pay')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralBranch(models.Model):
    _name = 'funeral.branch'
    _description = 'Branch'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Branch Name', required=True)
    branch_code = fields.Char(string='Branch Code')
    physical_address = fields.Text(string='Physical Address')
    city_id = fields.Many2one('funeral.city', string='City ID')
    region_id = fields.Many2one('funeral.region', string='Region ID')
    contact_number = fields.Char(string='Contact Number')
    email_address = fields.Char(string='Email Address')
    branch_manager = fields.Char(string='Branch Manager')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralPolicyStatus(models.Model):
    _name = 'funeral.policy.status'
    _description = 'Policy Status'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Status Name', required=True)
    duration_months = fields.Integer(string='Duration (Months)', help='How many months before transition')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralControlRight(models.Model):
    _name = 'funeral.control.right'
    _description = 'Management Systems Control Right'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Role Name', required=True)
    access_rights = fields.Selection([('create', 'Create'), ('read', 'Read'), ('update', 'Update'), ('delete', 'Delete')], string='Access Rights')
    module_name = fields.Char(string='Module/Feature Name')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralRelationship(models.Model):
    _name = 'funeral.relationship'
    _description = 'Relationship'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Relationship Name', required=True)
    premium_amount = fields.Float(string='Premium Amount', required=True)
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralBenefit(models.Model):
    _name = 'funeral.benefit'
    _description = 'Benefit'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='Benefit Name', required=True)
    benefit_type = fields.Selection([
        ('mandatory', 'Mandatory'),
        ('optional', 'Optional')
    ], string='Benefit Type', required=True, default='optional')
    description = fields.Text(string='Description')
    premium_amount = fields.Float(string='Premium Amount (Cost)')
    beneficial_amount = fields.Float(string='Beneficial Amount (Payout)')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)

class FuneralReceiptBook(models.Model):
    _name = 'funeral.receipt.book'
    _description = 'Receipt Book Range'
    
    name = fields.Char(string='Book Name/Reference', required=True)
    prefix = fields.Char(string='Receipt Prefix', default='R', help="E.g. 'R' for R1000")
    start_number = fields.Integer(string='Start Number', required=True)
    end_number = fields.Integer(string='End Number', required=True)
    active = fields.Boolean(default=True)
    
    @api.constrains('start_number', 'end_number')
    def _check_ranges(self):
        from odoo.exceptions import ValidationError
        for record in self:
            if record.start_number >= record.end_number:
                raise ValidationError("End Number must be greater than Start Number.")
