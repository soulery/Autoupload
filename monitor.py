from smb.SMBConnection import SMBConnection
import shutil
import subprocess
import time
import os
import errno
import zipfile
import ConfigParser
import sharefile as sf
import urllib
import urllib2
import re
import thread
import shutil
from BeautifulSoup import BeautifulSoup as bs

def run_windows_command(cmd):
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while p.poll() == None:
    # We can do other things here while we wait
        time.sleep(1)
        p.poll()
    print p.communicate()

def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, ".."))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def establish_dir(directory,txt):
    f= open(txt,"w+")
    dirlist = os.listdir(directory)
    for item in dirlist:
        path = directory+"\\"+item
        if os.path.isdir(path):
            path = path +"\n"
            f.write(path)
    f.close()

def turn_dir_into_list(filename):
    filelist = []
    f = open(filename,"r")
    for line in f:
        line = line.strip("\n")
        filelist.append(line)
    f.close()
    return filelist

def download_apps_from_cifs(directory,basefilename,apptype):
    changed = False
    filelist = turn_dir_into_list(basefilename)
    dirlist = os.listdir(directory)
    for item in dirlist:
        path = directory+"\\"+item
        if os.path.isdir(path):
            if path not in filelist:
                upload_build(directory,item,apptype)
                changed= True

    if changed:
        establish_dir(directory,basefilename) #create new baseline
    else:
        print "Nothing has changed or there is a file lock"

def check_lock():
    lockfile = "lock.txt"
    if os.path.exists(lockfile):
        return False
    else:
        f = open(lockfile,"w")
        f.close
        return True

def http_or_cifs(link):
    pattern = "http"
    if pattern in link:
        return True
    else:
        return False

def upload_to_sharefile(zipfile_name,sharefile_name,build,appname):
    authid = sf.authenticate('citrix', 'sharefile.com', 'hao.wu@citrix.com', 'adminIWSS85')
    if authid:
        sf.file_upload('citrix', 'sharefile.com', authid, zipfile_name)

    #Step 6 Send file by mail
    sharefile_mail_title = "["+appname+"] Build "+str(build)+" download link"
    sf.file_send('citrix', 'sharefile.com', authid, sharefile_name, 'hao.wu@citrix.com', sharefile_mail_title)


def get_ios_build(str):
    array=str.split('.ipa')
    build = array[0].split('-')
    return build[4]

def upload_to_njrdfs1(app_name,new_dir,directory):

    if app_name == "WorxWeb_iOS":
        create_dir(new_dir)
        copy_cmd_app = "xcopy /S /Y "+directory+"*.ipa "+new_dir
        run_windows_command(copy_cmd_app)

    elif app_name == "WorxMail_iOS":
        create_dir(new_dir)
        copy_cmd_app = "xcopy /S /Y "+directory+"*.ipa "+new_dir
        run_windows_command(copy_cmd_app)

    elif app_name == "WorxWeb_wp":
        create_dir(new_dir)
        run_windows_command(copy_cmd_web)
        copy_cmd_app = "xcopy /S /Y "+directory+"\WorxWeb*.mdx "+new_dir
        run_windows_command(copy_cmd_app)

    elif app_name == "WorxMail_wp":
        create_dir(new_dir)
        copy_cmd_app = "xcopy /S /Y "+directory+"\WorxMail*.mdx "+new_dir
        run_windows_command(copy_cmd_app)

    elif app_name == "WorxWeb_Android":
        create_dir(new_dir)
        copy_cmd_app = "xcopy /S /Y "+directory+"\*release.apk "+new_dir
        run_windows_command(copy_cmd_app)

    elif app_name == "WorxMail_Android":
        create_dir(new_dir)
        copy_cmd_app = "xcopy /S /Y "+directory+"\*release.apk "+new_dir
        run_windows_command(copy_cmd_app)

    else:
        print "Not supported app in upload"


def upload_build(download_link, build, apptype):

    if check_lock():
        changed = True
        #sccm_build_directory = "X:\\Layouts\\sccm\\loki\\base\\"
        lockfile = "lock.txt"
        desktop = "C:\\Users\\administrator\\Desktop\\"
        directory = desktop + str(build)

        if apptype == "ipa": #IOS build is downloaded by HTTP
            urllib.urlretrieve (download_link, directory)
            zipfile_name =  desktop + build
            sharefile_name = "File box\\" + build
            worxweb = "WorxWeb"
            worxmail = "WorxMail"
            if worxweb in download_link:
                app_name =  "WorxWeb_iOS"
                ios_build = get_ios_build(build)
                new_dir = "G:\\Builds\\Artemis_MR1\\WorxWeb_iOS\\"+ios_build
                upload_to_njrdfs1(app_name,new_dir,desktop)


            elif worxmail in download_link:
                app_name = "WorxMail_iOS"
                ios_build = get_ios_build(build)
                new_dir = "G:\\Builds\\Artemis_MR1\\WorxMail_iOS\\"+ios_build
                upload_to_njrdfs1(app_name,new_dir,desktop)


        else: #Other is downloaded by CIFS

            zipfile_name = str(build)+".zip"
            sharefile_name = "File box\\" + zipfile_name
            rmdir_cmd = "rmdir /s /q "+directory
            run_windows_command(rmdir_cmd) #Step 1 remove dir
            create_dir(directory) #Step 2 Create dir

            if apptype == "xap":

                copy_cmd_web = "xcopy /S /Y "+download_link+"\\"+str(build)+"\\Signed\\Release\\ARM\WorxWeb*.mdx "+directory
                new_dir = "G:\\Builds\\Artemis_MR1\\WorxWeb_WP\\"+build
                app_name = "WorxWeb_wp"
                upload_to_njrdfs1(app_name,new_dir,directory)

                copy_cmd_mail = "xcopy /S /Y "+download_link+"\\"+str(build)+"\\Signed\\Release\\ARM\WorxMail*.mdx "+directory
                run_windows_command(copy_cmd_mail)
                new_dir = "G:\\Builds\\Artemis_MR1\\WorxMail_WP\\"+build
                app_name = "WorxMail_wp"
                upload_to_njrdfs1(app_name,new_dir,directory)

                copy_cmd_home = "xcopy /S /Y "+download_link+"\\"+str(build)+"\\Signed\\Release\\ARM\*BFSLMDM.xap "+directory
                run_windows_command(copy_cmd_home)
                app_name = "WindowsPhone"

            elif apptype == "apk":

                worxweb = "browser"
                worxmail = "email"
                if worxweb in download_link:
                    copy_cmd = "xcopy /S /Y "+download_link+"\\"+str(build)+"\\binaries\\internal"+"\*release.apk "+directory
                    run_windows_command(copy_cmd)
                    app_name = "WorxWeb_Android"

                    new_dir = "G:\\Builds\\Artemis_MR1\\WorxWeb_Android\\"+build
                    upload_to_njrdfs1(app_name,new_dir,directory)

                elif worxmail in download_link:

                    copy_cmd = "xcopy /S /Y "+download_link+"\\"+str(build)+"\\binaries\\bin\\CitrixEmail-release.apk "+directory
                    run_windows_command(copy_cmd)
                    app_name = "WorxMail_Android"
                    new_dir = "G:\\Builds\\Artemis_MR1\\WorxMail_Android\\"+build
                    cupload_to_njrdfs1(app_name,new_dir,directory)

            else: #the case is SCCM
                copy_cmd = "xcopy /S /Y "+download_link+"\\"+str(build)+"\* "+directory
                run_windows_command(copy_cmd)  #Step 3 Copy file
                app_name = "SCCM"

            make_zipfile(zipfile_name,directory) #Step 4 Create zip file

        upload_to_sharefile(zipfile_name,sharefile_name,build,app_name)
        os.remove(zipfile_name)

        if not http_or_cifs(download_link):
            run_windows_command(rmdir_cmd)

        os.remove(lockfile) #Remove lock


def download_apps_from_http(app):#import needed modules
    '''
    Usage: downloadWorxAppIOS("web/mail")
    '''
    #make a string to hold the url of the request

    if app == "mail":
        url = "http://banwautomation.eng.citrite.net:8080/view/Mobile%20Mail/job/WorxMail_Release_Artemis_9.0/lastSuccessfulBuild/artifact/build/"
    elif app == "web":
        url = "http://banwautomation.eng.citrite.net:8080/view/Mobile%20Browse/job/WorxWeb_Release_Artemis_9.0/lastSuccessfulBuild/artifact/build/"

    request_object = urllib2.Request(url)

    response = urllib2.urlopen(request_object)

    content = response.read()
    soup = bs(content)
    for i in soup.findAll('a'):
        pattern = 'ipa"'
        a = str(i)
        try:
            if pattern in a:
                link =  i.get('href')
                if app_build_change(link,app):
                    url = url + link
                    upload_build(url,link,"ipa")
                    update_ini_mobile(app,link)
                    break
                else:
                    print "No new iOS build"
        except:
            pass



def app_build_change(link,app):
    if app == "mail":
        item = "worxmail_ios"
    elif app == "web":
        item = "worxweb_ios"
    cf = ConfigParser.ConfigParser()
    cf.read("C:\\test\\other\\config.ini")
    build_name = cf.get("build", item)
    if build_name == link:
        return False
    else:
        return True


def config_parser(app):
    cf = ConfigParser.ConfigParser()
    cf.read("C:\\test\\other\\config.ini")
    worxmail = cf.get("build", "worxmail_ios")
    cf.set("build", "worxweb_ios", "zhaowei")
    cf.write(open("config.ini", "w"))
    print worxmail
    return buildno

def update_ini_mobile(app,link):
    if app == "mail":
        item = "worxmail_ios"
    else:
        item = "worxweb_ios"
    cf = ConfigParser.ConfigParser()
    cf.read("config.ini")
    cf.set("build", item, link)
    cf.write(open("config.ini", "w"))

def main():

    download_apps_from_http("mail")
    download_apps_from_http("web")
    download_apps_from_cifs("H:\\PLANB\\Android\\email\\artemis","worxmail_log.txt","apk")
    download_apps_from_cifs("H:\\PLANB\\Android\\browser\\artemis","worxweb_log.txt","apk")
    download_apps_from_cifs("S:\\CitrixBuilds\\Artemis\\WP8\\Worx","log_wp.txt","xap")

    return

if __name__ == '__main__':

    os.chdir("C:\\test\\other")
    main()




