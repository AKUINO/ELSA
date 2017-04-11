import web
import ConfigurationELSA as elsa
import time
import myuseful as useful
import traceback
import os
import sys

global c, render

#
#Ligne 62 - connexion 9000 a la place de 900
#



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
	method = data.get("method","malformed")
	connectedUser = connexion(data._username_,data._password_)
	if connectedUser is not None:
	    infoCookie = data._username_ + ',' + connectedUser.fields['password']
	    web.setcookie('webpy', infoCookie, expires=9000)
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
	    imgDirectory = 'static/img'
	    infoCookie = mail + ',' + user.fields['password']
	    web.setcookie('webpy', infoCookie, expires=900)
	    if currObject is None:
		raise web.seeother('/')
	    
	    data = web.input(placeImg={})
	    method = data.get("method","malformed")
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
		    currObject.addComponent(data['component'])
		    
		if 'phase' in data:
		    currObject.addPhase(data['phase'])
		    
		if'measure' in data:
		    currObject.addMeasure(data['measure'])
		    
		if 'position' in data :
		    currObject.set_position(data['position'])
		    currObject.set_object(data['object'])
		
		if data['placeImg'] != {}: 
		    if data.placeImg.filename != '': 
			printinfo(data['placeImg'])
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
	
class WebIndex(WebObject):
    def __init(self):
	self.name = u"WebIndex"
	
    def getRender(self, mail):
	return render.index(True,mail)
	
class WebPlaces(WebObject):
    def __init__(self):
	self.name=u"WebPlaces"
    
    def getRender(self, mail):
	return render.listing(mail,'places')
	
class WebEquipments(WebObject):
    def __init__(self):
	self.name=u"WebEquipments"
	
    def getRender(self, mail):
	return render.listing(mail,'equipments')

class WebPlace(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebPlace"
	
    def getRender(self, id, mail, errormess):
	return render.place(id,mail, errormess)
	
    def getListing(self,mail):
	return render.listing(mail,'places')

	
class WebEquipment(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebEquipment"
	
    def getRender(self, id, mail, errormess):
	return render.equipment(id,mail, errormess)
	
    def getListing(self,mail):
	return render.listing(mail,'equipments')

class WebUsers(WebObject):
    def __init__(self):
	self.name=u"WebUsers"
    
    def getRender(self, mail):
	return render.listing(mail,'users')
	
class WebUser(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebUser"
	
    def getRender(self, id, mail, mess):
	return render.user(id,mail, mess)
	
    def getListing(self,mail):
	return render.listing(mail,'users')

class WebGroups(WebObject):
    def __init__(self):
	self.name=u"WebGroups"
    
    def getRender(self, mail):
	return render.listing(mail,'groups')
	
class WebGroup(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebGroup"
	
    def getRender(self, id, mail, mess):
	return render.group(id,mail, mess)
	
    def getListing(self,mail):
	return render.listing(mail,'groups')
	
class WebPermission(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebPermission"
	
    def getRender(self,id,mail, error):
	typeobject = id.split('_')[0]
	idobject = id.split('_')[1]
	return render.permissions(mail,idobject,typeobject)
	
    def POST(self, id):
	mail = isConnected()
	user  = c.connectedUsers.users[mail].cuser
	if mail is not None:
	    typeobject = id.split('_')[0]
	    idobject = id.split('_')[1]
	    currObject = c.getObject(idobject, typeobject)
	    if currObject is None:
		raise web.seeother('/')
	    data = web.input(placeImg={})
	    method = data.get("method","malformed")
	    print data
	    for k,group in currObject.groups.items():
		print  str(k) + '\n'
		if k not in data:
		    currObject.deleteGroup(k,c,user)
	    for k,group in c.AllGroups.elements.items():
		if k in data :
		    currObject.add_group(k, c, user)
	    return self.get_listing(id, mail)
	return render.index(False,'')
	
    def get_listing(self, id, mail):
	typeobject = id.split('_')[0]
	tmp = ''
	if typeobject == 'p':
	    tmp = 'places'
	elif typeobject == 'e':
	    tmp = 'equipments'
	elif typeobject == 'c':
	    tmp = 'containers'
	elif typeobject == 'cpehm':
	    tmp = 'sensors'
	elif typeobject == 'a':
	    tmp = 'alarms'
	elif typeobject == 'u':
	    tmp = 'users'
	elif typeobject == 'g':
	    tmp = 'groups'
	elif typeobject == 'm':
	    tmp = 'measures'
	return render.listing(mail,tmp)

class WebContainers(WebObject):
    def __init__(self):
	self.name=u"WebContainers"
    
    def getRender(self, mail):
	return render.listing(mail,'containers')
	

class WebContainer(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebContainer"
	
    def getRender(self, id, mail, mess):
	return render.container(id,mail, mess)
    
    def getListing(self,mail):
	return render.listing(mail,'containers')
	
class WebMeasures(WebObject):
    def __init__(self):
	self.name=u"WebMeasures"
    
    def getRender(self, mail):
	return render.listing(mail,'measures')
	

class WebMeasure(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebMeasure"
	
    def getRender(self, id, mail, mess):
	return render.measure(id,mail, mess)
    
    def getListing(self,mail):
	return render.listing(mail,'measures')
	
class WebSensors(WebObject):
    def __init__(self):
	self.name=u"Sensors"
    
    def getRender(self, mail):
	return render.listing(mail,'sensors')
	

class WebSensor(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebSensor"
	
    def getRender(self, id, mail, mess):
	return render.sensor(id,mail, mess)
    
    def getListing(self,mail):
	return render.listing(mail,'sensors')
	
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
	return render.itemtransfers(myType,myID,mail)
    
    def getListing(self,mail):
	return render.listingtransfers(mail)
	
class WebCreateTransfer():
    def __init__(self):
	self.name=u"WebTransfer"
    
    def GET(self, id1,id2):
	mail = isConnected()
	if mail is not None:
	    return self.getRender(id2,mail, '')
	return render.index(False,'')
	
    def POST(self, id1, id2):
	print 'Bon Post\n'
	mail = isConnected()
	user  = c.connectedUsers.users[mail].cuser
	if mail is not None:
	    currObject = c.getObject('new',self.name)
	    imgDirectory = 'static/img'
	    infoCookie = mail + ',' + user.fields['password']
	    web.setcookie('webpy', infoCookie, expires=900)
	    data = web.input(placeImg={})
	    method = data.get("method","malformed")
	    cond = currObject.validate_form(data, c, user.fields['language'])
	    if cond is True :
		if currObject is None:
		    raise web.seeother('/')
		currObject.set_position(data['position'])
		currObject.set_object(data['object'])
		currObject.save(c,user)
		return self.getListing(mail)
	    else:
		if id == 'new' :
		    currObject.delete(c)
		return self.getRender(id2, mail, cond)
	raise web.seeother('/')
    
    def getRender(self, id, mail, mess):
	return render.transfer(id,mail, mess)
    
    def getListing(self,mail):
	return render.listingtransfers(mail)
	
class getRRD(): 
    def GET(self, filename):
        try: 
            f = open('rrd/' + filename)
            return f.read()  
        except IOError: 
            web.notfound()
	    
class getRRD2(): 
    def GET(self, idobj,filename):
        try: 
            f = open('rrd/' + filename)
            return f.read()  
        except IOError: 
            web.notfound()
	    
class WebMonitoring(WebObject):
    def __init__(self):
	self.name=u"WebMonitoring"
    
    def getRender(self, mail):
	return render.monitoring(mail)
	
class WebSensorGraph():
    def __init__(self):
	self.name=u"WebSensorGraph"
    
    def GET(self,id):
	mail = isConnected()
	if mail is not None:
	    return render.graphic(mail,id)
	return render.index(False,'')

	    
class WebAlarms(WebObject):
    def __init__(self):
	self.name=u"WebAlarms"
	
    def getRender(self, mail):
	return render.listing(mail,'alarms')

class WebAlarm(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebAlarm"
	
    def getRender(self, id, mail, mess):
	return render.alarm(id,mail, mess)
	
    def getListing(self,mail):
	return render.listing(mail,'alarms')
	
	
class WebBatches(WebObject):
    def __init__(self):
	self.name=u"WebBatches"
	
    def getRender(self, mail):
	return render.listing(mail,'batches')

class WebBatch(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebBatch"
	
    def getRender(self, id, mail, mess):
	return render.batch(id,mail, mess)
	
    def getListing(self,mail):
	return render.listing(mail,'batches')
	
class WebListing():
    def __init__(self):
	self.name=u"WebListing"
	
    def GET(self, id):
	mail = isConnected()
	if mail is not None:
	    return self.getRender(id,mail, '')
	return render.index(False,'')
	
    def getRender(self,id,mail, error):
	typeobject = id.split('_')[0]
	idobject = id.split('_')[1]
	return render.listingcomponent(mail,idobject,typeobject)
	

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

c = None
    
def main():

    global c, render
    try:
        web.config.debug = False
        render=web.template.render('templates/', base='layout')

        urls = (
            '/', 'WebIndex',
            '/index','WebIndex',
            '/places/(.+)', 'WebPlace',
            '/places/', 'WebPlaces',
            '/equipments/', 'WebEquipments',
            '/equipments/(.+)','WebEquipment',
            '/users/', 'WebUsers',
            '/users/(.+)', 'WebUser',
            '/groups/', 'WebGroups',
            '/groups/(.+)', 'WebGroup',
            '/permissions/(.+)', 'WebPermission',
            '/containers/', 'WebContainers',
            '/containers/(.+)','WebContainer',
            '/measures/', 'WebMeasures',
            '/measures/(.+)', 'WebMeasure',
            '/sensors/', 'WebSensors',
            '/sensors/(.+)', 'WebSensor',
            '/graphic/(.+)/(.+)', 'getRRD2',
            '/monitoring/', 'WebMonitoring',
            '/monitoring/(.+)', 'getRRD',
            '/graphic/(.+)', 'WebSensorGraph',
            '/alarms/', 'WebAlarms',
            '/alarms/(.+)', 'WebAlarm',
            '/batches/', 'WebBatches',
            '/batches/(.+)', 'WebBatch',
            '/transfers/(.+)/(.+)', 'WebCreateTransfer',
            '/transfers/', 'WebTransfers',
            '/transfers/(.+)', 'WebTransfer',    
            '/listing/(.+)', 'WebListing',    
        )

	#Configuration Singleton ELSA
	c=elsa.Configuration()
	c.load()
	c.InfoSystem.updateInfoSystem(time.time())
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
            os.unlink(c.pidfile)
	print 'Exit system'

if __name__ == "__main__":
    main()
