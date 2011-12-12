# -*- coding: utf-8 -*-
# developed by Massimo Di Pierro, BSD License

@auth.requires_login()
def index():
    form=SQLFORM.factory(Field('url',requires=IS_URL(),default='http://...'))
    if form.process().accepted:
        redirect(URL('edit',vars=dict(url=form.vars.url)))
    clones = db(db.cms_clone).select()
    return locals()

@auth.requires_login()
def delete():
    db(db.cms_clone.id==request.args(0))(db.cms_clone.created_by==auth.user.id).delete()
    redirect(URL('index'))

@auth.requires_login()
def edit():
    return locals()

@auth.requires_login()
def edit_clone():
    session._unlock(response)                    
    import urllib,re
    if request.args(0)=='post':
        return request.vars.value or ''
    elif request.args(0)=='store':
        session.new_html = session.html.split('<body')[0]+'<body>' + \
            request.vars.html+'</body></html>'
        return 'ok'
    url = request.vars.url
    try:
        html = urllib.urlopen(url).read()
    except IOError:
        session.flash = 'web page does not exist!'
        redirect(URL('index'))
    url.rstrip('/')
    session.url = url
    a,b = url.split('://')
    items = b.split('/')
    base = a+'://'+items[0]+'/'
    if len(items)>2:
        full = base+'/'.join(items[1:-1])+'/'
    else:
        full = base
    html = re.sub('\s+[\n]','\n',html)
    html = re.sub('>[ \t]+<','> <',html)
    html = re.sub('(src|SRC)\s*=\s*"/(?!/)','src="'+base,html)
    html = re.sub('(src|SRC)\s*=\s*"(?!(/|http))','src="'+full,html)
    html = re.sub('(href|HREF)\s*=\s*"/(?!/)','href="'+base,html)
    html = re.sub('(href|HREF)\s*=\s*"(?!(/|http))','href="'+full,html)
    html = re.sub('url\(/(?!/)','url('+base,html)
    html = re.sub('url\((?!(/|http))','url('+full,html)
    session.new_html = session.html = html
    inject = '<script src="%s" language="javascript"></script>' % URL('static','js/inject.js')
    html = html.replace('</head>',inject+'</head>')
    return html

@auth.requires_login()
def clone():
    id = db.cms_clone.insert(url=session.url,html=session.new_html)
    redirect(URL('page',args=id))

def page():
    if request.args(0)=='clone': redirect(URL('index'))
    html = db.cms_clone(request.args(0)).html
    inject = '<script language="javascript">alert("This is an altered copy of another page.\nIt was made as an experimental proof of concept.\nIf this page infringes a copyright, we will take it down.");</script>'
    html = html.replace('</head>',inject+'</head>')
    return html

def user():
    return dict(form=auth())

@auth.requires_login()
def folder():
    folder = db.cms_folder(request.args(0),created_by=auth.user.id)
    if not folder:
        if db(db.cms_folder).isempty():
            db.cms_folder.insert(name='root',parent_folder=0,created_by=auth.user.id)
        folder = db.cms_folder(parent_folder=0,created_by=auth.user.id)
    folder.path, f = [folder.name], folder.parent_folder
    while f: folder.path, f = [A(f.name,_href=URL('folder',args=f))]+folder.path, f.parent_folder
    files = db(db.cms_file.folder==folder.id).select(orderby=db.cms_file.name)
    folders = db(db.cms_folder.parent_folder==folder.id).select(orderby=db.cms_folder.name)
    return locals()

@auth.requires_login()
def edit_file():
    folder = db.cms_folder(request.args(0),created_by=auth.user.id)
    db.cms_file.folder.default=folder.id
    db.cms_file.name.requires=IS_NOT_IN_DB(
        db(db.cms_file.folder==folder.id),'cms_file.name')
    file = db.cms_file(request.args(1),created_by=auth.user.id)
    form = SQLFORM(db.cms_file,file,deletable=True)\
        .process(next=URL('folder',args=folder.id))
    return locals()

@auth.requires_login()
def edit_folder():
    folder = db.cms_folder(request.args(0),created_by=auth.user.id)
    db.cms_folder.parent_folder.default=folder.id
    db.cms_folder.name.requires=IS_NOT_IN_DB(
        db(db.cms_folder.parent_folder==folder.id),'cms_folder.name')
    ofolder = db.cms_folder(request.args(1),created_by=auth.user.id)
    form = SQLFORM(db.cms_folder,ofolder,deletable=True)\
        .process(next=URL('folder',args=folder.id))
    return locals()

def doc():
    import re
    import contenttype
    items = re.compile('(?P<id>.*?)\.(?P<ext>\w*)').match(request.args(0) or '')
    if not items:
        raise HTTP(404)
    (id, ext) = (items.group('id'), items.group('ext'))
    name = db.cms_file(id).file
    (filename, stream) = db.cms_file.file.retrieve(name)
    print filename
    file = db.cms_file(id)
    response.headers['Content-Type'] = contenttype.contenttype(name)
    response.headers['Content-Disposition'] = "attachment; filename=%s" % filename
    return response.stream(stream, request=request)
