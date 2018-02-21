#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
import sys

global c, render


class WebColor():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.colorpicker(mail, type, id)
        return ''


class WebDisconnect():
    def GET(self):
        mail = isConnected()
        if mail is not None:
            c.connectedUsers.disconnect(mail)
        raise web.seeother('/')


class WebPermission():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            if len(id.split('/')) > 1:
                context = id.split('/')[-1]
                id = id.split('/')[0]
            else:
                context = ''
            return render.permission(mail, type, id, context)
        return ''


class WebModal():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.modal(mail, type, id)
        return ''


class WebFullEntry():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.fullentry(mail, type, id)
        return ''


class WebList():
    def __init__(self):
        self.name = u"WebList"

    def GET(self, type):
        id = ''
        data = web.input(nifile={})
        if 'status' in data:
            id = data['status']
        mail = isConnected()
        if mail is not None:
            if type in 'abcpehsmugugrgftmdmvm' and type != 't' and type != 'f':
                return self.getRender(type, mail, id)
            else:
                return render.notfound()
        raise web.seeother('/')

    def POST(self, type):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            data = web.input(placeImg={})
            if 'quantity' in data:
                try:
                    if type == 'b':
                        count = 1
                        borne = int(data['quantity'])
                        elem = c.AllBatches.elements[data['batch'].split('_')[
                            1]]
                        try:
                            name = int(
                                elem.fields['acronym'][elem.fields['acronym'].rfind('_')+1:])
                        except:
                            name = 0
                        while count <= borne:
                            elem.clone(user, (name + count))
                            count += 1
                    return self.getRender(type, mail)
                except:
                    raise render.notfound()
        raise web.seeother('/')

    def getRender(self, type, mail, id=''):
        return render.listing(mail, type, id)


class WebItem():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            try:
                return render.item(type, id, mail)
            except:
                return render.notfound()
        raise web.seeother('/')


class WebEdit():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail, '', '')
        raise web.seeother('/')

    def POST(self, type, id, context=None):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(id, type)
            infoCookie = mail + ',' + user.fields['password']
            data = web.input(placeImg={})
            method = data.get("method", "malformed")
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                currObject.set_value_from_data(data, c, user)
                if 'a_id' in data:
                    if len(data['a_id']) > 0:
                        c.AllAlarms.elements[data['a_id']
                                             ].launch_alarm(currObject, c)
                if type not in 'tdv':
                    raise web.seeother('/item/'+type+'_'+currObject.getID())
                else:
                    if currObject.get_type() == 'v':
                        elemtype = 'b'
                        elemid = currObject.fields['dest']
                    elif currObject.get_type() == 't':
                        elemtype = currObject.fields['object_type']
                        elemid = currObject.fields['object_id']
                    elif currObject.get_type() == 'd':
                        elemtype = currObject.fields['object_type']
                        elemid = currObject.fields['object_id']
                    raise web.seeother('/find/'+type+'/'+elemtype+'_'+elemid)
            else:
                if id == 'new':
                    currObject.delete(c)
                return self.getRender(type, id, mail, cond, data)
        raise web.seeother('/')

    def getListing(self, mail, type, id=''):
        return render.listing(mail, type, id)

    def getRender(self, type, id, mail, errormess, data, context=''):
        print 'context :' + context
        if type in 'hpebcsmagugrgfutmdmvm' and type != 'g' and type != 'f' and type != 'd' and type != 'v'and type != 't':
            if type == 'p':
                return render.place(id, mail, errormess, data, context)
            elif type == 'e':
                return render.equipment(id, mail, errormess, data, context)
            elif type == 'b':
                return render.batch(id, mail, errormess, data, context)
            elif type == 'c':
                return render.container(id, mail, errormess, data, context)
            elif type == 's':
                return render.sensor(id, mail, errormess, data)
            elif type == 'm':
                return render.measure(id, mail, errormess, data)
            elif type == 'a':
                return render.alarm(id, mail, errormess, data)
            elif type == 'gu':
                return render.group(type, id, mail, errormess, data)
            elif type == 'gr':
                return render.group(type, id, mail, errormess, data)
            elif type == 'gf':
                return render.group(type, id, mail, errormess, data)
            elif type == 'h':
                return render.group(type, id, mail, errormess, data, context)
            elif type == 'u':
                return render.user(id, mail, errormess, data, context)
            elif type == 'tm':
                return render.transfermodel(id, mail, errormess, data, context)
            elif type == 'dm':
                return render.manualdatamodel(id, mail, errormess, data, context)
            elif type == 'vm':
                return render.pouringmodel(id, mail, errormess, data, context)
        elif type == 't':
            return render.transfer(id, mail, errormess, context)
        elif type == 'd':
            return render.manualdata(id, mail, errormess, context)
        elif type == 'v':
            return render.pouring(id, mail, errormess, context)


class WebCreate(WebEdit):
    def GET(self, type):
        mail = isConnected()
        if mail is not None:
            if len(type.split('/')) == 1:
                return self.getRender(type, 'new', mail, '', '')
            else:
                return self.getRender(type.split('/')[0], 'new', mail, '', '', type.split('/')[-1])
        raise web.seeother('/')

    def POST(self, type):
        if len(type.split('_')) > 1:
            return WebEdit.POST(self, type.split('/')[0], 'new', type.split('/')[-1])
        else:
            return WebEdit.POST(self, type.split('/')[0], 'new')


class WebControl():
    def GET(self, idbatch, idcontrol):
        mail = isConnected()
        if mail is not None:
            return render.control(idbatch, idcontrol, mail, '')
        raise web.seeother('/')

    def POST(self, idbatch, idcontrol, context=None):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            method = data.get("method", "malformed")
            currObject = c.getObject(idcontrol, 'h')
            cond = currObject.validate_control(data, user.fields['language'])
            if cond is True:
                currObject.create_control(data, user)
                raise web.seeother('/find/h/b_' + str(idbatch))
            else:
                return render.control(idbatch, idcontrol, mail, cond)
        raise web.seeother('/')


class WebFind():
    def GET(self, type, id1, id2):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id1, id2, mail)
        raise web.seeother('/')

    def POST(self, type, id1, id2):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            if type == 'h':
                if 'checkpoint' in data:
                    raise web.seeother('/control/b_'+id2 +
                                       '/h_'+data['checkpoint'])
                raise web.seeother('/item/b_'+id2)
        raise web.seeother('/')

    def getRender(self, type, id1, id2, mail):
        try:
            if type == 'related' and id1 == 'm':
                return render.listingmeasures(id2, mail)
            elif type == 'd'and id1 in 'pceb':
                return render.itemdata(id1, id2, mail)
            elif type == 't' and id1 in 'ceb':
                return render.itemtransfers(id1, id2, mail)
            elif type == 'v' and id1 in 'ecb':
                return render.listingpourings(id2, mail)
            elif type == 'related'and ('g' in id1 or id1 == 'h'):
                return render.listinggroup(id1, id2, mail)
            elif type == 'related':
                return render.listingcomponent(id1, id2, mail)
            elif type == 'h':
                return render.listingcontrol(id1, id2, mail)
            else:
                return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()


class WebGraphic():
    def __init__(self):
        self.name = u"WebGraph"

    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            objects = c.findAllFromType(type)
            if id in objects.elements.keys() and type in 'scpem':
                return render.listinggraphics(mail, type, id)
            return render.notfound()
        raise web.seeother('/')


class WebIndex():
    def __init(self):
        self.name = u"WebIndex"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return self.getRender(mail)
        return render.index(False, '')

    def POST(self):
        data = web.input(nifile={})
        #method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_)
        return render.index(False, '')

    def getRender(self, mail):
        return render.index(True, mail)


class WebBarcode():
    def __init__(self):
        self.name = u"WebBarcode"

    def GET(self, id=""):
        mail = isConnected()
        if mail is not None:
            try:
                data = web.input(nifile={})
                if 'barcode' in data:
                    id = data['barcode']
                return self.getRender(id, mail)
            except:
                return self.getRender(id, mail, 'notfound')
        raise web.seeother('/')

    def getRender(self, id, mail, errormess=''):
        return render.barcode(mail, id, errormess)

    def getListing(self, mail):
        return render.listing(mail, 'places')


class getRRD():
    def GET(self, filename):
        try:
            f = open(elsa.DIR_RRD + filename)
            return f.read()
        except IOError:
            web.notfound()


class getCSV():
    def GET(self, filename):
        try:
            f = open(elsa.DIR_CSV + filename)
            return f.read()
        except IOError:
            web.notfound()


class WebMonitoring():
    def __init__(self):
        self.name = u"WebMonitoring"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return self.getRender(mail)
        return render.index(False, '')

    def POST(self):
        data = web.input(nifile={})
        #method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_)
        return render.index(False, '')

    def getRender(self, mail):
        return render.monitoring(mail)


class WebListing():
    def __init__(self):
        self.name = u"WebListing"

    def GET(self, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id, mail, '')
        return render.index(False, '')

    def getRender(self, id, mail, error):
        typeobject = id.split('_')[0]
        idobject = id.split('_')[1]
        if typeobject in 'pceb':
            return render.listingcomponent(mail, idobject, typeobject)
        elif typeobject == 'g':
            return render.listinggroup(mail, idobject)
        elif typeobject == 'm':
            return render.listingmeasures(mail, idobject)
        else:
            return render.notfound()


class WebExport():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail)
        return render.index(False, '')

    def POST(self, type, id):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
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
            method = data.get("method", "malformed")
            elem = c.findAllFromType(data['element'].split(
                '_')[0]).elements[data['element'].split('_')[1]]
            tmp = elsa.ExportData(c, elem, cond, user)
            tmp.create_export()
            if "download" in data:
                tmp.write_csv()
                raise web.seeother('/export/'+str(type) +
                                   '_'+str(id)+'/exportdata.csv')
            else:
                user.exportdata = tmp
                raise web.seeother('/datatable/'+str(type)+'_'+str(id))
        return render.index(False, '')

    def getRender(self, type, id, mail):
        try:
            if type in 'cpeb':
                return render.exportdata(mail, type, id)
            else:
                return render.notfound()
        except:
            return render.notfound()


class WebDataTable():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail)
        return render.index(False, '')

    def getRender(self, type, id, mail):
        # try:
        if type in 'cpeb':
            return render.datatable(mail, type, id)
        else:
            return render.notfound()
        """except :
            return render.notfound()"""


class WebDownloadData():
    def GET(self, id1, id2, filename):
        try:
            web.header('Content-Disposition',
                       'attachment; filename="'+str(filename)+'"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            f = open(elsa.DIR_CSV + filename)
            return f.read()
        except IOError:
            web.notfound()


def connexion(username, password):
    user = c.AllUsers.getUser(username)
    if user is not None:
        cryptedPassword = useful.encrypt(password, user.fields['registration'])
        if user.checkPassword(cryptedPassword) is True:
            return user
    return None


def isConnected():
    infoCookie = web.cookies().get('webpy')
    if infoCookie is not None:
        infoCookie = infoCookie.split(',')
        if c.connectedUsers.isConnected(infoCookie[0], infoCookie[1]) is True:
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
        web.config.debug = False
        # Configuration Singleton ELSA
        c = elsa.Configuration()
        c.load()
        web.template.Template.globals['c'] = c
        web.template.Template.globals['useful'] = useful
        layout = web.template.frender(elsa.TEMPLATES_DIR+'/layout.html')
        render = web.template.render(elsa.TEMPLATES_DIR, base=layout)
        urls = (
            '/', 'WebIndex',
            '/index', 'WebIndex',
            '/edit/(.+)_(.+)', 'WebEdit',
            '/item/(.+)_(.+)', 'WebItem',
            '/create/(.+)', 'WebCreate',
            '/monitoring/', 'WebMonitoring',
            '/rrd/(.+)', 'getRRD',
            '/csv/(.+)', 'getCSV',
            '/list/(.+)', 'WebList',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/barcode/(.+)', 'WebBarcode',
            '/barcode/', 'WebBarcode',
            '/modal/(.+)_(.+)', 'WebModal',
            '/color/(.+)_(.+)', 'WebColor',
            '/fullentry/(.+)_(.+)', 'WebFullEntry',
            '/export/(.+)_(.+)/(.+)', 'WebDownloadData',
            '/export/(.+)_(.+)', 'WebExport',
            '/datatable/(.+)_(.+)', 'WebDataTable',
            '/find/(.+)/(.+)_(.+)', 'WebFind',
            '/permission/(.+)_(.+)', 'WebPermission',
            '/control/b_(.+)/h_(.+)', 'WebControl',
            '/disconnect', 'WebDisconnect',
        )
        app = web.application(urls, globals())
        app.notfound = notfound
        app.run()
        #wsgiapp = app.wsgifunc()
    except:
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
