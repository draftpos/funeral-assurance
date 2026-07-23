import re
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
    residential_address = fields.Text(string='Residential Address', required=True)
    business_address = fields.Text(string='Business Address')
    
    home_phone = fields.Char(string='Home/Cell Number', required=True)
    business_phone = fields.Char(string='Business Phone')
    email = fields.Char(string='Email Address')
    
    employer = fields.Char(string='Employer')
    occupation_id = fields.Many2one('funeral.occupation', string='Occupation')
    ec_number = fields.Char(string='EC/Acc Number')
    gross_salary = fields.Float(string='Gross Salary')
    net_salary = fields.Float(string='Net Salary')
    
    national_id = fields.Char(string='National ID', required=True, tracking=True)
    first_payment_date = fields.Date(string='1st Date of Payment', default=fields.Date.context_today)
    is_override_id = fields.Boolean(string='Override National ID Format', tracking=True)
    
    gender_id = fields.Many2one('funeral.gender', string='Gender', required=True)
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')], string='Marital Status', required=True)
    
    next_of_kin = fields.Char(string='Next of Kin', required=True)
    
    structural_type_id = fields.Many2one('funeral.structural.type', string='Plan Type', required=True)
    is_policy_state = fields.Boolean(related='status_id.is_policy_state', readonly=True)
    allow_dependants = fields.Boolean(related='structural_type_id.allow_dependants', readonly=True)
    allow_extended_family = fields.Boolean(related='structural_type_id.allow_extended_family', readonly=True)
    grocery_benefit = fields.Float(string='Grocery Benefit (USD)')
    casket_allocation = fields.Char(string='Casket Allocation')
    
    product_id = fields.Many2one('funeral.product', string='Product Name', required=True)
    has_sub_plans = fields.Boolean(compute='_compute_has_sub_plans')
    structural_type_id = fields.Many2one('funeral.structural.type', string='Plan Type', required=True)
    product_rate_id = fields.Many2one('funeral.product.rate', string='Sub-Plan')
    premium_amount = fields.Float(string='Premium Amount', tracking=True)
    total_premium = fields.Float(string='Total Premium', compute='_compute_total_premium', store=True)
    sum_assured = fields.Float(string='Sum Assured')
    policy_term = fields.Char(string='Policy Term')
    waiting_period = fields.Boolean(string='Waiting Period (Y/N)')
    
    agent_id = fields.Many2one('funeral.agent', string='Agent', required=True)
    branch_id = fields.Many2one('funeral.branch', string='Branch', required=True)
    mode_of_payment = fields.Selection([('cash', 'Cash (1)'), ('stop_order', 'S/O (2)')], string='Mode of Payment')
    frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Frequency', default='monthly', required=True)
    
    dependant_ids = fields.One2many('funeral.dependant', 'proposal_id', string='Beneficiaries / Dependants')
    extended_family_ids = fields.One2many('funeral.extended.family', 'proposal_id', string='Extended Families')
    benefit_ids = fields.Many2many('funeral.benefit', string='Benefits')
    
    underwriting_decision = fields.Selection([('accepted', 'Accepted Loaded / Adjusted'), ('declined', 'Declined')], string='Underwriting Decision', tracking=True)
    
    # State / Status
    status_id = fields.Many2one('funeral.policy.status', string='Status', tracking=True)
    state = fields.Char(related='status_id.name', string='State Name')
    has_payment = fields.Boolean(compute='_compute_has_payment')
    
    # Policy Fields
    paid_up_to = fields.Date(string='Paid Up To', tracking=True)
    is_in_arrears = fields.Boolean(string='In Arrears', compute='_compute_is_in_arrears')
    months_in_arrears = fields.Integer(string='Months in Arrears', compute='_compute_is_in_arrears')
    arrears_amount = fields.Float(string='Arrears Balance', compute='_compute_is_in_arrears')
    months_paid_to_agent = fields.Integer(string='Months Paid to Agent', default=0, tracking=True)
    revival_payments_count = fields.Integer(string='Revival Payments Count', default=0, tracking=True)
    commencement_date = fields.Date(string='Commencement Date')
    cancellation_reason = fields.Text(string='Reason for Cancellation', tracking=True)
    # Admin Policy Attachment
    admin_policy_id = fields.Many2one('funeral.admin.policy', string='Select User Admin Policy', tracking=True)
    admin_policy_filename = fields.Char(string='Admin Policy Filename', compute='_compute_admin_policy_filename')
    admin_policy_description = fields.Text(related='admin_policy_id.policy_description', string='Admin Policy Terms & Summary', readonly=True)

    @api.depends('admin_policy_id', 'admin_policy_id.name')
    def _compute_admin_policy_filename(self):
        for record in self:
            if record.admin_policy_id and record.admin_policy_id.name:
                record.admin_policy_filename = f"{record.admin_policy_id.name}.pdf"
            else:
                record.admin_policy_filename = "Admin_Policy_Document.pdf"

    policy_document = fields.Binary(string='Policy Document', attachment=True)
    policy_document_name = fields.Char(string='Document Name')

    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        if self.agent_id and self.agent_id.branch_id:
            self.branch_id = self.agent_id.branch_id.id

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', record.email.lower())
                if match == None:
                    raise ValidationError(_('Please enter a valid email address!'))

    @api.depends('paid_up_to', 'total_premium', 'premium_amount')
    def _compute_is_in_arrears(self):
        for record in self:
            if record.paid_up_to and record.paid_up_to < fields.Date.context_today(self):
                record.is_in_arrears = True
                today = fields.Date.context_today(self)
                diff = relativedelta(today, record.paid_up_to)
                months = diff.years * 12 + diff.months
                if diff.days > 0:
                    months += 1
                record.months_in_arrears = months
                base_premium = record.total_premium or record.premium_amount
                record.arrears_amount = months * base_premium
            else:
                record.is_in_arrears = False
                record.months_in_arrears = 0
                record.arrears_amount = 0.0

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

    @api.depends('product_id')
    def _compute_has_sub_plans(self):
        for record in self:
            if record.product_id:
                rates = self.env['funeral.product.rate'].search([('product_id', '=', record.product_id.id)])
                type_counts = {}
                for r in rates:
                    if r.structural_type_id:
                        tid = r.structural_type_id.id
                        type_counts[tid] = type_counts.get(tid, 0) + 1
                
                # If ANY plan type has more than 1 rate, it means this product uses sub-plans.
                record.has_sub_plans = any(count > 1 for count in type_counts.values())
            else:
                record.has_sub_plans = False

    @api.onchange('product_id')
    def _onchange_product_domain(self):
        # Clear child fields when parent changes
        self.structural_type_id = False
        self.product_rate_id = False

    @api.onchange('product_id', 'product_rate_id', 'structural_type_id')
    def _onchange_calculate_price(self):
        # NEVER auto-fill Plan Type or Product.
        # ONLY calculate money if Product and Plan Type are selected.
        if self.product_id and self.structural_type_id:
            domain = [
                ('product_id', '=', self.product_id.id),
                ('structural_type_id', '=', self.structural_type_id.id)
            ]
            
            # If the product has sub-plans, ensure one is selected before pricing
            if self.has_sub_plans:
                if not self.product_rate_id:
                    self._clear_money()
                    return
                # Use the selected sub-plan name to find the exact rate for this plan type
                domain.append(('name', '=', self.product_rate_id.name))
                
            rates = self.env['funeral.product.rate'].search(domain, limit=1)
            if rates:
                rate = rates[0]
                self.premium_amount = rate.premium_amount
                self.sum_assured = rate.sum_assured
                self.grocery_benefit = rate.grocery_benefit
                if rate.casket_allocation:
                    self.casket_allocation = dict(rate._fields['casket_allocation'].selection).get(rate.casket_allocation)
                else:
                    self.casket_allocation = ''
            else:
                self._clear_money()
        else:
            self._clear_money()

    def _clear_money(self):
        self.premium_amount = 0.0
        self.sum_assured = 0.0
        self.grocery_benefit = 0.0
        self.casket_allocation = ''
        
    def action_accept_proposal(self):
        for record in self:
            status = self.env['funeral.policy.status'].search([('name', '=', 'Accepted')], limit=1)
            if status:
                record.status_id = status.id
            if not record.admin_policy_id:
                default_admin_policy = self.env['funeral.admin.policy'].search([('active', '=', True)], limit=1)
                if default_admin_policy:
                    record.admin_policy_id = default_admin_policy.id
                
    def action_print_proposal(self):
        return self.env.ref('funeral_assurance.action_report_proposal_form').report_action(self)

    def action_download_user_policy(self):
        self.ensure_one()
        if not self.admin_policy_id or not self.admin_policy_id.document_upload:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Document Found',
                    'message': 'No User Policy document has been uploaded under Static Data -> Company Admin Policies.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=funeral.admin.policy&id={self.admin_policy_id.id}&field=document_upload&filename_field=name',
            'target': 'new',
        }

    def action_activate_policy(self):
        for record in self:
            status = self.env['funeral.policy.status'].search([('name', '=', 'Active')], limit=1)
            if status:
                record.status_id = status.id

    def action_activate_error(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Initial Payment Required',
                'message': "Please use the 'Make Payment' button to capture the first premium. You can activate the policy immediately after the payment is saved!",
                'type': 'info',
                'sticky': False,
            }
        }

    def _compute_has_payment(self):
        for record in self:
            count = self.env['funeral.payment'].search_count([('proposal_id', '=', record.id)])
            record.has_payment = count > 0

    @api.constrains('dependant_ids', 'extended_family_ids', 'structural_type_id')
    def _check_structural_limits(self):
        for record in self:
            if not record.structural_type_id:
                continue
                
            if not record.structural_type_id.allow_dependants and len(record.dependant_ids) > 0:
                raise ValidationError(_("This plan type does not allow dependants."))
            if record.structural_type_id.max_dependants > 0 and len(record.dependant_ids) > record.structural_type_id.max_dependants:
                raise ValidationError(_("You cannot exceed the maximum allowed dependants (%s) for this plan.") % record.structural_type_id.max_dependants)
                
            if not record.structural_type_id.allow_extended_family and len(record.extended_family_ids) > 0:
                raise ValidationError(_("This plan type does not allow extended family members."))
            if record.structural_type_id.max_extended_family > 0 and len(record.extended_family_ids) > record.structural_type_id.max_extended_family:
                raise ValidationError(_("You cannot exceed the maximum allowed extended family members (%s) for this plan.") % record.structural_type_id.max_extended_family)

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
        if vals.get('status_id'):
            status_record = self.env['funeral.policy.status'].browse(vals.get('status_id'))
            if status_record.name.lower() in ['accepted', 'active']:
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
                    raise ValidationError(_("The National ID format is invalid. Please use the correct format (e.g. 63-1234567A89)."))

    def action_print_proposal(self):
        return self.env.ref('funeral_assurance.action_report_proposal_form').report_action(self)

    def action_open_promo_wizard(self):
        self.ensure_one()
        return {
            'name': _('Apply Promotion'),
            'type': 'ir.actions.act_window',
            'res_model': 'funeral.promo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_proposal_id': self.id}
        }

    def action_force_lapse(self):
        for record in self:
            lapse_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Lapse')], limit=1)
            if lapse_status:
                record.status_id = lapse_status.id

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
                'default_payment_frequency': self.frequency,
            }
        }
        
    @api.model
    def process_policy_lapses(self):
        # Lapsing logic for Proposal
        # Total arrears / monthly premium >= 4
        active_statuses = self.env['funeral.policy.status'].search(['|', ('name', 'ilike', 'Active'), ('name', 'ilike', 'Revived')])
        if not active_statuses:
            return
        active_proposals = self.search([('status_id', 'in', active_statuses.ids)])
        for proposal in active_proposals:
            if not proposal.paid_up_to:
                continue
                
            today = fields.Date.context_today(self)
            if proposal.paid_up_to < today:
                # Calculate months in arrears
                diff = relativedelta(today, proposal.paid_up_to)
                months_in_arrears = diff.years * 12 + diff.months
                
                lapse_threshold = int(self.env['ir.config_parameter'].sudo().get_param('funeral.lapse_months', default=4))
                
                if months_in_arrears >= lapse_threshold:
                    lapse_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Lapse')], limit=1)
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
    has_college_proof = fields.Boolean(string='Has College Proof / Enrollment')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)

    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = relativedelta(fields.Date.context_today(self), record.dob).years
            else:
                record.age = 0
    
    @api.constrains('dob', 'has_college_proof')
    def _check_extended_family_age(self):
        for record in self:
            if record.dob:
                age = relativedelta(fields.Date.context_today(self), record.dob).years
                if age > 18 and age <= 23 and not record.has_college_proof:
                    raise ValidationError(_("Extended family members over 18 require college proof for coverage up to 23 years old. (Age: %s)") % age)
                elif age > 23:
                    raise ValidationError(_("Extended family members over the age of 23 cannot be covered under this policy, even with college proof. (Age: %s)") % age)
    
    @api.onchange('relationship_id')
    def _onchange_relationship_id(self):
        if self.relationship_id:
            self.extended_premium_amount = self.relationship_id.premium_amount

class FuneralPromoWizard(models.TransientModel):
    _name = 'funeral.promo.wizard'
    _description = 'Promo Wizard'

    proposal_id = fields.Many2one('funeral.proposal', string='Proposal', required=True)
    months_paid = fields.Integer(string='Months to Pay', required=True, default=1)
    months_forgiven = fields.Integer(string='Months to Forgive', required=True, default=0)
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mobile', 'Mobile Money'),
        ('debit', 'Debit Order')
    ], string='Payment Method', required=True, default='cash')
    receipt_number = fields.Char(string='Receipt Number', required=True)
    
    @api.constrains('months_paid')
    def _check_months_paid(self):
        for record in self:
            if record.months_paid <= 0:
                raise ValidationError("To revive a policy, the client MUST pay for at least 1 month. You can forgive the rest.")
    
    def action_apply_promo(self):
        self.ensure_one()
        current_date = self.proposal_id.paid_up_to or self.proposal_id.commencement_date or fields.Date.context_today(self)
        
        total_months_advanced = self.months_paid + self.months_forgiven
        self.proposal_id.paid_up_to = current_date + relativedelta(months=total_months_advanced)
        
        if self.proposal_id.status_id and self.proposal_id.status_id.name.lower() in ['lapse', 'ntu']:
            active_status = self.env['funeral.policy.status'].search([('name', 'ilike', 'Active')], limit=1)
            if active_status:
                self.proposal_id.status_id = active_status.id
            
        if self.months_paid > 0:
            self.env['funeral.payment'].create({
                'proposal_id': self.proposal_id.id,
                'premium_amount': self.proposal_id.total_premium * self.months_paid,
                'payment_frequency': 'monthly',
                'payment_method': self.payment_method,
                'receipt_number': self.receipt_number,
                'premium_status': 'paid'
            })
