from odoo import models, fields, api

class TombstoneType(models.Model):
    _name = 'funeral.tombstone.type'
    _description = 'Tombstone Type'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)


class TombstoneSupplier(models.Model):
    _name = 'funeral.tombstone.supplier'
    _description = 'Tombstone Supplier'

    name = fields.Char(string='Supplier Name', required=True)
    contact_person = fields.Char(string='Contact Person')
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')
    address = fields.Text(string='Physical Address')
    active = fields.Boolean(default=True)


class TombstoneItem(models.Model):
    _name = 'funeral.tombstone.item'
    _description = 'Tombstone Item and Pricing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tombstone Name', required=True, tracking=True)
    type_id = fields.Many2one('funeral.tombstone.type', string='Tombstone Type', required=True, tracking=True)
    supplier_id = fields.Many2one('funeral.tombstone.supplier', string='Preferred Supplier', tracking=True)
    
    cost_price = fields.Float(string='Cost Price', tracking=True)
    selling_price = fields.Float(string='Selling Price', required=True, tracking=True)
    margin = fields.Float(string='Profit Margin', compute='_compute_margin', store=True)
    
    description = fields.Html(string='Details & Specifications')
    image = fields.Binary(string='Tombstone Image')
    active = fields.Boolean(default=True)

    @api.depends('cost_price', 'selling_price')
    def _compute_margin(self):
        for rec in self:
            rec.margin = rec.selling_price - rec.cost_price


class TombstoneOrder(models.Model):
    _name = 'funeral.tombstone.order'
    _description = 'Tombstone Order Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, default=lambda self: 'New')
    policy_id = fields.Many2one('funeral.policy', string='Related Policy', tracking=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_phone = fields.Char(string='Customer Phone')
    
    branch_id = fields.Many2one('funeral.branch', string='Branch', tracking=True)
    item_id = fields.Many2one('funeral.tombstone.item', string='Tombstone Item', required=True, tracking=True)
    supplier_id = fields.Many2one('funeral.tombstone.supplier', string='Fulfilling Supplier', tracking=True)
    
    order_date = fields.Date(string='Order Date', default=fields.Date.context_today, tracking=True)
    expected_date = fields.Date(string='Expected Delivery Date', tracking=True)
    
    cost_price = fields.Float(string='Supplier Cost', related='item_id.cost_price', readonly=False, tracking=True)
    selling_price = fields.Float(string='Amount Charged', related='item_id.selling_price', readonly=False, tracking=True)
    amount_paid = fields.Float(string='Amount Paid', default=0.0, tracking=True)
    balance_due = fields.Float(string='Balance Due', compute='_compute_balance', store=True)
    
    inscription = fields.Text(string='Tombstone Inscription (Message)')
    
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('pending', 'Pending Order'),
        ('ordered', 'Ordered from Supplier'),
        ('completed', 'Completed & Installed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('selling_price', 'amount_paid')
    def _compute_balance(self):
        for rec in self:
            rec.balance_due = rec.selling_price - rec.amount_paid

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            # We would normally use ir.sequence here, but keeping it simple for now
            vals['name'] = 'TMB/' + self.env['ir.sequence'].next_by_code('tombstone.order') or '/New'
        return super(TombstoneOrder, self).create(vals)
