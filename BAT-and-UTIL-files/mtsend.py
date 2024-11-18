#!/usr/bin/env python


#                    dateCreated => '20080121T12:38:30',
#                     date_created_gmt => '20080121T20:38:30',


# Command Line Movable Type Client
# ================================
# This application allows you to edit/post entries on a Movable Type site via
# XML-RPC calls. For more information about this script, visit:
#
#   http://scott.yang.id.au/2002/12/mtsendpy/
#
# HISTORY
# =======
#
# 1.1 - 19 Nov 2005
# + Add SSL support for proxy.
#
# 1.0 - 20 May 2005
# + time module related fix for Python 2.4.
# + Ensure all cells passed to print_table() function are in string-type.
#
# 0.6.1 - 6 Apr 2004
# + Properly handles mt_allow_comments for MT2.6 servers.
#
# 0.6 - 1 Apr 2004
# + Add build-in support for HTTP proxy server, which is detected via
#   environment variable HTTP_PROXY.
# + Alternative encoding for XML-RPC packets.
#
# 0.5 - 14 Oct 2003
# + Remove the support of MT2.5. Use the older version of mtsend.py if you
#   need these supports.
# + Support KEYWORDS and PING into the header.
# + Add new functionalities provided by MT2.6's backend.
#   - List out trackback pings of a post.
#   - List out text filters installed.
# + Documentation in the source code.
#
# 0.4 - 10 Mar 2003
# + Support the new metaWeblog.newMediaObject() function via mtsend.py -U
#   filename, i.e. you can now upload text/binary files to your
#   MovableType site via mtsend.py!
# + Use mt.getRecentPostTitles() function in MT2.6 to save bandwidth.
# + Some bug fixes due to some inconsistency between MT2.6 and MT2.5.
# 
# 0.3 - 3 Jan 2003
# + Make it to work on Python 2.1. "xmlrpclib" needs to be downloaded
#   separately. It is tested
#   on Python 2.1.2 for Windows.
#   
# 0.2 - 30 Dec 2002
# + Fixed a bug in saving the post entry back, where new line characters
#   are stripped.
#
# 0.1 - 30 Dec 2002
# + Initial public version
#
#
# CONFIGURATION FILE
# ==================
# Configuration file for mtsend.py is in the style of Windows INI files, which
# consist of sections and key/value pairs. There are 3 main sections - global,
# site and blog.
#
# Global Section:
#   There is only one key/value in this section, and it is used to note the
#   default blog alias to use if it is not provided on the command line.
#   For example:
#
#     [global]
#     default=example
#
#   It shows the default blog alias will be 'example'
#
# Site Section:
#   You can have multiple site sections for each Movable Type installation
#   you have access to. The section name will be [site-"site name"]. For
#   example:
#     
#     [site-test]
#     url=http://testdomain.com/mtinstall/mt-xmlrpc.cgi
#     username=foo
#     password=bar
#     encoding=UTF-8
#
#   It defines site "test" with the URL to the MovableType's XML-RPC CGI
#   script, and the username/password used to access that site. "encoding" is
#   optional, and defaults to UTF-8.
#
# Blog Section:
#   You can have multiple blog sections for each Movable Type blogs you have
#   on the sites you have access to. Blogs are distinguished by their 'alias',
#   which you can select in the command line using -a. The section name for
#   this blog will be [blog-"blog alias"]. For example,
#
#     [blog-example]
#     site=test
#     blogid=3
#
#   Each blog section must have "site", which indicates the site this blog
#   belongs to, so that mtsend would be able to locate site-related
#   information from the configuration file. It also needs the blog ID on that
#   site. To find out all the blog IDs, you can use -B "site name" to print
#   out the list.
#
#
# POST FORMAT
# ===========
# When editing or posting via mtsend, the post needs to be in a specific
# format. The format is very close to Movable Type's import/export format,
# which is documented here:
#
#   http://www.movabletype.org/docs/mtmanual_importing.html
#
# It consists of a header and body. For example:
#
#   [header1]: [value1]
#   [header2]: [value2]
#   [header3]: [value3]
#   -----
#   BODY:
#   ....
#   -----
#   EXTENDED BODY:
#   ....
#   -----
#   EXCERPT:
#   ....
#
# Extended body and excerpt are optional in a post. Most header elements are
# optional when you are creating a new post. If they do not provide a value,
# then the default value configured by Movable Type will be used.
#
# These are the header keys/values:
#
#   TITLE:
#     The title of this post.
#     
#   ALLOW COMMENTS: 0/1 
#     Whether this post allows comments.
#
#   ALLOW PINGS: 0/1
#     Whether this post allows trackback pings.
#
#   CATEGORY:
#     The category associated with this post entry. You can have multiple
#     CATEGORY in the header. The first CATEGORY automatically becomes the
#     primary category, if PRIMARY CATEGORY is not specified.
#
#   CONVERT BREAKS: 0/1/customised text filter name.
#     Whether the line break will be automatically converted into <br/> and
#     <p/> when posted. It can also be the name of an installed text filer. To
#     get the list of installed text filter, use mtsend.py -T
#
#   DATE: mm/dd/yyyy HH:MM:SS [AM|PM] 
#     DOCUMENTATION WAS WRONG! HAD MM AND DD SWITCHED!
#     The post date. It might not work if you are creating a new post.
#
#   KEYWORDS:
#     The keywords of your post.
#
#   PING:
#     The URL to be pinged during posting. You can have multiple PING in the
#     header.

'''\
Usage: 
    mtsend.py [action] [options]

Actions:
    -B site     List all the blogs you can access in [site]. Site has to be in
                the configuration file.
    -C          Print out a list of existing categories.
    -E postid   Edit an old post. It will read the post entry from the
                standard input, in Movable Type's import/export format, and
                then save it back to the server. If the value is '-', then it
                will try to detect the postid from the input message itself.
    -G postid   Retrieve/get post from the blog. If the value is '-', it will
                then try to get the most recent blog entry. Retrieved entry
                will be printed to the standard output.
    -L num      List the most recent [num] posts.
    -N          Posting a new blog. The entry, in the Movable Type
                import/export format, is read from the standard input.
    -P postid   List out trackback pings to this post.
    -R postid   Rebuild all the static files related to this entry.
    -T          List out the text filters installed on the server.
    -U filename Upload a file, reading from standard input, to the blog site,
                with destination filename provided.
    -V          Show version information.

Options:
    -a alias    Use "alias" as the blog alias. This script will locate
                relavent site URL/username/password information using this
                alias.
    -c config   Load "config" as configuration file, instead of $HOME/.mtsendrc
    -h          Display this help message.
    -q          Decrease verbose level.
    -v          Increase verbose level. Message goes to standard error.

For more information, please visit:
    http://scott.yang.id.au/2002/12/mtsendpy/
'''

__author__      = 'Scott Yang <scotty@yang.id.au>'
__copyright__   = 'Copyright (c) 2002-2005 Scott Yang'
__date__        = '2005-11-19'
__version__     = '1.1'

import ConfigParser
import httplib
import os
import re
import sys
import time
import urllib


class MTSend(object):
    def __init__(self):
        self.alias = None
        self.input = None
        self.config = None
        self.mode = None
        self.verbose = 1
        self.rpcsrv = None
        self.site = None
        self.modeopt = None

    def execute(self):
        try:
            handler = getattr(self, 'execute_%s' % self.mode)
        except AttributeError:
            raise Exception, 'Unknown execution mode: %s' % self.mode
        else:
            handler()

    def execute_b(self):
        self.site = self.modeopt
        srv = self.getRPCServer()
        blogs = srv.blogger.getUsersBlogs('', self.get_username(), 
            self.get_password())
        result = [['ID', 'Blog Name', 'URL']]
        for blog in blogs:
            result.append([blog['blogid'], blog['blogName'], blog['url']])
        print_table(result)

    def execute_c(self):
        srv = self.getRPCServer()
        cts = srv.mt.getCategoryList(self.get_blogid(), self.get_username(), 
            self.get_password())
        result = []
        for cat in cts:
            result.append([cat['categoryId'], cat['categoryName']])
        result.sort(lambda x, y: cmp(x[1], y[1]))
        result[0:0] = [['ID', 'Category Name']]
        print_table(result)

    def execute_e(self):
        self.log(1, 'Parsing post entry from standard input...')
        post, cts, publish = parse_post()

        postid = self.modeopt
        if self.modeopt == '-':
            try:
                postid = post['postid']
            except KeyError:
                raise Exception, 'Cannot discover post ID from the input.'
            
        elif post.has_key('postid') and (post['postid'] != postid):
            raise Exception, \
                'Post ID does not match. ID in the input is "%s"' % \
                    post['postid']

        srv = self.getRPCServer()
        self.log(1, 'Saving post entry "%s"...', postid)
        srv.metaWeblog.editPost(postid, self.get_username(), 
            self.get_password(), post, publish)

        cts = self._fixCategories(cts)
        if len(cts) > 0:
            self.log(1, 'Add categories "%s" to post entry "%s"...',
				#original categories line, worked for years:
                #','.join([cat['categoryId'] for cat in cts]), postid)
				#new one sent in 2016:
                ','.join([str(cat['categoryId']) for cat in cts]), postid)
            srv.mt.setPostCategories(postid, self.get_username(),
                self.get_password(), cts)

        #TODO write postid to a file, untested
		#file = open("c:\\delme-last-post-id.dat", "w")
		#myFileName = os.path.normpath("c:/delme-last-post-id.dat")
		#self.log(1, 'Trying to write postid %s to file...', postid)
        file = open('c:/delme-last-post-id.dat', "w")
        file.write("%s" % postid)
        file.close()
		#self.log(1, 'Done: Trying to write postid %s to file...', postid)

	
 
    def execute_g(self):
        srv = self.getRPCServer()
        if self.modeopt.lower() == '-':
            self.log(1, 'Retrieve most recent post entry...')
            post = srv.metaWeblog.getRecentPosts(self.get_blogid(), 
                self.get_username(), self.get_password(), 1)
            if len(post) > 0:
                post = post[0]
            else:
                raise Exception, 'The current blog does not have any entry.'
        else:
            self.log(1, 'Retrieve post entry "%s"...', self.modeopt)
            post = srv.metaWeblog.getPost\
                ( self.modeopt, self.get_username(), self.get_password() )

        # Get the categories of this post.
        self.log(1, 'Retrieve categories for post entry "%s"...', 
                 post['postid'])
        cts = srv.mt.getPostCategories(post['postid'], self.get_username(), 
            self.get_password())

        print_post(post, cts)

    def execute_l(self):
        srv = self.getRPCServer()
        try:
            num = int(self.modeopt)
        except:
            num = 5

        func  = srv.mt.getRecentPostTitles
        posts = func(self.get_blogid(), self.get_username(), 
            self.get_password(), num)

        self.log(1, 'Retrieve "%d" recent posts...', num)
        result = [['ID', 'Date', 'Title']]
        for post in posts:
            result.append([
                post['postid'],
                time.strftime('%Y-%m-%d %H:%M:%S', 
                    decode_iso8601(post['dateCreated'].value)),
                post['title']
            ])

        print_table(result)

    def execute_n(self):
        self.log(1, 'Parsing post entry from standard input...')
        post, cts, publish = parse_post()
        srv = self.getRPCServer()

        self.log(1, 'Saving new post entry...')
        postid = srv.metaWeblog.newPost(self.get_blogid(), self.get_username(), 
            self.get_password(), post, publish)

        cts = self._fixCategories(cts)
        if len(cts) > 0:
            self.log(1, 'Add categories "%s" to post entry "%s"...',
                    #','.join([cat['categoryId'] for cat in cts]), postid)
					#new 2016 line:
                     ','.join([str(cat['categoryId']) for cat in cts]), postid)
            srv.mt.setPostCategories(postid, self.get_username(), 
                self.get_password(), cts)

        # Somehow under MovableType 2.5, the new post will not trigger a
        # rebuild. Therefore we will force a rebuild here.
        #
        # XXX: Apparently this behaviour no longer exists in later version of
        # MT.
        if False:
            self.modeopt = postid
            self.execute_r()

        print postid
    
    def execute_p(self):
        srv = self.getRPCServer()
        result = [[
            val['pingTitle'],
            val['pingURL'],
            val['pingIP'],
        ] for val in srv.mt.getTrackbackPings(self.modeopt)]

        result.insert(0, ['Title', 'URL', 'IP'])
        print_table(result)

    def execute_r(self):
        srv = self.getRPCServer()
        srv.mt.publishPost(self.modeopt, self.get_username(), 
            self.get_password())

    def execute_t(self):
        srv = self.getRPCServer()
        result = []
        for val in srv.mt.supportedTextFilters():
            result.append([val['key'], val['label']])

        result.sort()
        result.insert(0, ['Key', 'Label'])
        print_table(result)

    def execute_u(self):
        srv = self.getRPCServer()
        bin = sys.stdin.read()

        self.log(1, 'Uploading "%s" (%d bytes)...', self.modeopt, len(bin))
        media_object = {
            'name': self.modeopt,
            'bits': xmlrpclib.Binary(bin),
        }
        
        result = srv.metaWeblog.newMediaObject(self.get_blogid(), 
            self.get_username(), self.get_password(), media_object)

        print result['url']

    def getRPCServer(self):
        if self.rpcsrv is not None:
            return self.rpcsrv

        httptype = urllib.splittype(self._getSite('url'))[0]
        transport = get_rpc_transport(httptype)

        # Default we will use 'UTF-8' encoding, if the site encoding option is
        # not provided.
        return xmlrpclib.ServerProxy(self._getSite('url'), transport, 
            self._getSite('encoding', 'UTF-8'))

    def get_blogid(self):
        return self._getBlog('blogid')

    def get_password(self):
        return self._getSite('password')

    def get_username(self):
        return self._getSite('username')

    def loadConfig(self, config):
        if config is None:
            config = os.path.join(os.environ['HOME'], '.mtsendrc')

        if not os.access(config, os.R_OK):
            raise Exception, \
                'Configuration file "%s" is not readable' % config

        self.config = ConfigParser.ConfigParser()
        self.config.read([config])

    def log(self, level, msg, *fmt):
        if self.verbose >= level:
            print >> sys.stderr, msg % fmt

    def setMode(self, mode, modeopt=None):
        if self.mode is None:
            self.mode = mode
            self.modeopt = modeopt
        else:
            raise Exception, 'Conflicting operational mode.'

    def _fixCategories(self, cts):
        if len(cts) > 0:
            srv = self.getRPCServer()
            new = []

            self.log(1, 'Retrieve available categories...')
            old = srv.mt.getCategoryList(self.get_blogid(), 
                self.get_username(), self.get_password())
            ctsmap = {}
            for cat in old:
                ctsmap[cat['categoryName'].lower()] = cat['categoryId']

            for cat in cts:
                try:
                    new.append({'categoryId': ctsmap[cat]})
                    del ctsmap[cat]
                except KeyError:
                    pass

            return new
        else:
            return []

    def _getBlog(self, option, default=None):
        if self.config is None:
            raise Exception, 'Configuration has not been loaded.'

        if self.alias is None:
            try:
                alias = self._getGlobal('default')
            except KeyError:
                raise Exception, 'Blog alias has not been specified.'
        else:
            alias = self.alias

        try:
            return self.config.get('blog-%s' % alias, option)
        except ConfigParser.Error:
            if default is not None:
                return default
            else:
                raise KeyError, option

    def _getGlobal(self, option, default=None):
        if self.config is None:
            raise Exception, 'Configuration has not been loaded.'
        try:
            return self.config.get('global', option)
        except ConfigParser.Error:
            if default is not None:
                return default
            else:
                raise KeyError, option

    def _getSite(self, option, default=None):
        try:
            if self.site is None:
                self.site = self._getBlog('site')
                
            return self.config.get('site-%s' % self.site, option)
        except (ConfigParser.Error, KeyError):
            if default is not None:
                return default
            else:
                raise KeyError, option

try:
    import xmlrpclib
except ImportError:
    # Error reporting will be raised in the main() function. We will simply
    # ignore the error here.
    xmlrpclib = None
else:
    class HTTP(httplib.HTTP):
        def __init__(self, conn):
            httplib.HTTP.__init__(self)
            self._setup(conn)


    class ProxyTransport(xmlrpclib.Transport):
        """Transport class for the XMLRPC.

        Instead of using the HTTP/HTTPS transport, it tries to use a proxy
        server to send/receive XMLRPC messages. This transport must be
        initialised with the hostname and port number of the proxy server,
        e.g.

            transport = ProxyTransport('proxy.mydomain.com', 3128)
            server = Server("http://betty.userland.com", transport)
            print server.examples.getStateName(41)

        """

        def __init__(self, host, port=3128, username=None, password=None, 
                ssl=False):
            self.__host = host
            self.__port = port
            self.__username = username
            self.__password = password
            self.__ssl = ssl
            self.__target_host = None

        def get_authentication(self):
            import base64
            auth_token = '%s:%s' % (self.__username, self.__password)
            auth_token = base64.encodestring(urllib.unquote(auth_token))
            auth_token = auth_token.strip()
            return 'Basic '+auth_token

        def make_connection(self, host):
            "Make a connection to the proxy server"
            
            # Note that we will try to connect to the proxy server instead of
            # our target host. It also needs to store the information about
            # the target host so that we can use that information in
            # send_request() call.

            import socket

            if self.__ssl:
                # XXX: Code pieces taken from
                # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/301740
                header = [
                    'CONNECT %s:443 HTTP/1.0' % host,
                    'User-Agent: mtsend.py/%s' % __version__,
                ]
                if self.__username and self.__password:
                    header.append('Proxy-Authentication: %s' %
                        self.get_authentication())
                proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                proxy.connect((self.__host, self.__port))
                proxy.sendall('\r\n'.join(header)+'\r\n\r\n')

                response = proxy.recv(8192) 
                status = response.split()[1]
                if status != '200':
                    print response
                    raise Exception, 'Invalid CONNECT response "%s"' % status

                ssl = socket.ssl(proxy, None, None)
                sock = httplib.FakeSocket(proxy, ssl)
                conn = httplib.HTTPConnection('localhost')
                conn.sock = sock
                return HTTP(conn)
            else:
                self.__target_host = host
                return httplib.HTTP('%s:%d' % (self.__host, self.__port))

        def send_content(self, connection, request_body):
            """Send the content of the XML-RPC request to the server.

            This method override the default send_content. If the proxy
            username and password has been configured, then we will place an
            extra header here so the connection can be authenticated.

            """
            if (self.__username is not None) and (self.__password is not None):
                connection.putheader("Proxy-Authorization", 
                    self.get_authentication())

            xmlrpclib.Transport.send_content(self, connection, request_body)

        def send_request(self, connection, handler, request_body):
            if not self.__ssl:
                handler = 'http://' + self.__target_host + handler
            connection.putrequest("POST", handler)


def decode_iso8601(date):
    # Translate an ISO8601 date to the tuple format used in Python's time
    # module.
    regex = r'^(\d{4})(\d{2})(\d{2})T(\d{2}):(\d{2}):(\d{2})'
    match = re.search(regex, str(date))
    if not match:
        raise Exception, '"%s" is not a correct ISO8601 date format' % date
    else:
        result = match.group(1, 2, 3, 4, 5, 6)
        result = map(int, result)
        result += [0, 1, -1]
        return tuple(result)


def get_rpc_transport(httptype):
    # Detect whether we need to use 'ProxyTranspory'. Proxy detection is
    # done using HTTP_PROXY or http_proxy environment variable.
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if proxy:
        match = re.match(r'^(http://)?(([^:@]+)(:([^@]*))?@)?([^:]+):(\d+)',
            proxy)

        if match:
            username = match.group(3) or None
            password = match.group(5) or None
            hostname = match.group(6)
            bindport = int(match.group(7))

            return ProxyTransport(hostname, bindport, username, password,
                httptype=='https')

    # Letting ServerProxy to pick the best suitable transport
    return None


re_date = r'^(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2})( ([AP]M))?$'
re_date = re.compile(re_date).search

def parse_date(val):
    match = re_date(val.upper())
    if match is None:
        raise Exception, 'Date value "%s" is invalid.' % val
    result = map(int, match.group(1, 2, 3, 4, 5, 6))
    try:
        ampm = match.group(8)
    except IndexError:
        pass
    else:
        if ampm == 'PM':
            if result[3] != 12:
                result[3] += 12
        elif ampm == 'AM':
            if result[3] == 12:
                result[3] = 0
        elif ampm is not None:
            raise Exception, 'Expect (AM|PM) get "%s"' % ampm

    result[0:3] = [result[2], result[0], result[1]]
    result += [0, 1, -1]

    return tuple(result)


def parse_post():
    state = 0
    code = None
    post = {}
    cts = []
    publish = xmlrpclib.Boolean(0)

    for line in sys.stdin:
        line = line.rstrip()
        if state == 0:
            if line == '-----':
                state = 1
            else:
                idx = line.find(':')
                if idx < 0:
                    continue        # Invalid entry

                key, val = line[:idx].strip().upper(), line[idx+1:].strip()
                if key == 'TITLE':
                    post['title'] = val
                elif key == 'DATE':
                    val = time.strftime('%Y%m%dT%H:%M:%S', parse_date(val))
                    post['dateCreated'] = xmlrpclib.DateTime(val)
                elif key == 'STATUS':
                    publish = xmlrpclib.Boolean(val.lower() == 'publish')
                elif key == 'ALLOW COMMENTS':
                    val = int(val)
                    if val not in (0, 1, 2):
                        raise Exception, \
                            'ALLOW COMMENTS must be either 0, 1 or 2'
                    post['mt_allow_comments'] = val
                elif key == 'ALLOW PINGS':
                    post['mt_allow_pings'] = int(val)
                elif key == 'PING':
                    try:
                        post['mt_tb_ping_urls'].append(val)
                    except KeyError:
                        post['mt_tb_ping_urls'] = [val]
                elif key == 'CONVERT BREAKS':
                    # MT2.6 - mt_convert_breaks has changed its value from
                    # XML-RPC boolean to string.
                    post['mt_convert_breaks'] = val
                elif key == 'POSTID':
                    post['postid'] = val
                elif key == 'PRIMARY CATEGORY':
                    cts.insert(0, val.lower())
                elif key == 'CATEGORY':
                    cts.append(val.lower())
                elif key == 'KEYWORDS':
                    post['mt_keywords'] = val
                else:
                    raise Exception, 'Invalid field key: %s' % key

        elif state == 1:
            line = line.upper()
            if line == 'BODY:':
                code = 'description'
            elif line == 'EXTENDED BODY:':
                code = 'mt_text_more'
            elif line == 'EXCERPT:':
                code = 'mt_excerpt'
            else:
                raise Exception, 'Invalid line in the current state: \"%s\"' % line

            state = 2

        elif state == 2:
            if line.startswith('-----') and (not line.rstrip('-')):
                code = None
                state = 1
            else:
                if post.has_key(code):
                    post[code] += '\n' + line
                else:
                    post[code]  = line


    return post, cts, publish


def print_post(post, cts):
    if post.has_key('title'):
        print 'TITLE:', post['title']
    print 'DATE:', time.strftime('%m/%d/%Y %H:%M:%S',
        decode_iso8601(post['dateCreated'].value))
                      
    for cat in cts:
        if cat['isPrimary']:
            print 'PRIMARY CATEGORY:', cat['categoryName']
        print 'CATEGORY:', cat['categoryName']

    # We cannot really determine whether the post has been published.
    # Therefore we assume that it is.
    print 'STATUS: publish'

    if post.has_key('mt_allow_comments'):
        print 'ALLOW COMMENTS:', post['mt_allow_comments']
    
    if post.has_key('mt_allow_pings'):
        print 'ALLOW PINGS:', post['mt_allow_pings']
    
    if post.has_key('mt_convert_breaks'):
        print 'CONVERT BREAKS:', post['mt_convert_breaks']

    if post.get('mt_keywords'):
        print 'KEYWORDS:', post['mt_keywords']

    # We will also print the postid so that it can be verified later.
    print 'POSTID:', post['postid']

    # Start printing the body
    if post.get('description'):
        print '-----'
        print 'BODY:'
        print post['description']

    if post.get('mt_text_more'):
        print '-----'
        print 'EXTENDED BODY:'
        print post['mt_text_more']
        
    if post.get('mt_excerpt'):
        print '-----'
        print 'EXCERPT:'
        print post['mt_excerpt']


def print_table(table, heading=1):
    # We have to work out the maximum width first.
    if not table:
        return

    widths = [0] * len(table[0])
    for row in table:
        for idx, cell in zip(range(len(row)), row):
            if isinstance(cell, unicode):
                cell = cell.encode(DEFAULT_ENCODING)
            elif not isinstance(cell, str):
                cell = str(cell)
            row[idx] = cell
            if len(cell) > widths[idx]:
                widths[idx] = len(cell)

    border = '+'+('+'.join(['-'*(width + 2) for width in widths]))+'+'
    format = '|'+('|'.join([' %%-%ds ' % width for width in widths]))+'|'

    hdrs = 0

    print border
    for row in table:
        print format % tuple(row)
        if (not hdrs) and heading and (len(table) > 1):
            print border
            hdrs = 1
    print border


DEFAULT_ENCODING = 'utf-8'


def main(args):
    import getopt
    try:
        opts, args = getopt.getopt(args, 'a:B:Cc:E:G:hL:NP:qR:TU:vV')
    except getopt.GetoptError, ex:
        print >> sys.stderr, 'Error: '+str(ex)
        print >> sys.stderr, __doc__
        sys.exit(1)

    mtsend = MTSend()
    config = None

    for opt, arg in opts:
        if opt == '-a':
            mtsend.alias = arg
        elif opt == '-B':
            mtsend.setMode('b', arg)
        elif opt == '-C':
            mtsend.setMode('c')
        elif opt == '-c':
            config = arg
        elif opt == '-E':
            mtsend.setMode('e', arg)
        elif opt == '-G':
            mtsend.setMode('g', arg)
        elif opt == '-h':
            print >> sys.stderr, __doc__
            sys.exit(0)
        elif opt == '-L':
            mtsend.setMode('l', arg)
        elif opt == '-N':
            mtsend.setMode('n')
        elif opt == '-P':
            mtsend.setMode('p', arg)
        elif opt == '-q':
            mtsend.verbose -= 1
        elif opt == '-R':
            mtsend.setMode('r', arg)
        elif opt == '-T':
            mtsend.setMode('t')
        elif opt == '-U':
            mtsend.setMode('u', arg)
        elif opt == '-v':
            mtsend.verbose += 1
        elif opt == '-V':
            print >> sys.stderr, 'Version %s' % __version__
            sys.exit(0)
        else:
            print >> sys.stderr, 'Warning: Option "%s" is not handled.' % opt

    if mtsend.mode is None:
        print >> sys.stderr, 'Error: Action is not specified'
        print >> sys.stderr, __doc__
        sys.exit(1)

    if xmlrpclib is None:
        print >> sys.stderr, '''Error: Cannot import "xmlrpclib" module.

You should either upgrade to Python 2.2+, or download and install the 
"xmlrpclib" from the following website:

    http://www.pythonware.com/products/xmlrpc/
'''
        sys.exit(1)

    try:
        mtsend.loadConfig(config)
        mtsend.execute()
    except Exception, ex:
        if mtsend.verbose > 1:
            raise
        else:
            print >> sys.stderr, 'Error:', ex


if __name__ == '__main__':
    main(sys.argv[1:])
