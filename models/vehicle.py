from odoo import models, fields, api

class FuneralVehicle(models.Model):
    _name = 'funeral.vehicle'
    _description = 'Funeral Vehicle Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Vehicle Reg / Name', required=True, tracking=True)
    vehicle_type = fields.Selection([
        ('hearse', 'Hearse'),
        ('family_car', 'Family Car'),
        ('utility', 'Utility/Pool Car'),
        ('bus', 'Bus'),
        ('other', 'Other')
    ], string='Vehicle Type', required=True, tracking=True)
    license_plate = fields.Char(string='License Plate', required=True, tracking=True)
    make = fields.Char(string='Make')
    model = fields.Char(string='Model')
    year = fields.Char(string='Year of Manufacture')
    color = fields.Char(string='Color')
    chassis_number = fields.Char(string='Chassis Number')
    engine_number = fields.Char(string='Engine Number')
    
    branch_id = fields.Many2one('funeral.branch', string='Branch Allocation', tracking=True)
    
    # Dates and Compliance
    purchase_date = fields.Date(string='Purchase Date')
    license_expiry = fields.Date(string='License Expiry Date', tracking=True)
    insurance_expiry = fields.Date(string='Insurance Expiry Date', tracking=True)
    roadworthy_expiry = fields.Date(string='Roadworthy Expiry Date')
    
    # Tracking
    mileage = fields.Float(string='Current Mileage', tracking=True)
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], string='Fuel Type')
    
    status = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
        ('sold', 'Sold/Disposed')
    ], string='Status', default='active', tracking=True)
    active = fields.Boolean(default=True)
    
    # Service Tracking
    next_service_due = fields.Date(string='Next Service Due Date', tracking=True)
    next_service_mileage = fields.Float(string='Next Service Mileage', tracking=True)


class FuneralDriver(models.Model):
    _name = 'funeral.driver'
    _description = 'Vehicle Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Driver Name', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='System User Link')
    license_number = fields.Char(string='License Number', required=True, tracking=True)
    license_expiry = fields.Date(string='License Expiry Date', tracking=True)
    contact_number = fields.Char(string='Contact Number')
    active = fields.Boolean(default=True)


class VehicleTrip(models.Model):
    _name = 'funeral.vehicle.trip'
    _description = 'Vehicle Trip Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Trip Reference', required=True, copy=False, readonly=True, default=lambda self: 'New')
    vehicle_id = fields.Many2one('funeral.vehicle', string='Vehicle', required=True, tracking=True)
    driver_id = fields.Many2one('funeral.driver', string='Driver', required=True, tracking=True)
    claim_id = fields.Many2one('funeral.claim', string='Funeral Reference (Claim)', tracking=True)
    
    date = fields.Date(string='Date of Trip', default=fields.Date.context_today, tracking=True)
    start_mileage = fields.Float(string='Start Mileage', required=True)
    end_mileage = fields.Float(string='End Mileage')
    distance = fields.Float(string='Distance Travelled (km)', compute='_compute_distance', store=True)
    
    destination = fields.Char(string='Destination')
    purpose = fields.Text(string='Purpose of Trip')

    @api.depends('start_mileage', 'end_mileage')
    def _compute_distance(self):
        for rec in self:
            if rec.end_mileage and rec.start_mileage:
                rec.distance = rec.end_mileage - rec.start_mileage
            else:
                rec.distance = 0.0
                
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = 'TRIP/' + self.env['ir.sequence'].next_by_code('vehicle.trip') or '/New'
        return super(VehicleTrip, self).create(vals)


class VehicleFuelLog(models.Model):
    _name = 'funeral.vehicle.fuel.log'
    _description = 'Vehicle Fuel Log'

    vehicle_id = fields.Many2one('funeral.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('funeral.driver', string='Driver', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    liters = fields.Float(string='Liters Filled', required=True)
    cost = fields.Float(string='Total Cost', required=True)
    odometer = fields.Float(string='Odometer Reading')
    receipt_number = fields.Char(string='Receipt Number')
    notes = fields.Text(string='Notes')


class VehicleMaintenance(models.Model):
    _name = 'funeral.vehicle.maintenance'
    _description = 'Vehicle Maintenance Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one('funeral.vehicle', string='Vehicle', required=True, tracking=True)
    date = fields.Date(string='Service Date', default=fields.Date.context_today, tracking=True)
    service_type = fields.Selection([
        ('routine', 'Routine Service'), 
        ('repair', 'Breakdown Repair'),
        ('inspection', 'Inspection')
    ], string='Service Type', required=True, tracking=True)
    
    odometer = fields.Float(string='Odometer at Service')
    description = fields.Text(string='Description / Parts Replaced')
    cost = fields.Float(string='Total Cost', tracking=True)
    mechanic = fields.Char(string='Workshop / Mechanic')
    invoice_number = fields.Char(string='Invoice Number')
