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
    
    proposal_id = fields.Many2one('funeral.proposal', string='Proposal Number', tracking=True)
    
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
    
    deceased_dependant_id = fields.Many2one('funeral.dependant', string='Select Dependant', domain="[('proposal_id', '=', proposal_id)]")
    deceased_extended_id = fields.Many2one('funeral.extended.family', string='Select Extended Family', domain="[('proposal_id', '=', proposal_id)]")

    deceased_name = fields.Char(string='Deceased Full Name', required=True)
    deceased_dob = fields.Date(string='Deceased Date of Birth')
    date_of_death = fields.Date(string='Date of Death', required=True)
    cause_of_death = fields.Char(string='Cause of Death')
    place_of_death = fields.Selection([
        ('hospital', 'Hospital'),
        ('home', 'Home'),
        ('other', 'Other')
    ], string='Place of Death', required=True, default='hospital')
    
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

    @api.onchange('proposal_id', 'claim_for', 'deceased_dependant_id', 'deceased_extended_id')
    def _onchange_deceased_selection(self):
        if not self.proposal_id:
            return
            
        if self.claim_for == 'main':
            if self.proposal_id:
                first = self.proposal_id.first_name or ''
                last = self.proposal_id.last_name or ''
                self.deceased_name = self.proposal_id.full_name or f"{first} {last}".strip()
                self.deceased_dob = self.proposal_id.dob
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
        ('pending', 'Pending Verification'),
        ('verified', 'Verified (Awaiting Approval)'),
        ('approved', 'Approved for Disbursement'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], string='Claim Status', default='pending', tracking=True)
    
    payment_details = fields.Text(string='Payment Details (Bank/Mobile)')
    
    # Verification Matrix Output
    verification_notes = fields.Text(string='Verification Matrix Notes', readonly=True)

    def action_verify_claim(self):
        from odoo.exceptions import UserError
        for claim in self:
            if not claim.proposal_id:
                raise UserError("Cannot verify without a linked Proposal.")
                
            status_name = claim.proposal_id.status_id.name.lower() if claim.proposal_id.status_id else ''
            notes = []
            passed = True
            
            # Check 1: Is the policy structurally active?
            if 'active' not in status_name and 'revived' not in status_name:
                notes.append(f"FAILED: Policy is currently {status_name.upper()}, not Active.")
                passed = False
            else:
                notes.append("PASSED: Policy is structurally Active.")
                
            # Check 2: Arrears Check
            if claim.proposal_id.is_in_arrears:
                notes.append(f"WARNING: Policy is in arrears by {claim.proposal_id.months_in_arrears} month(s). Outstanding Balance: ${claim.proposal_id.arrears_amount}.")
                # It might still pass depending on rules, but we flag it.
                
            # Check 3: Death Certificate Attached
            if not claim.doc_death_certificate:
                notes.append("FAILED: Missing Death Certificate.")
                passed = False
            else:
                notes.append("PASSED: Death Certificate attached.")
                
            claim.verification_notes = "\n".join(notes)
            
            if passed:
                claim.state = 'verified'
            else:
                raise UserError(f"Verification Failed. See Verification Notes for details.\n\n{claim.verification_notes}")
                
    def action_approve_claim(self):
        for claim in self:
            if claim.state != 'verified':
                from odoo.exceptions import UserError
                raise UserError("Claim must be verified by the Verification Matrix before approval.")
            claim.state = 'approved'

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
