from odoo import models, fields, api, _

class FuneralClaim(models.Model):
    _name = 'funeral.claim'
    _description = 'Funeral Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Claim ID', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    
    claim_category = fields.Selection([
        ('sum_assured', 'Sum Assured'),
        ('standard', 'Standard Claim'),
        ('private', 'Private Claim')
    ], string='Claim Category', required=True, default='standard', tracking=True)
    
    policy_id = fields.Many2one('funeral.policy', string='Policy Number', tracking=True)
    
    # Claimant Details
    claimant_name = fields.Char(string='Claimant Name', required=True)
    claimant_relationship = fields.Char(string='Relationship to Deceased')
    claimant_contact = fields.Char(string='Claimant Contact')
    
    # Deceased Details
    claim_for = fields.Selection([
        ('main', 'Main Member'),
        ('dependant', 'Dependant'),
        ('extended', 'Extended Family')
    ], string='Claim For', required=True, default='main', tracking=True)
    
    deceased_dependant_id = fields.Many2one('funeral.dependant', string='Select Dependant', domain="[('policy_id', '=', policy_id)]")
    deceased_extended_id = fields.Many2one('funeral.extended.family', string='Select Extended Family', domain="[('policy_id', '=', policy_id)]")

    deceased_name = fields.Char(string='Deceased Full Name', required=True)
    deceased_dob = fields.Date(string='Deceased Date of Birth')
    date_of_death = fields.Date(string='Date of Death', required=True)
    cause_of_death = fields.Char(string='Cause of Death')
    
    # Documents
    doc_death_certificate = fields.Binary(string='Death Certificate')
    doc_medical_report = fields.Binary(string='Medical Report')
    doc_burial_order = fields.Binary(string='Burial Order')
    doc_id_copies = fields.Binary(string='ID Copies')
    
    # Specific Claim Form Fields
    claimed_by = fields.Char(string='Claimed By')
    authorised_by = fields.Char(string='Authorised By')
    employer = fields.Char(string='Company/Group Employer')
    place_of_burial = fields.Char(string='Place of Burial')
    certificate_of_death_no = fields.Char(string='Certificate of Death No.')
    sum_assured_payable_by = fields.Selection([
        ('nostro', 'Nostro Account'),
        ('zig', 'ZiG Account')
    ], string='Sum Assured Payable By')
    
    # Funeral Services Fields
    driver_name = fields.Char(string='Name of Driver')
    funeral_service_provider = fields.Char(string='Funeral Service Provider Name')
    provider_contact = fields.Char(string='Provider Contact Details')
    provider_invoice_ref = fields.Char(string='Provider Invoice Reference')
    service_cost_ids = fields.One2many('funeral.claim.service', 'claim_id', string='Service Cost Analysis')
    
    total_service_cost = fields.Float(string='Total Service Cost', compute='_compute_total_service_cost', store=True)

    @api.depends('service_cost_ids.amount')
    def _compute_total_service_cost(self):
        for claim in self:
            claim.total_service_cost = sum(line.amount for line in claim.service_cost_ids)

    @api.onchange('policy_id', 'claim_for', 'deceased_dependant_id', 'deceased_extended_id')
    def _onchange_deceased_selection(self):
        if not self.policy_id:
            return
            
        if self.claim_for == 'main':
            if self.policy_id.proposal_id:
                first = self.policy_id.proposal_id.first_name or ''
                last = self.policy_id.proposal_id.last_name or ''
                self.deceased_name = self.policy_id.proposal_id.full_name or f"{first} {last}".strip()
                self.deceased_dob = self.policy_id.proposal_id.dob
        elif self.claim_for == 'dependant' and self.deceased_dependant_id:
            first = self.deceased_dependant_id.first_name or ''
            last = self.deceased_dependant_id.last_name or ''
            self.deceased_name = f"{first} {last}".strip()
            self.deceased_dob = self.deceased_dependant_id.dob
        elif self.claim_for == 'extended' and self.deceased_extended_id:
            first = self.deceased_extended_id.first_name or ''
            last = self.deceased_extended_id.last_name or ''
            self.deceased_name = f"{first} {last}".strip()
            self.deceased_dob = self.deceased_extended_id.dob

    # Claim Details
    claim_type = fields.Selection([
        ('cash', 'Cash Payout'),
        ('service', 'Funeral Service'),
        ('both', 'Both')
    ], string='Claim Type', required=True)
    
    claim_amount = fields.Float(string='Claim Amount', tracking=True)
    date_submitted = fields.Date(string='Date Submitted', default=fields.Date.context_today)
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], string='Claim Status', default='pending', tracking=True)
    
    payment_details = fields.Text(string='Payment Details (Bank/Mobile)')

    def action_print_sum_assured(self):
        return self.env.ref('funeral_assurance.action_report_sum_assured_claim').report_action(self)

    def action_print_funeral_services(self):
        return self.env.ref('funeral_assurance.action_report_funeral_services_claim').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('funeral.claim') or _('New')
        return super(FuneralClaim, self).create(vals_list)

class FuneralClaimService(models.Model):
    _name = 'funeral.claim.service'
    _description = 'Claim Service Cost'

    claim_id = fields.Many2one('funeral.claim', string='Claim', ondelete='cascade')
    name = fields.Char(string='Service/Item Description', required=True)
    amount = fields.Float(string='Amount (USD)')
