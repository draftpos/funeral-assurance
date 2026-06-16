import sys
import os

# Mock Odoo classes
class MockOdoo:
    class models:
        class Model:
            pass
        class TransientModel:
            pass
    class fields:
        Date = lambda *a, **k: None
        Date.context_today = None
        Datetime = lambda *a, **k: None
        Datetime.now = None
        Char = lambda *a, **k: None
        Selection = lambda *a, **k: None
        Float = lambda *a, **k: None
        Boolean = lambda *a, **k: None
        Many2one = lambda *a, **k: None
        One2many = lambda *a, **k: None
        Many2many = lambda *a, **k: None
        Text = lambda *a, **k: None
        Integer = lambda *a, **k: None
        Binary = lambda *a, **k: None
        class date_utils:
            relativedelta = lambda *a, **k: None
    class api:
        def depends(*args): return lambda f: f
        def model_create_multi(f): return f
        def onchange(*args): return lambda f: f
        def constrains(*args): return lambda f: f
        model = lambda f: f
    def _(s): return s

sys.modules['odoo'] = MockOdoo
sys.modules['odoo.exceptions'] = type('exceptions', (), {'ValidationError': Exception})

try:
    print("Trying to import models.__init__")
    import models
    print("Successfully imported models")
except Exception as e:
    import traceback
    traceback.print_exc()
