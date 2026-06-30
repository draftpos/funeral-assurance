from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class FuneralProposal(models.Model):
    _name = 'funeral.proposal'
    _description = 'Funeral Proposal / Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Proposal / Policy Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    proposal_date = fields.Date(string='Date of Proposal', default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Linked Customer Profile', readonly=True, tracking=True)
    
    title = fields.Selection([('mr', 'Mr'), ('mrs', 'Mrs'), ('miss', 'Miss'), ('dr', 'Dr'), ('prof', 'Prof')], string='Title', required=True, tracking=True)
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
    is_override_id = fields.Boolean(string='Override National ID Format', tracking=True)
    
    gender_id = fields.Many2one('funeral.gender', string='Gender', required=True)
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')], string='Marital Status')
    
    next_of_kin = fields.Char(string='Next of Kin')
    
    plan_type = fields.Selection([('individual', 'Individual'), ('family', 'Family'), ('group', 'Group')], string='Plan Type', required=True)
    
    product_id = fields.Many2one('funeral.product', string='Product Name')
    premium_amount = fields.Float(string='Base Premium', tracking=True)
    total_premium = fields.Float(string='Total Premium', compute='_compute_total_premium', store=True)
    sum_assured = fields.Float(string='Sum Assured')
    policy_term = fields.Char(string='Policy Term')
    waiting_period = fields.Boolean(string='Waiting Period (Y/N)')
    
    agent_id = fields.Many2one('funeral.agent', string='Agent')
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    mode_of_payment = fields.Selection([('cash', 'Cash (1)'), ('stop_order', 'S/O (2)')], string='Mode of Payment')
    frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Frequency')
    
    dependant_ids = fields.One2many('funeral.dependant', 'proposal_id', string='Beneficiaries / Dependants')
    extended_family_ids = fields.One2many('funeral.extended.family', 'proposal_id', string='Extended Families')
    benefit_ids = fields.Many2many('funeral.benefit', string='Benefits')
    
    underwriting_decision = fields.Selection([('accepted', 'Accepted Loaded / Adjusted'), ('declined', 'Declined')], string='Underwriting Decision', tracking=True)
    
    # State / Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('ntu', 'NTU'),
        ('active', 'Active'),
        ('lapse', 'Lapse'),
        ('revival', 'Revival')
    ], string='System State', default='pending', tracking=True)
    status_id = fields.Many2one('funeral.policy.status', string='Custom Status', tracking=True)
    
    # Policy Fields
    paid_up_to = fields.Date(string='Paid Up To', tracking=True)
    is_in_arrears = fields.Boolean(string='In Arrears', compute='_compute_is_in_arrears', store=True)
    months_paid_to_agent = fields.Integer(string='Months Paid to Agent', default=0)
    commencement_date = fields.Date(string='Commencement Date')
    cancellation_reason = fields.Text(string='Reason for Cancellation', tracking=True)
    policy_document = fields.Binary(string='Policy Document', attachment=True)
    policy_document_name = fields.Char(string='Document Name')

    @api.depends('paid_up_to')
    def _compute_is_in_arrears(self):
        for record in self:
            if record.paid_up_to and record.paid_up_to < fields.Date.context_today(self):
                record.is_in_arrears = True
            else:
                record.is_in_arrears = False

    @api.depends('premium_amount', 'extended_family_ids.extended_premium_amount', 'benefit_ids.premium_amount')
    def _compute_total_premium(self):
        for record in self:
            ext_prem = sum(ext.extended_premium_amount for ext in record.extended_family_ids)
            opt_prem = sum(opt.premium_amount for opt in record.benefit_ids)
            record.total_premium = record.premium_amount + ext_prem + opt_prem

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            record.full_name = f"{record.first_name} {record.last_name}" if record.first_name and record.last_name else ""

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            rate = self.env['funeral.product.rate'].search([('product_id', '=', self.product_id.id)], limit=1)
            if rate:
                self.premium_amount = rate.premium_amount
                self.sum_assured = rate.coverage_amount
            else:
                self.premium_amount = self.product_id.base_premium
                self.sum_assured = 0.0
            # Auto-pull mandatory benefits
            mandatory_benefits = self.env['funeral.benefit'].search([('benefit_type', '=', 'mandatory')])
            self.benefit_ids = [(6, 0, mandatory_benefits.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('national_id'):
                vals['name'] = vals['national_id']
            if not vals.get('status_id'):
                underwriting_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Underwriting')], limit=1)
                if underwriting_status:
                    vals['status_id'] = underwriting_status.id
        return super(FuneralProposal, self).create(vals_list)

    def write(self, vals):
        if 'national_id' in vals:
            vals['name'] = vals['national_id']
            
        res = super(FuneralProposal, self).write(vals)
        
        # Automatically create Customer Profile when Proposal is Accepted or Active
        if vals.get('state') in ['accepted', 'active']:
            for record in self:
                if not record.partner_id:
                    partner = self.env['res.partner'].create({
                        'name': record.full_name,
                        'phone': record.home_phone,
                        'email': record.email or '',
                        'street': record.residential_address or '',
                        'vat': record.national_id,
                        'is_company': False,
                        'customer_rank': 1,
                        'comment': f'Auto-created from Funeral Proposal {record.name}'
                    })
                    record.partner_id = partner.id
        return res

    @api.constrains('national_id', 'is_override_id')
    def _check_national_id_unique_and_format(self):
        import re
        for record in self:
            if self.search_count([('national_id', '=', record.national_id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("A proposal with this National ID already exists."))
            
            if not record.is_override_id:
                pattern = r'^\d{2}-\d{6,7}[a-zA-Z]\d{2}$'
                if not re.match(pattern, record.national_id.replace(" ", "")):
                    raise ValidationError(_("The National ID format is invalid."))

    def action_print_proposal(self):
        return self.env.ref('funeral_assurance.action_report_proposal_form').report_action(self)

    def action_create_payment(self):
        self.ensure_one()
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'funeral.payment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_proposal_id': self.id,
                'default_branch_id': self.branch_id.id,
                'default_premium_amount': self.total_premium or self.premium_amount,
                'default_payment_frequency': self.frequency,
            }
        }
        
    @api.model
    def process_policy_lapses(self):
        # Lapsing logic for Proposal
        # Total arrears / monthly premium >= 4
        active_proposals = self.search([('state', '=', 'active')])
        for proposal in active_proposals:
            if not proposal.paid_up_to:
                continue
                
            today = fields.Date.context_today(self)
            if proposal.paid_up_to < today:
                # Calculate months in arrears
                diff = relativedelta(today, proposal.paid_up_to)
                months_in_arrears = diff.years * 12 + diff.months
                
                if months_in_arrears >= 4:
                    lapse_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Lapse')], limit=1)
                    proposal.state = 'lapse'
                    if lapse_status:
                        proposal.status_id = lapse_status.id

class FuneralDependant(models.Model):
    _name = 'funeral.dependant'
    _description = 'Policy Dependant'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', ondelete='cascade')
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Surname', required=True)
    relationship = fields.Selection([('spouse', 'Spouse'), ('child', 'Child'), ('parent', 'Parent')], string='Relationship', required=True)
    dob = fields.Date(string='Date of Birth')
    national_id = fields.Char(string='National ID Number')
    gender_id = fields.Many2one('funeral.gender', string='Gender')
    occupation = fields.Char(string='Occupation/School')
    contact_number = fields.Char(string='Contact Cell Number')
    coverage_status = fields.Selection([('active', 'Active'), ('removed', 'Removed'), ('deceased', 'Deceased')], string='Coverage Status', default='active')

class FuneralExtendedFamily(models.Model):
    _name = 'funeral.extended.family'
    _description = 'Extended Family Member'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', ondelete='cascade')
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Surname', required=True)
    relationship_id = fields.Many2one('funeral.relationship', string='Relationship to Proposer', required=True)
    dob = fields.Date(string='Date of Birth')
    national_id = fields.Char(string='National ID Number')
    gender_id = fields.Many2one('funeral.gender', string='Gender')
    occupation = fields.Char(string='Occupation')
    contact_number = fields.Char(string='Contact Cell Number')
    extended_premium_amount = fields.Float(string='Extended Premium Amount')
    coverage_status = fields.Selection([('active', 'Active'), ('removed', 'Removed'), ('deceased', 'Deceased')], string='Coverage Status', default='active')
    
    @api.onchange('relationship_id')
    def _onchange_relationship_id(self):
        if self.relationship_id:
            self.extended_premium_amount = self.relationship_id.premium_amount

class FuneralPromoWizard(models.TransientModel):
    _name = 'funeral.promo.wizard'
    _description = 'Promo Wizard'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', required=True)
    months_paid = fields.Integer(string='Months to Pay', required=True)
    months_forgiven = fields.Integer(string='Months to Forgive', required=True)
    
    def action_apply_promo(self):
        self.ensure_one()
        current_date = self.proposal_id.paid_up_to or self.proposal_id.commencement_date or fields.Date.context_today(self)
        
        total_months_advanced = self.months_paid + self.months_forgiven
        self.proposal_id.paid_up_to = current_date + relativedelta(months=total_months_advanced)
        
        if self.proposal_id.state in ['lapse', 'ntu']:
            self.proposal_id.state = 'active'
            active_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Active')], limit=1)
            if active_status:
                self.proposal_id.status_id = active_status.id
            
        if self.months_paid > 0:
            self.env['funeral.payment'].create({
                'proposal_id': self.proposal_id.id,
                'premium_amount': self.proposal_id.total_premium * self.months_paid,
                'payment_frequency': 'monthly',
                'payment_method': 'cash',
                'premium_status': 'paid'
            })
