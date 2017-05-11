#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
import sys

global c, render
rrdDir = '../ELSArrd/rrd/'


class WebModal():
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.modal(mail,type,id)
        return ''
	
class WebMenu():        
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.menu(mail,type,id)
        return ''
	
class WebAllmenu():        
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.allmenu(mail,type,id)
        return ''

class WebObject():
    def __init__(self):
        self.name = u"WebIndex"
        
    def GET(self):
        mail = isConnected()
        if mail is not None:
            return self.getRender(mail)
        return render.index(False,'')
        
    def POST(self):
        data = web.input(nifile={})
        #method = data.get("method","malformed")
        connectedUser = connexion(data._username_,data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_) 
        return render.index(False, '')
        
class WebObjectUpdate():
    def GET(self,id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id,mail, '')
        raise web.seeother('/')
        
    def POST(self, id):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(id,self.name)
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                for key in c.getFieldsname(self.name):
                    if key in data:
                        currObject.fields[key] = data[key]
                        
                for key in c.AllLanguages.elements:
                    if key in data:
                        currObject.setName(key, data[key],user, c.getKeyColumn(currObject))
                        
                if 'deny'in data:
                    currObject.set_deny('1')
                else:
                    currObject.set_deny('0')
                
                if 'remark' in currObject.fields:
                    currObject.fields['remark'] = currObject.fields['remark'][:-1]
                    
                if currObject.creator is None:
                    currObject.creator = user.fields['u_id']
                    currObject.created = currObject.fields['begin']
                    
                if 'password' in currObject.fields:
                    currObject.fields['registration'] = currObject.created
                    currObject.fields['password'] = useful.encrypt(currObject.fields['password'],currObject.created)
                    
                if 'code' in data:
                    c.AllBarcodes.add_barcode(currObject, data['code'], user)
                    
                if 'component' in data:
                    currObject.add_component(data['component'])
                    
                if 'phase' in data:
                    currObject.add_phase(data['phase'])
                    
                if'measure' in data:
                    currObject.add_measure(data['measure'])
                    
                if 'position' in data :
                    currObject.set_position(data['position'])
                    currObject.set_object(data['object'])
                
                if data['placeImg'] != {}: 
                    if data.placeImg.filename != '': 
                        filepath = data.placeImg.filename.replace('\\','/') 
                        ext = ((filepath.split('/')[-1]).split('.')[-1])
                        fout = open(currObject.getImageDirectory()+'jpg','w')
                        fout.write(data.placeImg.file.read())
                        fout.close()
                currObject.save(c,user)
                if currObject.__class__.__name__ == u"Sensor" and id == 'new':
                    currObject.createRRD()
                return self.getListing(mail)
            else :
                if id == 'new' :
                    currObject.delete(c)
                return self.getRender(id, mail, cond)
        raise web.seeother('/')

class WebAll():
    def __init__(self):
        self.name = u"WebAll"
        
    def GET(self, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender( id, mail)
        raise web.seeother('/')
	
    def getRender(self, id, mail):
        return render.listing(mail, id)
	
class WebEdit():
        
    def GET(self,type,id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id,mail, '')
        raise web.seeother('/')
        
    def POST(self, type, id):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(id, type)
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
	    print data
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                for key in c.getFieldsname(type):
                    if key in data:
                        currObject.fields[key] = data[key]
                        
                for key in c.AllLanguages.elements:
                    if key in data:
                        currObject.setName(key, data[key],user, c.getKeyColumn(currObject))
                        
                if 'deny'in data:
                    currObject.set_deny('1')
                else:
                    currObject.set_deny('0')
                
                if 'remark' in currObject.fields:
                    currObject.fields['remark'] = currObject.fields['remark'][:-1]
                    
                if currObject.creator is None:
                    currObject.creator = user.fields['u_id']
                    currObject.created = currObject.fields['begin']
                    
                if 'password' in currObject.fields:
                    currObject.fields['registration'] = currObject.created
                    currObject.fields['password'] = useful.encrypt(currObject.fields['password'],currObject.created)
                    
                if 'code' in data:
		    if len(data['code']) >0 :
			c.AllBarcodes.add_barcode(currObject, data['code'], user)
                    
                if 'component' in data:
                    currObject.add_component(data['component'])
                    
                if 'phase' in data:
                    currObject.add_phase(data['phase'])
                    
                if'measure' in data:
                    currObject.add_measure(data['measure'])
                    
                if 'position' in data :
                    currObject.set_position(data['position'])
                    currObject.set_object(data['object'])
                
                if data['placeImg'] != {}: 
                    if data.placeImg.filename != '': 
                        filepath = data.placeImg.filename.replace('\\','/') 
                        ext = ((filepath.split('/')[-1]).split('.')[-1])
                        fout = open(currObject.getImageDirectory()+'jpg','w')
                        fout.write(data.placeImg.file.read())
                        fout.close()
                currObject.save(c,user)
                if currObject.__class__.__name__ == u"Sensor" and id == 'new':
                    currObject.createRRD()
                return self.getListing(mail, type)
            else :
		print cond
                if id == 'new' :
                    currObject.delete(c)
                return self.getRender(type,id, mail, cond)
        raise web.seeother('/')
	
    def getListing(self,mail, type):
        return render.listing(mail, type)
    
    def getRender(self,type, id, mail, errormess):
	if id in c.findAllFromType(type).elements.keys() or id == 'new' :
	    if type == 'p' :
		return render.place(id,mail, errormess)
	    elif type == 'e' :
		return render.equipment(id,mail, errormess) 
	    elif type == 'b' :
		return render.batch(id,mail, errormess) 
	    elif type == 'c' :
		return render.container(id,mail, errormess) 
	    elif type == 'cpehm' :
		return render.sensor(id,mail, errormess) 
	    elif type == 'm' :
		return render.measure(id,mail, errormess) 
	    elif type == 'a' :
		return render.alarm(id,mail, errormess) 
	    elif type == 'g' :
		return render.group(id,mail, errormess) 
	    elif type == 'u' :
		return render.user(id,mail, errormess) 
	return render.notfound()

class WebGraphic():
    def __init__(self):
        self.name=u"WebGraph"
    
    def GET(self,type,id):
        mail = isConnected()
        if mail is not None:
	    objects = c.findAllFromType(type)
	    if id in objects.elements.keys() :
		return render.listinggraphics(mail,type,id)
	    return render.notfound()
        raise web.seeother('/')	


class WebObjectDoubleID():
    def __init__(self):
        self.name = u"WebIndex"
        
    def GET(self, id1, id2):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id1, id2, mail)
        raise web.seeother('/')
        
class WebObjectID():
    def __init__(self):
        self.name = u"WebIndex"
        
    def GET(self, id2):
        mail = isConnected()
        if mail is not None:
            return self.getRender( id2, mail)
        return render.index(False,'')
        
class WebIndex(WebObject):
    def __init(self):
        self.name = u"WebIndex"
        
    def getRender(self, mail):
        return render.index(True,mail)


class WebBarcode():
    def __init__(self):
        self.name=u"WebBarcode"
	
    def GET(self,id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id,mail)
        raise web.seeother('/')
        
    def getRender(self, id, mail):
	return render.barcode(mail,id)
	        
        
    def getListing(self,mail):
        return render.listing(mail,'places')


        
class WebPermission(WebObjectUpdate):
    def __init__(self):
        self.name=u"WebPermission"
        
    def getRender(self,id,mail, error):
        typeobject = id.split('_')[0]
        idobject = id.split('_')[1]
	currObject = c.getObject(idobject, typeobject)
	if currObject is not None:
	    return render.permissions(mail,idobject,typeobject)
	return render.notfound()
        
    def POST(self, id):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            typeobject = id.split('_')[0]
            idobject = id.split('_')[1]
            currObject = c.getObject(idobject, typeobject)
            if currObject is None:
                return render.notfound()
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            print data
            for k,group in currObject.groups.items():
                print  unicode(k) + '\n'
                if k not in data:
                    currObject.deleteGroup(k,c,user)
            for k,group in c.AllGroups.elements.items():
                if k in data :
                    currObject.add_group(k, c, user)
            return self.get_listing(id, mail)
        return render.index(False,'')
        
    def get_listing(self, id, mail):
        typeobject = id.split('_')[0]
        return render.listing(mail,typeobject)
        
class WebTransfers(WebObject):
    def __init__(self):
        self.name=u"Transfers"
    
    def getRender(self, mail):
        return render.listingtransfers(mail)    

class WebTransfer(WebObjectUpdate):
    def __init__(self):
        self.name=u"WebTransfer"
        
    def getRender(self, id, mail, mess):
        myID = id.split('_')[1]
        myType = id.split('_')[0]
	currObject = c.getObject(myID, myType)
	if currObject is None :
	    return render.notfound()
        return render.itemtransfers(myType,myID,mail)
    
    def getListing(self,mail):
        return render.listingtransfers(mail)
        
class WebCreateTransfer(WebObjectDoubleID):
    def __init__(self):
        self.name=u"WebTransfer"
        
    def POST(self, id1, id2):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            getID = 'new'
            if id1 == 'update':
                getID = id2.split('_')[-1]
            currObject = c.getObject(getID,self.name)
	    if currObject is None :
		return render.notfound()
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True :
                if currObject is None:
                    raise web.seeother('/')
                currObject.fields['time'] = data['time']
                currObject.set_position(data['position'])
                currObject.set_object(data['object'])
                currObject.save(c,user)
                return self.getListing(mail,data['object'].split('_')[0])
            else:
                if id2 == 'new' :
                    currObject.delete(c)
                return self.getRender(id1,id2, mail, cond)
        raise web.seeother('/')
    
    def getRender(self,id1, id2, mail, mess = None):
        if len(id1.split('_')) >1 or id1 == 'new' or id1 =='update':
            return render.transfer(id1,id2,mail, mess)
        return self.getListing(mail)
    
    def getListing(self,mail,type='p'):
        return render.listing(mail,type)
        
class getRRD(): 
    def GET(self, filename):
        try: 
            f = open(rrdDir + filename)
            return f.read()  
        except IOError: 
            web.notfound()
            
class getRRD2(): 
    def GET(self,id1,id2,filename):
        try: 
            f = open(rrdDir + filename)
            return f.read()  
        except IOError: 
            web.notfound()
            
class WebMonitoring(WebObject):
    def __init__(self):
        self.name=u"WebMonitoring"
    
    def getRender(self, mail):
        return render.monitoring(mail)
        
class WebManualDataList(WebObjectUpdate):
    def __init__(self):
        self.name=u"WebManualData"
        
    def getRender(self, id, mail, mess):
	myID = id.split('_')[1]
	myType = id.split('_')[0]
	if myType in 'pceb':
	    currObject = c.getObject(myID,myType)
	    if currObject is None :
		return render.notfound()
	    return render.itemdata(myType,myID,mail)
	elif myType == 'm':
		return render.listingmeasures(mail,myID)
	return render.notfound()
    
    def getListing(self,mail):
        raise web.seeother('/')

class WebManualData(WebObjectDoubleID):
    def __init__(self):
        self.name=u"WebManualData"
        
    def POST(self, id1, id2):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            getID = id2
            currObject = c.getObject(getID,self.name)
	    if currObject is None :
		return render.notfound()
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True :
                if currObject is None:
                    return render.notfound()
                currObject.fields['time'] = data['time']
                currObject.add_component(data['component'])
                currObject.add_measure(data['measure'])
                currObject.fields['value'] = data['value']
                currObject.fields['remark'] = data['remark']
                currObject.save(c,user)
		if 'a_id' in data :
		    if len(data['a_id']) >0 :
			c.AllAlarms.elements[data['a_id']].launch_alarm(currObject,c)
                c.findAllFromType(currObject.fields['object_type']).elements[currObject.fields['object_id']].add_data(currObject)
                return self.getListing(mail, id1)
            else:
                if id2 == 'new' :
                    currObject.delete(c)
                return self.getRender(id1,id2, mail, cond)
        raise web.seeother('/')
    
    def getRender(self,id1, id2, mail, mess = None):
	try :
	    if len(id1.split('_')) >1:
		return render.manualdata(id1,id2,mail, mess)
	except:
	    return render.notfound()
        return render.notfound()
    
    def getListing(self,mail, id):
	try :
	    myType = id.split('_')[0]
	    myID = id.split('_')[1]
	    return render.itemdata(myType,myID,mail)
	except :
	    return render.notfound()

class WebPouringList(WebObjectUpdate):
    def __init__(self):
        self.name=u"WebPouring"
        
    def getRender(self, id, mail, mess):
	myID = id.split('_')[1]
	myType = id.split('_')[0]
	if myType in 'pceb':
	    currObject = c.getObject(myID,myType)
	    if currObject is None :
		return render.notfound()
	    return render.itemdata(myType,myID,mail)
	elif myType == 'm':
		return render.listingmeasures(mail,myID)
	return render.notfound()
    
    def getListing(self,mail):
        raise web.seeother('/')

class WebPouring(WebObjectDoubleID):
    def __init__(self):
        self.name=u"WebPouring"
        
    def POST(self, id1, id2):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            getID = id2
            currObject = c.getObject(getID,self.name)
	    if currObject is None :
		return render.notfound()
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True :
                if currObject is None:
                    return render.notfound()
                currObject.fields['time'] = data['time']
                currObject.add_batch(data['inputbatch'])
                currObject.add_measure(data['measure'])
                currObject.fields['value'] = data['value']
                currObject.fields['remark'] = data['remark']
                currObject.save(c,user)
		if 'a_id' in data :
		    if len(data['a_id']) >0 :
			c.AllAlarms.elements[data['a_id']].launch_alarm(currObject,c)
                c.findAllFromType(currObject.fields['object_type']).elements[currObject.fields['object_id']].add_data(currObject)
                return self.getListing(mail, id1)
            else:
                if id2 == 'new' :
                    currObject.delete(c)
                return self.getRender(id1,id2, mail, cond)
        raise web.seeother('/')
    
    def getRender(self,id1, id2, mail, mess = None):
	try :
	    if len(id1.split('_')) >1:
		return render.pouring(id1,id2,mail, mess)
	except:
	    return render.notfound()
        return render.notfound()
    
    def getListing(self,mail, id):
	try :
	    myType = id.split('_')[0]
	    myID = id.split('_')[1]
	    return render.itemdata(myType,myID,mail)
	except :
	    return render.notfound()

        
class WebListing():
    def __init__(self):
        self.name=u"WebListing"
        
    def GET(self, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id,mail, '')
        return render.index(False,'')
        
    def getRender(self,id,mail, error):
	try:
	    typeobject = id.split('_')[0]
	    idobject = id.split('_')[1]
	    if typeobject in 'pceb':
		return render.listingcomponent(mail,idobject,typeobject)
	    elif typeobject == 'g':
		return render.listinggroup(mail,idobject)
	    else:
		return render.notfound()
	except :
	    return render.notfound()
       
        

def connexion(username,password):
    user = c.AllUsers.getUser(username)
    if user is not None:
        cryptedPassword = useful.encrypt(password,user.fields['registration'])
        if user.checkPassword(cryptedPassword) is True:
            return user
    return None
    
def isConnected():
    infoCookie = web.cookies().get('webpy')
    if infoCookie is not None : 
        infoCookie = infoCookie.split(',')
        if c.connectedUsers.isConnected(infoCookie[0],infoCookie[1]) is True:
            return infoCookie[0]
    return None

def notfound():
    return web.notfound(render.notfound())
    
def update_cookie(infoCookie):
    web.setcookie('webpy', infoCookie, expires=9000)

c = None
    
def main():

    global c, render
    try:
        web.config.debug = False
        render=web.template.render('templates/', base='layout')
        urls = (
            '/', 'WebIndex',
            '/index','WebIndex',
	    '/transfers/(.+)/(.+)', 'WebCreateTransfer',
	    '/transfers/(.+)', 'WebTransfer',   
            '/edit/(.+)_(.+)', 'WebEdit',
            '/group/(.+)', 'WebPermission',
            '/measures/(.+)/(.+)', 'WebManualData',
            '/measures/(.+)', 'WebManualDataList',
            '/pourings/(.+)/(.+)', 'WebPouring',
            '/pourings/(.+)', 'WebPouringList',
            '/graphic/(.+)_(.+)/(.+)', 'getRRD2',
            '/monitoring/', 'WebMonitoring',
            '/monitoring/(.+)', 'getRRD',
            '/all/t', 'WebTransfers',
            '/all/(.+)', 'WebAll',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/listing/(.+)', 'WebListing',
	    '/barcode/(.+)', 'WebBarcode',
	    '/permissions/(.+)', 'WebPermission',
	    '/modal/(.+)_(.+)', 'WebModal',  
	    '/menu/(.+)_(.+)', 'WebMenu',  
	    '/allmenu/(.+)_(.+)', 'WebAllmenu',  
        )

        #Configuration Singleton ELSA
        c=elsa.Configuration()
        c.load()
        web.template.Template.globals['c'] = c
        app = web.application(urls, globals())
        app.notfound = notfound
        app.run()       
    except :
        traceback.print_exc(file=sys.stdout)
    finally:
        print 'fin des threads'
        if c:
            c.isThreading = False
            c.UpdateThread.join()
            c.RadioThread.join()
# Replaced by an abstract socket:
#            unlink(c.pidfile)
        print 'Exit system'

if __name__ == "__main__":
    main()
