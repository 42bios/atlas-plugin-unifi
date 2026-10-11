import base64,http.cookiejar,io,json,sys,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'worker'))
from api import Client
class Response:
 def __init__(self,data,headers=None):self.data=json.dumps(data).encode();self.headers=headers or {}
 def read(self,limit):return self.data[:limit]
 def __enter__(self):return self
 def __exit__(self,*args):pass
class ApiTests(unittest.TestCase):
 def test_login_and_site_paths(self):
  for mode,path in [('os','/api/auth/login'),('classic','/api/login')]:
   client=Client('https://unifi.example','user','secret',mode=mode)
   with patch.object(client.opener,'open',return_value=Response({'meta':{'rc':'ok'}},{'X-CSRF-Token':'csrf'})) as call:
    client.login();req=call.call_args.args[0];self.assertTrue(req.full_url.endswith(path));self.assertEqual(req.get_method(),'POST')
   with patch.object(client.opener,'open',return_value=Response({'data':[]})) as call:
    client.get('stat/device');req=call.call_args.args[0]
    self.assertEqual(req.get_method(),'GET');self.assertEqual(req.get_header('X-csrf-token'),'csrf')
    self.assertIn('/proxy/network/' if mode=='os' else '/api/s/',req.full_url)
 def test_auth_retry_is_bounded(self):
  client=Client('https://unifi.example','user','secret')
  error=urllib.error.HTTPError('https://unifi.example',401,'Unauthorized',{},None)
  with patch.object(client,'_request',side_effect=[error,{'data':[]}]),patch.object(client,'login') as login:
   self.assertEqual(client.get('stat/device'),[]);login.assert_called_once()
  with patch.object(client,'_request',side_effect=error),patch.object(client,'login') as login:
   with self.assertRaises(ValueError):client.get('stat/device')
   login.assert_called_once()
 def test_invalid_envelope_and_controls_rejected(self):
  client=Client('https://unifi.example','user','secret')
  with patch.object(client.opener,'open',return_value=Response({'meta':{'rc':'error'},'data':[]})):
   with self.assertRaises(ValueError):client.get('stat/device')
  with self.assertRaises(ValueError):client.get('cmd/devmgr')
 def test_requires_verified_https_origin(self):
  for url in ['http://unifi.example','https://user:secret@unifi.example','https://unifi.example/path']:
   with self.assertRaises(ValueError):Client(url,'user','secret')
 def test_jwt_csrf_fallback(self):
  client=Client('https://unifi.example','user','secret');payload=base64.urlsafe_b64encode(json.dumps({'csrfToken':'fallback'}).encode()).decode().rstrip('=')
  cookie=http.cookiejar.Cookie(0,'TOKEN','header.'+payload+'.signature',None,False,'unifi.example',False,False,'/',True,True,None,True,None,None,{})
  def login(*args):client.cookies.set_cookie(cookie);return {}
  with patch.object(client,'_request',side_effect=login):client.login()
  self.assertEqual(client.csrf,'fallback')

class PinTests(unittest.TestCase):
 def test_wrong_pin_closes_before_sending_credentials(self):
  from api import PinnedConnection
  import hashlib,http.client
  from unittest.mock import MagicMock
  conn=PinnedConnection('unifi.example',fingerprint='a'*64);sock=MagicMock();sock.getpeercert.return_value=b'wrong-certificate';conn.sock=sock
  with patch.object(http.client.HTTPSConnection,'connect'),patch.object(conn,'close') as close:
   with self.assertRaises(Exception):conn.connect()
   close.assert_called_once();sock.sendall.assert_not_called()
 def test_matching_certificate_pin(self):
  from api import PinnedConnection
  import hashlib,http.client
  from unittest.mock import MagicMock
  cert=b'test-certificate';conn=PinnedConnection('unifi.example',fingerprint=hashlib.sha256(cert).hexdigest());conn.sock=MagicMock();conn.sock.getpeercert.return_value=cert
  with patch.object(http.client.HTTPSConnection,'connect'),patch.object(conn,'close') as close:
   conn.connect();close.assert_not_called()
 def test_malformed_pin_rejected(self):
  with self.assertRaises(ValueError):Client('https://unifi.example','user','secret',fingerprint='not-a-pin')
