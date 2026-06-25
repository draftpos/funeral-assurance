from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FuneralProposal(models.Model):
    _name = 'funeral.proposal'
    _description = 'Funeral Proposal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Proposal Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    proposal_date = fields.Date(string='Date of Proposal', default=fields.Date.context_today)
    
    title = fields.Selection([
        ('mr', 'Mr'),
        ('mrs', 'Mrs'),
        ('miss', 'Miss'),
        ('dr', 'Dr'),
        ('prof', 'Prof')
    ], string='Title', required=True, tracking=True)
    
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    last_name = fields.Char(string='Surname', required=True, tracking=True)
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)
    
    dob = fields.Date(string='Date of Birth', required=True)
    residential_address = fields.Text(string='Residential Address')
    business_address = fields.Text(string='Business Address')
    
    home_phone = fields.Char(string='Home/Cell Number', required=True)
    business_phone = fields.Char(string='Business Phone')
    email = fields.Char(string='Email Address')
    
    employer = fields.Char(string='Employer')
    occupation = fields.Char(string='Occupation')
    ec_number = fields.Char(string='EC/Acc Number')
    gross_salary = fields.Float(string='Gross Salary')
    net_salary = fields.Float(string='Net Salary')
    
    national_id = fields.Char(string='National ID', required=True, tracking=True)
    
    first_payment_date = fields.Date(string='1st Date of Payment')
    is_override_id = fields.Boolean(string='Override National ID Format', tracking=True, help="Check this to bypass the standard National ID format validation. Requires approval.")
    
    
    gender_id = fields.Many2one('funeral.gender', string='Gender', required=True)
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], string='Marital Status')
    
    next_of_kin = fields.Char(string='Next of Kin')
    
    plan_type = fields.Selection([
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('group', 'Group')
    ], string='Plan Type', required=True)
    
    premium_amount = fields.Float(string='Premium Amount', tracking=True)
    product_id = fields.Many2one('funeral.product', string='Product Name')
    sum_assured = fields.Float(string='Sum Assured')
    policy_term = fields.Char(string='Policy Term')
    waiting_period = fields.Boolean(string='Waiting Period (Y/N)')
    
    groceries = fields.Boolean(string='Grocery Allowance ($50)', tracking=True)
    airtime = fields.Boolean(string='Airtime ($20)', tracking=True)
    
    agent_id = fields.Many2one('funeral.agent', string='Agent')
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    mode_of_payment = fields.Selection([
        ('cash', 'Cash (1)'),
        ('stop_order', 'S/O (2)')
    ], string='Mode of Payment')
    frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Frequency')
    
    dependant_ids = fields.One2many('funeral.dependant', 'proposal_id', string='Beneficiaries / Dependants')
    extended_family_ids = fields.One2many('funeral.extended.family', 'proposal_id', string='Extended Families')
    
    underwriting_decision = fields.Selection([
        ('accepted', 'Accepted Loaded / Adjusted'),
        ('declined', 'Declined')
    ], string='Underwriting Decision', tracking=True)
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('ntu', 'NTU')
    ], string='Status', default='pending', tracking=True)

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            record.full_name = f"{record.first_name} {record.last_name}" if record.first_name and record.last_name else ""

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.premium_amount = self.product_id.base_premium

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('national_id'):
                vals['name'] = vals['national_id']
        return super(FuneralProposal, self).create(vals_list)

    def write(self, vals):
        if 'national_id' in vals:
            vals['name'] = vals['national_id']
        return super(FuneralProposal, self).write(vals)

    @api.constrains('national_id', 'is_override_id')
    def _check_national_id_unique_and_format(self):
        import re
        for record in self:
            if self.search_count([('national_id', '=', record.national_id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("A proposal with this National ID already exists. The Proposer ID Number must not be duplicated."))
            
            if not record.is_override_id:
                # Basic validation for typical National ID format, e.g. 12-3456789A12
                pattern = r'^\d{2}-\d{6,7}[a-zA-Z]\d{2}$'
                if not re.match(pattern, record.national_id.replace(" ", "")):
                    raise ValidationError(_("The National ID format is invalid. Ensure it follows the format '12-3456789A12'. If this is a special ID, check 'Override National ID Format' (Requires Approval)."))

    def action_print_proposal(self):
        return self.env.ref('funeral_assurance.action_report_proposal_form').report_action(self)
