# -*- coding: utf-8 -*-
import web
import urllib
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
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
import calendar
import bisect

global c, render, includes


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
    return cgi.escape(input, True).replace("'", "&#39;")


def protectJS(input):
    if not input:  # if input is None
        return u''
    return unicode(input).replace("'", "\\'").replace("\\", "\\\\")


def redirect_when_not_logged(redir=True):
    """
    Should be used at the begining of every GET, POST, etc.
    When the user is not logged, will redirect to login page and preserve
    current path. Returns None
    When the user is logged, returns the mail (does not redirect)
    When redir is Fals, will log into home page
    """
    connected = isConnected()
    if connected is None:
        if redir:
            path = web.ctx.env.get('PATH_INFO')
            query = web.ctx.env.get('QUERY_STRING')
            if query:
                path = path + u'?' + urllib.quote(query)
                print query
                print path
            raise web.seeother('/?redir=' + path)
        else:
            raise web.seeother('/')
    return connected


def redirect_when_not_allowed(type, redir=True):
    connected = redirect_when_not_logged(redir)
    if connected:
        user = connected.cuser
        if user and user.updateAllowed(c, type):
            return connected
    raise web.seeother('/')


def redirect_when_not_admin(redir=True):
    connected = redirect_when_not_logged(redir)
    if connected:
        user = connected.cuser
        if user and user.adminAllowed(c):
            return connected
    raise web.seeother('/')


class WebColor:
    def GET(self, type, id):
        connected = isConnected()
        if connected is None:
            return ''
        color = ''
        if id != 'new':
            elem = c.get_object(type, id)
            if elem:
                color = elem.fields['colorgraph']
        return render.colorpicker(connected, color)


class WebBackup:
    def __init(self):
        self.name = u"WebBackup"

    def GET(self):
        connected = redirect_when_not_admin()
        return render.backup(connected, getLinkForLatestBackupArchive(), "")

    def POST(self):
        connected = redirect_when_not_admin()
        data = web.input()
        if data is None:
            return render.backup(connected, getLinkForLatestBackupArchive(), "")
        if 'shutdown' in data and 'restart' in data:
            flags.set_restart()
            raise web.seeother('/restarting')
        elif 'shutdown' in data:
            flags.set_shutdown()
            raise web.seeother('/restarting')
        elif data.create_backup is not None:
            backup.create_backup_zip()
            return render.backup(connected,
                                 getLinkForLatestBackupArchive(),
                                 "backupDone")
        else:
            connected = redirect_when_not_logged()
            return render.backup(connected, "", "")


class WebRestore:
    def __init(self):
        self.name = u"WebRestore"

    def GET(self):
        connected = redirect_when_not_admin()
        return render.backup(connected, getLinkForLatestBackupArchive(), "")

    def POST(self):
        connected = redirect_when_not_admin()

        data = web.input(zip_archive_to_restore={})
        if data is not None and 'zip_archive_to_restore' in data \
                and data['zip_archive_to_restore'].filename:
            # replaces the windows-style slashes with linux ones.
            fpath = data['zip_archive_to_restore'].filename.replace('\\', '/')
            # splits the and chooses the last part (filename with extension)
            fname = fpath.split('/')[-1]
            file_uri = os.path.join(elsa.DIR_WEB_TEMP, fname)
            try:
                fout = open(file_uri, 'w')
                fout.write(data.zip_archive_to_restore.file.read())
            except IOError:
                print("Error while restoring file.")
                return render.backup(connected,
                                     getLinkForLatestBackupArchive(),
                                     "restoreError")
            finally:
                fout.close()
            if backup.check_zip_backup(file_uri) == False:
                return render.backup(connected,
                                     getLinkForLatestBackupArchive(),
                                     "restoreError")
            flags.set_restore(fname)
            raise web.seeother('/restarting')
        else:
            return render.backup(connected,
                                 getLinkForLatestBackupArchive(),
                                 "restoreEmpty")


class WebUpdateELSA:
    def __init(self):
        self.name = u"WebUpdateELSA"

    def GET(self):
        connected = redirect_when_not_admin()

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
        return render.updateELSA(connected, git_status_out)

    def POST(self):
        connected = redirect_when_not_admin()
        data = web.input()
        if connected is not None and data.start_elsa_update is not None:
            flags.set_check_update(True)
            raise web.seeother('/restarting')
        else:
            raise web.seeother('/')


def get_list_of_active_sensors_acronyms(lang):
    list = []
    for i, s in c.AllSensors.elements.items():
        if s.fields['active'] == '1':
            acronym = s.get_acronym()
            if lang is None:
                list.append(acronym)
            else:
                list.append(s.getName(lang)
                            + u' [' + acronym + u']')
    return list


def get_data_points_for_grafana_api(target, lang, time_from_utc, time_to_utc):
    datapoints = []
    sensor = None
    acronym = target
    if lang is not None:
        acronym = target[target.find('[') + 1: -1]

    sensor = c.AllSensors.findAcronym(acronym)
    try:
        sensor_id = sensor.fields['s_id']
    except AttributeError:
        raise AttributeError("That acronym does not exist : " + target)

    return {"target": target,
            "datapoints": rrd.get_datapoints_from_s_id(sensor_id,
                                                       time_from_utc,
                                                       time_to_utc)}


class WebApiGrafana:
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
        data = json.loads(web.data())
        if request == 'search':
            web.header('Content-type', 'application/json')
            return json.dumps(get_list_of_active_sensors_acronyms(lang))
        elif request == 'query':
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
            web.header('Content-type', 'application/json')
            return json.dumps(out)
        else:
            return 'Error: Invalid url requested'


class WebApiKeyValue:
    def __init(self):
        self.name = u"WebApiKeyValue"

    def GET(self):
        query_string = web.ctx.env.get('QUERY_STRING')
        inputData = useful.parse_url_dict(query_string)
        inputData['H'] = useful.get_timestamp()
        if inputData['M']:
            c.AllSensors.storeLoraValue(inputData)
        web.header('Content-type', 'application/json')
        return json.dumps(inputData)

    def POST(self):
        return ""

class WebRestarting:
    global app

    def __init(self):
        self.name = u"WebRestarting"

    def GET(self):
        connected = redirect_when_not_logged(False)
        app.stop()
        # sys.exit()
        return render.restarting(connected)


class WebDisconnect:
    def GET(self):
        connected = redirect_when_not_logged()

        c.connectedUsers.disconnect(connected)
        raise web.seeother('/')


# Menu of groups within an update form
class WebSelect:
    def GET(self, datafield, context):
        connected = isConnected()
        if connected is None:
            return ''
        return render.select(connected, datafield, context)


class WebSelectMul:
    def GET(self, type, id, context=''):
        connected = isConnected()
        if connected is None:
            return ''
        return render.selectmul(connected, type, id, context)


# Display of  a record within a list
class WebModal:
    def GET(self, type, id):
        connected = isConnected()
        if connected is None:
            return ''

        data = web.input(nifile={})
        return render.modal(connected, type, id, data)


# Short (and not full!) Entry in a list of records
class WebFullEntry:
    def GET(self, type, id):
        connected = isConnected()
        if connected is None:
            return ''
        current = id[0] in '*!'
        if current:
            if id[0] == '!':
                current = "menu"
        if current:
            id = id[1:]
        return render.fullentry(connected, type, id, current)


# List of all (active) elements of a Class
class WebList:
    def __init__(self):
        self.name = u"WebList"

    def GET(self, type):
        connected = redirect_when_not_logged()
        status = ''
        data = web.input(nifile={})
        if 'status' in data:
            status = data['status']
        allRec = type[0] == '*'
        if allRec:
            type = type[1:]
        if type in elsa.ALL_NAMED_TYPES or type == 'al':
            return render.list(connected, ('*' if allRec else '') + type, status)
        else:
            return render.notfound()

    def POST(self, type):
        connected = redirect_when_not_logged()
        raise web.seeother('/')


# Make copies of an element
class WebClone:
    def __init__(self):
        self.name = u"WebClone"

    def GET(self, type, id):
        return render.notfound()

    def POST(self, type, id):
        connected = redirect_when_not_logged()

        user = connected.cuser
        data = web.input()
        if 'quantity' in data:
            try:
                if type == 'b':
                    count = 1
                    borne = int(data['quantity'])
                    elem = c.AllBatches.get(id)
                    try:
                        recipe = elem.get_group()
                        acro = elem.fields['acronym']
                        name = int(acro[acro.rfind('_') + 1:])
                    except:
                        name = 0
                    while count <= borne:
                        if not elem.clone(user, (name + count)):
                            break
                        count += 1
                    raise web.seeother('/find/related/gr_' + recipe)
                return render.notfound()
            except:
                traceback.print_exc()
                return render.notfound()
        raise web.seeother('/')


# Display of one item
class WebItem:
    def GET(self, type, id):
        connected = redirect_when_not_logged()

        try:
            return render.item(connected, type, id)
        except:
            traceback.print_exc()
            return render.notfound()


# Display complete history of one item
class WebHistory:
    def GET(self, type, id):
        connected = redirect_when_not_logged()

        try:
            return render.history(connected, type, id)
        except:
            traceback.print_exc()
            return render.notfound()


# UPDATE of Place, Equipment, Container, etc.
class WebEdit:
    def GET(self, type, id):
        connected = redirect_when_not_allowed(type)
        return self.getRender(connected, type, id, '', '')

    def POST(self, type, id, context=None):
        connected = redirect_when_not_allowed(type)
        user = connected.cuser
        currObject = c.getObject(id, type)
        data = web.input(placeImg={}, linkedDocs={})
        if currObject is None:
            raise web.seeother('/')
        cond = currObject.validate_form(data, c, user)
        if cond is True:
            currObject.set_value_from_data(data, c, user)
            if data['linkedDocs'] != {}:
                linkedDocs = web.webapi.rawinput().get('linkedDocs')
                if not isinstance(linkedDocs, list):
                    linkedDocs = [linkedDocs]
                aDir = None
                for aDoc in linkedDocs:
                    if aDoc.filename != '':
                        filepath = aDoc.filename.replace('\\', '/')
                        name = filepath.split('/')[-1]
                        if name:
                            if not aDir:
                                aDir = currObject.getDocumentDir(True)
                            with open(aDir + u'/' + name, 'w') as fout:
                                fout.write(aDoc.file.read())

            ##            if 'a_id' in data:
            ##                if len(data['a_id']) > 0:
            ##                    c.AllAlarms.elements[data['a_id']
            ##                                         ].launch_alarm(currObject, c)
            if type not in ['t', 'd', 'v']:
                raise web.seeother('/item/' + type + '_' + currObject.getID())
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
                raise web.seeother('/find/' + type + '/' + elemtype + '_' + elemid)
        else:
            if id == 'new':
                currObject.delete(c)
            return self.getRender(connected, type, id, cond, data)

    def getRender(self, connected, type, id, errormess, data, context=''):
        if type == 'p':
            return render.place(connected, id, errormess, data, context)
        elif type == 'e':
            return render.equipment(connected, id, errormess, data, context)
        elif type == 'b':
            return render.batch(connected, id, errormess, data, context)
        elif type == 'c':
            return render.container(connected, id, errormess, data, context)
        elif type == 's':
            return render.sensor(connected, id, errormess, data)
        elif type == 'm':
            return render.measure(connected, id, errormess, data)
        elif type == 'a':
            return render.alarm(connected, id, errormess, data)
        elif type == 'al':
            return render.alarmlog(connected, id, errormess, data)
        elif type == 'gu':
            return render.group(connected, type, id, errormess, data, context)
        elif type == 'gr':
            return render.group(connected, type, id, errormess, data, context)
        elif type == 'gf':
            return render.group(connected, type, id, errormess, data, context)
        elif type == 'h':
            return render.group(connected, type, id, errormess, data, context)
        elif type == 'u':
            return render.user(connected, id, errormess, data, context)
        elif type == 'tm':
            return render.transfermodel(connected, id, errormess, data, context)
        elif type == 'dm':
            return render.manualdatamodel(connected, id, errormess, data, context)
        elif type == 'vm':
            return render.pouringmodel(connected, id, errormess, data, context)
        elif type == 't':
            return render.transfer(connected, id, errormess, data, context)
        elif type == 'd':
            return render.manualdata(connected, id, errormess, data, context)
        elif type == 'v':
            return render.pouring(connected, id, errormess, data, context)


class WebCreate(WebEdit):
    def GET(self, type):
        types = type.split('/')
        connected = redirect_when_not_allowed(types[0])

        if len(types) == 1:
            return self.getRender(connected, types[0], 'new', '', '')
        else:
            return self.getRender(connected, types[0],
                                  'new',
                                  '',
                                  '',
                                  types[-1])

    def POST(self, type):
        types = type.split('/')
        connected = redirect_when_not_allowed(types[0])

        if len(types) > 1:
            return WebEdit.POST(self,
                                types[0],
                                'new',
                                types[-1])
        else:
            return WebEdit.POST(self, types[0], 'new')


class WebPin:
    def GET(self, typeobj, idobj):
        connected = redirect_when_not_logged()
        currObject = c.getObject(idobj,typeobj)
        connected.pinit(typeobj,currObject)
        raise web.seeother('/find/related/' + typeobj + '_' + idobj)


class WebUnPin:
    def GET(self, typeobj):
        connected = redirect_when_not_logged()
        currPin = connected.pinned(typeobj)
        if currPin:
            connected.pinit(typeobj,None)
            raise web.seeother('/find/related/' + currPin)
        else:
            raise web.seeother('/')


class WebPinList:
    def GET(self):
        connected = redirect_when_not_logged()
        return render.pinlist(connected)


class WebControl:
    def GET(self, idbatch, idcontrol):
        connected = redirect_when_not_logged()

        return render.control(connected, idbatch, idcontrol, '')

    def POST(self, idbatch, idcontrol, context=None):
        connected = redirect_when_not_logged()
        user = connected.cuser
        data = web.input()
        currObject = c.getObject(idcontrol, 'h')
        cond = currObject.validate_control(data, user.fields['language'])
        if cond is True:
            currObject.create_control(data, user)
            raise web.seeother('/find/h/b_' + str(idbatch))
        else:
            return render.control(connected, idbatch, idcontrol, cond)


class WebFind:
    def GET(self, type, id1, id2):
        connected = redirect_when_not_logged()

        status = ''
        data = web.input(nifile={})
        if 'status' in data:
            status = data['status']
        allRec = type[0] == '*'
        if allRec:
            type = type[1:]
        barcode = ''
        if 'barcode' in data:
            barcode = data['barcode']
        return self.getRender(connected, type, id1, id2, barcode, status, allRec)

    def POST(self, type, id1, id2):
        connected = redirect_when_not_logged()
        user = connected.cuser
        data = web.input()
        if 'action' in data and data['action'] == 'map':
            raise web.seeother('/map/b_' + data['batch'])
        elif 'checkpoint' in data and 'batch' in data:
            allowed = user.allowed(c)
            if (" upd_d " in allowed) or (" upd_t " in allowed) or (" upd_v " in allowed):
                raise web.seeother('/control/b_' + data['batch'] +
                                   '/h_' + data['checkpoint'])
            else:
                return self.getRender(connected, type, id1, id2, '', '', False)
        return self.getRender(connected, type, id1, id2)

    def getRender(self, connected, type, id1, id2, barcode='', status='', allRec=False):
        try:
            if type == 'related':
                if id1 == 'm':
                    return render.findrelatedmeasures(connected, id2, barcode)
                elif ('g' in id1 or id1 == 'h'):
                    return render.findrelatedgroups(connected, id1, id2, barcode)
                elif id1 == 'al':
                    return render.findrelatedlogs(connected, id1, id2, barcode)
                else:
                    return render.findrelatedcomponents(connected, id1, id2, barcode)
            else:
                if type == 'd' and id1 in elsa.OBSERVABLE_TYPES:
                    return render.findlinkeddata(connected, id1, id2, None)
                elif type == 't' and id1 in elsa.TRANSFERABLE_TYPES:
                    return render.findlinkedtransfers(connected, id1, id2, None)
                elif type == 'v' and id1 in elsa.POURABLE_TYPES:
                    return render.findlinkedpourings(connected, id2, None)
                elif type == 'h':
                    return render.findcontrol(connected, id1, id2)
                elif type == 'b':
                    return render.findbatch(connected, id1, id2, status, allRec)
                elif type == 'al':
                    return render.findalarmlog(connected, id1, id2, allRec)
                else:
                    return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()


class WebFindModel:
    def GET(self, type, id1, id2, modelid):
        connected = redirect_when_not_logged()
        data = web.input()
        barcode = ''
        if 'barcode' in data:
            barcode = data['barcode']
        return self.getRender(connected, type, id1, id2, modelid, barcode)

    def getRender(self, connected, type, id1, id2, modelid, barcode=''):
        try:
            if type == 'd' and id1 in elsa.OBSERVABLE_TYPES:
                return render.findlinkeddata(connected, id1, id2, modelid)
            elif type == 't' and id1 in elsa.TRANSFERABLE_TYPES:
                return render.findlinkedtransfers(connected, id1, id2, modelid)
            elif type == 'v' and id1 in elsa.POURABLE_TYPES:
                return render.findlinkedpourings(connected, id2, modelid)
            else:
                return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()


class WebGraphic:
    def __init__(self):
        self.name = u"WebGraphic"

    def GET(self, type, id):
        connected = redirect_when_not_logged()
        if type in elsa.COMPONENT_TYPES + ['s', 'm']:
            data = web.input()
            begin = ''
            end = ''
            if 'begin' in data:
                begin = data['begin']
            if 'end' in data:
                end = data['end']
            objects = c.findAll(type)
            if objects and id and id in objects.elements.keys():
                return render.graphic(connected, type, id, begin, end)
        return render.notfound()


class WebFiles:
    def __init__(self):
        self.name = u"WebFiles"

    def GET(self, type, id):
        connected = redirect_when_not_logged()
        user = connected.cuser
        objects = c.findAll(type)
        if objects:
            elem = objects.get(id)
            if elem:
                fileList = elem.getDocumentList()
                if fileList:
                    data = web.input()
                    if 'remove' in data:
                        connected = redirect_when_not_allowed(type)
                        toRemove = data['remove']
                        if toRemove and toRemove in fileList:
                            toRemove = toRemove.replace('\\', '/')
                            name = toRemove.split('/')[-1]
                            if name:
                                aDir = elem.getDocumentDir(False)
                                if aDir:
                                    try:
                                        os.remove(aDir + u'/' + name)
                                    except:
                                        traceback.print_exc()
                        raise web.seeother('/edit/' + type + '_' + id)
                    elif len(fileList) == 1:
                        raise web.seeother(elem.getDocumentURL(fileList[0]))
                    else:
                        return render.files(connected, type, id)
        return render.notfound()


class WebMapRecipe:
    def __init__(self):
        self.name = u"WebMapRecipe"

    def GET(self, id):
        connected = redirect_when_not_logged()

        if id and id in c.AllGrRecipe.elements.keys():
            return render.maprecipe(connected, type, id)
        return render.notfound()


class WebCalendar:
    def __init__(self):
        self.name = u"WebCalendar"

    def makeMyDay(self, today, afterToday, sortedKeys, elements, before, after):
        cal = u""
        i = bisect.bisect(sortedKeys, today)
        j = bisect.bisect(sortedKeys, afterToday)
        prv_use = None
        opened = False
        for k in sortedKeys[i:j]:
            pieces = k.split('/')
            if len(pieces) >= 3:
                print pieces
                if pieces[1] != prv_use:
                    if opened:
                        cal += u")<br/>"
                    prv_use = pieces[1]
                    prv_recipe = None
                    cal += c.getHalfling(before) if before else u''
                    if pieces[1]:
                        use = pieces[1].split('_')
                        # useAll = c.findAll(use[0])
                        # cal+=c.linkedAcronym(useAll,use[1])
                        usage = c.get_object(use[0], use[1])
                        cal += usage.statusIcon(c, None, False)
                        cal += usage.fields['acronym']
                        cal += c.getHalfling(after) if after else u''
                        cal += u"("
                        opened = True
                if pieces[2] != prv_recipe:
                    prv_recipe = pieces[2]
                    if pieces[2]:
                        recipe = c.AllGrRecipe.get(pieces[2])
                        if recipe:
                            cal += recipe.fields['acronym']
                for b in elements[k]:
                    cal += "<a href=\"/find/related/b_" + b.getID() + "\" alt=\"" + b.fields[
                        'acronym'] + "\">" + b.statusIcon(c) + "</a>"
        if opened:
            cal += u")<br/>"
        return cal

    def GET(self):
        connected = redirect_when_not_logged()
        lang = connected.cuser.fields['language']

        calendarObject = calendar.HTMLCalendar(calendar.MONDAY)  # Locale is bugged

        data = web.input()
        if 'date' in data:
            refDate = data['date']
        else:
            refDate = useful.now()
        month = refDate[5:7]
        year = refDate[:4]
        rac = refDate[:7]
        quots = {}
        begs = {}
        ends = {}
        dlcs = {}
        for k, b in c.AllBatches.elements.items():
            if b.isActive() and not b.isComplete():
                recipe = "/" + b.get_group()
                t = b.get_last_transfer(c)
                use = "/"
                if t:
                    where = t.get_component(c)
                    if where:
                        use += where.getTypeId()
                    use += recipe
                    print "use=" + use
                    beg = t.getTimestring()
                    end = ""
                    if beg:
                        ##                        elapsed = self.get_quantity_string()
                        ##                        typeAlarm, symbAlarm, self.colorAlarm,self.colorTextAlarm = self.getTypeAlarm(elapsed,model)
                        planned = t.get_planned_duration(c)  # seconds
                        print("plan=" + unicode(planned))
                        if planned >= 0:
                            # planned = planned*60 WAS MINUTES
                            dBeg = useful.date_to_timestamp(beg)
                            end = useful.timestamp_to_ISO(dBeg + planned)[:10]
                        beg = beg[:10]
                        if end and beg == end:
                            if beg[:7] == rac:
                                if not end + use in quots:
                                    quots[end + use] = set()
                                quots[end + use].add(b)
                                print "quots+" + end + use
                        elif end:
                            if end[:7] == rac:
                                if not end + use in ends:
                                    ends[end + use] = set()
                                ends[end + use].add(b)
                                print "ends+" + end + use
                        elif beg[:7] == rac:
                            if not beg + use in begs:
                                begs[beg + use] = set()
                            begs[beg + use].add(b)
                            print "begs+" + beg + use
                dlc = b.fields['expirationdate']
                if dlc:
                    dlc = dlc[:10]
                    if dlc[:7] == rac:
                        if not dlc + u'/' + recipe in dlcs:
                            dlcs[dlc + u'/' + recipe] = set()
                        dlcs[dlc + u'/' + recipe].add(b)
                        print "dlcs+" + dlc + '/' + recipe
        dlcK = dlcs.keys()
        dlcK.sort()
        begK = begs.keys()
        begK.sort()
        endK = ends.keys()
        endK.sort()
        quotK = quots.keys()
        quotK.sort()
        cal = u""
        for w in calendarObject.monthdays2calendar(int(year), int(month)):
            cal += u"<tr>"
            for d in w:
                cal += "<td class=\"text-center\">"
                if not d[0]:
                    cal += u"&nbsp;"
                else:
                    cal += unicode(d[0]) + "<br/>"
                    today = rac + ('0' if d[0] < 10 else '') + "-" + unicode(d[0])
                    after = rac + ('0' if d[0] < 9 else '') + "-" + unicode(d[0] + 1)
                    cal += self.makeMyDay(today, after, endK, ends, '', '')
                    # cal += self.makeMyDay(today,after,quotK,quots,'to','from')
                    cal += self.makeMyDay(today, after, quotK, quots, '', '')
                    cal += self.makeMyDay(today, after, begK, begs, '', 'to')
                    cal += self.makeMyDay(today, after, dlcK, dlcs, 'time', '')
                cal += u"</td>"
            cal += u"</tr>"
        return render.calendar(connected, calendarObject, int(year), int(month), cal)


class WebMapBatch:
    def __init__(self):
        self.name = u"WebMapBatch"

    def GET(self, id):
        connected = redirect_when_not_logged()

        elem = c.AllBatches.get(id)
        if elem:
            return render.mapbatch(connected, elem)
        return render.notfound()


class WebGraphHelp:
    def __init__(self):
        self.name = u"WebGraphHelp"

    def GET(self, type, id):
        connected = redirect_when_not_logged()

        objects = c.findAll(type)
        return render.graphhelp(connected, type, id)


class WebGraphRecipe:
    def __init__(self):
        self.name = u"WebGraphRecipe"

    def GET(self, type, id):
        connected = redirect_when_not_logged()
        lang = connected.cuser.fields['language']
        graph = ""

        kusage = ''
        if type == 'b':
            batch = c.AllBatches.get(id)
            if batch:
                id = batch.get_group()
                place = batch.get_actual_position_here(c)
                if place:
                    kusage = place.get_group()
        elif type == 'gr':
            batch = None
        else:
            return render.notfound()

        elem = c.AllGrRecipe.get(id)
        if elem:
            summit = [id] + elem.get_supermap_str()
            usagesTop = c.AllGrUsage.get_usages_for_recipe(summit)
            prec = ""
            stack = []
            start_u = None
            for krecipe in summit:
                if krecipe == '>>':
                    stack.append(prec)
                elif krecipe == '<<':
                    prec = stack.pop()
                else:
                    recipe = c.AllGrRecipe.get(krecipe)
                    if recipe:
                        if prec:
                            graph += 'xgr_' + krecipe + '->xgr_' + prec + '[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];'
                        graph += 'xgr_' + krecipe
                        graph += "[labelType=\"html\",label=\"<a href=/find/related/gr_" + krecipe + ">" + recipe.getNameHTML(
                            lang) + "</a>\""
                        graph += ",tooltip=\"" + recipe.fields['acronym'] + "\""
                        graph += ",id=\"xgr_" + krecipe + "\",shape=ellipse,style=\"fill:" + (
                            "#fbcfaa" if krecipe == id else "#fff") + ";stroke:1px;\"];"
                        if recipe.fields['gu_id']:
                            start_u = recipe.fields['gu_id']
                            graph += "xgr_" + krecipe + "->gu_" + start_u + "[style=\"stroke-width:3px;stroke:#3d3\"];"
                    prec = krecipe
            recipes_todo = set()
            next_usage = []
            done = set()
            prec_u = ""
            for usageTop in usagesTop:
                usaTopID = 'gu_' + usageTop.getID()
                if prec_u:
                    # graph += prec_u+"->"+usaTopID+"[style=\"stroke-width:0px;stroke:#fff\"];"
                    next_usage.append(prec_u + " " + usaTopID)
                prec_u = usaTopID
            for usageTop in usagesTop:
                usaTopID = 'gu_' + usageTop.getID()
                graph += usaTopID  # +"[url=\"/find/related/"+usaTopID+"\""
                graph += "[labelType=\"html\",label=\"<a href=/find/related/" + usaTopID + ">" + usageTop.getNameHTML(
                    lang) + "</a>"
                components = usageTop.get_members()
                if components:
                    graph += ':'
                    for i in range(len(components)):
                        if i >= 2:
                            graph += " +"+unicode(len(components)-2)
                            break
                        #+ components[i].getGlyph(c)
                        graph += " <a href=/find/related/" + components[i].getTypeId() + ">" + components[i].getGlyph(c) + components[i].getNameHTML(lang) + "</a>"
                # ,labelStyle=\"font-family:'Glyphicons Halflings'\"
                graph += "\",tooltip=\"" + usageTop.fields['acronym'] + "\""
                graph += ",id=\"" + usaTopID + "\",shape=diamond,style=\"fill:" + (
                    "#fbcfaa" if kusage == usageTop.getID() else "#fff") + ";stroke:1px;\"];"

                checkpoints = c.AllCheckPoints.get_checkpoints_for_recipe_usage(summit, [usageTop.getID()])
                prec_v = ""
                for v in checkpoints:
                    # print "h="+v.getID()
                    hid = "h_" + v.getID()
                    if v.getID() not in done:
                        if not prec_v:
                            graph += usaTopID + '->' + hid + "[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
                        ##                                if v.fields['gr_id'] != id:
                        ##                                    graph += "gr_"+v.fields['gr_id']+'->'+hid+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
                        elems = v.get_model_sorted()
                        obs = ""
                        for e in elems:
                            if e.get_type() == 'tm':
                                nx_usage = e.fields['gu_id']
                                if nx_usage == '0':
                                    nx_usage = start_u
                                if nx_usage:
                                    graph += hid + "->" + "gu_" + nx_usage + "[style=\"stroke-width:3px\""
                                    if batch:
                                        events = batch.fromModel(c, e)
                                        if len(events) > 0:
                                            graph += ",labelType=\"html\",label=\"<a href=/find/t/b_" + batch.getID() + "/" + e.getID() + ">" + unicode(
                                                len(events)) + " x</a>\""
                                    elif 'typical' in e.fields and e.fields['typical']:
                                        graph += ",label=\"" + c.seconds_to_string(int(e.fields['typical']),
                                                                                   lang) + "\""
                                    graph += "];"
                                    points = usaTopID + " " + "gu_" + nx_usage
                                    # print points+" in "+unicode(next_usage)
                                    if points in next_usage:
                                        next_usage.remove(points)
                            elif e.get_type() == 'vm':
                                v_recipe = None
                                if e.fields['dest']:
                                    nx_recipe = e.fields['dest']
                                    v_recipe = c.AllGrRecipe.get(nx_recipe)
                                    if v_recipe:
                                        graph += hid + "->" + "gr_" + nx_recipe
                                if e.fields['src']:
                                    nx_recipe = e.fields['src']
                                    v_recipe = c.AllGrRecipe.get(nx_recipe)
                                    if v_recipe:
                                        graph += "gr_" + nx_recipe + "->" + hid
                                if v_recipe:
                                    graph += "[style=\"stroke-width:3px;stroke:#f07e26\",labelType=\"html\",label=\""
                                    events = []
                                    if batch:
                                        events = batch.fromModel(c, e)
                                    if len(events) == 0:
                                        graph += unicode(e.get_quantity()) + ' ' + protectJS(
                                            e.get_unit_in_context(c, elem))
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
                                                graph += "<a href=/edit/v_" + ev.getID() + ">" + (
                                                    "<font color=" + Acolor + ">" if Acolor else "")
                                                graph += unicode(qtity) + " " + protectHTML(
                                                    ev.get_unit_in_context(c, elem)) + (
                                                             "</font>" if Acolor else "") + "</a>"
                                                first = False
                                    graph += "\"];"
                                    recipes_todo.add(v_recipe)
                            elif e.get_type() == 'dm':
                                obs += u"<br>" + e.getNameHTML(lang)
                                events = []
                                if batch:
                                    events = batch.fromModel(c, e)
                                if len(events) == 0:
                                    target = "?"
                                    if e.fields['typical']:
                                        target = e.fields['typical']
                                    measure = e.get_measure(c)
                                    if measure:
                                        obs += u" / " + measure.getNameHTML(lang) + ": " + target + " " + protectHTML(
                                            measure.fields['unit'])
                                    else:
                                        obs += ": " + target
                                else:
                                    first = True
                                    for edata in events:
                                        Acolor = None
                                        qtity = edata.get_quantity()
                                        if qtity:
                                            # qt = float(qtity)
                                            Aname, Aacronym, Acolor, Atext_color = e.getTypeAlarm(qtity, None)
                                            if Aname == 'typical':
                                                Acolor = None
                                            obs += (": " if first else ", ")
                                            obs += "<a href=/edit/d_" + edata.getID() + ">" + (
                                                "<font color=" + Acolor + ">" if Acolor else "")
                                            obs += unicode(qtity) + " " + protectHTML(edata.get_unit(c)) + (
                                                "</font>" if Acolor else "") + "</a>"
                                            first = False
                        graph += hid  # +"[url=\"/find/related/"+hid+"\""
                        graph += "[labelType=\"html\",label=\"<a href=/find/related/" + hid + ">"
                        ##                        ext = v.isImaged()
                        ##                        if ext:
                        ##                            graph += "<img scale=both src="+self.getImageURL(ext)+">"
                        if batch and v.getID() in batch.checkpoints:
                            graph += "* "
                        graph += v.getNameHTML(lang)
                        graph += "</a>" + obs + "\""  # +v.fields['rank']
                        graph += ",tooltip=\"" + v.fields['acronym'] + "\""
                        graph += ",id=\"" + hid + "\"];"
                        if prec_v:
                            graph += "h_" + prec_v + '->' + hid + "[style=\"stroke-width:3px;stroke:#888\"];"
                        prec_v = v.getID()
                        done.add(prec_v)
            for remain in next_usage:
                points = remain.split(" ")
                graph += points[0] + "->" + points[
                    1] + "[style=\"stroke-width:1px;stroke-dasharray:3,12;stroke:#888;\"];"
            for recipe in recipes_todo:
                ##                if not recipe.getID() in summit:
                grID = "gr_" + recipe.getID()
                ##                    for above in recipe.parents:
                ##                        if above in summit:
                ##                            graph += "xgr_"+above+"->"+grID+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
                graph += grID
                graph += "[labelType=\"html\",label=\"<a href=/find/related/" + grID + ">" + recipe.getNameHTML(
                    lang) + "</a>\""
                graph += ",tooltip=\"" + recipe.fields['acronym'] + "\""
                graph += ",id=\"" + grID + "\",shape=ellipse,style=\"fill:#fff;stroke:1px;\"];"
            ##            for usage in usages:
            ##                    usaID = 'gu_'+usage.getID()
            ##                    for parent in usage.parents:
            ##                        usage = c.AllGrUsage.elements[parent]
            ##                        aboveID = 'gu_'+parent
            ##                        graph += aboveID+"->"+usaID+"[style=\"stroke-width:1px;stroke-dasharray:5,5;\"];"
            return render.graphrecipe(connected, batch, id, graph)
        return render.notfound()


##class WebGraphBatch:
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

class WebMapFunctions:
    def __init__(self):
        self.name = u"WebMapFunctions"

    def GET(self):
        connected = redirect_when_not_logged()
        return render.mapfunctions(connected)


class WebMapComponents:
    def __init__(self):
        self.name = u"WebMapComponents"

    def GET(self):
        connected = redirect_when_not_logged()
        return render.mapcomponents(connected)


class WebMapUsages:
    def __init__(self):
        self.name = u"WebMapUsages"

    def GET(self):
        connected = redirect_when_not_logged()
        return render.mapusages(connected)


class WebMapRecipes:
    def __init__(self):
        self.name = u"WebMapRecipes"

    def GET(self):
        connected = redirect_when_not_logged()
        return render.maprecipes(connected, False)


class WebMapCheckPoints:
    def __init__(self):
        self.name = u"WebMapCheckPoints"

    def GET(self):
        connected = redirect_when_not_logged()
        return render.mapcheckpoints(connected)


class WebRRDfetch:
    def __init__(self):
        self.name = u"WebRRDfetch"

    def GET(self, id):
        connected = redirect_when_not_logged()
        data = web.input(nifile={})
        period = None
        if 'period' in data:
            period = data['period']

        currSensor = c.AllSensors.get(id)
        if currSensor:
            web.header('Content-Disposition',
                       'attachment; filename="s_' + str(id) + '.csv"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            return currSensor.fetchRRD(period)
        return render.notfound()


class WebIndex:
    def __init(self):
        self.name = u"WebIndex"

    def GET(self):
        data = web.input(nifile={})
        # Incomplete NFC reference !
        if 'uid' in data and data['uid']:
            raise web.seeother('/nfc?uid='+data['uid'])
        connected = isConnected()
        if connected is None:
            return render.index(connected)
        data = web.input(nifile={})
        if 'completeMenu' in data:
            connected.completeMenu = data['completeMenu'] == '1'
        return self.getRender(connected)

    def POST(self):
        data = web.input(nifile={})
        connectedUser = checkUser(data._username_, data._password_)
        if connectedUser is not None:
            connected = c.connectedUsers.addUser(connectedUser)
            ensureLogin(connectedUser.fields['mail'].lower())

            query_string = web.ctx.env.get('QUERY_STRING')
            redirect_url = useful.parse_url_query_string(query_string, 'redir')
            print redirect_url
            if (redirect_url is not None):
                raise web.seeother(redirect_url)
            else:
                return self.getRender(connected)
        return render.index(None)

    def getRender(self, connected):
        return render.maprecipes(connected, True)


class WebSearch:
    def __init__(self):
        self.name = u"WebSearch"

    def GET(self):
        connected = redirect_when_not_logged()

        try:
            barcode = ''
            remark = ''
            data = web.input()
            if 'search' in data:
                barcode = data['search'].strip()
                # Remove the scanner prefix if it falled through (scan in a readily opened search box)
                if barcode and barcode[0]=='`':
                    barcode = barcode[1:]
            if 'remark' in data:
                remark = data['remark']
                if remark and remark.lower() in ['0', 'off', 'no', '-']:
                    remark = 'YES'
            if barcode:
                elem = c.AllBarcodes.barcode_to_item(barcode)
                if elem:
                    raise web.seeother('/find/related/' + elem.getTypeId() + '?barcode=' + barcode)
                else:
                    listElem = c.search_acronym(barcode, [])
                    endAcro = len(listElem)
                    listElem = c.search_names(barcode, listElem)
                    endName = len(listElem)
                    if remark:
                        listElem = c.search_remark(barcode, listElem)
                    if len(listElem) > 0:
                        if len(listElem) == 1:
                            raise web.seeother('/find/related/' + listElem[0].getTypeId() + '?barcode=' + barcode)
                        else:
                            return render.searchlist(connected, barcode, listElem, endAcro, endName)
                    else:
                        return render.search(connected, barcode, 'errorbarcode')
            else:
                return render.search(connected, barcode, 'emptybarcode')
        except:
            traceback.print_exc()
            return render.search(connected, barcode, 'emptybarcode')


class WebLabel:
    def __init__(self):
        self.name = u"WebLabel"

    def GET(self, type, id="", children=""):
        connected = redirect_when_not_logged()
        return render.label(connected, type, id, children)


class WebNFC:
    def __init__(self):
        self.name = u"WebNFC"

    def GET(self, type="", id=""):
        connected = redirect_when_not_logged()
        user = connected.cuser
        try:
            nfc_uid = ''
            data = web.input()
            if 'uid' in data:
                nfc_uid = data['uid'].strip()
            else:
                nfc_uid = connected.nfc
            if nfc_uid:
                connected.nfc = nfc_uid
                if type and id:
                    elem = c.get_object(type,id)
                    oldelem = c.AllBarcodes.barcode_to_item(nfc_uid,"N")
                    if elem != oldelem:
                        if oldelem:
                            c.AllBarcodes.delete_barcode(nfc_uid, "N", user)
                        c.AllBarcodes.add_barcode(elem, nfc_uid, "N", user)
                else:
                    elem = c.AllBarcodes.barcode_to_item(nfc_uid, "N")
                if elem:
                    raise web.seeother('/find/related/' + elem.getTypeId() + '?barcode=' + nfc_uid)
        except:
            traceback.print_exc()
        return render.search(connected, nfc_uid, 'nfcunknown')


class getRRD:
    def GET(self, filename):
        with open(elsa.DIR_RRD + filename) as f:
            try:
                return f.read()
            except IOError:
                web.notfound()


class getCSV:
    def GET(self, filename):
        with open(elsa.DIR_DATA_CSV + filename) as f:
            try:
                return f.read()
            except IOError:
                web.notfound()


class getDoc:
    def GET(self, filename):
        with open(elsa.DIR_DOC + filename) as f:
            try:
                return f.read()
            except IOError:
                web.notfound()


class WebExport:
    def GET(self, type, id):
        connected = redirect_when_not_logged()
        return self.getRender(connected, type, id)

    def POST(self, type, id):
        connected = redirect_when_not_logged()
        user = connected.cuser
        data = web.input()
        cond = {}
        cond['alarm'] = True if 'alarm' in data else False
        cond['manualdata'] = True if 'manualdata' in data else False
        cond['transfer'] = True if 'transfer' in data else False
        cond['pouring'] = True if 'pouring' in data else False
        cond['specialvalue'] = True if 'specialvalue' in data else False
        cond['valuesensor'] = True if 'valuesensor' in data else False
        cond['acronym'] = True if 'acronym' in data else False
        splits = data['element'].split('_')
        elem = c.get_object(splits[0], splits[1])
        tmp = elsa.ExportData(c, elem, cond, user)
        tmp.create_export()
        if "download" in data:
            tmp.write_csv()
            raise web.seeother('/export/' + str(type) +
                               '_' + str(id) + '/exportdata.csv')
        else:
            user.exportdata = tmp
            raise web.seeother('/datatable/' + str(type) + '_' + str(id))

    def getRender(self, connected, type, id):
        try:
            if type in elsa.OBSERVABLE_TYPES:
                return render.exportdata(connected, type, id)
            else:
                return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()


class WebDataTable:
    def GET(self, type, id):
        connected = redirect_when_not_logged()
        return self.getRender(connected, type, id)

    def getRender(self, connected, type, id):
        # try:
        if type in elsa.TRANSFERABLE_TYPES:
            return render.datatable(connected, type, id)
        else:
            return render.notfound()
        """except :
            return render.notfound()"""


class WebDownloadData:
    def GET(self, id1, id2, filename):
        try:
            f = open(elsa.DIR_DATA_CSV + filename)
            web.header('Content-Disposition',
                       'attachment; filename="' + str(filename) + '"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            return f.read()
        except IOError:
            web.notfound()
        finally:
            f.close()


class WebTest:
    def __init__(self):
        self.name = u"WebTest"

    def GET(self):
        connected = redirect_when_not_admin(True)
        acro = "TEST"
        data = web.input()
        if 'acronym' in data:
            acro = data['acronym']

        testUrls = ['/', '/index',
                    '/api/grafana/en/request',  # Only POST really exercices Grafana API...
                    #            '/disconnect',
                    '/backup',
                    '/restore',
                    '/updateELSA',
                    #            '/restarting',
                    '/map/gf',
                    '/map/gu',
                    '/map/pec',
                    '/map/h',
                    '/map/gr',
                    '/unpin/h',
                    '/graphhelp/b_1',
                    '/calendar',
                    '/nfc?uid=04715C7A894981',
                    '/api/kv?M=1&T',
                    '/search']
        #            '/rrd/(.+)',
        #            '/csv/(.+)',
        #            '/doc/(.+)',
        for someType in elsa.ALL_NAMED_TYPES:
            testUrls.extend(['/list/' + someType, '/create/' + someType])
        result = []
        result = c.search_acronym(acro, result)
        for aTest in result:
            ti = aTest.getTypeId()
            if aTest.get_type() == 'b':
                testUrls.extend(['/clone/' + ti,
                                 '/export/' + ti,
                                 '/datatable/' + ti,
                                 '/pin/' + ti,
                                 '/unpin/b',
                                 '/map/' + ti,
                                 '/create/v/' + ti + "_in",
                                 '/create/v/' + ti + "_out",
                                 '/find/v/' + ti,
                                 '/create/t/' + ti,
                                 '/find/t/' + ti,
                                 '/create/d/' + ti,
                                 '/find/d/' + ti,
                                 '/find/h/' + ti,
                                 '/find/al/' + ti,
                                 '/graph/' + ti])
                testControl, recipes, usages = aTest.get_allowed_checkpoints(c)
                if testControl:
                    for aControl in testControl:
                        testUrls.extend(['/control/' + ti + '/' + aControl.getTypeId()])
                testV = aTest.get_events(c)
                if testV:
                    for aRec in testV:
                        testUrls.extend(['/edit/' + aRec.getTypeId(),
                                         '/history/' + aRec.getTypeId(),
                                         '/modal/' + aRec.getTypeId(),
                                         '/fullentry/' + aRec.getTypeId(),
                                         '/item/' + aRec.getTypeId()])
            elif aTest.get_type() == 'gr':
                testUrls.extend(['/map/' + ti,
                                 '/selectmul/' + aTest.get_type() + '_new/' + aTest.getID(),
                                 '/selectmul/' + ti + '/',
                                 '/select/group/' + ti,
                                 '/create/gr/' + ti,
                                 '/create/b/' + ti,
                                 '/create/h/' + ti,
                                 '/graph/' + ti])
            elif aTest.get_type() == 'gu':
                testUrls.extend(['/select/group/' + ti,
                                 '/create/gu/' + ti,
                                 '/create/p/' + ti,
                                 '/create/e/' + ti,
                                 '/create/c/' + ti,
                                 '/create/h/' + ti])
            elif aTest.get_type() == 'gf':
                testUrls.extend(['/select/group/' + ti,
                                 '/create/gf/' + ti,
                                 '/create/u/' + ti])
            elif aTest.get_type() == 'h':
                testUrls.extend(['/select/group/' + ti,
                                 '/pin/' + ti,
                                 '/create/vm/' + ti,
                                 '/create/tm/' + ti,
                                 '/create/dm/' + ti,
                                 '/create/h/' + ti])
            elif aTest.get_type() in elsa.COMPONENT_TYPES + ['s']:
                testUrls.extend(['/label/' + ti,
                                 '/find/al/' + ti,
                                 '/graphic/' + ti])
                if aTest.get_type() == 's':
                    testUrls.append('/rrdfetch/' + ti)
                else:
                    if aTest.get_type() in ["c", "e"]:
                        testUrls.append('/find/t/' + ti)
                        testUrls.append('/pin/' + ti)
                    testUrls.extend(['/find/d/' + ti,
                                     '/color/' + ti])
            testUrls.extend(['/edit/' + ti,
                             '/item/' + ti,
                             '/find/related/' + ti,
                             '/history/' + ti,
                             '/files/' + ti,
                             '/nfc/' + ti,
                             '/modal/' + ti,
                             '/fullentry/' + ti])
        testUrls.append('/pinlist')
        testUrls.append('/unpin/p')
        testUrls.append('/nfc?uid=04715C7A894981')
        return render.test(connected, testUrls)


def checkUser(username, password):
    user = c.AllUsers.getUser(username)
    if user is None:
        return None

    cryptedPassword = useful.encrypt(password, user.fields['registration'])
    if user.checkPassword(cryptedPassword) is True:
        return user


# returns connnectedUser object
def isConnected():
    infoCookie = web.cookies().get('akuinoELSA')
    if infoCookie is None:
        return None

    infoCookie = infoCookie.split(',')
    if len(infoCookie) > 1:
        connected = c.connectedUsers.isConnected(infoCookie[0].lower(), infoCookie[1])
        return connected
    return None


def ensureLogin(mail):
    current = c.connectedUsers.users[mail]
    user = current.cuser
    if user and user.isActive():
        infoCookie = mail + ',' + user.fields['password'] + ',' + ('1' if current.completeMenu else '0')
        web.setcookie('akuinoELSA', infoCookie, expires=9000)


def notfound():
    return web.notfound(render.notfound())


def cleanup_web_temp_dir():
    try:
        shutil.rmtree(elsa.DIR_WEB_TEMP)
    except OSError, e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
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
            raise ("Invalid value received : expected bool")

    def set_restart_elsa(self):
        self._restart_elsa = True

    def set_shutdown(self):
        self._shutdown = True

    def set_restart(self):
        self._restart = True

    def launch_end_activities(self):
        if self._restore:
            # returns False if restore did not work but no way to alert the user !
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

    global c, wsgiapp, render, includes, app
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
        web.template.Template.globals['unicode'] = unicode
        web.template.Template.globals['useful'] = useful
        web.template.Template.globals['bisect'] = bisect
        web.template.Template.globals['round'] = round
        web.template.Template.globals['subprocess'] = subprocess
        layout = web.template.frender(elsa.TEMPLATES_DIR + '/layout.html')
        render = web.template.render(elsa.TEMPLATES_DIR, base=layout)
        includes = web.template.render(elsa.TEMPLATES_DIR + '/includes')
        web.template.Template.globals['includes'] = includes
        urls = (
            '/', 'WebIndex',
            '/index', 'WebIndex',
            '/edit/(.+)_(.+)', 'WebEdit',
            '/item/(.+)_(.+)', 'WebItem',
            '/history/(.+)_(.+)', 'WebHistory',
            '/create/(.+)', 'WebCreate',
            '/rrd/(.+)', 'getRRD',
            '/csv/(.+)', 'getCSV',
            '/doc/(.+)', 'getDoc',
            '/list/(.+)', 'WebList',
            '/clone/(.+)_(.+)', 'WebClone',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/files/(.+)_(.+)', 'WebFiles',
            '/graphhelp/(.+)_(.+)', 'WebGraphHelp',
            '/map/b_(.+)', 'WebMapBatch',
            '/map/gr_(.+)', 'WebMapRecipe',
            '/graph/(.+)_(.+)', 'WebGraphRecipe',
            '/map/gf', 'WebMapFunctions',
            '/map/gu', 'WebMapUsages',
            '/map/pec', 'WebMapComponents',
            '/map/h', 'WebMapCheckPoints',
            '/map/gr', 'WebMapRecipes',
            '/calendar', 'WebCalendar',
            '/label/(.+)_(.+)/(.+)', 'WebLabel',
            '/label/(.+)_(.+)', 'WebLabel',
            '/label/(.+)', 'WebLabel',
            '/search', 'WebSearch',
            '/modal/(.+)_(.+)', 'WebModal',
            '/color/(.+)_(.+)', 'WebColor',
            '/fullentry/(.+)_(.+)', 'WebFullEntry',
            '/export/(.+)_(.+)/(.+)', 'WebDownloadData',
            '/export/(.+)_(.+)', 'WebExport',
            '/rrdfetch/(.+)', 'WebRRDfetch',
            '/datatable/(.+)_(.+)', 'WebDataTable',
            '/find/(.+)/(.+)_(.+)/(.+)', 'WebFindModel',
            '/find/(.+)/(.+)_(.+)', 'WebFind',
            '/pin/(.+)_(.+)', 'WebPin',
            '/unpin/(.+)', 'WebUnPin',
            '/pinlist', 'WebPinList',
            '/selectmul/(.+)_(.+)/(.*)', 'WebSelectMul',
            '/select/(.+)/(.+)', 'WebSelect',
            '/control/b_(.+)/h_(.+)', 'WebControl',
            '/disconnect', 'WebDisconnect',
            '/backup', 'WebBackup',
            '/restore', 'WebRestore',
            '/updateELSA', 'WebUpdateELSA',
            '/restarting', 'WebRestarting',
            '/api/grafana/([^/]*)/{0,1}(.*)', 'WebApiGrafana',
            '/api/grafana', 'WebApiGrafana',
            '/api/kv', 'WebApiKeyValue',
            '/nfc/(.+)_(.+)', 'WebNFC',
            '/nfc', 'WebNFC',
            '/test', 'WebTest'
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
            c.TimerThread.join()

        flags.launch_end_activities()

        print 'Exit system'


if __name__ == "__main__":
    main()
