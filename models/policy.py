from odoo import models, fields

class FuneralPolicy(models.Model):
    _name = 'funeral.policy'
    _description = 'Funeral Policy (Deprecated)'

    name = fields.Char(string='Policy Number')
