"""Session and CSRF approach adapted from 42bios/unifi-network-plus (MIT).
See THIRD_PARTY_NOTICES.md for the original copyright and license.
"""
import base64,http.cookiejar,http.client,hashlib,hmac,json,re,ssl,urllib.request,urllib.error
from urllib.parse import urlsplit,quote
from common.runtime import NoRedirect

class PinnedConnection(http.client.HTTPSConnection):
 def __init__(self,*args,fingerprint,**kwargs):
  self.fingerprint=fingerprint
  context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);context.check_hostname=False;context.verify_mode=ssl.CERT_NONE
  kwargs['context']=context
  super().__init__(*args,**kwargs)
 def connect(self):
  super().connect()
  actual=hashlib.sha256(self.sock.getpeercert(binary_form=True)).hexdigest()
  if not hmac.compare_digest(actual,self.fingerprint):
   self.close();raise ssl.SSLError('UniFi certificate fingerprint mismatch')

class PinnedHandler(urllib.request.HTTPSHandler):
 def __init__(self,fingerprint):super().__init__();self.fingerprint=fingerprint
 def https_open(self,req):
  return self.do_open(lambda *a,**kw:PinnedConnection(*a,fingerprint=self.fingerprint,**kw),req)

class Client:
 def __init__(self,url,username,password,site='default',mode='os',ca=None,fingerprint=None):
  target=urlsplit(url)
  if target.scheme!='https' or not target.hostname or target.username or target.password or target.path not in ('','/') or target.query or target.fragment:raise ValueError('Use an HTTPS controller origin URL')
  if mode not in ('os','classic'):raise ValueError('Controller type must be os or classic')
  self.url=url.rstrip('/');self.username=username;self.password=password;self.site=quote(site,safe='');self.mode=mode;self.csrf=''
  self.cookies=http.cookiejar.CookieJar()
  if fingerprint:
   fingerprint=fingerprint.replace(':','').lower()
   if not re.fullmatch(r'[a-f0-9]{64}',fingerprint):raise ValueError('Certificate fingerprint must contain 64 hexadecimal characters')
  transport=PinnedHandler(fingerprint) if fingerprint else urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=ca))
  self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPCookieProcessor(self.cookies),transport)
 def _request(self,path,body=None):
  headers={'Accept':'application/json'}
  if self.csrf:headers['X-CSRF-Token']=self.csrf
  if body is not None:headers['Content-Type']='application/json'
  req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
  with self.opener.open(req,timeout=30) as response:
   data=response.read(8000001)
   if len(data)>8000000:raise ValueError('UniFi response exceeds import limit')
   self.csrf=response.headers.get('X-CSRF-Token') or self.csrf
   result=json.loads(data)
   if not isinstance(result,dict) or result.get('meta',{}).get('rc','ok')!='ok':raise ValueError('UniFi API rejected the request')
   return result
 def login(self):
  self.csrf='';self.cookies.clear()
  self._request('/api/auth/login' if self.mode=='os' else '/api/login',{'username':self.username,'password':self.password,'remember':False})
  if not self.csrf:
   for cookie in self.cookies:
    if cookie.name=='TOKEN':
     try:
      payload=cookie.value.split('.')[1];value=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4))).get('csrfToken')
      if isinstance(value,str):self.csrf=value
     except (ValueError,IndexError,TypeError):pass
 def get(self,suffix):
  if suffix not in ('stat/device','stat/sta','rest/user','rest/networkconf'):raise ValueError('Unsupported read-only inventory endpoint')
  prefix='/proxy/network/api/s/' if self.mode=='os' else '/api/s/'
  for attempt in range(2):
   try:
    result=self._request(prefix+self.site+'/'+suffix);items=result.get('data')
    if not isinstance(items,list) or len(items)>20000:raise ValueError('Invalid or excessive UniFi inventory')
    return items
   except urllib.error.HTTPError as error:
    if error.code!=401 or attempt:raise ValueError('UniFi request failed (HTTP '+str(error.code)+')') from None
    self.login()
