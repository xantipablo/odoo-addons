# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Copyright (C) 2012 Avanzosc (http://Avanzosc.com). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields

class aid(osv.osv):
    _name = 'aid'
    _description = 'aid'
    
    _columns = {
            
            'contact_id': fields.many2one('res.partner.contact', 'Contact', required=True),
            'denomination':fields.char('Denomination', size=128),
            'finality':fields.char('Finality', size=128),
            'entity':fields.char('Entity', size=128),
            'financier_entity':fields.char('Financier Entity', size=128),
            'grant_date': fields.date('Grant Date'),
            'duration':fields.char('Duration', size=128),

    }
aid()
