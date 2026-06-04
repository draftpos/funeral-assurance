from odoo import models, fields, api

class FuneralCity(models.Model):
    _name = 'funeral.city'
    _description = 'City'

    capture_date = fields.Date(string='Date Captured', default=fields.Date.context_today)
    name = fields.Char(string='City Name', required=True)
    region_id = fields.Many2one('funeral.region', string='Region ID')
    active = fields.Boolean(string='Status (Active/Inactive)', default=True)
