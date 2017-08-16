#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
import sys

global c, render
rrdDir = '../ELSArrd/rrd/'


class WebColor():
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.colorpicker(mail,type,id)
        return ''
	
class WebPermission():
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.permission(mail,type,id)
        return ''

class WebModal():
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.modal(mail,type,id)
        return ''
	
class WebEntry():        
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.entry(mail,type,id)
        return ''
	
class WebFullEntry():        
    def GET(self, type,id):
        mail = isConnected()
        if mail is not None:
            return render.fullentry(mail,type,id)
        return ''
	
class WebList():
    def __init__(self):
        self.name = u"WebList"
	
    def GET(self, type):
        mail = isConnected()
        if mail is not None:
	    if type in 'abcpesmugugrgf':
		return self.getRender(type, mail)
	    else:
		return render.notfound()
        raise web.seeother('/')
	
    def POST(self,type):
	mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
	    if type == 'b':
		data = web.input(placeImg={})
		count = 1
		borne  = int(data['quantity'])
		elem = c.AllBatches.elements[data['batch'].split('_')[1]]
		while count <= borne :
		    elem.clone(user,'_'+str(count))
		    count+=1
	    return self.getRender(type,mail)
	raise web.seeother('/') 
	
    def getRender(self, type, mail):
	if type == 't' :
	    return render.listingtransfers(mail)
        return render.listing(mail, type)
	
class WebEdit():        
    def GET(self,type,id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id,mail, '', '')
        raise web.seeother('/')
        
    def POST(self, type, id, context = None):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(id, type)
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            data = web.input(placeImg={})
            method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                currObject.set_value_from_data(data,c,user)
		if 'a_id' in data :
		    if len(data['a_id']) >0 :
			c.AllAlarms.elements[data['a_id']].launch_alarm(currObject,c)
		if type not in 'tdv':
		    return self.getListing(mail, type)
		else :
		    raise web.seeother('/find/'+type+'/'+id)
            else :
                if id == 'new' :
                    currObject.delete(c)
                return self.getRender(type,id, mail, cond,data)
        raise web.seeother('/')
	
    def getListing(self,mail, type):
        return render.listing(mail, type)
    
    def getRender(self,type, id, mail, errormess, data):
	if not type in 'tdv':
	    if id in c.findAllFromType(type).elements.keys() or  id == 'new':
		if type == 'p' :
		    return render.place(id,mail, errormess, data)
		elif type == 'e' :
		    return render.equipment(id,mail, errormess, data) 
		elif type == 'b' :
		    return render.batch(id,mail, errormess, data) 
		elif type == 'c' :
		    return render.container(id,mail, errormess, data) 
		elif type == 's' :
		    return render.sensor(id,mail, errormess, data) 
		elif type == 'm' :
		    return render.measure(id,mail, errormess, data) 
		elif type == 'a' :
		    return render.alarm(id,mail, errormess, data) 
		elif type == 'gu' :
		    return render.group(type,id,mail, errormess, data) 
		elif type == 'gr' :
		    return render.group(type,id,mail, errormess, data) 
		elif type == 'gf' :
		    return render.group(type,id,mail, errormess, data) 
		elif type == 'u' :
		    return render.user(id,mail, errormess, data) 
	elif type =='t':
	    return render.transfer(id,mail, errormess) 
	elif type =='d':
	    return render.manualdata(id,mail, errormess) 
	elif type == 'v':
	    return render.pouring(id,mail, errormess) 
        return render.notfound()
	
class WebCreate(WebEdit):
    def GET(self,type):
        mail = isConnected()
        if mail is not None:
	    if len(type.split('/')) == 1 :
		return self.getRender(type, 'new',mail,'', '')
	    else:
		return self.getRender(type.split('/')[0], type.split('/')[-1],mail,'', '')
        raise web.seeother('/')
	
    def POST(self, type):
	return WebEdit.POST(self,type.split('/')[0],'new')    

class WebFind():
    def GET(self,type,id1,id2):
	mail = isConnected()
        if mail is not None:
	    return self.getRender(type, id1,id2,mail)
        raise web.seeother('/')
	
    def POST(self, type, id1, id2):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(type, 'new')
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            data = web.input(placeImg={})
            #method = data.get("method","malformed")
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                currObject.set_value_from_data(data,c,user)
                return self.getListing(mail, type)
            else :
                if id == 'new' :
                    currObject.delete(c)
                return self.getRender(type,id, mail, cond)
        raise web.seeother('/')
	
    def getRender(self, type, id1, id2, mail):
	if type == 'd' and id1 == 'm':
	    return render.listingmeasures(id2,mail)
	elif type == 'd':
	    return render.itemdata(id1,id2,mail)
	elif type == 't' and id1 in 'ceb':
	    return render.itemtransfers(id1,id2,mail)
	elif type == 'v':
	    return render.listingpourings(id2,mail)
	elif type == 'related'and 'g' in id1:
	    return render.listinggroup(id1,id2,mail)
	elif type == 'related':
	    return render.listingcomponent(id1,id2,mail)
	else:
	    return render.notfound()

class WebGraphic():
    def __init__(self):
        self.name=u"WebGraph"
    
    def GET(self,type,id):
        mail = isConnected()
        if mail is not None:
            objects = c.findAllFromType(type)
            if id in objects.elements.keys() and type in 'scpem':
                return render.listinggraphics(mail,type,id)
            return render.notfound()
        raise web.seeother('/') 
        
class WebIndex():
    def __init(self):
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

        
class getRRD(): 
    def GET(self, filename):
        try: 
            f = open(rrdDir + filename)
            return f.read()  
        except IOError: 
            web.notfound()
            
class WebMonitoring():
    def __init__(self):
        self.name=u"WebMonitoring"
	
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
    
    def getRender(self, mail):
        return render.monitoring(mail)

	
class WebListing():
    def __init__(self):
        self.name=u"WebListing"
        
    def GET(self, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id,mail, '')
        return render.index(False,'')
	
    def getRender(self,id,mail, error):
        #try:
        typeobject = id.split('_')[0]
        idobject = id.split('_')[1]
        if typeobject in 'pceb':
            return render.listingcomponent(mail,idobject,typeobject)
        elif typeobject == 'g':
            return render.listinggroup(mail,idobject)
        elif typeobject == 'm':
	    print 'flibidi'
            return render.listingmeasures(mail,idobject)
        else:
            return render.notfound()
        """except :
            return render.notfound()"""
       
class WebExport():        
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id,mail)
        return render.index(False,'')
        
    def POST(self,type, id):
        mail = isConnected()
        user  = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            cond = {}
            cond['alarm'] = True if 'alarm' in data else False
            cond['manualdata'] = True if 'manualdata' in data else False
            cond['transfer'] = True if 'transfer' in data else False
            cond['pouring'] = True if 'pouring' in data else False
            cond['specialvalue'] = True if 'specialvalue' in data else False
            cond['valuesensor'] = True if 'valuesensor' in data else False
            cond['acronym'] = True if 'acronym' in data else False
            method = data.get("method","malformed")
            elem = c.findAllFromType(data['element'].split('_')[0]).elements[data['element'].split('_')[1]]
            tmp = elsa.ExportData(c,elem,cond,user)
            tmp.create_export()
            if "download" in data :
                tmp.write_csv()
                raise web.seeother('/export/'+str(type)+'_'+str(id)+'/exportdata.csv')
            else:
                user.exportdata = tmp
                raise web.seeother('/datatable/'+str(type)+'_'+str(id))
        return render.index(False,'')
        
    def getRender(self,type, id,mail):
        try:
            if type in 'cpeb':
                return render.exportdata(mail,type, id)
            else:
                return render.notfound()
        except :
            return render.notfound()
            
class WebDataTable():        
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id,mail)
        return render.index(False,'')
              
    def getRender(self,type, id,mail):
        try:
            if type in 'cpeb':
                return render.datatable(mail,type, id)
            else:
                return render.notfound()
        except :
            return render.notfound()
            
class WebDownloadData():     
    def GET(self,id1,id2, filename):
        try:
            web.header('Content-Disposition', 'attachment; filename="'+str(filename)+'"')
            web.header('Content-type','text/tab-separated-values')
            web.header('Content-transfer-encoding','binary')
            f = open(elsa.csvDir + filename)
            return f.read()  
        except IOError: 
            web.notfound()

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
wsgiapp = None
    
def main():

    global c, wsgiapp, render
    try:
        web.config.debug = True
        render=web.template.render('templates/', base='layout')
        urls = (
            '/', 'WebIndex',
            '/index','WebIndex',  
            '/edit/(.+)_(.+)', 'WebEdit',
            '/create/(.+)', 'WebCreate',
            '/monitoring/', 'WebMonitoring',
            '/rrd/(.+)', 'getRRD',
            '/list/(.+)', 'WebList',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/barcode/(.+)', 'WebBarcode',
            '/modal/(.+)_(.+)', 'WebModal',  
            '/color/(.+)_(.+)', 'WebColor',  
            '/entry/(.+)_(.+)', 'WebEntry',  
            '/fullentry/(.+)_(.+)', 'WebFullEntry',  
            '/export/(.+)_(.+)/(.+)', 'WebDownloadData',
            '/export/(.+)_(.+)', 'WebExport',  
            '/datatable/(.+)_(.+)', 'WebDataTable',  
            '/find/(.+)/(.+)_(.+)', 'WebFind',  
            '/permission/(.+)_(.+)', 'WebPermission',  
        )

        #Configuration Singleton ELSA
        c=elsa.Configuration()
        c.load()
        web.template.Template.globals['c'] = c
        web.template.Template.globals['useful'] = useful
        app = web.application(urls, globals())
        app.notfound = notfound
        app.run()
        #wsgiapp = app.wsgifunc()
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
#main()
