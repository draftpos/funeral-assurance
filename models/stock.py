from odoo import models, fields, api

class FuneralStockType(models.Model):
    _name = 'funeral.stock.type'
    _description = 'Stock Type'

    name = fields.Char(string='Stock Type Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

class FuneralStockItem(models.Model):
    _name = 'funeral.stock.item'
    _description = 'Stock Item'

    name = fields.Char(string='Stock Name', required=True)
    stock_type_id = fields.Many2one('funeral.stock.type', string='Stock Type', required=True)
    price = fields.Float(string='Price', required=True)
    quantity_on_hand = fields.Float(string='Quantity On Hand', default=0.0)
    branch_id = fields.Many2one('funeral.branch', string='Branch')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
    valuation = fields.Float(string='Stock Valuation', compute='_compute_valuation', store=True)

    @api.depends('price', 'quantity_on_hand')
    def _compute_valuation(self):
        for rec in self:
            rec.valuation = rec.price * rec.quantity_on_hand

class FuneralStockTransaction(models.Model):
    _name = 'funeral.stock.transaction'
    _description = 'Stock Transaction'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: 'New')
    stock_item_id = fields.Many2one('funeral.stock.item', string='Stock Item', required=True)
    transaction_type = fields.Selection([
        ('in', 'Receipt'),
        ('out', 'Issue'),
        ('adjustment', 'Adjustment')
    ], string='Transaction Type', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Processed By', default=lambda self: self.env.user)
    adjustment_reason = fields.Char(string='Adjustment Reason')
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('funeral.stock.transaction') or 'New'
        record = super(FuneralStockTransaction, self).create(vals)
        # Update stock quantity
        if record.stock_item_id:
            if record.transaction_type == 'in':
                record.stock_item_id.quantity_on_hand += record.quantity
            elif record.transaction_type == 'out':
                record.stock_item_id.quantity_on_hand -= record.quantity
            elif record.transaction_type == 'adjustment':
                record.stock_item_id.quantity_on_hand = record.quantity
        return record
