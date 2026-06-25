from odoo import models, fields, api, _

class FuneralPolicy(models.Model):
    _name = 'funeral.policy'
    _description = 'Funeral Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Policy Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal ID', required=True, tracking=True)
    
    product_id = fields.Many2one('funeral.product', string='Product', required=True)
    plan_type = fields.Selection(string='Plan Type', related='proposal_id.plan_type', store=True)
    
    sum_assured = fields.Float(string='Sum Assured', tracking=True)
    premium = fields.Float(string='Base Premium', tracking=True)
    
    policy_term = fields.Char(string='Policy Term')
    waiting_period = fields.Boolean(string='Waiting Period')
    
    mode_of_payment = fields.Char(string='Mode of Payment')
    frequency_of_payments = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Frequency of Payments', default='monthly')
    
    agent_id = fields.Many2one('funeral.agent', string='Agent')
    agent_code = fields.Char(string='Agent Code')
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    region_id = fields.Many2one('funeral.region', string='Region')
    
    payment_method = fields.Selection([
        ('bank', 'Bank'),
        ('ecocash', 'Ecocash'),
        ('biller_code', 'Biller Code'),
        ('cash', 'Cash')
    ], string='Payment Method')
    
    commencement_date = fields.Date(string='Commencement Date')
    
    state = fields.Selection([
        ('active', 'Active'),
        ('lapsed', 'Lapsed'),
        ('revived', 'Revived'),
    ], string='Policy Status', default='active', tracking=True)
    
    cancellation_reason = fields.Text(string='Reason for Cancellation', tracking=True)
    
    months_paid_to_agent = fields.Integer(string='Months Paid to Agent', default=0)
    
    dependant_ids = fields.One2many('funeral.dependant', 'policy_id', string='Dependants')
    extended_family_ids = fields.One2many('funeral.extended.family', 'policy_id', string='Extended Family')
    optional_benefit_ids = fields.Many2many('funeral.optional.benefit', string='Optional Benefits')
    
    groceries = fields.Boolean(string='Grocery Allowance ($50)', tracking=True)
    airtime = fields.Boolean(string='Airtime ($20)', tracking=True)
    
    policy_document = fields.Binary(string='Policy Document', attachment=True)
    policy_document_name = fields.Char(string='Document Name')
    
    total_premium = fields.Float(string='Total Premium', compute='_compute_total_premium', store=True)

    @api.depends('premium', 'extended_family_ids.extended_premium_amount', 'optional_benefit_ids.premium_amount')
    def _compute_total_premium(self):
        for record in self:
            ext_prem = sum(ext.extended_premium_amount for ext in record.extended_family_ids)
            opt_prem = sum(opt.premium_amount for opt in record.optional_benefit_ids)
            record.total_premium = record.premium + ext_prem + opt_prem

    def action_print_policy(self):
        return self.env.ref('funeral_assurance.action_report_policy_schedule').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('proposal_id') and vals.get('name', _('New')) == _('New'):
                proposal = self.env['funeral.proposal'].browse(vals['proposal_id'])
                if proposal.national_id:
                    vals['name'] = proposal.national_id
        return super(FuneralPolicy, self).create(vals_list)

    @api.model
    def process_policy_lapses(self):
        # Fetch configured lapse months (default to 3, industry standard)
        lapse_months = int(self.env['ir.config_parameter'].sudo().get_param('funeral.lapse_months', default=3))
        
        # Rule 1: Proposals older than X months with no payments -> NTU
        lapse_date = fields.Date.context_today(self) - fields.date_utils.relativedelta(months=lapse_months)
        
        stale_proposals = self.env['funeral.proposal'].search([
            ('state', '=', 'pending'),
        ])
        for prop in stale_proposals:
            if prop.proposal_date and prop.proposal_date <= lapse_date:
                prop.state = 'ntu'
            
        # Rule 2: Active policies with last payment > X months ago -> Lapsed
        active_policies = self.search([('state', '=', 'active')])
        for policy in active_policies:
            last_payment = self.env['funeral.payment'].search(
                [('policy_id', '=', policy.id), ('premium_status', '=', 'paid')],
                order='payment_date desc', limit=1
            )
            
            should_lapse = False
            if last_payment and last_payment.payment_date <= lapse_date:
                should_lapse = True
            elif not last_payment and policy.commencement_date and policy.commencement_date <= lapse_date:
                should_lapse = True
                
            if should_lapse:
                policy.state = 'lapsed'
                # Charge penalty to agent
                if policy.agent_id:
                    penalty_amount = policy.premium * -0.3333
                    self.env['funeral.commission'].create({
                        'agent_id': policy.agent_id.id,
                        'policy_id': policy.id,
                        'amount': penalty_amount,
                        'type': 'penalty',
                        'state': 'draft'
                    })

class FuneralDependant(models.Model):
    _name = 'funeral.dependant'
    _description = 'Policy Dependant'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', ondelete='cascade')
    policy_id = fields.Many2one('funeral.policy', string='Policy Number', ondelete='cascade')
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Surname', required=True)
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent')
    ], string='Relationship', required=True)
    
    dob = fields.Date(string='Date of Birth')
    national_id = fields.Char(string='National ID Number')
    gender_id = fields.Many2one('funeral.gender', string='Gender')
    occupation = fields.Char(string='Occupation/School')
    contact_number = fields.Char(string='Contact Cell Number')
    coverage_status = fields.Selection([
        ('active', 'Active'),
        ('removed', 'Removed'),
        ('deceased', 'Deceased')
    ], string='Coverage Status', default='active')

class FuneralExtendedFamily(models.Model):
    _name = 'funeral.extended.family'
    _description = 'Extended Family Member'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', ondelete='cascade')
    policy_id = fields.Many2one('funeral.policy', string='Policy Number', ondelete='cascade')
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Surname', required=True)
    relationship = fields.Selection([
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('cousin', 'Cousin'),
        ('grandparent', 'Grandparent'),
        ('other', 'Other')
    ], string='Relationship to Proposer', required=True)
    
    dob = fields.Date(string='Date of Birth')
    national_id = fields.Char(string='National ID Number')
    gender_id = fields.Many2one('funeral.gender', string='Gender')
    occupation = fields.Char(string='Occupation')
    contact_number = fields.Char(string='Contact Cell Number')
    extended_premium_amount = fields.Float(string='Extended Premium Amount')
    coverage_status = fields.Selection([
        ('active', 'Active'),
        ('removed', 'Removed'),
        ('deceased', 'Deceased')
    ], string='Coverage Status', default='active')
