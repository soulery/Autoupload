import urllib2, urllib
import json
import os
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

"""
Copyright (c) 2013 Citrix Systems, Inc.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

"""
The functions in this file will make use of the ShareFile API to perform some
of the basic operations.  Please see api.sharefile.com for more information.

Functions were tested with Python 2.7.3

Requirements:

poster module for multipart/form upload, see http://pypi.python.org/pypi/poster/

Optional parameters can be passed to functions as a dictionary as follows:

ex:

users_create('mysubdomain', 'mytopleveldomain', 'myauthid',          # required parameters
             'firstname', 'lastname', 'an@email.address', False,     # required parameters
             {'company':'ACompany',                                  # optional parameter
              'password':'Apassword',
              'notify':True,
              'canviewmysettings':False})

See api.sharefile.com for optional parameter names for each operation.
"""

def authenticate(subdomain, tld, username, password):
    """Calls getAuthID to retrieve an authid that will be used for subsequent calls to API.

    If you normally login to ShareFile at an address like https://mycompany.sharefile.com
    then you will call this function like:

    authenticate('mycompany', 'sharefile.com', 'my@user.name', 'mypassword')

    and you will be returned an authid or in the case of failure None.  The error code
    and error message will also be output.

    Args:
        string subdomain
        string tld
        string username
        string password
    Return:
        an authId string or None if failure
    """

    # parameter dictionary
    url_params = {'username':username, 'password':password, 'fmt':'json'}

    # construct url
    url = 'https://%s.%s/rest/getAuthID.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))

    authid = None

    try:
        response = json.loads(urllib2.urlopen(url).read())
        # the response will either be returned with errod=False (no error) and include
        # a value, or error=True and include an errorCode and errorMessage
        if not response['error']:
            authid = response['value']
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])
    except urllib2.HTTPError as ex_http:
        print ex_http

    print "auth successed"
    return authid

def folder_list(subdomain, tld, authid, path='/'):
    """ Prints out a folder list for the specified path or root if none is provided.

    Currently prints out id, filename, creationdate, type.  Uncomment the 'print response'
    line to see the entire response.

    Args:
        string subdomain
        string tld
        string authid
        string path folder to list
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'list', 'path':path}

    url = 'https://%s.%s/rest/folder.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))

    try:
        response = json.loads(urllib2.urlopen(url).read())

        if not response['error']:
            #print response
            for item in response['value']:
                print '%s %s %s %s'%(item['id'], item['filename'], item['creationdate'], item['type'])
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http


def file_upload(subdomain, tld, authid, filepath, optional_params = {}):
    """ Upload a file to ShareFile.  Requires poster module http://pypi.python.org/pypi/poster/

    Args:
        string subdomain
        string tld
        string authid
        string filepath complete path to local file to upload
        dictionary optional_parameters see api.sharefile.com for optional parameter names
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'upload', 'filename':os.path.basename(filepath)}
    url_params.update(optional_params)

    url = 'https://%s.%s/rest/file.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))

    register_openers()

    try:
        response = json.loads(urllib2.urlopen(url).read())

        if not response['error']:
            upload_url = response['value']

            datagen, headers = multipart_encode({'File1':open(filepath, 'rb')})
            request = urllib2.Request(upload_url, datagen, headers)
            print 'Starting upload...'
            upload_response = urllib2.urlopen(request)
            print upload_response.read()
            print 'Upload complete.'
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http

def file_download(subdomain, tld, authid, fileid, localpath):
    """ Downloads a file from ShareFile.

    Args:
        string subdomain
        string tld
        string authid
        string fileid id of the file to download
        string localpath complete path to download file to including filename
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'download', 'id':fileid}

    url = 'https://%s.%s/rest/file.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))
    print url

    try:
        response = json.loads(urllib2.urlopen(url).read())
        if not response['error']:
            downloadurl = response['value']

            source = urllib2.urlopen(downloadurl)
            target = open(localpath, 'wb')

            while True:
                chunk = source.read(8192)
                if not chunk:
                    break
                target.write(chunk)

            target.close()
            print 'Done downloading.'
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http


def file_send(subdomain, tld, authid, path, to, subject, optional_parameters = {}):
    """ Sends a Send a File email.

    Args:
        string subdomain
        string tld
        string authid
        string path path to file in ShareFile to send
        string to email address to send to
        string subject email subject of the email
        dictionary optional_parameters see api.sharefile.com for optional parameter names
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'send', 'path':path, 'to':to, 'subject':subject}
    url_params.update(optional_parameters)

    url = 'https://%s.%s/rest/file.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))
    print url

    try:
        response = json.loads(urllib2.urlopen(url).read())
        if not response['error']:
            print response
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http


def users_create(subdomain, tld, authid, firstname, lastname, email, isemployee, optional_parameters = {}):
    """ Create a client or employee user in ShareFile.

    Args:
        string subdomain
        string tld
        string authid
        string firstname
        string lastname
        string email
        boolean isemployee true to create an employee, false to create a client
        dictionary optional_parameters see api.sharefile.com for optional parameter names
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'create', 'firstname':firstname, 'lastname':lastname, 'email':email, 'isemployee':isemployee}
    url_params.update(optional_parameters)

    url = 'https://%s.%s/rest/users.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))
    print url

    try:
        response = json.loads(urllib2.urlopen(url).read())
        if not response['error']:
            print response
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http


def group_create(subdomain, tld, authid, name, optional_parameters = {}):
    """ Create a distribution group in ShareFile.

    Ex: to create a group and add users to it at the same time

    group_create('mysubdomain', 'mytld', 'myauthid',         # required parameters
                 'mygroupname',                              # required parameters
                 {'isshared':True,
                  'contacts':
                      ['user@email.address','another@email.address']}) # optional parameters

    Args:
        string subdomain
        string tld
        string authid
        string name
        dictionary optional_parameters see api.sharefile.com for optional parameter names
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'create', 'name':name}

    if 'contacts' in optional_parameters:
        optional_parameters['contacts'] = ','.join(optional_parameters['contacts'])

    url_params.update(optional_parameters)

    url = 'https://%s.%s/rest/group.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))
    print url

    try:
        response = json.loads(urllib2.urlopen(url).read())
        if not response['error']:
            print response
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http

def search(subdomain, tld, authid, query, optional_parameters = {}):
    """ Search for items in ShareFile.

    Args:
        string subdomain
        string tld
        string authid
        string query
        dictionary optional_parameters see api.sharefile.com for optional parameter names
    """
    url_params = {'authid':authid, 'fmt':'json', 'op':'search', 'query':query}
    url_params.update(optional_parameters)

    url = 'https://%s.%s/rest/search.aspx?%s'%(subdomain, tld, urllib.urlencode(url_params))
    print url

    try:
        response = json.loads(urllib2.urlopen(url).read())
        if not response['error']:
            print response
            for item in response['value']:
                path = '/'
                if item['parentid'] == 'box':
                    path = '/File Box'
                else:
                    path = item['parentsemanticpath']
                print '%s/%s %s %s'%(path, item['filename'], item['creationdate'], item['type'])
        else:
            print 'Error %d : %s'%(response['errorCode'], response['errorMessage'])

    except urllib2.HTTPError as ex_http:
        print ex_http

if __name__ == '__main__':
    authid = authenticate('citrix', 'sharefile.com', 'hao.wu@citrix.com', 'adminIWSS85')
    if authid:

        #folder_list('citrix', 'sharefile.com', authid,'hao.wu@citrix.com')
        folder_list('citrix', 'sharefile.com', authid,'File box')
        #file_upload('citrix', 'sharefile.com', authid,'c:\\2860728E1.pdf')
        file_send('citrix', 'sharefile.com', authid,'File box\\2860728E1.pdf', 'hao.wu@citrix.com', 'pdf test')