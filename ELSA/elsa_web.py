#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
import urllib
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
import math as mathlibrary
import sys
import shutil
import os
import backup
import argparse
import subprocess
import json
import cgi
import rrd
import time
global c, render

def manage_cmdline_arguments():
    parser = argparse.ArgumentParser(description='Enregistrement des Lots \
                                                  pour la Sécurité Alimentaire')
    # Est interprété directement par WebPY
    parser.add_argument('port', type=int, help='Port number of the internal \
                                                web server')
    parser.add_argument('--hw-config', help='Configuration file for this \
                                             particular computer')
    return parser.parse_args()

def web_link_from_abs_path(path):
    """
    Will strip DIR_BASE from path. Intended to be used in href
    """
    return path[len(elsa.DIR_BASE):]

def getLinkForLatestBackupArchive():
    """
    Returns the web path (as in web_link_from_abs_path) of the lastest backup
    archive in the temporary web folder
    """
    list = os.listdir(elsa.DIR_WEB_TEMP)
    lastFile = None
    for f in sorted(list):
        if f.find(backup.ARCHIVE_FILE_NAME_PREFIX) >= 0:
            lastFile = f
    if lastFile is not None:
        return web_link_from_abs_path(os.path.join(elsa.DIR_WEB_TEMP, lastFile))
    else:
        return None

def protectHTML(input):
    return cgi.escape(input,True).replace("'","&#39;");

def protectJS(input):
    if not input: # if input is None
        return u''
    return unicode(input).replace("'","\\'").replace("\\","\\\\")

def redirect_when_not_logged(redir=True):
    """
    Should be used at the begining of every GET, POST, etc.
    When the user is not logged, will redirect to login page and preserve
    current path. Returns None
    When the user is logged, returns the mail (does not redirect)
    When redir is Fals, will log into home page
    """
    mail = isConnected()
    if mail is None:
        if redir:
            path = web.ctx.env.get('PATH_INFO')
            query = web.ctx.env.get('QUERY_STRING')
            if query:
                path = path+u'?'+urllib.quote(query)
                print query
                print path
            raise web.seeother('/?redir=' + path)
        else:
            raise web.seeother('/')
    return mail

class WebColor():
    def GET(self, type, id):
        mail = isConnected()
        if mail is None:
            return ''
        
        return render.colorpicker(mail, type, id)

class WebBackup():
    def __init(self):
        self.name = u"WebBackup"

    def GET(self):
        mail = redirect_when_not_logged()
        return render.backup(mail, getLinkForLatestBackupArchive(),"")
    
    def POST(self):
        mail = redirect_when_not_logged()
        data = web.input()
        if data is None:
            return render.backup(mail, getLinkForLatestBackupArchive(),"")
        if 'shutdown' in data and 'restart' in data:
            flags.set_restart()
            raise web.seeother('/restarting')
        elif 'shutdown' in data:
            flags.set_shutdown()
            raise web.seeother('/restarting')
        elif data.create_backup is not None:
            backup.create_backup_zip()
            return render.backup(mail,
                                 getLinkForLatestBackupArchive(),
                                 "backupDone")
        else:
            mail = redirect_when_not_logged()
            return render.backup(mail, "","")
        
class WebRestore():
    def __init(self):
        self.name = u"WebRestore"

    def GET(self):
        mail = redirect_when_not_logged()            
        return render.backup(mail, getLinkForLatestBackupArchive(),"")
    
    def POST(self):
        mail = redirect_when_not_logged()
        
        data = web.input(zip_archive_to_restore={})
        if data is not None and 'zip_archive_to_restore' in data\
                            and data['zip_archive_to_restore'].filename:
            # replaces the windows-style slashes with linux ones.
            fpath = data['zip_archive_to_restore'].filename.replace('\\', '/')
            # splits the and chooses the last part (filename with extension)
            fname = fpath.split('/')[-1]
            file_uri = os.path.join(elsa.DIR_WEB_TEMP, fname)
            try:
                fout = open(file_uri,'w')
                fout.write(data.zip_archive_to_restore.file.read())
            except IOError:
                print("Error while restoring file.")
                return render.backup(mail,
                                     getLinkForLatestBackupArchive(),
                                     "restoreError")
            finally:
                fout.close()
            if backup.check_zip_backup(file_uri) == False:
                return render.backup(mail,
                                     getLinkForLatestBackupArchive(),
                                     "restoreError")
            flags.set_restore(fname)
            raise web.seeother('/restarting')
        else:
            return render.backup(mail,
                                 getLinkForLatestBackupArchive(),
                                 "restoreEmpty")

class WebUpdateELSA():
    def __init(self):
        self.name = u"WebUpdateELSA"

    def GET(self):
        mail = redirect_when_not_logged()
        
        subprocess.call(['git', 'remote', 'update'])
        git_status_out = subprocess.check_output(['git', 'status'])
        git_status_out = git_status_out.split('\n')
        try:
            git_status_out = (git_status_out[0]
                              + '<br>'
                              + git_status_out[1])
        except IndexError:
            print("Error reading git status output. " + git_status_out)
            raise
        return render.updateELSA(mail, git_status_out)
    
    def POST(self):
        mail = redirect_when_not_logged()
        data = web.input()
        if mail is not None and data.start_elsa_update is not None:
            flags.set_check_update(True)
            raise web.seeother('/restarting')
        else:
            raise web.seeother('/')
        
def get_list_of_active_sensors_acronyms(lang):
    list = []
    for i in c.AllSensors.elements:
        if c.AllSensors.elements[i].fields['active'] == '1':
            acronym = c.AllSensors.elements[i].get_acronym()
            if lang is None:
                list.append(acronym)
            else:
                list.append(c.AllSensors.elements[i].getName(lang)
                            + u' [' + acronym + u']')
    return list

def get_data_points_for_grafana_api(target, lang, time_from_utc, time_to_utc):
    datapoints = []
    sensor = None
    acronym = target
    if lang is not None:
        acronym = target[target.find('[')+1 : -1]

    sensor = c.AllSensors.findAcronym(acronym)
    try:
        sensor_id = sensor.fields['s_id']
    except AttributeError:
        raise AttributeError("That acronym does not exist : " + target)
    
    return {"target": target,
            "datapoints": rrd.get_datapoints_from_s_id(sensor_id,
                                                       time_from_utc,
                                                       time_to_utc)}

class WebApiGrafana():
    def __init(self):
        self.name = u"WebApiGrafana"

    def GET(self, lang='', request=''):
        # When no lang is set, WebPY inverts lang and request variables
        if request == '':
            request = lang
            lang = None
        return 'You have reached the / of ELSA\'s API for Grafana'

    def POST(self, lang='', request=''):
        # When no lang is set, WebPY inverts lang and request variables
        if request == '':
            request = lang
            lang = None
        data=json.loads(web.data())
        if request=='search':
            return json.dumps(get_list_of_active_sensors_acronyms(lang))
        elif request=='query':
            time_from_utc = data['range']['from']
            time_from_utc = time_from_utc.split('.')[0]
            time_from_utc = time.strptime(time_from_utc, "%Y-%m-%dT%H:%M:%S")
            time_to_utc = time.strptime(data['range']['to'].split('.')[0],
                                        "%Y-%m-%dT%H:%M:%S")
            
            targets = []
            for elem in data['targets']:
# .replace removes all '\' in the target name. Fixes a grafana/simple-json bug.
                targets.append(elem['target'].replace('\\', ''))
            out = []
            for elem in targets:
                out.append(get_data_points_for_grafana_api(elem,
                                                           lang,
                                                           time_from_utc,
                                                           time_to_utc))
            return json.dumps(out)
        else:
            return 'Error: Invalid url requested'
    

class WebRestarting():
    global app
    def __init(self):
        self.name = u"WebRestarting"

    def GET(self):
        mail = redirect_when_not_logged(False)
        
        app.stop()
        # sys.exit()
        return render.restarting(mail)
    
class WebDisconnect():
    def GET(self):
        mail = redirect_when_not_logged()
            
        c.connectedUsers.disconnect(mail)
        raise web.seeother('/')

# Menu of groups within an update form
class WebPermission():
    def GET(self, type, id):
        mail = isConnected()
        if mail is None:
            return ''

        splitted = id.split('/')
        if len(splitted) > 1:
            context = splitted[-1]
            id = splitted[0]
        else:
            context = ''
        print type+'-'+id+'-'+context
        return render.permission(mail, type, id, context)

# Display of  a record within a list
class WebModal():
    def GET(self, type, id):
        mail = isConnected()
        if mail is None:
            return ''
        
        data = web.input(nifile={})
        return render.modal(mail, type, id, data)

# Short (and not full!) Entry in a list of records
class WebFullEntry():
    def GET(self, type, id):
        mail = isConnected()
        if mail is None:
            return ''
        current = id[0] == '*'
        if current:
            id = id[1:]
        return render.fullentry(mail, type, id, current)

# List of all (active) elements of a Class
class WebList():
    def __init__(self):
        self.name = u"WebList"
    
    def GET(self, type):
        mail = redirect_when_not_logged()
        id = ''
        data = web.input(nifile={})
        if 'status' in data:
            id = data['status']

        if type == 'al':
            return render.listalarmlog(mail, type, id)
        elif type in 'abcpehsmugugrgftmdmvm' and type != 't' and type != 'f':
            return self.getRender(type, mail, id)
        else:
            return render.notfound()

    def POST(self, type):
        mail = redirect_when_not_logged()
            
        user = c.connectedUsers.users[mail].cuser
        data = web.input()
        if 'quantity' in data:
            try:
                if type == 'b':
                    count = 1
                    borne = int(data['quantity'])
                    elem = c.AllBatches.elements[data['batch'].split('_')[1]]
                    try:
                        name = int(
                            elem.fields['acronym'][elem.fields['acronym'].rfind('_')+1:])
                    except:
                        name = 0
                    while count <= borne:
                        if not elem.clone(user, (name + count)):
                            break
                        count += 1
                return self.getRender(type, mail)
            except:
                raise render.notfound()
        raise web.seeother('/')

    def getRender(self, type, mail, id=''):
        return render.list(mail, type, id)

# Display of one item
class WebItem():
    def GET(self, type, id):
        mail = redirect_when_not_logged()
        
        try:
            return render.item(type, id, mail)
        except:
            return render.notfound()

# UPDATE of Place, Equipment, Container, etc.
class WebEdit():
    def GET(self, type, id):
        mail = redirect_when_not_logged()
        return self.getRender(type, id, mail, '', '')

    def POST(self, type, id, context=None):
        mail = redirect_when_not_logged()
            
        user = c.connectedUsers.users[mail].cuser
        currObject = c.getObject(id, type)
        infoCookie = mail + ',' + user.fields['password']
        data = web.input(placeImg={},linkedDocs={})
        method = data.get("method", "malformed")
        update_cookie(infoCookie)
        if currObject is None:
            raise web.seeother('/')
        cond = currObject.validate_form(data, c, user.fields['language'])
        if cond is True:
            currObject.set_value_from_data(data, c, user)
            if data['linkedDocs'] != {}:
                linkedDocs = web.webapi.rawinput().get('linkedDocs')
                if not isinstance(linkedDocs,list):
                    linkedDocs = [linkedDocs]
                aDir = None
                for aDoc in linkedDocs:
                    if aDoc.filename != '':
                        filepath = aDoc.filename.replace('\\', '/')
                        name = filepath.split('/')[-1]
                        if name:
                            if not aDir:
                                aDir = currObject.getDocumentDir(True)
                            with open(aDir+u'/'+name, 'w') as fout:
                                fout.write(aDoc.file.read())

##            if 'a_id' in data:
##                if len(data['a_id']) > 0:
##                    c.AllAlarms.elements[data['a_id']
##                                         ].launch_alarm(currObject, c)
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

    def getListing(self, mail, type, id=''):
        return render.list(mail, type, id)

    def getRender(self, type, id, mail, errormess, data, context=''):
        if type in 'hpebcsmagugrgfutmdmvm' and not type in 'dvtfg':
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
        mail = redirect_when_not_logged()
            
        if len(type.split('/')) == 1:
            return self.getRender(type, 'new', mail, '', '')
        else:
            return self.getRender(type.split('/')[0],
                                  'new',
                                  mail,
                                  '',
                                  '',
                                  type.split('/')[-1])

    def POST(self, type):
        mail = redirect_when_not_logged()
        
        if len(type.split('_')) > 1:
            return WebEdit.POST(self,
                                type.split('/')[0],
                                'new',
                                type.split('/')[-1])
        else:
            return WebEdit.POST(self, type.split('/')[0], 'new')


class WebControl():
    def GET(self, idbatch, idcontrol):
        mail = redirect_when_not_logged()
            
        return render.control(idbatch, idcontrol, mail, '')

    def POST(self, idbatch, idcontrol, context=None):
        mail = redirect_when_not_logged()
            
        user = c.connectedUsers.users[mail].cuser
        infoCookie = mail + ',' + user.fields['password']
        update_cookie(infoCookie)
        data = web.input()
        method = data.get("method", "malformed")
        currObject = c.getObject(idcontrol, 'h')
        cond = currObject.validate_control(data, user.fields['language'])
        if cond is True:
            currObject.create_control(data, user)
            raise web.seeother('/find/h/b_' + str(idbatch))
        else:
            return render.control(idbatch, idcontrol, mail, cond)


class WebFind():
    def GET(self, type, id1, id2):
        mail = redirect_when_not_logged()
            
        data = web.input()
	barcode = ''
        if 'barcode' in data:
	    barcode = data['barcode']
        return self.getRender(type, id1, id2, mail, barcode)

    def POST(self, type, id1, id2):
        mail = redirect_when_not_logged()
        
        user = c.connectedUsers.users[mail].cuser
        infoCookie = mail + ',' + user.fields['password']
        update_cookie(infoCookie)
        data = web.input()
        if 'action' in data and data['action']=='map':
            raise web.seeother('/map/b_'+data['batch'])
        elif 'checkpoint' in data and 'batch' in data:
          raise web.seeother('/control/b_'+data['batch'] +
                             '/h_'+data['checkpoint'])
        return self.getRender(type, id1, id2, mail)

    def getRender(self, type, id1, id2, mail, barcode=''):
        try:
            if type == 'related': # sync with getRender from WebBarcode
                if id1 == 'm':
                    return render.findrelatedmeasures(id2, mail, barcode)
                elif ('g' in id1 or id1 == 'h'):
                    return render.findrelatedgroups(id1, id2, mail, barcode)
                else:
                    return render.findrelatedcomponents(id1, id2, mail, barcode)
            else:
                if type == 'd'and id1 in 'pceb':
                    return render.findlinkeddata(id1, id2, mail,None)
                elif type == 't' and id1 in 'ceb':
                    return render.findlinkedtransfers(id1, id2, mail,None)
                elif type == 'v' and id1 == 'b':
                    return render.findlinkedpourings(id2, mail,None)
                elif type == 'h':
                    return render.findcontrol(id1, id2, mail)
                elif type == 'b':
                    return render.findbatch(id1, id2, mail)
                elif type == 'al':
                    return render.findalarmlog(id1, id2, mail)
                else:
                    return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()

class WebFindModel():
    def GET(self, type, id1, id2, modelid):
        mail = redirect_when_not_logged()
            
        data = web.input()
	barcode = ''
        if 'barcode' in data:
	    barcode = data['barcode']
        return self.getRender(type, id1, id2, modelid, mail, barcode)

    def getRender(self, type, id1, id2, modelid, mail, barcode=''):
        try:
                if type == 'd'and id1 in 'pceb':
                    return render.findlinkeddata(id1, id2, mail, modelid)
                elif type == 't' and id1 in 'ceb':
                    return render.findlinkedtransfers(id1, id2, mail, modelid)
                elif type == 'v' and id1 == 'b':
                    return render.findlinkedpourings(id2, mail, modelid)
                else:
                    return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()

class WebGraphic():
    def __init__(self):
        self.name = u"WebGraphic"

    def GET(self, type, id):
        mail = redirect_when_not_logged()
            
        objects = c.findAllFromType(type)
        if id in objects.elements.keys() and type in 'scpem':
            return render.graphic(mail, type, id)
        return render.notfound()

class WebMapRecipe():
    def __init__(self):
        self.name = u"WebMapRecipe"

    def GET(self,id):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        
        if id in c.AllGrRecipe.elements.keys():
            return render.maprecipe(mail, type, id)
        return render.notfound()

class WebMapBatch():
    def __init__(self):
        self.name = u"WebMapBatch"

    def GET(self,id):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        
        if id in c.AllBatches.elements.keys():
            elem = c.AllBatches.elements[id]
            return render.mapbatch(mail, elem)
        return render.notfound()

class WebGraphHelp():
    def __init__(self):
        self.name = u"WebGraphHelp"

    def GET(self, type, id):
        mail = redirect_when_not_logged()
            
        objects = c.findAllFromType(type)
        return render.graphhelp(mail, type, id)

class WebGraphRecipe():
    def __init__(self):
        self.name = u"WebGraphRecipe"

    def GET(self,type,id):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        graph = ""

        kusage = ''
        if type == 'b':
            if id in c.AllBatches.elements.keys():
                batch = c.AllBatches.elements[id]
                id = batch.get_group()
                place = batch.get_actual_position_here(c)
                if place:
                    kusage = place.get_group()
                    if kusage and kusage in c.AllGrUsage.elements.keys():
                        usage = c.AllGrUsage.elements[kusage]
        elif type == 'gr':
            batch = None
        else:
            return render.notfound()

        if id in c.AllGrRecipe.elements.keys():
            elem = c.AllGrRecipe.elements[id]
            summit = [id] + elem.get_supermap_str()
            usagesTop = c.AllGrUsage.get_usages_for_recipe(summit)
            recipes_todo = set()
            next_usage = []
            done = set()
            prec_u = ""
            for usageTop in usagesTop:
                usaTopID = 'gu_'+usageTop.getID()
                if prec_u:
                    #graph += prec_u+"->"+usaTopID+"[style=\"stroke-width:0px;stroke:#fff\"];"
                    next_usage.append(prec_u+" "+usaTopID)
                prec_u = usaTopID
            for usageTop in usagesTop:
                usaTopID = 'gu_'+usageTop.getID()
                graph += usaTopID # +"[url=\"/find/related/"+usaTopID+"\""
                graph += "[labelType=\"html\",label=\"<a href=/find/related/"+usaTopID+">"+usageTop.getNameHTML(lang)+"</a>\""
                graph += ",tooltip=\""+usageTop.fields['acronym']+"\""
                graph += ",id=\""+usaTopID+"\",shape=diamond,style=\"fill:"+("#fbcfaa" if kusage == usageTop.getID() else "#fff")+";stroke:1px;\"];"
                
                checkpoints = c.AllCheckPoints.get_checkpoints_for_recipe_usage(summit, [usageTop.getID()])
                prec_v = ""
                for v in checkpoints:
                    #print "h="+v.getID()
                    hid = "h_"+v.getID()
                    if v.getID() not in done:
                        if not prec_v:
                            graph += usaTopID+'->'+hid+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
##                                if v.fields['gr_id'] != id:
##                                    graph += "gr_"+v.fields['gr_id']+'->'+hid+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
                        elems = v.get_local_model_sorted()
                        obs = ""
                        for e in elems:
                            if e.get_type() == 'tm':
                                if e.fields['gu_id']:
                                    nx_usage = e.fields['gu_id']
                                    graph += hid+"->"+"gu_"+nx_usage+"[style=\"stroke-width:3px\""
                                    if batch:
                                        events = batch.fromModel(c,e)
                                        if len(events) > 0:
                                            graph += ",labelType=\"html\",label=\"<a href=/find/t/b_"+batch.getID()+"/"+e.getID()+">"+unicode(len(events))+" x</a>\""
                                    graph += "];"
                                    points = usaTopID+" "+"gu_"+nx_usage
                                    #print points+" in "+unicode(next_usage)
                                    if points in next_usage:
                                        next_usage.remove(points)
                            elif e.get_type() == 'vm':
                                v_recipe = None
                                if e.fields['dest']:
                                    nx_recipe = e.fields['dest']
                                    if nx_recipe and nx_recipe in c.AllGrRecipe.elements.keys():
                                        v_recipe = c.AllGrRecipe.elements[nx_recipe]
                                        graph += hid+"->"+"gr_"+nx_recipe
                                if e.fields['src']:
                                    nx_recipe = e.fields['src']
                                    if nx_recipe and nx_recipe in c.AllGrRecipe.elements.keys():
                                        v_recipe = c.AllGrRecipe.elements[nx_recipe]
                                        graph += "gr_"+nx_recipe+"->"+hid
                                if v_recipe:
                                    graph += "[style=\"stroke-width:3px;stroke:#f07e26\",labelType=\"html\",label=\""
                                    events = []
                                    if batch:
                                        events = batch.fromModel(c,e)
                                    if len(events) == 0:
                                        graph += e.get_quantity()+' '+protectJS(e.get_unit_in_context(c,elem))
                                    else:
                                        first = True
                                        for ev in events:
                                            Acolor = None
                                            qtity = ev.get_quantity()
                                            if qtity:
##                                                qt = float(qtity)
##                                                Aname, Aacronym, Acolor, Atext_color = e.getTypeAlarm(qt,None)
##                                                if Aname == 'typical':
##                                                    Acolor = None
                                                graph += ("" if first else ", ")
                                                graph += "<a href=/edit/v_"+ev.getID()+">" + ("<font color="+Acolor+">" if Acolor else "")
                                                graph += qtity+" "+protectHTML(ev.get_unit_in_context(c,elem))+("</font>" if Acolor else "")+"</a>"
                                                first = False
                                    graph += "\"];"
                                    recipes_todo.add(v_recipe)
                            elif e.get_type() == 'dm':
                                obs += u"<br>"+e.getNameHTML(lang)
                                events = []
                                if batch:
                                    events = batch.fromModel(c,e)
                                if len(events) == 0:
                                    target = "?"
                                    if e.fields['typical']:
                                        target = e.fields['typical']
                                    measure = e.get_measure(c)
                                    if measure:
                                        obs += u" / " + measure.getNameHTML(lang)+": "+target+" "+protectHTML(measure.fields['unit'])
                                    else:
                                        obs += ": " + target                                    
                                else:
                                    first = True
                                    for edata in events:
                            		Acolor = None
                                        qtity = edata.get_quantity()
                                        if qtity:
                                            qt = float(qtity)
                                            Aname, Aacronym, Acolor, Atext_color = e.getTypeAlarm(qt,None)
                                            if Aname == 'typical':
                                                Acolor = None
                                            obs += (": " if first else ", ")
                                            obs += "<a href=/edit/d_"+edata.getID()+">" + ("<font color="+Acolor+">" if Acolor else "")
                                            obs += qtity+" "+protectHTML(edata.get_unit(c))+("</font>" if Acolor else "")+"</a>"
                                            first = False
                        graph += hid # +"[url=\"/find/related/"+hid+"\""
                        graph += "[labelType=\"html\",label=\"<a href=/find/related/"+hid+">"
##                        ext = v.isImaged()
##                        if ext:
##                            graph += "<img scale=both src="+self.getImageURL(ext)+">"
                        if batch and v.getID() in batch.checkpoints:
                            graph += "* "
                        graph += v.getNameHTML(lang)
                        graph += "</a>"+obs+"\"" #+v.fields['rank']
                        graph += ",tooltip=\""+v.fields['acronym']+"\""
                        graph += ",id=\""+hid+"\"];"
                        if prec_v:
                            graph += "h_"+prec_v+'->'+hid+"[style=\"stroke-width:3px;stroke:#888\"];"
                        prec_v = v.getID()
                        done.add(prec_v)
            for remain in next_usage:
                points = remain.split(" ")
                graph += points[0]+"->"+points[1]+"[style=\"stroke-width:1px;stroke-dasharray:3,12;stroke:#888;\"];"
            prec = ""
            stack = []
            for krecipe in summit:
                if krecipe == '>>':
                    stack.append(prec)
                elif krecipe == '<<':
                    prec = stack.pop()
                else:
                    if krecipe and krecipe in c.AllGrRecipe.elements:
                        recipe = c.AllGrRecipe.elements[krecipe]
                        if prec:
                            graph += 'gr_'+krecipe+'->gr_'+prec+'[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];'
                        graph += 'gr_'+krecipe
                        graph += "[labelType=\"html\",label=\"<a href=/find/related/gr_"+krecipe+">"+recipe.getNameHTML(lang)+"</a>\""
                        graph += ",tooltip=\""+recipe.fields['acronym']+"\""
                        graph += ",id=\"gr_"+krecipe+"\",shape=ellipse,style=\"fill:"+("#fbcfaa" if krecipe == id else "#fff")+";stroke:1px;\"];"
                        if recipe.fields['gu_id']:
                            graph += "gr_"+krecipe+"->gu_"+recipe.fields['gu_id']+"[style=\"stroke-width:3px;stroke:#3d3\"];"
                    prec = krecipe
            for recipe in recipes_todo:
                if not recipe.getID() in summit:
                    grID = "gr_"+recipe.getID()
                    for above in recipe.parents:
                        if above in summit:
                            graph += "gr_"+above+"->"+grID+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
                    graph += grID
                    graph += "[labelType=\"html\",label=\"<a href=/find/related/"+grID+">"+recipe.getNameHTML(lang)+"</a>\""
                    graph += ",tooltip=\""+recipe.fields['acronym']+"\""
                    graph += ",id=\""+grID+"\",shape=ellipse,style=\"fill:#fff;stroke:1px;\"];"
##            for usage in usages:
##                    usaID = 'gu_'+usage.getID()
##                    for parent in usage.parents:
##                        usage = c.AllGrUsage.elements[parent]
##                        aboveID = 'gu_'+parent
##                        graph += aboveID+"->"+usaID+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
            return render.graphrecipe(mail, batch, id, graph)
        return render.notfound()

##class WebGraphBatch():
##    def __init__(self):
##        self.name = u"WebGraphBatch"
##
##    def GET(self,id):
##        mail = redirect_when_not_logged()
##        lang = c.connectedUsers.users[mail].cuser.fields['language']
##        
##        if id in c.AllBatches.elements.keys():
##            elem = c.AllBatches.elements[id]
##            recipes = set()
##            recipe_id = elem.fields['gr_id']
##            recipe = None
##            if recipe_id and recipe_id in c.AllGrRecipe.elements.keys():
##                recipes.add(recipe_id)
##                recipe = c.AllGrRecipe.elements[recipe_id]
##                new_recipes = set(recipe.get_all_parents([],None))
##                recipes = recipes | new_recipes
##            #print "grs="+unicode(recipes)
##            components = elem.get_actual_position_hierarchy(c)
##            usages_todo = []
##            recipes_todo = set()
##            for place in reversed(components):
##                if place.get_type() in "pec":
##                    #print place
##                    gr_usage = place.get_group()
##                    #print "begu="+gr_usage
##                    if gr_usage and gr_usage in c.AllGrUsage.elements.keys():
##                        usage = c.AllGrUsage.elements[gr_usage]
##                        for parent in reversed(usage.get_all_parents([],None)):
##                            #print "begup="+parent
##                            if parent and parent in c.AllGrUsage.elements.keys():
##                                usages_todo.append(c.AllGrUsage.elements[parent])
##                        usages_todo.append(usage)
##            graph = ""
##            done = set()
##            prec = None
##            while len(usages_todo) > 0:
##              usage = usages_todo[0]
##              #print "gu="+usage.getID()
##              usaID = "gu_"+usage.getID()
##              usages_todo.remove(usage)
##              if not usaID in done:
##                done.add(usaID)
##                if prec:
##                    graph += prec+"->"+usaID+"[style=\"stroke-dasharray:5,5\"];"
##                graph += usaID # +"[url=\"/find/related/"+usaID+"\""
##                graph += "[labelType=\"html\",label=\"<a href=/find/related/"+usaID+">"+usage.getNameHTML(lang)+"</a>\""
##                graph += ",tooltip=\""+usage.fields['acronym']+"\""
##                graph += ",id=\""+usaID+"\",shape=diamond,style=\"fill:#fff;stroke:1px;\"];"
##                prec = usaID
##                allowedcheckpoints = c.AllCheckPoints.get_checkpoints_for_recipe_usage(recipes,set([usage.getID()]))
##                for v in allowedcheckpoints:
##                    #print "h="+v.getID()
##                    hid = "h_"+v.getID()
##                    graph += prec+"->"+hid+";"
##                    prec = hid
##                    elems = v.get_model_sorted()
##                    obs = ""
##                    for e in elems:
##                        if e.get_type() == 'tm':
##                            if e.fields['gu_id']:
##                                nx_usage = e.fields['gu_id']
##                                #print "nxu="+nx_usage
##                                if nx_usage and nx_usage in c.AllGrUsage.elements.keys():
##                                    nx_usage = c.AllGrUsage.elements[nx_usage]
##                                    # graph += hid+"->"+"gu_"+e.fields['gu_id']+"[style=\"stroke-dasharray:5,5\"];"
##                                    for parent in reversed(nx_usage.get_all_parents([],None)):
##                                        #print "nxup="+parent
##                                        if parent and not parent in done and parent in c.AllGrUsage.elements.keys():
##                                            usages_todo.append(c.AllGrUsage.elements[parent])
##                                    usages_todo.append(nx_usage)
##                        elif e.get_type() == 'vm':
##                            if e.fields['dest']:
##                                nx_recipe = e.fields['dest']
##                                if nx_recipe and nx_recipe in c.AllGrRecipe.elements.keys():
##                                    dest_recipe = c.AllGrRecipe.elements[nx_recipe]
##                                    graph += hid+"->"+"gr_"+nx_recipe+"[style=\"stroke-width:3px\",label=\""+protectJS(e.getName(lang))+"\"];"
##                                    recipes_todo.add(dest_recipe)
##                            if e.fields['src']:
##                                nx_recipe = e.fields['src']
##                                if nx_recipe and nx_recipe in c.AllGrRecipe.elements.keys():
##                                    src_recipe = c.AllGrRecipe.elements[nx_recipe]
##                                    graph += "gr_"+nx_recipe+"->"+hid+"[style=\"stroke-width:3px\",label=\""+protectJS(e.getName(lang))+"\"];"
##                                    recipes_todo.add(src_recipe)
##                        elif e.get_type() == 'dm':
##                            obs += "<br>"+e.getNameHTML(lang)
##                            measure = e.get_measure(c)
##                            if measure:
##                                obs += " / "+measure.getNameHTML(lang)+": ? "+protectHTML(measure.fields['unit'])
##                    graph += hid # +"[url=\"/find/related/"+hid+"\""
##                    graph += "[labelType=\"html\",label=\"<a href=/find/related/"+hid+">"
##                    graph += ("* " if v.getID() in elem.checkpoints else "")+v.getNameHTML(lang)
##                    graph += "</a> <a href=/control/b_"+id+"/"+hid+"><big><strong>+</strong></big></a>"+obs+"\""
##                    graph += ",tooltip=\""+v.fields['acronym']+"\""
##                    graph += ",id=\""+hid+"\"];"
##            for recipe in recipes_todo:
##                grID = "gr_"+recipe.getID()
##                graph += grID
##                graph += "[labelType=\"html\",label=\"<a href=/find/related/"+grID+">"+recipe.getNameHTML(lang)+"</a>\""
##                graph += ",tooltip=\""+recipe.fields['acronym']+"\""
##                graph += ",id=\""+grID+"\",shape=ellipse,style=\"fill:#fff;stroke:1px;\"];"
##            return render.graphbatch(mail, 'b', id, graph)
##        return render.notfound()

class WebMapFunctions():
    def __init__(self):
        self.name = u"WebMapFunctions"

    def GET(self):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        return render.mapfunctions(mail)

class WebMapComponents():
    def __init__(self):
        self.name = u"WebMapComponents"

    def GET(self):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        return render.mapcomponents(mail)

class WebMapRecipes():
    def __init__(self):
        self.name = u"WebMapRecipes"

    def GET(self):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        return render.maprecipes(mail)

class WebMapCheckPoints():
    def __init__(self):
        self.name = u"WebMapCheckPoints"

    def GET(self):
        mail = redirect_when_not_logged()
        lang = c.connectedUsers.users[mail].cuser.fields['language']
        return render.mapcheckpoints(mail)

class WebRRDfetch():
    def __init__(self):
        self.name = u"WebRRDfetch"

    def GET(self, id):
        mail = redirect_when_not_logged()
        data = web.input(nifile={})
        period = None
        if 'period' in data:
            period = data['period']
            
        if id in c.AllSensors.elements:
            currSensor = c.AllSensors.elements[id]
            web.header('Content-Disposition',
                       'attachment; filename="s_'+str(id)+'.csv"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            return currSensor.fetchRRD(period)
        return render.notfound()

class WebIndex():
    def __init(self):
        self.name = u"WebIndex"

    def GET(self):
        mail = isConnected()
        if mail is None:
            return render.index(False, '')
        
        return self.getRender(mail)

    def POST(self):
        data = web.input(nifile={})
        # method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)

            query_string = web.ctx.env.get('QUERY_STRING')
            redirect_url = useful.parse_url_query_string(query_string, 'redir')
            print redirect_url
            if (redirect_url is not None):
                raise web.seeother(redirect_url)
            else:
                return render.index(True, data._username_)
        return render.index(False, '')

    def getRender(self, mail):
        return render.index(True, mail)


class WebBarcode():
    def __init__(self):
        self.name = u"WebBarcode"

    def GET(self, id=""):
        mail = redirect_when_not_logged()
            
        try:
            data = web.input()
            if 'barcode' in data:
                id = data['barcode']
            return self.getRender(id, mail)
        except:
            return self.getRender(id, mail, 'notfound')

    def getRender(self, id, mail, errormess=''):
         id = id.strip()
         if errormess:
             return render.barcode(mail, id, errormess)
	 elem  = c.AllBarcodes.barcode_to_item(id)
         if elem == None:
             return render.barcode(mail, id, errormess)
         else:
            aType = elem.get_type()
            raise web.seeother('/find/related/'+aType+'_'+elem.getID()+'?barcode='+id)
         return render.barcode(mail, id, errormess)

    def getListing(self, mail):
        return render.list(mail, 'places')


class getRRD():
    def GET(self, filename):
        with open(elsa.DIR_RRD + filename) as f:
            try:
                return f.read()
            except IOError:
                web.notfound()

class getCSV():
    def GET(self, filename):
        with open(elsa.DIR_DATA_CSV + filename) as f:
            try:            
                return f.read()
            except IOError:
                web.notfound()

class getDoc():
    def GET(self, filename):
        with open(elsa.DIR_DOC + filename) as f:
            try:
                return f.read()
            except IOError:
                web.notfound()

class WebMonitoring():
    def __init__(self):
        self.name = u"WebMonitoring"

    def GET(self):
        mail = redirect_when_not_logged()
        
        return self.getRender(mail)

    def POST(self):
        mail = redirect_when_not_logged()
        
        data = web.input(nifile={})
        # method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_)
        raise web.seeother('/')

    def getRender(self, mail):
        return render.monitoring(mail)

class WebExport():
    def GET(self, type, id):
        mail = redirect_when_not_logged()
        
        return self.getRender(type, id, mail)

    def POST(self, type, id):
        mail = redirect_when_not_logged()
        
        user = c.connectedUsers.users[mail].cuser
        infoCookie = mail + ',' + user.fields['password']
        update_cookie(infoCookie)
        data = web.input()
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
        mail = redirect_when_not_logged()
        return self.getRender(type, id, mail)

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
            f = open(elsa.DIR_DATA_CSV + filename)
            web.header('Content-Disposition',
                       'attachment; filename="'+str(filename)+'"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            return f.read()
        except IOError:
            web.notfound()
        finally:
            f.close()


def connexion(username, password):
    user = c.AllUsers.getUser(username)
    if user is None:
        return None
    
    cryptedPassword = useful.encrypt(password, user.fields['registration'])
    if user.checkPassword(cryptedPassword) is True:
        return user


def isConnected():
    infoCookie = web.cookies().get('webpy')
    if infoCookie is None:
        return None
    
    infoCookie = infoCookie.split(',')
    if c.connectedUsers.isConnected(infoCookie[0], infoCookie[1]) is True:
        return infoCookie[0]


def notfound():
    return web.notfound(render.notfound())


def update_cookie(infoCookie):
    web.setcookie('webpy', infoCookie, expires=9000)

def cleanup_web_temp_dir():
    try:
        shutil.rmtree(elsa.DIR_WEB_TEMP)
    except OSError, e:
        print ("Error: %s - %s." % (e.filename,e.strerror))
        raise
    finally:
        if not os.path.exists(elsa.DIR_WEB_TEMP):
            os.makedirs(elsa.DIR_WEB_TEMP)


def start_update():
    print("Debut de la mise à jour d'ELSA avec Git")
    try:
        subprocess.check_call("git pull", shell=True)
    except subprocess.CalledProcessError:
        print("Update error. Please update manually.")
    finally:
        print("Fin du processus de mise à jour")

def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    elsa._lock_socket.close()
    python = sys.executable
    args = sys.argv
    args[0] = os.path.join(elsa.DIR_BASE, os.path.basename(sys.argv[0]))
    os.execl(python, python, *args)

class end_activities_flags:
    """
    An object that holds some flags until just before the end of the program.
    Intended to launch things when we want to ELSA to be in a coherent state.
    """
    def __init__(self):
        self._check_update = False
        self._restart_elsa = False
        self._restart = False
        self._shutdown = False
        self._restore = False
    
    def set_restore(self, fname):
        self._restore = fname

    def set_check_update(self, value):
        if value == False:
            self._check_update = False
        elif value == True:
            self._check_update = True
        else:
            raise("Invalid value received : expected bool")

    def set_restart_elsa(self):
        self._restart_elsa = True
    
    def set_shutdown(self):
        self._shutdown = True
    
    def set_restart(self):
        self._restart = True
    
    def launch_end_activities(self):
        if self._restore:
#returns False if restore did not work but no way to alert the user !
            if not backup.restore_from_zip(self._restore): 
                print ("Error while restoring from bacup.")
            self.set_restart_elsa()

        if self._check_update:
            start_update()
            self.set_restart_elsa()
	
        if self._restart_elsa:
	    restart_program()
        
        if self._restart:
            subprocess.call(['sudo', '/sbin/shutdown', '-r', 'now'])
        
        if self._shutdown: 
            subprocess.call(['sudo', '/sbin/shutdown', '-h', 'now'])

c = None
wsgiapp = None
flags = end_activities_flags()
app = None

def main():
    # restart_program()
    args = manage_cmdline_arguments()
    cleanup_web_temp_dir()

    global c, wsgiapp, render, app
    try:
        web.config.debug = False
        # Configuration Singleton ELSA
        if 'config' in args:
            c = elsa.Configuration(args.config)
        else:
            c = elsa.Configuration(None)
        c.load()
        web.template.Template.globals['c'] = c
        web.template.Template.globals['str'] = str
        web.template.Template.globals['useful'] = useful
        web.template.Template.globals['round'] = round
        web.template.Template.globals['subprocess'] = subprocess
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
            '/doc/(.+)', 'getDoc',
            '/list/(.+)', 'WebList',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/graphhelp/(.+)_(.+)', 'WebGraphHelp',
            '/map/b_(.+)', 'WebMapBatch',
            '/map/gr_(.+)', 'WebMapRecipe',
            '/graph/(.+)_(.+)', 'WebGraphRecipe',
            '/map/gf', 'WebMapFunctions',
            '/map/gu', 'WebMapComponents',
            '/map/h', 'WebMapCheckPoints',
            '/map/gr', 'WebMapRecipes',
            '/barcode/(.+)', 'WebBarcode',
            '/barcode/', 'WebBarcode',
            '/modal/(.+)_(.+)', 'WebModal',
            '/color/(.+)_(.+)', 'WebColor',
            '/fullentry/(.+)_(.+)', 'WebFullEntry',
            '/export/(.+)_(.+)/(.+)', 'WebDownloadData',
            '/export/(.+)_(.+)', 'WebExport',
            '/rrdfetch/(.+)', 'WebRRDfetch',
            '/datatable/(.+)_(.+)', 'WebDataTable',
            '/find/(.+)/(.+)_(.+)/(.+)', 'WebFindModel',
            '/find/(.+)/(.+)_(.+)', 'WebFind',
            '/permission/(.+)_(.+)', 'WebPermission',
            '/control/b_(.+)/h_(.+)', 'WebControl',
            '/disconnect', 'WebDisconnect',
            '/backup', 'WebBackup',
            '/restore', 'WebRestore',
            '/updateELSA', 'WebUpdateELSA',
            '/restarting', 'WebRestarting',
            '/api/grafana/([^/]*)/{0,1}(.*)', 'WebApiGrafana'
        )
        app = web.application(urls, globals())
        app.notfound = notfound
        app.run()
        # wsgiapp = app.wsgifunc()
    except:
        traceback.print_exc(file=sys.stdout)
    finally:
        print 'fin des threads'
        if c:
            c.isThreading = False
            c.UpdateThread.join()
            c.RadioThread.join()
        
        flags.launch_end_activities()

        print 'Exit system'


if __name__ == "__main__":
    main()
