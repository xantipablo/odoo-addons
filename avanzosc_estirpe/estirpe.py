# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2011 - 2012 Avanzosc <http://www.avanzosc.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import osv, fields
from tools.translate import _

class estado_productivo(osv.osv):    
    _name = 'estado.productivo'
    
    _columns = {
                'name':fields.char('Nombre', size=20, required=True),
                'cod':fields.char('Cod.', size=10),
                }   
estado_productivo()

class estandar_estirpe(osv.osv):
    _name = 'estandar.estirpe'
    
    _columns = {
                'name':fields.char('Nombre', size=20, required=True),
                'cod':fields.char('Cod.', size=10),                
                }
estandar_estirpe()

class estirpe_estirpe(osv.osv):
    
    _name = 'estirpe.estirpe'
        
    _columns = {
                'product_id':fields.many2one('estandar.estirpe','Estándar', required=True),
                'age': fields.integer('Edad', size=10, help="Se mide en semanas", required=True),
                'state_cod':fields.many2one('estado.productivo','Estado Productivo'),
                'baj_acu':fields.float('Bajas acumuladas(%)', digits = (10,3)),
                'baj_sem':fields.float('Bajas semanales(%)', digits = (10,3)),
                'peso_gall':fields.float('Peso Gallina', digits = (10,3), help="Se mide en Kg."),
                'cons_dia_gr':fields.integer('Consumo por dia',size=10, help="Se mide en gr."),
                'hue_prod':fields.float('Huevos produccion(%)', digits = (10,3)),
                'peso_medio_hue_gr':fields.float('Peso medio huevo', digits = (10,3), help="Se mide en gr."),                
                } 
    _defaults = {  
                'state_cod': lambda self,cr,uid,c: self.pool.get('estado.productivo').search(cr, uid, [('name', '=', 'Prepuesta')])[0],
                } 
 
estirpe_estirpe()

class estirpe_lot_prevision(osv.osv):
    _name = 'estirpe.lot.prevision'
    
    _columns = {
                'lot':fields.many2one('stock.production.lot', 'Lot', required=True),
                'product_id':fields.many2one('product.product', 'Estirpe'),
                'estandar_id':fields.many2one('estandar.estirpe', 'Estándar', required=True),
                'lines':fields.one2many('estirpe.line', 'previ_id', 'Lines'),
                'cre_date':fields.related('lot','date', type="date", relation="stock.production.lot", string="Create date", store=True, readonly=True),
                'date':fields.date('Load date', required=True),
                } 
    
    def onchange_lot(self, cr, uid, ids, lot, context=None):
        res = {}
        if lot:            
            lote = self.pool.get('stock.production.lot').browse(cr,uid,lot)            
            product = lote.product_id       
            res = {
                'product_id': product.id,
                }
        return {'value': res} 
    
    
             
                        
    def load_data(self, cr, uid, ids, context=None):               
        
        previ= self.pool.get('estirpe.lot.prevision').browse(cr, uid, ids, context)[0]        
        
        startdate=time.strftime('%Y-%m-%d', time.strptime(previ.date, '%Y-%m-%d'))                
        lote = previ.lot
        self.pool.get('estirpe.lot.prevision').write(cr, uid, [previ.id], {'cre_date': lote.date}) 
        
        estandar = previ.estandar_id.id
        estirpe_ids = self.pool.get('estirpe.estirpe').search(cr,uid, [('product_id', '=', estandar)])
        
        lot = previ.lot
        lines = previ.lines         
        product = lote.product_id  
        
        if lines:
            last_id = 1
            for line in lines:
                if ((line.baj_sem_real > 0.0) or (line.cons_sem_real > 0) or (line.baj_acu_real > 0.0) or (line.hue_prod_real > 0.0) or (line.peso_hue_real > 0.0)):
                    last_id = line.id
            for line in lines:
                if (line.id > last_id):
                    self.pool.get('estirpe.line').unlink(cr, uid, [line.id])
            
            last_line = self.pool.get('estirpe.line').browse(cr, uid, last_id)
            last_date = last_line.date
            last_age = last_line.age
            
            if estirpe_ids:                
                startdate = last_date                
                for id in estirpe_ids: 
                    est = self.pool.get('estirpe.estirpe').browse(cr, uid, id)
                    if est.age > last_age:
                        get_date = datetime.strptime(startdate,"%Y-%m-%d") + relativedelta(weeks=1)
            
                        line_id = self.pool.get('estirpe.line').create(cr,uid,{
                              'estandar_id':est.product_id.id,
                              'lot':lot.id,
                              'product_id':product.id,                                                
                              'date':get_date,                                                                   
                              'age' : est.age,
                              'state_cod' : est.state_cod.id,
                              'baj_acu':est.baj_acu,
                              'baj_sem':est.baj_sem,
                              'peso_gall':est.peso_gall,
                              'cons_sem_gr':est.cons_dia_gr * 7,
                              'hue_prod':est.hue_prod,
                              'peso_medio_hue_gr':est.peso_medio_hue_gr,
                              'previ_id':previ.id,
                              'baj_sem_real':0.0,
                              'cons_sem_real':0,
                              'baj_acu_real':0.0,
                              'hue_prod_real':0.0,
                              'peso_hue_real':0.0,
                        })  
                        startdate=datetime.strftime(get_date,"%Y-%m-%d")               
        else:
            if estirpe_ids:                
                get_date = datetime.strptime(startdate, '%Y-%m-%d') + relativedelta(weeks=-1)
                startdate=datetime.strftime(get_date,'%Y-%m-%d')              
                for id in estirpe_ids:
                    est = self.pool.get('estirpe.estirpe').browse(cr, uid, id)
                    get_date = datetime.strptime(startdate,"%Y-%m-%d") + relativedelta(weeks=1)
        
                    line_id = self.pool.get('estirpe.line').create(cr,uid,{
                          'estandar_id':est.product_id.id,  
                          'lot':lot.id,                                           
                          'product_id':product.id,                                                
                          'date':get_date,                                                                   
                          'age' : est.age,
                          'state_cod' : est.state_cod.id,
                          'baj_acu':est.baj_acu,
                          'baj_sem':est.baj_sem,
                          'peso_gall':est.peso_gall,
                          'cons_sem_gr':est.cons_dia_gr * 7,
                          'hue_prod':est.hue_prod,
                          'peso_medio_hue_gr':est.peso_medio_hue_gr,
                          'previ_id':previ.id,
                          'baj_sem_real':0.0,
                          'cons_sem_real':0,
                          'baj_acu_real':0.0,
                          'hue_prod_real':0.0,
                          'peso_hue_real':0.0,
                    })  
                    startdate=datetime.strftime(get_date,"%Y-%m-%d")
            else: 
                raise osv.except_osv(_('Error!'),_('There is no lineage asigned for this lot.'))       
        return previ.id  
        
estirpe_lot_prevision()

class estirpe_line(osv.osv):
    
    _name = 'estirpe.line'    
    _columns = {
                'estandar_id':fields.many2one('estandar.estirpe', 'Estándar', readonly=True),
                'age': fields.integer('Edad', size=10, help="Se mide en semanas", readonly=True),
                'state_cod':fields.many2one('estado.productivo','Estado Pro.', readonly=True),
                'baj_acu':fields.float('Baj. acu.', digits = (10,3), readonly=True),
                'baj_sem':fields.float('Baj. sem.', digits = (10,3), readonly=True),
                'peso_gall':fields.float('Peso Gallina', digits = (10,3), help="Se mide en Kg.", readonly=True),
                'cons_sem_gr':fields.integer('Con. sem.',size=10, help="Se mide en gr.", readonly=True),
                'hue_prod':fields.float('Hue. pro.', digits = (10,3), readonly=True),
                'peso_medio_hue_gr':fields.float('Peso me. hue.', digits = (10,3), help="Se mide en gr.", readonly=True),
                'previ_id':fields.many2one('estirpe.lot.prevision', 'Prevision'),
                'lot':fields.many2one('stock.production.lot', 'Lot'),
                'date':fields.date('Date', readonly=True),
                'baj_sem_real':fields.float('%Baj. sem.', digits = (10,3), required=True),  
                'cons_sem_real':fields.integer('Con. sem.',size=10, help="Se mide en gr.", required=True),
                'baj_acu_real':fields.float('%Baj. acu.', digits = (10,3), required=True),
                'hue_prod_real':fields.float('%Hue. pro.', digits = (10,3), required=True),
                'peso_hue_real':fields.float('Peso hue.', digits = (10,3), help="Se mide en gr.", required=True)    
               }
estirpe_line()

class selection_mode(osv.osv):
    _name = 'selection.mode'
    
    _columns = {
                'estandar':fields.many2one('estandar.estirpe', 'Estándar', required=True),
                'date':fields.date('Prevision start date',required=True),
                'lot':fields.many2one('stock.production.lot', 'Lot', required=True),
                }
    
    def create_prevision(self, cr, uid, ids, context=None):
        if context is None: context = {}        
        selec = self.pool.get("selection.mode").browse(cr,uid,ids)[0]
        lot = selec.lot.id
        estirpe = self.pool.get("estirpe.lot.prevision").search(cr,uid,[('lot','=',lot)])
        
        if estirpe:
            prev = estirpe[0]
            self.pool.get("estirpe.lot.prevision").write(cr, uid, [prev], {'estandar_id':selec.estandar.id})
        else:
            prev = self.pool.get("estirpe.lot.prevision").create(cr, uid, {'date': selec.date, 'estandar_id':selec.estandar.id, 'lot':selec.lot.id, 'product_id':selec.lot.product_id.id }, context=dict(context, active_ids=ids))
        
        data = self.pool.get('estirpe.lot.prevision').browse(cr,uid,prev)
        data.load_data()
       
        
        mod_obj = self.pool.get('ir.model.data')
        form_res = mod_obj.get_object_reference(cr, uid, 'avanzosc_estirpe', 'stirpe_lot_prevision_form')
        form_id = form_res and form_res[1] or False
        tree_res = mod_obj.get_object_reference(cr, uid, 'avanzosc_estirpe', 'stirpe_lot_prevision_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
#            'name':_("Prevision"),
#            'view_mode': 'form',
#            'view_type': 'form,tree',
#            'view_id': False,
#            'res_model': 'estirpe.lot.prevision',
#            'res_id': data.id,
#            'views':[(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window.close()',
#            'nodestroy': True,
#            'domain': '[]',
#            'context': dict(context, active_ids=ids) 
            }
            
            
            
    
selection_mode()

class stock_production_lot(osv.osv):
        
    _inherit = 'stock.production.lot'
    
    _columns = {
                'gallina':fields.boolean('Es gallina'),
                'lines':fields.one2many('estirpe.line', 'lot', 'Lines'),
                }

    def is_pro_name(self, cr, uid, ids, product_id, context=None):
        res={}
        if product_id:
            pro = self.pool.get('product.product').browse(cr,uid,product_id)
            if pro:            
                if ('Gallina' in pro.name):
                    res = {
                           'gallina':True
                           }
                else:
                    res = {
                           'gallina':False
                           }
        return {'value':res}
    
    
    def create_prevision(self, cr, uid, ids, context=None):
        if context is None: context = {}
       
        lot = self.pool.get('stock.production.lot').browse(cr,uid,ids)[0].id
        date =  time.strftime('%Y-%m-%d')
        est_lot = self.pool.get('estirpe.lot.prevision').search(cr, uid, [('lot','=',lot)])
        
        
        mod_obj = self.pool.get('ir.model.data')
        form_res1 = mod_obj.get_object_reference(cr, uid, 'avanzosc_estirpe', 'selection_mode_form')
        form_id1 = form_res1 and form_res1[1] or False
        form_res2 = mod_obj.get_object_reference(cr, uid, 'avanzosc_estirpe', 'selection_mode_form2')
        form_id2 = form_res2 and form_res2[1] or False
        
        
        if est_lot:
            lot_pre=self.pool.get('estirpe.lot.prevision').browse(cr,uid,est_lot[0])
            selec = self.pool.get("selection.mode").create(cr, uid, {'date':date, 'estandar':lot_pre.estandar_id.id, 'lot':lot }, context=dict(context, active_ids=ids))
            return {
                'name':_("Select options"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'selection.mode',
                'res_id': selec,
                'views': [(form_id2, 'form')],
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': dict(context, active_ids=ids) 
                }     
        else:
            selec = self.pool.get("selection.mode").create(cr, uid, {'date':date, 'estandar':1, 'lot':lot }, context=dict(context, active_ids=ids))
            return {
                'name':_("Select options"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'selection.mode',
                'res_id': selec,
                'views': [(form_id1, 'form')],
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': dict(context, active_ids=ids) 
        }
    
stock_production_lot()


class stock_move():
    _inherit = 'stock.move'
    
    def _create_lot(self, cr, uid, ids, product_id, prefix=False):
        """ Creates production lot
        @return: Production lot id
        """
        pro_name = product_id.name
        print pro_name
        if ('Gallina' in pro_name):
            ema=True
        else:
            ema=False
        prodlot_obj = self.pool.get('stock.production.lot')
        prodlot_id = prodlot_obj.create(cr, uid, {'prefix': prefix, 'product_id': product_id, 'gallina':ema})
        return prodlot_id
stock_move()

class split_in_production_lot(osv.osv_memory):
    _inherit = "stock.move.split"
     
    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into production lot
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param move_ids: the ID or list of IDs of stock move we want to split
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                for line in lines:
                    quantity = line.quantity
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        break
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        if ('Gallina' in move.product_id.name):
                            ema=True
                        else:
                            ema=False
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': move.product_id.id, 'gallina':ema},
                        context=context)

                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        move_obj.write(cr, uid, [move.id], update_val)

        return new_move
    
split_in_production_lot()